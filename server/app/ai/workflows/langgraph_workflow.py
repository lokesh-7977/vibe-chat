from __future__ import annotations

import re
import time
from collections.abc import AsyncGenerator
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from app.ai.agents.react import run_react_agent_stream
from app.ai.services.audio_summary_service import AudioSummaryService
from app.ai.services.channel_summary_service import ChannelSummaryService
from app.ai.services.local_embeddings import HuggingFaceEmbeddingsService
from app.ai.services.nv_client import NvChatService
from app.ai.services.rag_service import RagService
from app.ai.services.streaming_service import StreamingCollector, sse
from app.ai.services.translation_service import TranslationService
from app.ai.services.website_summary_service import WebsiteSummaryService
from app.ai.services.youtube_summary_service import YouTubeSummaryService
from app.ai.prompts.base import ChatMessage
from app.core.config import get_settings
from app.db.models.activity import Activity
from app.db.models.ai import AIInteraction, AIRun
from app.db.models.channel import Channel
from app.db.models.user import User
from app.repositories.ai_interaction_repository import AIInteractionRepository
from app.repositories.channel_repository import ChannelRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.realtime.connection_manager import realtime_manager


class WorkflowError(RuntimeError):
    pass


def _require_channel_member(db: Session, *, current_user: User, channel_id: UUID) -> Channel:
    channel_repo = ChannelRepository(db)
    workspace_repo = WorkspaceRepository(db)

    channel = channel_repo.get_by_id(channel_id)
    if not channel:
        raise WorkflowError("Channel not found")

    workspaces = workspace_repo.list_for_user(current_user.id)
    if not any(ws.id == channel.workspace_id for ws in workspaces):
        raise WorkflowError("You do not have access to this workspace")

    return channel


