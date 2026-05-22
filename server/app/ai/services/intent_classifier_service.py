from __future__ import annotations

import re
from dataclasses import dataclass

from app.ai.types import Intent


@dataclass(frozen=True)
class IntentResult:
    intent: Intent
    reason: str


class IntentClassifierService:
    """
    Lightweight intent classifier.

    Production note: you can swap this for an LLM-based classifier later; this
    implementation is deterministic and fast.
    """

    _youtube_re = re.compile(r"(https?://)?(www\\.)?(youtube\\.com|youtu\\.be)/", re.I)
    _url_re = re.compile(r"https?://\\S+", re.I)

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

        if normalized_action in {
            "translate_message",
            "summarize_youtube",
            "summarize_website",
            "summarize_audio",
            "rag_question_answering",
        }:
            return IntentResult(intent=normalized_action, reason="Explicit action provided")

        # auto mode heuristics
        if target_language or ("translate" in lower and message_id):
            return IntentResult(intent="translate_message", reason="Translate keywords/target_language")

        url_match = self._url_re.search(text)
        if url_match:
            url = url_match.group(0)
            if self._youtube_re.search(url):
                return IntentResult(intent="summarize_youtube", reason="Detected YouTube URL")
            if any(ext in lower for ext in [".mp3", ".wav", ".m4a", ".ogg", ".webm"]):
                return IntentResult(intent="summarize_audio", reason="Detected audio URL extension")
            return IntentResult(intent="summarize_website", reason="Detected website URL")

        # Default to RAG Q&A.
        if text:
            return IntentResult(intent="rag_question_answering", reason="Default to RAG for plain text")

        return IntentResult(intent="unknown", reason="No input")

