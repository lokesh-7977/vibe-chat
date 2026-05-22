from __future__ import annotations

from collections.abc import AsyncGenerator

from app.ai.services.groq_client import GroqChatService


class TranslationService:
    def __init__(self, groq: GroqChatService) -> None:
        self.groq = groq

    async def stream_translation(
        self,
        *,
        text: str,
        target_language: str,
    ) -> AsyncGenerator[str, None]:
        system = (
            "You are a professional translator. Preserve meaning, tone, names, and technical terms. "
            "Do not add commentary. Output only the translation."
        )
        user = f"Translate to {target_language}:\n\n{text}"
        async for token in self.groq.stream_chat(system=system, user=user):
            yield token

