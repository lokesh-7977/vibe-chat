from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.ai.workflows.langgraph_workflow import run_ai_action_workflow
from app.api.dependencies.user import CurrentUserDep
from app.db.schemas.ai_actions import AIActionStreamRequest
from app.db.session import get_db


router = APIRouter(prefix="/channels", tags=["ai"])


@router.post(
    "/{channel_id}/ai/actions/stream",
    status_code=status.HTTP_200_OK,
)
async def stream_ai_action(
    channel_id: UUID,
    payload: AIActionStreamRequest,
    request: Request,
    current_user: CurrentUserDep,
    db: Session = Depends(get_db),
):
    async def event_generator():
        async for chunk in run_ai_action_workflow(
            db=db,
            channel_id=channel_id,
            current_user=current_user,
            action=payload.action,
            message_id=payload.message_id,
            user_input=payload.input,
            target_language=payload.target_language,
            private_response=payload.private_response,
            history=payload.history,
        ):
            if await request.is_disconnected():
                continue
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
