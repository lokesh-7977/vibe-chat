from __future__ import annotations

import re
import time
from collections.abc import AsyncGenerator
from typing import Any, TypedDict
from uuid import UUID

import httpx
from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.ai.services.audio_summary_service import AudioSummaryService
from app.ai.services.groq_client import GroqAudioService, GroqChatService
from app.ai.services.hf_embeddings import HfEmbeddingsService
from app.ai.services.intent_classifier_service import IntentClassifierService
from app.ai.services.rag_service import RagService
from app.ai.services.streaming_service import StreamingCollector, sse, stream_tokens_as_sse
from app.ai.services.translation_service import TranslationService
from app.ai.services.website_summary_service import WebsiteSummaryService
from app.ai.services.youtube_summary_service import YouTubeSummaryService
from app.ai.types import Intent
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


_url_re = re.compile(r"https?://\\S+", re.I)


class WorkflowError(RuntimeError):
    pass


class WorkflowState(TypedDict, total=False):
    channel_id: UUID
    workspace_id: UUID
    user_id: UUID

    action: str
    message_id: UUID | None
    input: str
    target_language: str | None

    intent: Intent
    intent_reason: str

    url: str | None
    selected_message: str | None

    rag_sources: list[dict[str, Any]]
    rag_citations: list[dict[str, Any]]


def _extract_url(text: str) -> str | None:
    m = _url_re.search(text or "")
    return m.group(0) if m else None


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


