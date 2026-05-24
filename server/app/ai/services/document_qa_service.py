from __future__ import annotations

from app.ai.prompts.base import ChatMessage
from app.ai.services.nv_client import NvChatService


class DocumentQaService:
    def __init__(self) -> None:
        self.chat = NvChatService()

    def _build_messages(self, *, text: str, file_name: str, question: str) -> list[ChatMessage]:
        q = (question or "").strip()
        clipped = (text or "").strip()
        if len(clipped) > 14_000:
            clipped = clipped[:14_000] + "\n\n[TRUNCATED]"

        return [
            ChatMessage(
                role="system",
                content=(
                    "You answer questions using ONLY the provided DOCUMENT TEXT.\n"
                    "STRICT RULES (no hallucination):\n"
                    "- Do NOT use outside knowledge.\n"
                    "- If the answer is not explicitly supported by the DOCUMENT TEXT, output exactly:\n"
                    "  Insufficient information in the document.\n"
                    "- Do not invent section numbers, question numbers, titles, or quotes.\n"
                    "- Prefer exact wording from the text.\n"
                    "\n"
                    "OUTPUT FORMAT (Markdown):\n"
                    "Return a single Markdown answer that reads naturally.\n"
                    "- Use headings/bullets only if it improves clarity.\n"
                    "- Bold key terms when helpful.\n"
                    "- Do NOT include any confidence rating.\n"
                ),
            ),
            ChatMessage(
                role="user",
                content=f"FILE: {file_name}\n\nQUESTION:\n{q}\n\nDOCUMENT TEXT:\n{clipped}",
            ),
        ]

    async def stream(self, *, text: str, file_name: str, question: str):
        messages = self._build_messages(text=text, file_name=file_name, question=question)
        async for token in self.chat.stream_chat(messages=messages, temperature=0.2):
            yield token
