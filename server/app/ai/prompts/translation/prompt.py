from __future__ import annotations

from app.ai.prompts.base import ChatPrompt
from app.ai.prompts.base import ChatMessage
from app.ai.prompts.translation.few_shot import few_shot_translation_examples


def build_translation_prompt(*, text: str, target_language: str, user_prompt: str | None) -> ChatPrompt:
    system = (
        "You are a professional translator.\n"
        "Rules:\n"
        "- Preserve meaning, tone, names, and technical terms.\n"
        "- Do not add commentary, explanations, or notes.\n"
        "- Output ONLY the translation.\n"
    )

    extra = f"\n\nUser request (style constraints only):\n{user_prompt.strip()}" if user_prompt and user_prompt.strip() else ""
    user = f"Translate to {target_language}:\n\n{text}{extra}"

    messages: list[ChatMessage] = [ChatMessage(role="system", content=system)]
    messages.extend(few_shot_translation_examples())
    messages.append(ChatMessage(role="user", content=user))
    return ChatPrompt(messages=messages, meta={"intent": "translate_message"})