def build_langgraph(
    *,
    db: Session,
    intent_classifier: IntentClassifierService,
    rag_service: RagService,
) -> Any:
    async def detect_intent_node(state: WorkflowState) -> WorkflowState:
        result = intent_classifier.classify(
            action=state.get("action", "auto"),
            user_input=state.get("input", ""),
            target_language=state.get("target_language"),
            message_id=str(state.get("message_id")) if state.get("message_id") else None,
        )
        return {"intent": result.intent, "intent_reason": result.reason}

    async def load_sources_node(state: WorkflowState) -> WorkflowState:
        selected_message: str | None = None
        if state.get("message_id"):
            msg = db.query(Activity).filter(Activity.id == state["message_id"]).one_or_none()
            if not msg or msg.channel_id != state["channel_id"]:
                raise WorkflowError("Selected message not found in this channel")
            selected_message = msg.content or ""

        url = _extract_url(state.get("input", "")) or _extract_url(selected_message or "")
        return {"selected_message": selected_message, "url": url}

    async def retrieve_context_node(state: WorkflowState) -> WorkflowState:
        if state.get("intent") != "rag_question_answering":
            return {}
        sources, citations = await rag_service.retrieve(channel_id=state["channel_id"], query=state.get("input", ""))
        return {
            "rag_sources": [s.__dict__ for s in sources],
            "rag_citations": [c.__dict__ for c in citations],
        }

    graph = StateGraph(WorkflowState)
    graph.add_node("detect_intent", detect_intent_node)
    graph.add_node("load_sources", load_sources_node)
    graph.add_node("retrieve_context", retrieve_context_node)
    graph.add_edge(START, "detect_intent")
    graph.add_edge("detect_intent", "load_sources")
    graph.add_edge("load_sources", "retrieve_context")
    graph.add_edge("retrieve_context", END)
    return graph.compile()


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
    Runs the LangGraph planning steps and then streams generation token-by-token.
    """
    started = time.time()
    channel = _require_channel_member(db, current_user=current_user, channel_id=channel_id)

    # Create AI interaction log early.
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
    run = AIRun(interaction_id=interaction.id, workflow_name="channel_ai_actions", status="running", state=None)
    interaction_repo.create_run(run)
    db.commit()
    db.refresh(interaction)

    collector = StreamingCollector()
    async_client = httpx.AsyncClient()
    embeddings = HfEmbeddingsService(async_client=async_client)
    groq_chat = GroqChatService()
    groq_audio = GroqAudioService()

    intent_classifier = IntentClassifierService()
    translation = TranslationService(groq_chat)
    yt_summary = YouTubeSummaryService(groq_chat)
    web_summary = WebsiteSummaryService(groq_chat)
    audio_summary = AudioSummaryService(groq_audio, groq_chat)
    rag_service = RagService(db, embeddings=embeddings, groq=groq_chat)

    compiled = build_langgraph(db=db, intent_classifier=intent_classifier, rag_service=rag_service)

    state: WorkflowState = {
        "channel_id": channel_id,
        "workspace_id": channel.workspace_id,
        "user_id": current_user.id,
        "action": action or "auto",
        "message_id": message_id,
        "input": user_input or "",
        "target_language": target_language,
    }

    try:
        # Stream planning events from LangGraph steps.
        yield sse("source_loading", {"message": "Starting AI workflow"})
        async for update in compiled.astream(state, stream_mode="updates"):
            if "detect_intent" in update:
                payload = update["detect_intent"]
                yield sse("intent_detected", {"intent": payload.get("intent"), "reason": payload.get("intent_reason")})
                state.update(payload)
            if "load_sources" in update:
                payload = update["load_sources"]
                yield sse("source_loading", {"message": "Sources loaded"})
                state.update(payload)
            if "retrieve_context" in update:
                yield sse("retrieval_started", {"message": "Retrieval started"})
                payload = update["retrieve_context"]
                state.update(payload)
                yield sse("retrieval_completed", {"sources": state.get("rag_citations", [])})

        # Generation phase (stream tokens).
        intent: Intent = state.get("intent", "unknown")
        yield sse("generation_started", {"message": "Streaming started"})

        if intent == "translate_message":
            if not state.get("selected_message"):
                raise WorkflowError("message_id is required for translation")
            if not state.get("target_language"):
                raise WorkflowError("target_language is required for translation")
            token_stream = translation.stream_translation(
                text=state["selected_message"],
                target_language=state["target_language"],
            )
        elif intent == "summarize_youtube":
            if not state.get("url"):
                raise WorkflowError("No URL found to summarize")
            token_stream = yt_summary.stream_summary(url=state["url"])
        elif intent == "summarize_website":
            if not state.get("url"):
                raise WorkflowError("No URL found to summarize")
            token_stream = web_summary.stream_summary(url=state["url"])
        elif intent == "summarize_audio":
            if not state.get("url"):
                raise WorkflowError("No audio URL found to summarize")
            token_stream = audio_summary.stream_summary_from_url(url=state["url"])
        elif intent == "rag_question_answering":
            sources = state.get("rag_sources", [])
            citations = state.get("rag_citations", [])
            token_stream = rag_service.stream_answer(
                question=state.get("input", ""),
                sources=[type("SD", (), s) for s in sources],  # lightweight adapter
                citations=[type("RS", (), c) for c in citations],
            )
        else:
            raise WorkflowError("Unknown intent")

        async for evt in stream_tokens_as_sse(token_stream, collector):
            yield evt

        yield sse("generation_completed", {"status": "completed"})

    except Exception as exc:
        yield sse("error", {"message": str(exc)})
        interaction.status = "failed"
        interaction.output = None
        db.commit()
        await async_client.aclose()
        return

    # Persist final answer after streaming.
    interaction.status = "completed"
    interaction.output = collector.full_text
    interaction.latency_ms = int((time.time() - started) * 1000)
    run.status = "completed"
    db.commit()

    # Save as an activity in channel.
    ai_activity = Activity(
        workspace_id=channel.workspace_id,
        channel_id=channel_id,
        actor_id=None,
        activity_type="ai_message",
        content=collector.full_text,
        meta_data={"intent": state.get("intent"), "interaction_id": str(interaction.id)},
        parent_activity_id=None,
    )
    db.add(ai_activity)
    db.commit()
    db.refresh(ai_activity)

    # Broadcast best-effort to realtime subscribers.
    try:
        await realtime_manager.broadcast_to_channel(
            channel_id,
            {
                "type": "activity_created",
                "channel_id": str(channel_id),
                "workspace_id": str(channel.workspace_id),
                "activity": {"id": str(ai_activity.id), "content": ai_activity.content, "activity_type": ai_activity.activity_type},
            },
        )
    except Exception:
        pass

    await async_client.aclose()

