from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class AIActionStreamRequest(BaseModel):
    action: str = Field(default="auto")
    message_id: UUID | None = None
    input: str = Field(default="")
    target_language: str | None = None

