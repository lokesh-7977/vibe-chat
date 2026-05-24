from __future__ import annotations

from app.ai.prompts.base import ChatMessage
from app.ai.services.nv_client import NvChatService


class DocumentSummaryService:
    def __init__(self) -> None:
        self.chat = NvChatService()

    def _build_messages(self, *, text: str, file_name: str, user_prompt: str | None) -> list[ChatMessage]:
        prompt = (user_prompt or "").strip() or "Summarize this document and list clear next steps for the user."
        clipped = (text or "").strip()
        if len(clipped) > 12_000:
            clipped = clipped[:12_000] + "\n\n[TRUNCATED]"
        return [
            ChatMessage(
                role="system",
                content=(
                    "You summarize documents carefully with zero hallucination.\n"
                    "STRICT RULES:\n"
                    "- Use ONLY the provided DOCUMENT TEXT.\n"
                    "- Do NOT add, infer, or guess facts not explicitly present.\n"
                    "- If the DOCUMENT TEXT is incomplete or unclear, say so explicitly.\n"
                    "- Prefer quoting short phrases from the text when possible.\n"
                    "\n"
                    "OUTPUT FORMAT (Markdown):\n"
                    "**Summary**: One paragraph.\n"
                    "**Key topics**: 5-7 bullets, each grounded in the text.\n"
                    "**Next steps for user**: 5-7 bullets, actionable and specific.\n"
                    "\n"
                    ),
            ),
            ChatMessage(
                role="user",
                content=f"{prompt}\n\nFILE: {file_name}\n\nDOCUMENT TEXT:\n{clipped}",
            ),
        ]

    async def summarize(self, *, text: str, file_name: str, user_prompt: str | None) -> str:
        messages = self._build_messages(text=text, file_name=file_name, user_prompt=user_prompt)
        resp = await self.chat.chat(messages=messages, temperature=0.2)
        return (resp.get("content") or "").strip()

    async def stream(self, *, text: str, file_name: str, user_prompt: str | None):
        messages = self._build_messages(text=text, file_name=file_name, user_prompt=user_prompt)
        async for token in self.chat.stream_chat(messages=messages, temperature=0.2):
            yield token
