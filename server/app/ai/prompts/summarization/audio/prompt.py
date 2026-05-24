from __future__ import annotations

from app.ai.prompts.base import ChatPrompt
from app.ai.prompts.base import ChatMessage
from app.ai.prompts.summarization.audio.few_shot import few_shot_audio_summary_examples


def build_audio_summary_prompt(*, url: str, transcript: str, user_prompt: str | None) -> ChatPrompt:
    system = (
        "You are a concise, grounded assistant. Your ONLY source of truth is the transcript below.\n"
        "STRICT RULES:\n"
        "- Summarize ONLY what is explicitly stated in the transcript. Never invent speakers, events, or details.\n"
        "- If the transcript is incomplete or ambiguous, state that limitation. Do not fabricate.\n"
        "- Prefer: summary + key points + action items.\n"
        "- Every factual claim must be directly traceable to a line in the transcript.\n"
    )
    extra = f"\n\nUser request:\n{user_prompt.strip()}" if user_prompt and user_prompt.strip() else ""
    user = f"Summarize this audio.\n\nURL: {url}\n\nTranscript:\n{transcript}{extra}"

    messages: list[ChatMessage] = [ChatMessage(role="system", content=system)]
    messages.extend(few_shot_audio_summary_examples())
    messages.append(ChatMessage(role="user", content=user))
    return ChatPrompt(messages=messages, meta={"intent": "summarize_audio"})
