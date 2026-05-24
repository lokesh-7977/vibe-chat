from __future__ import annotations

import re
from collections.abc import AsyncGenerator
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.orm import Session

import os

from app.ai.prompts.base import ChatMessage
from app.db.models.activity import Activity
from app.db.models.channel_summary import ChannelSummary
from app.storage.r2 import presign_get_object

_GENERATION_TEMPERATURE = 0.3
_IMAGE_PATTERN = re.compile(r"!\[.*?\]\(r2://([^)]+)\)")
_VISION_MODEL = os.getenv("NVAPI_VISION_MODEL", "meta/llama-3.2-11b-vision-instruct")


class ChannelSummaryService:
    def __init__(self, chat: object) -> None:
        self.chat = chat

    async def _describe_image(self, image_key: str) -> str:
        try:
            presigned = presign_get_object(object_key=image_key)
            img_messages = [
                ChatMessage(
                    role="system",
                    content="Describe what is visible in this image in 1-2 sentences. Focus on objects, people, text, and setting.",
                ),
                ChatMessage(
                    role="user",
                    content=[
                        {"type": "text", "text": "What is in this image?"},
                        {"type": "image_url", "image_url": {"url": presigned.view_url}},
                    ],
                ),
            ]
            resp = await self.chat.chat(messages=img_messages, temperature=0.2, model=_VISION_MODEL)
            return (resp.get("content") or "").strip()
        except Exception:
            return "[Image could not be analyzed]"

    async def _enrich_with_image_descriptions(self, messages: list[dict]) -> list[dict]:
        seen_keys: set[str] = set()
        for msg in messages:
            content = msg["content"]
            matches = _IMAGE_PATTERN.findall(content)
            for key in matches:
                if key not in seen_keys:
                    seen_keys.add(key)
                    description = await self._describe_image(key)
                    content = content.replace(f"![{key.split('/')[-1]}](r2://{key})", f"[Image: {description}]", 1)
                    content = content.replace(f"r2://{key}", f"[Image: {description}]")
            msg["content"] = content
        return messages

    def _parse_content_with_images(self, content: str) -> str:
        return _IMAGE_PATTERN.sub("[Image attached]", content)

    def _fetch_recent_messages(self, db: Session, channel_id: UUID, limit: int = 50) -> list[dict]:
        rows = db.execute(
            select(Activity)
            .where(
                Activity.channel_id == channel_id,
                Activity.activity_type == "chat_message",
                Activity.deleted_at.is_(None),
            )
            .order_by(desc(Activity.created_at))
            .limit(limit)
        ).scalars().all()
        rows.reverse()
        return [
            {
                "author": r.actor.full_name if r.actor else "Unknown",
                "content": r.content or "",
                "time": r.created_at.isoformat() if r.created_at else "",
            }
            for r in rows
            if r.content
        ]

    def _fetch_new_messages_since(
        self, db: Session, channel_id: UUID, last_message_id: UUID, limit: int = 50
    ) -> list[dict]:
        rows = db.execute(
            select(Activity)
            .where(
                Activity.channel_id == channel_id,
                Activity.activity_type == "chat_message",
                Activity.deleted_at.is_(None),
            )
            .order_by(desc(Activity.created_at))
            .limit(limit)
        ).scalars().all()
        rows.reverse()

        seen_last = False
        new_messages: list[dict] = []
        for r in rows:
            if r.id == last_message_id:
                seen_last = True
                continue
            if seen_last and r.content:
                new_messages.append(
                    {
                        "author": r.actor.full_name if r.actor else "Unknown",
                        "content": r.content or "",
                        "time": r.created_at.isoformat() if r.created_at else "",
                    }
                )

        if not seen_last:
            return self._fetch_recent_messages(db, channel_id)

        return new_messages

    def _build_messages(self, messages: list[dict], channel_name: str | None) -> list[ChatMessage]:
        conv_text = "\n\n".join(
            f"[{m['author']}]: {m['content']}" for m in messages
        )
        return [
            ChatMessage(
                role="system",
                content=(
                    "You summarize chat channel conversations. Follow these rules:\n"
                    "- Base your summary ONLY on the messages provided below.\n"
                    "- Do NOT invent facts, names, or topics not present in the messages.\n"
                    "- If the conversation is sparse or unclear, say so.\n"
                    "- Output in Markdown with two sections:\n"
                    "  **Summary**: 2-3 paragraph comprehensive overview of all discussed topics.\n"
                    "  **Conclusion**: A final takeaway summarizing the overall nature of the conversation.\n"
                ),
            ),
            ChatMessage(
                role="user",
                content=f"Channel: {channel_name or 'Unknown'}\n\nRecent messages:\n{conv_text}\n\nSummarize this conversation.",
            ),
        ]

    def _build_append_messages(
        self, existing_summary: str, new_messages: list[dict], channel_name: str | None
    ) -> list[ChatMessage]:
        new_text = "\n\n".join(
            f"[{m['author']}]: {m['content']}" for m in new_messages
        )
        return [
            ChatMessage(
                role="system",
                content=(
                    "You update an existing channel summary with new conversation messages. Follow these rules:\n"
                    "- Incorporate the new messages into the existing summary.\n"
                    "- Do NOT invent facts, names, or topics not present in the provided messages.\n"
                    "- If the new messages do not add substantial new information, keep the summary mostly unchanged.\n"
                    "- Output in Markdown with two sections:\n"
                    "  **Summary**: 2-3 paragraph comprehensive overview of all discussed topics.\n"
                    "  **Conclusion**: A final takeaway summarizing the overall nature of the conversation.\n"
                ),
            ),
            ChatMessage(
                role="user",
                content=(
                    f"Channel: {channel_name or 'Unknown'}\n\n"
                    f"Existing summary:\n{existing_summary}\n\n"
                    f"New messages since the last summary:\n{new_text}\n\n"
                    "Update the summary to include the new conversation."
                ),
            ),
        ]

    def _get_latest_message_id(self, db: Session, channel_id: UUID) -> UUID | None:
        return db.execute(
            select(Activity.id)
            .where(
                Activity.channel_id == channel_id,
                Activity.activity_type == "chat_message",
                Activity.deleted_at.is_(None),
            )
            .order_by(desc(Activity.created_at))
            .limit(1)
        ).scalar_one_or_none()

    def _load_cached_summary(self, db: Session, channel_id: UUID) -> ChannelSummary | None:
        return db.execute(
            select(ChannelSummary).where(ChannelSummary.channel_id == channel_id)
        ).scalar_one_or_none()

    def _save_summary(
        self, db: Session, channel_id: UUID, summary_text: str, last_message_id: UUID | None
    ) -> None:
        cached = self._load_cached_summary(db, channel_id)
        if cached:
            cached.summary = summary_text
            cached.last_message_id = last_message_id
        else:
            db.add(ChannelSummary(
                channel_id=channel_id,
                summary=summary_text,
                last_message_id=last_message_id,
            ))
        db.commit()

    async def stream_summary(
        self,
        db: Session,
        channel_id: UUID,
        channel_name: str | None,
    ) -> AsyncGenerator[str, None]:
        cached = self._load_cached_summary(db, channel_id)
        latest_id = self._get_latest_message_id(db, channel_id)

        if not latest_id:
            yield "No messages to summarize."
            return

        if cached and cached.last_message_id == latest_id:
            yield cached.summary
            return

        if cached and cached.last_message_id is not None:
            new_messages = self._fetch_new_messages_since(db, channel_id, cached.last_message_id)
            if not new_messages:
                yield cached.summary
                return
            enriched = await self._enrich_with_image_descriptions(new_messages)
            prompt = self._build_append_messages(cached.summary, enriched, channel_name)
        else:
            messages = self._fetch_recent_messages(db, channel_id)
            if not messages:
                yield "No recent messages to summarize."
                return
            enriched = await self._enrich_with_image_descriptions(messages)
            prompt = self._build_messages(enriched, channel_name)

        full_summary = ""
        async for token in self.chat.stream_chat(messages=prompt, temperature=_GENERATION_TEMPERATURE):
            full_summary += token
            yield token

        self._save_summary(db, channel_id, full_summary, latest_id)
