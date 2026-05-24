from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ActivityBase(BaseModel):
    workspace_id: UUID
    channel_id: UUID
    actor_id: UUID | None = None
    activity_type: str
    content: str | None = None
    meta_data: dict[str, Any] | None = None
    parent_activity_id: UUID | None = None


class ActivityCreate(ActivityBase):
    pass


class ActivityCreateRequest(BaseModel):
    content: str
    activity_type: str = "chat_message"
    meta_data: dict[str, Any] | None = None
    parent_activity_id: UUID | None = None


class ActivityUpdate(BaseModel):
    content: str | None = None
    meta_data: dict[str, Any] | None = None


class ActivityResponse(ActivityBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    actor_name: str | None = None
