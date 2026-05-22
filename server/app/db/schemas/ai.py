from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AIInteractionBase(BaseModel):
    workspace_id: UUID
    channel_id: UUID | None = None
    user_id: UUID | None = None
    input: str
    output: str | None = None
    status: str = "pending"
    model: str | None = None
    provider: str | None = None
    tokens_input: int | None = None
    tokens_output: int | None = None
    cost: float | None = None
    latency_ms: int | None = None


class AIInteractionCreate(AIInteractionBase):
    pass


class AIInteractionUpdate(BaseModel):
    output: str | None = None
    status: str | None = None
    model: str | None = None
    provider: str | None = None
    tokens_input: int | None = None
    tokens_output: int | None = None
    cost: float | None = None
    latency_ms: int | None = None


class AIInteractionResponse(AIInteractionBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


class AIRunBase(BaseModel):
    interaction_id: UUID
    workflow_name: str
    status: str = "running"
    state: dict[str, Any] | None = None


class AIRunCreate(AIRunBase):
    pass


class AIRunUpdate(BaseModel):
    status: str | None = None
    state: dict[str, Any] | None = None
    completed_at: datetime | None = None


class AIRunResponse(AIRunBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    started_at: datetime
    completed_at: datetime | None = None


class AIRunStepBase(BaseModel):
    ai_run_id: UUID
    step_name: str
    step_type: str
    input: dict[str, Any] | None = None
    output: dict[str, Any] | None = None
    status: str = "pending"


class AIRunStepCreate(AIRunStepBase):
    pass


class AIRunStepUpdate(BaseModel):
    output: dict[str, Any] | None = None
    status: str | None = None
    completed_at: datetime | None = None


class AIRunStepResponse(AIRunStepBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    started_at: datetime
    completed_at: datetime | None = None

