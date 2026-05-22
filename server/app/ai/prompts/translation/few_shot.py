from __future__ import annotations

from app.ai.prompts.base import ChatMessage


def few_shot_translation_examples() -> list[ChatMessage]:
    # Keep examples short to reduce prompt bloat.
    return [
        ChatMessage(role="user", content="Translate to Telugu:\n\nHello, how are you?"),
        ChatMessage(role="assistant", content="హలో, మీరు ఎలా ఉన్నారు?"),
    ]
