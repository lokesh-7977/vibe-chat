from __future__ import annotations

from app.ai.prompts.base import ChatMessage


def few_shot_rag_qa_examples() -> list[ChatMessage]:
    return [
        ChatMessage(
            role="user",
            content="Question:\nWhat did we decide about the release date?\n\nContext:\n[1] (channel_message) Let's ship on Friday.\n\nAllowed sources:\n[1] channel_message:MSGID\n\nReturn the answer followed by:\n\nSources:\n- <source>\n",
        ),
        ChatMessage(
            role="assistant",
            content="We decided to ship on Friday.\n\nSources:\n- channel_message:MSGID",
        ),
    ]
