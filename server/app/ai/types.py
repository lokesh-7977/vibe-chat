from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


Intent = Literal[
    "translate_message",
    "summarize_youtube",
    "summarize_website",
    "summarize_audio",
    "rag_question_answering",
    "unknown",
]


@dataclass(frozen=True)
class SourceDocument:
    source_type: str
    source_id: str | None
    title: str | None
    url: str | None
    content: str
    meta: dict[str, Any] | None = None

