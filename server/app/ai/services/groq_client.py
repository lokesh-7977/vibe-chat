from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

from groq import Groq

from app.core.config import get_settings
from app.ai.prompts.base import ChatMessage


class GroqChatService:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")
        self._client = Groq(api_key=settings.groq_api_key)
        self._model = settings.groq_chat_model

    @staticmethod
    def _clamp_temperature(temp: float | None) -> float:
        # Always keep temperature in [0.1, 0.3] to reduce hallucinations.
        if temp is None:
            return 0.2
        return max(0.1, min(0.3, float(temp)))

    async def stream_chat(
        self,
        *,
        messages: list[ChatMessage],
        temperature: float | None = None,
    ) -> AsyncGenerator[str, None]:
        queue: asyncio.Queue[str | None] = asyncio.Queue()
        error_queue: asyncio.Queue[BaseException | None] = asyncio.Queue()
        temp = self._clamp_temperature(temperature)

        def _produce() -> None:
            try:
                stream = self._client.chat.completions.create(
                    model=self._model,
                    messages=[m.model_dump() for m in messages],
                    temperature=temp,
                    stream=True,
                )
                for chunk in stream:
                    delta = getattr(chunk.choices[0].delta, "content", None)
                    if delta:
                        asyncio.run_coroutine_threadsafe(queue.put(delta), loop)
                asyncio.run_coroutine_threadsafe(queue.put(None), loop)
                asyncio.run_coroutine_threadsafe(error_queue.put(None), loop)
            except BaseException as exc:
                asyncio.run_coroutine_threadsafe(queue.put(None), loop)
                asyncio.run_coroutine_threadsafe(error_queue.put(exc), loop)

        loop = asyncio.get_running_loop()
        producer_task = asyncio.create_task(asyncio.to_thread(_produce))

        while True:
            token = await queue.get()
            if token is None:
                break
            yield token

        err = await error_queue.get()
        if err is not None:
            raise err

        await producer_task


class GroqAudioService:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")
        self._client = Groq(api_key=settings.groq_api_key)
        self._model = settings.groq_whisper_model

    async def transcribe(self, *, audio_bytes: bytes, content_type: str | None) -> str:
        def _run() -> str:
            # groq-python supports file tuples: (filename, bytes, content_type)
            file = ("audio", audio_bytes, content_type or "application/octet-stream")
            result = self._client.audio.transcriptions.create(
                file=file,
                model=self._model,
                response_format="text",
            )
            return str(result)

        return await asyncio.to_thread(_run)
