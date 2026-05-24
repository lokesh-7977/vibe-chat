from __future__ import annotations

from collections.abc import AsyncGenerator

from app.ai.services.url_fetcher import fetch_bytes_from_url
from app.ai.prompts.summarization.audio.prompt import build_audio_summary_prompt


class AudioSummaryService:
    def __init__(self, groq_audio: object, groq_chat: object) -> None:
        self.groq_audio = groq_audio
        self.groq_chat = groq_chat

    async def stream_summary_from_url(self, *, url: str, user_prompt: str | None) -> AsyncGenerator[str, None]:
        audio_bytes, content_type = await fetch_bytes_from_url(url)
        transcript = await self.groq_audio.transcribe(audio_bytes=audio_bytes, content_type=content_type)
        prompt = build_audio_summary_prompt(url=url, transcript=transcript, user_prompt=user_prompt)
        async for token in self.groq_chat.stream_chat(messages=prompt.messages, temperature=0.0):
            yield token
