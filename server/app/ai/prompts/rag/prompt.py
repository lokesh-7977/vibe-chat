from __future__ import annotations

from app.ai.prompts.base import ChatPrompt
from app.ai.prompts.base import ChatMessage
from app.ai.prompts.rag.few_shot import few_shot_rag_qa_examples


def build_rag_qa_prompt(*, question: str, context: str, allowed_sources: str, user_prompt: str | None = None) -> ChatPrompt:
    system = (
        "You answer using ONLY the provided context. No outside knowledge permitted.\n"
        "STRICT RULES:\n"
        "- If the answer is NOT in the context, say: \"I don't have enough information to answer this question.\"\n"
        "- Do NOT use any outside knowledge, training data, or assumptions.\n"
        "- Every factual statement MUST end with a source citation from the 'Allowed sources' list.\n"
        "- End with a 'Sources:' section listing ONLY the source IDs you actually used.\n"
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
