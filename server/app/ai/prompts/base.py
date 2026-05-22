from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


Role = Literal["system", "user", "assistant"]


class ChatMessage(BaseModel):
    role: Role
    content: str = Field(min_length=1)


class ChatPrompt(BaseModel):
    """
    A chat prompt with always-on few-shot examples.
    `messages` must be in the order the model should see them.
    """

    messages: list[ChatMessage]
    meta: dict[str, Any] | None = None
