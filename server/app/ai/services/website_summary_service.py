from __future__ import annotations

from collections.abc import AsyncGenerator

from app.ai.services.groq_client import GroqChatService
from app.ai.services.web_extractor import fetch_readable_text


class WebsiteSummaryService:
    def __init__(self, groq: GroqChatService) -> None:
        self.groq = groq

    async def stream_summary(self, *, url: str) -> AsyncGenerator[str, None]:
        text = await fetch_readable_text(url)
        system = "You are a concise assistant. Summarize the article clearly with key points."
        user = f"Summarize this webpage content:\n\nURL: {url}\n\nContent:\n{text}"
        async for token in self.groq.stream_chat(system=system, user=user):
            yield token

