from __future__ import annotations

from collections.abc import AsyncGenerator

from app.ai.services.groq_client import GroqChatService
from app.ai.services.web_extractor import fetch_readable_text
from app.ai.prompts.summarization.website.prompt import build_website_summary_prompt


class WebsiteSummaryService:
    def __init__(self, groq: GroqChatService) -> None:
        self.groq = groq

    async def stream_summary(self, *, url: str, user_prompt: str | None) -> AsyncGenerator[str, None]:
        text = await fetch_readable_text(url)
        prompt = build_website_summary_prompt(url=url, content=text, user_prompt=user_prompt)
        async for token in self.groq.stream_chat(messages=prompt.messages, temperature=0.2):
            yield token
