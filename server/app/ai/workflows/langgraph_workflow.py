from __future__ import annotations

import time
from collections.abc import AsyncGenerator
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from app.ai.agents.react import run_react_agent_stream
from app.ai.services.audio_summary_service import AudioSummaryService
from app.ai.services.groq_client import GroqAudioService, GroqChatService
from app.ai.services.hf_embeddings import HfEmbeddingsService
from app.ai.services.rag_service import RagService
from app.ai.services.streaming_service import StreamingCollector, sse
from app.ai.services.translation_service import TranslationService
from app.ai.services.website_summary_service import WebsiteSummaryService
from app.ai.services.youtube_summary_service import YouTubeSummaryService
from app.core.config import get_settings
from app.db.models.activity import Activity
from app.db.models.ai import AIInteraction, AIRun
from app.db.models.channel import Channel
from app.db.models.user import User
from app.repositories.ai_interaction_repository import AIInteractionRepository
from app.repositories.channel_member_repository import ChannelMemberRepository
from app.repositories.channel_repository import ChannelRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.realtime.connection_manager import realtime_manager


class WorkflowError(RuntimeError):
    pass


def _require_channel_member(db: Session, *, current_user: User, channel_id: UUID) -> Channel:
    channel_repo = ChannelRepository(db)
    workspace_repo = WorkspaceRepository(db)
    channel_member_repo = ChannelMemberRepository(db)

    channel = channel_repo.get_by_id(channel_id)
    if not channel:
        raise WorkflowError("Channel not found")

    workspaces = workspace_repo.list_for_user(current_user.id)
    if not any(ws.id == channel.workspace_id for ws in workspaces):
        raise WorkflowError("You do not have access to this workspace")

    membership = channel_member_repo.get(channel_id, current_user.id)
    if not membership:
        raise WorkflowError("You are not a member of this channel")

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
) -> AsyncGenerator[bytes, None]:
    """
    Runs a ReAct agent that uses tools to handle the user's request.
    """
    started = time.time()
    channel = _require_channel_member(db, current_user=current_user, channel_id=channel_id)

    interaction_repo = AIInteractionRepository(db)
    interaction = AIInteraction(
        workspace_id=channel.workspace_id,
        channel_id=channel_id,
        user_id=current_user.id,
        input=user_input or "",
        status="running",
        provider="groq",
        model=get_settings().groq_chat_model,
    )
    interaction_repo.create(interaction)
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
    async_client = httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0))

    try:
        embeddings = HfEmbeddingsService(async_client=async_client)
        groq_chat = GroqChatService()
        groq_audio = GroqAudioService()

        translation = TranslationService(groq_chat)
        yt_summary = YouTubeSummaryService(groq_chat)
        web_summary = WebsiteSummaryService(groq_chat)
        audio_summary = AudioSummaryService(groq_audio, groq_chat)
        rag_service = RagService(db, embeddings=embeddings, groq=groq_chat)

        yield sse("source_loading", {"message": "Starting AI agent"})

        async for evt in run_react_agent_stream(
            groq=groq_chat,
            translation=translation,
            yt_summary=yt_summary,
            web_summary=web_summary,
            audio_summary=audio_summary,
            rag_service=rag_service,
            user_input=user_input or "",
            channel_id=channel_id,
            collector=collector,
        ):
            yield evt

        yield sse("generation_completed", {"status": "completed"})

        interaction.status = "completed"
        interaction.output = collector.full_text
        interaction.latency_ms = int((time.time() - started) * 1000)
        run.status = "completed"
        run.state = {"intent": "react_agent", "output": collector.full_text[:500]}
        db.commit()

        ai_activity = Activity(
            workspace_id=channel.workspace_id,
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

        try:
            await realtime_manager.broadcast_to_channel(
                channel_id,
                {
                    "type": "activity_created",
                    "channel_id": str(channel_id),
                    "workspace_id": str(channel.workspace_id),
                    "activity": {
                        "id": str(ai_activity.id),
                        "content": ai_activity.content,
                        "activity_type": ai_activity.activity_type,
                    },
                },
            )
        except Exception:
            pass

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
