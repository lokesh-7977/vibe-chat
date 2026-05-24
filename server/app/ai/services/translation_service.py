from __future__ import annotations

from collections.abc import AsyncGenerator

from app.ai.prompts.translation.prompt import build_translation_prompt
from app.core.config import get_settings


class TranslationService:
    def __init__(self, groq: object) -> None:
        self.groq = groq

    @staticmethod
    def _looks_untranslated(source: str, translation: str, *, target_language: str) -> bool:
        src = (source or "").strip()
        out = (translation or "").strip()
        if not src or not out:
            return True
        if src == out:
            return True

        # If the user asked for a non-Latin script, require at least one char from that block.
        lang = (target_language or "").strip().lower()
        if "telugu" in lang:
            return not any("\u0C00" <= ch <= "\u0C7F" for ch in out)
        if "hindi" in lang or "devanagari" in lang:
            return not any("\u0900" <= ch <= "\u097F" for ch in out)
        return False

    @staticmethod
    def _validate(source: str, translation: str) -> None:
        if not translation.strip():
            raise RuntimeError("Translation model returned an empty response")
        src_words = len(source.strip().split())
        tgt_words = len(translation.strip().split())
        if src_words > 0 and tgt_words / src_words > 5.0:
            raise RuntimeError(
                f"Translation rejected: output is {tgt_words / src_words:.1f}x longer than input"
            )

    async def stream_translation(
        self,
        *,
        text: str,
        target_language: str,
        user_prompt: str | None,
    ) -> AsyncGenerator[str, None]:
        prompt = build_translation_prompt(
            text=text,
            target_language=target_language,
            user_prompt=user_prompt,
        )

        settings = get_settings()

        async def _collect(model: str | None) -> str:
            out = ""
            async for token in self.groq.stream_chat(
                messages=prompt.messages,
                temperature=0.0,
                model=model,
            ):
                out += token
            return out

        # Prefer the dedicated translate model; fall back if it's not available or doesn't translate.
        try:
            buffer = await _collect(settings.nvapi_translate_model or None)
        except RuntimeError as exc:
            msg = str(exc)
            if " 404" not in msg and "Not found" not in msg:
                raise
            buffer = await _collect(None)

        if self._looks_untranslated(text, buffer, target_language=target_language):
            fallback_model = settings.nvapi_translate_fallback_model or settings.nvapi_chat_model
            buffer = await _collect(fallback_model)

        self._validate(text, buffer)
        yield buffer
