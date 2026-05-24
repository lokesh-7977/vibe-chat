from __future__ import annotations

import json

from app.ai.prompts.base import ChatMessage


class GrammarCheckService:
    def __init__(self, chat: object) -> None:
        self.chat = chat

    async def check(self, text: str) -> dict:
        prompt = [
            ChatMessage(
                role="system",
                content=(
                    "You are a grammar and language detection assistant. "
                    "Given user input, determine if it is English or another language.\n"
                    "- If English with grammar/spelling mistakes: correct them.\n"
                    "- If English without mistakes: return no correction.\n"
                    "- If not English: flag it.\n\n"
                    'Respond in JSON only with this exact format:\n'
                    '{"language": "en"|"other", "has_errors": bool, "corrected_text": str|null, "message": str|null}\n\n'
                    'Examples:\n'
                    'Input: "I goes to school" -> {"language": "en", "has_errors": true, "corrected_text": "I go to school.", "message": null}\n'
                    'Input: "I am going to school" -> {"language": "en", "has_errors": false, "corrected_text": null, "message": null}\n'
                    'Input: "Je vais à l\'école" -> {"language": "other", "has_errors": false, "corrected_text": null, "message": "Only English is supported. Please type in English."}'
                ),
            ),
            ChatMessage(role="user", content=text),
        ]
        resp = await self.chat.chat(messages=prompt, temperature=0.1)
        content = (resp.get("content") or "").strip()
        content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"language": "en", "has_errors": False, "corrected_text": None, "message": None}
