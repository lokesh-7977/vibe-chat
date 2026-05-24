from __future__ import annotations

import re

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound


def _extract_video_id(url: str) -> str:
    m = re.search(r"youtu\.be/([A-Za-z0-9_-]{6,})", url)
    if m:
        return m.group(1)
    m = re.search(r"v=([A-Za-z0-9_-]{6,})", url)
    if m:
        return m.group(1)
    raise RuntimeError("Unable to extract YouTube video id")


def _pick_transcript_language(video_id: str) -> list[str]:
    try:
        listing = YouTubeTranscriptApi().list(video_id)
        available = listing._manually_created_transcripts | listing._generated_transcripts
        candidates = ["en", "en-US", "en-GB", "hi", "auto"]
        for code in candidates:
            if code in available:
                return [code]
        return [next(iter(available))]
    except Exception:
        return ["en", "hi"]


async def fetch_youtube_transcript_text(url: str) -> str:
    try:
        from langchain_community.document_loaders import YoutubeLoader

        loader = YoutubeLoader.from_youtube_url(url, add_video_info=False)
        docs = loader.load()
        text = "\n\n".join(d.page_content for d in docs if getattr(d, "page_content", None))
        if text.strip():
            return text[:200_000]
    except Exception:
        pass

    video_id = _extract_video_id(url)
    languages = _pick_transcript_language(video_id)
    try:
        transcript = YouTubeTranscriptApi().fetch(video_id, languages=languages)
    except NoTranscriptFound as exc:
        raise RuntimeError("Unable to fetch YouTube transcript") from exc

    text = "\n".join(s.text for s in transcript if s.text)
    if not text.strip():
        raise RuntimeError("Empty transcript")
    return text[:200_000]