async def run_ai_action_workflow(
    *,
    db: Session,
    channel_id: UUID,
    current_user: User,
    action: str,
    message_id: UUID | None,
    user_input: str,
    target_language: str | None,
    private_response: bool | None = None,
    history: list[dict] | None = None,
) -> AsyncGenerator[bytes, None]:
    """
    Routes requests to the right pipeline:
    - Translation -> direct TranslationService (avoids tool-calling LLM which may not reliably support it)
    - Everything else -> ReAct agent
    """
    started = time.time()
    channel = _require_channel_member(db, current_user=current_user, channel_id=channel_id)
    is_translation = bool(target_language) or (user_input or "").lower().startswith("translate")

    interaction_repo = AIInteractionRepository(db)
    workspace_id = channel.workspace_id
    interaction = AIInteraction(
        workspace_id=workspace_id,
        channel_id=channel_id,
        user_id=current_user.id,
        input=user_input or "",
        status="running",
        provider="nvidia",
        model=get_settings().nvapi_chat_model,
    )
    interaction_repo.create(interaction)
    db.flush()
    run = AIRun(
        interaction_id=interaction.id,
        workflow_name="react_agent",
        status="running",
        state=None,
    )
    interaction_repo.create_run(run)
    db.commit()
    db.refresh(interaction)

    collector = StreamingCollector()
    async_client = httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=10.0, read=120.0, write=60.0))

    try:
        embeddings = HuggingFaceEmbeddingsService()
        chat = NvChatService(async_client=async_client)
        audio: object = _DisabledAudioService()

        translation = TranslationService(chat)
        yt_summary = YouTubeSummaryService(chat, db=db, workspace_id=workspace_id)
        web_summary = WebsiteSummaryService(chat, embeddings=embeddings, db=db, workspace_id=workspace_id)
        audio_summary = AudioSummaryService(audio, chat)
        channel_summary = ChannelSummaryService(chat)
        rag_service = RagService(db, embeddings=embeddings, groq=chat)

        is_channel_summary = (
            not is_translation
            and (user_input or "").strip().lower().startswith("summarize")
            and any(kw in (user_input or "").lower() for kw in ["channel", "chat", "conversation", "recent"])
        )

        if is_channel_summary:
            yield sse("source_loading", {"message": "Summarizing channel conversations..."})
            async for token in channel_summary.stream_summary(
                db=db,
                channel_id=channel_id,
                channel_name=channel.name,
            ):
                collector.add_token(token)
                yield sse("token", {"content": token})
        elif is_translation:
            text_to_translate = user_input or ""
            lowered = text_to_translate.lower()
            if lowered.startswith("translate this message to") and ":" in text_to_translate:
                text_to_translate = text_to_translate.split(":", 1)[1].strip()
            async for token in translation.stream_translation(
                text=text_to_translate,
                target_language=target_language or "English",
                user_prompt=None,
            ):
                collector.add_token(token)
                yield sse("token", {"content": token})
        elif private_response:
            # Private, generic assistant response (no RAG/tools/sources). Not persisted or broadcasted.
            system = ChatMessage(
                role="system",
                content=(
                    "You are Aura Chat, a helpful AI assistant.\n"
                    "- Answer the user's question directly.\n"
                    "- Do not mention sources, IDs, tools, or internal context.\n"
                    "- If the user asks about the app, give actionable steps.\n"
                ),
            )
            msgs: list[ChatMessage] = [system]
            for h in history or []:
                role = str(h.get("role") or "").strip().lower()
                content = str(h.get("content") or "").strip()
                if role not in {"user", "assistant"} or not content:
                    continue
                msgs.append(ChatMessage(role=role, content=content))
            msgs.append(ChatMessage(role="user", content=user_input or ""))

            async for token in chat.stream_chat(messages=msgs, temperature=0.3):
                collector.add_token(token)
                yield sse("token", {"content": token})
        elif re.search(r"(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)", user_input or ""):
            match = re.search(r"(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)", user_input or "")
            url = match.group(0)
            yield sse("source_loading", {"message": "Summarizing YouTube video..."})
            async for token in yt_summary.stream_summary(url=url, user_prompt="Main points only. <=150 words."):
                collector.add_token(token)
                yield sse("token", {"content": token})
        else:
            async for evt in run_react_agent_stream(
                llm=chat,
                translation=translation,
                yt_summary=yt_summary,
                web_summary=web_summary,
                audio_summary=audio_summary,
                rag_service=rag_service,
                user_input=user_input or "",
                channel_id=channel_id,
                target_language=target_language,
                collector=collector,
            ):
                yield evt

        yield sse("generation_completed", {"status": "completed"})

        interaction.status = "completed"
        interaction.output = collector.full_text
        interaction.latency_ms = int((time.time() - started) * 1000)
        run.status = "completed"
        run.state = {"intent": "channel_summary" if is_channel_summary else "react_agent", "output": collector.full_text[:500]}
        db.commit()

        if not is_translation and not is_channel_summary and not private_response:
            ai_activity = Activity(
                workspace_id=workspace_id,
                channel_id=channel_id,
                actor_id=None,
                activity_type="ai_message",
                content=collector.full_text,
                meta_data={"intent": "react_agent", "interaction_id": str(interaction.id)},
                parent_activity_id=None,
            )
            db.add(ai_activity)
            db.commit()
            db.refresh(ai_activity)

    except GeneratorExit:
        interaction.status = "completed" if collector.full_text else "failed"
        interaction.output = collector.full_text or None
        interaction.latency_ms = int((time.time() - started) * 1000)
        run.status = interaction.status
        run.state = {"intent": "channel_summary" if is_channel_summary else "react_agent", "partial": True, "output": (collector.full_text or "")[:500]}
        db.commit()

        if not is_translation and not is_channel_summary and collector.full_text and not private_response:
            ai_activity = Activity(
                workspace_id=workspace_id,
                channel_id=channel_id,
                actor_id=None,
                activity_type="ai_message",
                content=collector.full_text,
                meta_data={"intent": "react_agent", "interaction_id": str(interaction.id), "partial": True},
                parent_activity_id=None,
            )
            db.add(ai_activity)
            db.commit()
            db.refresh(ai_activity)

        return

    except Exception as exc:
        yield sse("error", {"message": str(exc)})
        interaction.status = "failed"
        interaction.output = None
        interaction.latency_ms = int((time.time() - started) * 1000)
        run.status = "failed"
        run.state = {"error": str(exc)}
        db.commit()
        return
    finally:
        await async_client.aclose()


class _DisabledAudioService:
    async def transcribe(self, *, audio_bytes: bytes, content_type: str | None) -> str:  # pragma: no cover
        raise RuntimeError("ASR is disabled (configure an ASR provider to summarize audio)")
