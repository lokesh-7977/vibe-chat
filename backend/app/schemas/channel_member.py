from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ChannelMemberBase(BaseModel):
    channel_id: UUID
    user_id: UUID
    role: str = "member"


class ChannelMemberCreate(ChannelMemberBase):
    pass


class ChannelMemberUpdate(BaseModel):
    role: str | None = None


class ChannelMemberResponse(ChannelMemberBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    joined_at: datetime
