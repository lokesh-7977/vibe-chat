from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai.services.grammar_check_service import GrammarCheckService
from app.ai.services.nv_client import NvChatService
from app.api.dependencies.user import CurrentUserDep
from app.db.session import get_db

router = APIRouter(prefix="/ai", tags=["ai"])


class GrammarCheckRequest(BaseModel):
    text: str


class GrammarCheckResponse(BaseModel):
    language: str
    has_errors: bool
    corrected_text: str | None = None
    message: str | None = None


@router.post("/grammar-check", response_model=GrammarCheckResponse)
async def grammar_check(
    payload: GrammarCheckRequest,
    current_user: CurrentUserDep,
    db: Session = Depends(get_db),
) -> GrammarCheckResponse:
    import httpx
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
        chat = NvChatService(async_client=client)
        service = GrammarCheckService(chat)
        result = await service.check(payload.text)
    return GrammarCheckResponse(**result)
