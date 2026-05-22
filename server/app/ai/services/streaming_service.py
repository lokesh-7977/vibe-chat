from __future__ import annotations

import json
from collections.abc import AsyncGenerator, AsyncIterable
from dataclasses import dataclass
from typing import Any, Literal


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


def sse(event: SseEventName, data: dict[str, Any]) -> bytes:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n".encode("utf-8")


@dataclass
class StreamingCollector:
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

