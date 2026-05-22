from __future__ import annotations

from app.ai.prompts.base import ChatMessage


def few_shot_youtube_summary_examples() -> list[ChatMessage]:
    return [
        ChatMessage(
            role="user",
            content="Summarize this YouTube content.\n\nURL: https://youtu.be/VIDEO\n\nTranscript:\nWe discuss three deployment strategies: blue/green, canary, and rolling updates...",
        ),
        ChatMessage(
            role="assistant",
            content="TL;DR: The video compares blue/green, canary, and rolling deployments.\n\nKey points:\n- Blue/green: instant rollback, needs duplicate capacity.\n- Canary: gradual rollout with metrics gates.\n- Rolling: simplest, slower rollback.\n",
        ),
    ]
