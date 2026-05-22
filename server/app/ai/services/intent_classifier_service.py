from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field

from app.ai.types import Intent


class IntentResult(BaseModel):
    intent: Intent
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    signals: dict[str, Any]


class IntentClassifierService:
    """
    Lightweight intent classifier.

    Production note: you can swap this for an LLM-based classifier later; this
    implementation is deterministic and fast.
    """

    _youtube_re = re.compile(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/", re.I)
    _url_re = re.compile(r"https?://\S+", re.I)

    def classify(
        self,
        *,
        action: str,
        user_input: str,
        target_language: str | None,
        message_id: str | None,
    ) -> IntentResult:
        normalized_action = (action or "auto").strip().lower()
        text = (user_input or "").strip()
        lower = text.lower()
        signals: dict[str, Any] = {
            "action": normalized_action,
            "has_message_id": bool(message_id),
            "has_target_language": bool(target_language),
            "detected_url": None,
            "url_type": None,
            "matched_keywords": [],
        }

        if normalized_action in {
            "translate_message",
            "summarize_youtube",
            "summarize_website",
            "summarize_audio",
            "rag_question_answering",
        }:
            return IntentResult(
                intent=normalized_action,
                confidence=1.0,
                reason="Explicit action provided",
                signals=signals,
            )

        # auto mode heuristics
        if target_language or ("translate" in lower and message_id):
            if "translate" in lower:
                signals["matched_keywords"].append("translate")
            return IntentResult(
                intent="translate_message",
                confidence=0.9,
                reason="Translate keywords/target_language",
                signals=signals,
            )

        url_match = self._url_re.search(text)
        if url_match:
            url = url_match.group(0)
            signals["detected_url"] = url
            if self._youtube_re.search(url):
                signals["url_type"] = "youtube"
                return IntentResult(
                    intent="summarize_youtube",
                    confidence=0.95,
                    reason="Detected YouTube URL",
                    signals=signals,
                )
            if any(ext in lower for ext in [".mp3", ".wav", ".m4a", ".ogg", ".webm"]):
                signals["url_type"] = "audio"
                return IntentResult(
                    intent="summarize_audio",
                    confidence=0.9,
                    reason="Detected audio URL extension",
                    signals=signals,
                )
            signals["url_type"] = "website"
            return IntentResult(
                intent="summarize_website",
                confidence=0.85,
                reason="Detected website URL",
                signals=signals,
            )

        # Default to RAG Q&A.
        if text:
            return IntentResult(
                intent="rag_question_answering",
                confidence=0.7,
                reason="Default to RAG for plain text",
                signals=signals,
            )

        return IntentResult(
            intent="unknown",
            confidence=0.0,
            reason="No input",
            signals=signals,
        )
