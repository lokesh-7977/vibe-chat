from __future__ import annotations

from app.ai.prompts.base import ChatPrompt
from app.ai.prompts.base import ChatMessage
from app.ai.prompts.summarization.youtube.few_shot import few_shot_youtube_summary_examples


def build_youtube_summary_prompt(*, url: str, transcript: str, user_prompt: str | None) -> ChatPrompt:
    system = (
        "You are a concise assistant.\n"
        "Rules:\n"
        "- Summarize ONLY what is in the transcript.\n"
        "- Prefer: TL;DR + bullet points.\n"
        "- If transcript is incomplete, say so.\n"
    )
    extra = f"\n\nUser request:\n{user_prompt.strip()}" if user_prompt and user_prompt.strip() else ""
    user = f"Summarize this YouTube content.\n\nURL: {url}\n\nTranscript:\n{transcript}{extra}"

    messages: list[ChatMessage] = [ChatMessage(role="system", content=system)]
    messages.extend(few_shot_youtube_summary_examples())
    messages.append(ChatMessage(role="user", content=user))
    return ChatPrompt(messages=messages, meta={"intent": "summarize_youtube"})
