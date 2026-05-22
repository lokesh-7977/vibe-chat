from __future__ import annotations

import json
from collections.abc import AsyncGenerator, AsyncIterable
from typing import Any, Literal

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field


SseEventName = Literal[
    "intent_detected",
    "source_loading",
    "retrieval_started",
    "retrieval_completed",
    "generation_started",
    "token",
    "generation_completed",
    "error",
]


class SseEnvelope(BaseModel):
    event: SseEventName
    data: dict[str, Any] = Field(default_factory=dict)


def sse(event: SseEventName, data: dict[str, Any]) -> bytes:
    envelope = SseEnvelope(event=event, data=data)
    payload = json.dumps(jsonable_encoder(envelope.data), ensure_ascii=False)
    return f"event: {envelope.event}\ndata: {payload}\n\n".encode("utf-8")


class StreamingCollector(BaseModel):
    full_text: str = ""

    def add_token(self, token: str) -> None:
        self.full_text += token


async def stream_tokens_as_sse(
    token_stream: AsyncIterable[str],
    collector: StreamingCollector,
) -> AsyncGenerator[bytes, None]:
    async for token in token_stream:
        collector.add_token(token)
        yield sse("token", {"content": token})
