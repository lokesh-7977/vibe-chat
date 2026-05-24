from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


Intent = Literal[
    "translate_message",
    "summarize_youtube",
    "summarize_website",
    "summarize_audio",
    "summarize_channel",
    "rag_question_answering",
    "unknown",
]


class SourceDocument(BaseModel):
    source_type: str = Field(min_length=1)
    source_id: str | None
    title: str | None
    url: str | None
    content: str = Field(min_length=1)
    meta: dict[str, Any] | None = None


class RetrievedSource(BaseModel):
    kind: str = Field(min_length=1)
    id: str = Field(min_length=1)
    snippet: str = Field(min_length=1)
    url: str | None = None
