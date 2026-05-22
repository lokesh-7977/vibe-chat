from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ChannelBase(BaseModel):
    workspace_id: UUID
    name: str
    slug: str
    description: str | None = None
    channel_type: str = "general"
    created_by_id: UUID | None = None


class ChannelCreate(ChannelBase):
    pass


class ChannelUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    channel_type: str | None = None


class ChannelResponse(ChannelBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime

