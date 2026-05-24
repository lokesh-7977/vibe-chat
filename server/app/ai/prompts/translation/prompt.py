from __future__ import annotations

from app.ai.prompts.base import ChatMessage, ChatPrompt
from app.ai.prompts.translation.few_shot import few_shot_translation_examples


def build_translation_prompt(*, text: str, target_language: str, user_prompt: str | None) -> ChatPrompt:
    system = (
        "You are a machine translation engine. Translate the user's text into the requested target language.\n"
        "STRICT RULES:\n"
        "- Translate ALL words into the target language. DO NOT leave any words in English.\n"
        "- Output ONLY the translated text — nothing else, no explanations, no labels.\n"
        "- Keep names, brands, URLs, emails, numbers, and code as-is.\n"
    )

    extra = f"\n\nStyle constraints only:\n{user_prompt.strip()}" if user_prompt and user_prompt.strip() else ""
    user = (
        f"Target language: {target_language}\n"
        "Translate the text below. Output ONLY the translated text — no labels, quotes, or notes:\n\n"
        f"{text}{extra}"
    )

    messages: list[ChatMessage] = [ChatMessage(role="system", content=system)]
    messages.extend(few_shot_translation_examples())
    messages.append(ChatMessage(role="user", content=user))
    return ChatPrompt(messages=messages, meta={"intent": "translate_message"})
