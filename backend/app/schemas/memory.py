from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ContextualMemoryBase(BaseModel):
    workspace_id: UUID
    channel_id: UUID | None = None
    user_id: UUID | None = None
    scope: str
    memory_type: str
    content: str
    meta_data: dict[str, Any] | None = None


class ContextualMemoryCreate(ContextualMemoryBase):
    pass


class ContextualMemoryUpdate(BaseModel):
    scope: str | None = None
    memory_type: str | None = None
    content: str | None = None
    meta_data: dict[str, Any] | None = None


class ContextualMemoryResponse(ContextualMemoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
