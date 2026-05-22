from __future__ import annotations

from app.ai.prompts.base import ChatPrompt
from app.ai.prompts.base import ChatMessage
from app.ai.prompts.summarization.website.few_shot import few_shot_website_summary_examples


def build_website_summary_prompt(*, url: str, content: str, user_prompt: str | None) -> ChatPrompt:
    system = (
        "You are a concise assistant.\n"
        "Rules:\n"
        "- Summarize ONLY what is in the provided content.\n"
        "- Prefer: TL;DR + key points + action items (if any).\n"
        "- Do not invent details.\n"
    )
    extra = f"\n\nUser request:\n{user_prompt.strip()}" if user_prompt and user_prompt.strip() else ""
    user = f"Summarize this webpage/article.\n\nURL: {url}\n\nContent:\n{content}{extra}"

    messages: list[ChatMessage] = [ChatMessage(role="system", content=system)]
    messages.extend(few_shot_website_summary_examples())
    messages.append(ChatMessage(role="user", content=user))
    return ChatPrompt(messages=messages, meta={"intent": "summarize_website"})
