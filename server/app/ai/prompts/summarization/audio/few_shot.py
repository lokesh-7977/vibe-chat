from __future__ import annotations

from app.ai.prompts.base import ChatMessage


def few_shot_audio_summary_examples() -> list[ChatMessage]:
    return [
        ChatMessage(
            role="user",
            content="Summarize this audio.\n\nURL: https://example.com/audio.mp3\n\nTranscript:\nWe agreed to ship the feature on Friday and assign tests to Alex...",
        ),
        ChatMessage(
            role="assistant",
            content="Summary: The team agreed to ship on Friday.\n\nKey points:\n- Release target: Friday.\n- Alex owns adding tests.\n",
        ),
    ]
