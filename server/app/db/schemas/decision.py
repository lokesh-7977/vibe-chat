from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DecisionBase(BaseModel):
    workspace_id: UUID
    channel_id: UUID | None = None
    title: str
    description: str | None = None
    reason: str | None = None
    created_by_id: UUID | None = None
    source_activity_id: UUID | None = None


class DecisionCreate(DecisionBase):
    pass


class DecisionUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    reason: str | None = None


class DecisionResponse(DecisionBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
