from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field, field_validator


ALLOWED_LANGUAGES = {"telugu", "english", "hindi"}


class AIActionStreamRequest(BaseModel):
    action: str = Field(default="auto")
    message_id: UUID | None = None
    input: str = Field(default="")
    target_language: str | None = None
    private_response: bool | None = None
    history: list[dict] | None = None

    @field_validator("target_language")
    @classmethod
    def validate_language(cls, v: str | None) -> str | None:
        if v is not None and v.strip().lower() not in ALLOWED_LANGUAGES:
            allowed = ", ".join(sorted(ALLOWED_LANGUAGES))
            raise ValueError(f"Unsupported language '{v}'. Allowed: {allowed}")
        return v

    @field_validator("history")
    @classmethod
    def validate_history(cls, v: list[dict] | None) -> list[dict] | None:
        if v is None:
            return None
        # Keep payload bounded.
        if len(v) > 40:
            v = v[-40:]
        cleaned: list[dict] = []
        for item in v:
            role = str(item.get("role", "")).strip().lower()
            content = str(item.get("content", "")).strip()
            if role not in {"user", "assistant"}:
                continue
            if not content:
                continue
            cleaned.append({"role": role, "content": content[:4000]})
        return cleaned
