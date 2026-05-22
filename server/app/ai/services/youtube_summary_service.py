from __future__ import annotations

from collections.abc import AsyncGenerator

from app.ai.services.groq_client import GroqChatService
from app.ai.services.youtube_transcript import fetch_youtube_transcript_text
from app.ai.prompts.summarization.youtube.prompt import build_youtube_summary_prompt


class YouTubeSummaryService:
    def __init__(self, groq: GroqChatService) -> None:
        self.groq = groq

    async def stream_summary(self, *, url: str, user_prompt: str | None) -> AsyncGenerator[str, None]:
        transcript = await fetch_youtube_transcript_text(url)
        prompt = build_youtube_summary_prompt(url=url, transcript=transcript, user_prompt=user_prompt)
        async for token in self.groq.stream_chat(messages=prompt.messages, temperature=0.2):
            yield token
