from __future__ import annotations

from app.ai.prompts.base import ChatMessage


def few_shot_website_summary_examples() -> list[ChatMessage]:
    return [
        ChatMessage(
            role="user",
            content="Summarize this webpage/article.\n\nURL: https://example.com/article\n\nContent:\nThis article explains why caching improves performance and how to invalidate caches safely...",
        ),
        ChatMessage(
            role="assistant",
            content="TL;DR: Caching reduces latency but requires careful invalidation.\n\nKey points:\n- Cache where reads dominate.\n- Use TTLs + explicit invalidation.\n- Monitor hit rate and stale content risk.\n",
        ),
    ]
