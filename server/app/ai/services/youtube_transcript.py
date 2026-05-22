from __future__ import annotations

import re

from youtube_transcript_api import YouTubeTranscriptApi


def _extract_video_id(url: str) -> str:
    # supports youtu.be/<id> or youtube.com/watch?v=<id>
    m = re.search(r"youtu\\.be/([A-Za-z0-9_-]{6,})", url)
    if m:
        return m.group(1)
    m = re.search(r"v=([A-Za-z0-9_-]{6,})", url)
    if m:
        return m.group(1)
    raise RuntimeError("Unable to extract YouTube video id")


async def fetch_youtube_transcript_text(url: str) -> str:
    # Prefer LangChain loader when available.
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
    try:
        items = YouTubeTranscriptApi.get_transcript(video_id)
    except Exception as exc:
        raise RuntimeError("Unable to fetch YouTube transcript") from exc

    text = "\n".join(i.get("text", "") for i in items if i.get("text"))
    if not text.strip():
        raise RuntimeError("Empty transcript")
    return text[:200_000]
