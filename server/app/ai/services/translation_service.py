from __future__ import annotations

from collections.abc import AsyncGenerator

from app.ai.services.groq_client import GroqChatService
from app.ai.prompts.translation.prompt import build_translation_prompt


class TranslationService:
    def __init__(self, groq: GroqChatService) -> None:
        self.groq = groq

    async def stream_translation(
        self,
        *,
        text: str,
        target_language: str,
        user_prompt: str | None,
    ) -> AsyncGenerator[str, None]:
        prompt = build_translation_prompt(text=text, target_language=target_language, user_prompt=user_prompt)
        async for token in self.groq.stream_chat(messages=prompt.messages, temperature=0.2):
            yield token
