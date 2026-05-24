from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import HTTPException

import os

from app.ai.prompts.base import ChatMessage
from app.ai.services.nv_client import NvChatService


_VISION_MODEL = os.getenv("NVAPI_VISION_MODEL", "meta/llama-3.2-11b-vision-instruct")


class ImageSummaryService:
    def __init__(self) -> None:
        self.chat = NvChatService()

    async def summarize(self, *, image_url: str, user_prompt: str | None) -> str:
        prompt = (user_prompt or "").strip() or "Describe what is in this image directly. Max 150 words."
        messages = [
            ChatMessage(
                role="system",
                content=(
                    "You describe images directly and concisely. "
                    "State exactly what is visible: objects, people, text, setting, actions. "
                    "Max 150 words. No suggestions or next steps."
                ),
            ),
            ChatMessage(
                role="user",
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            ),
        ]
        try:
            resp = await self.chat.chat(messages=messages, temperature=0.2, model=_VISION_MODEL)
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc)[:200]) from exc
        return (resp.get("content") or "").strip()

    async def stream(
        self,
        *,
        image_url: str,
        user_prompt: str | None,
    ) -> AsyncGenerator[str, None]:
        prompt = (user_prompt or "").strip() or "Describe what is in this image directly. Max 150 words."
        messages = [
            ChatMessage(
                role="system",
                content=(
                    "You describe images directly and concisely. "
                    "State exactly what is visible: objects, people, text, setting, actions. "
                    "Max 150 words. No suggestions or next steps."
                ),
            ),
            ChatMessage(
                role="user",
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            ),
        ]
        async for token in self.chat.stream_chat(messages=messages, temperature=0.2, model=_VISION_MODEL):
            yield token

