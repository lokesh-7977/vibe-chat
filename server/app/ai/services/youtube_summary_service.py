from __future__ import annotations

from collections.abc import AsyncGenerator

from app.ai.services.groq_client import GroqChatService
from app.ai.services.youtube_transcript import fetch_youtube_transcript_text


class YouTubeSummaryService:
    def __init__(self, groq: GroqChatService) -> None:
        self.groq = groq

    async def stream_summary(self, *, url: str) -> AsyncGenerator[str, None]:
        transcript = await fetch_youtube_transcript_text(url)
        system = "You are a concise assistant. Summarize the content clearly with key points."
        user = f"Summarize this YouTube transcript:\n\nURL: {url}\n\nTranscript:\n{transcript}"
        async for token in self.groq.stream_chat(system=system, user=user):
            yield token

