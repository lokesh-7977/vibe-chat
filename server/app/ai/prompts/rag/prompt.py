from __future__ import annotations

from app.ai.prompts.base import ChatPrompt
from app.ai.prompts.base import ChatMessage
from app.ai.prompts.rag.few_shot import few_shot_rag_qa_examples


def build_rag_qa_prompt(*, question: str, context: str, allowed_sources: str, user_prompt: str | None = None) -> ChatPrompt:
    system = (
        "You answer using ONLY the provided context.\n"
        "Rules:\n"
        "- If the answer is not in context, say you don't know.\n"
        "- Do not use outside knowledge.\n"
        "- End with a 'Sources:' section listing only the source ids you used.\n"
    )
    extra = f"\n\nUser request:\n{user_prompt.strip()}" if user_prompt and user_prompt.strip() else ""
    user = (
        f"Question:\n{question}\n\n"
        f"Context:\n{context}\n\n"
        f"Allowed sources:\n{allowed_sources}{extra}\n\n"
        "Return the answer followed by:\n\nSources:\n- <source>\n- <source>\n"
    )

    messages: list[ChatMessage] = [ChatMessage(role="system", content=system)]
    messages.extend(few_shot_rag_qa_examples())
    messages.append(ChatMessage(role="user", content=user))
    return ChatPrompt(messages=messages, meta={"intent": "rag_question_answering"})
