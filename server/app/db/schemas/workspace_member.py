from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class WorkspaceMemberBase(BaseModel):
    workspace_id: UUID
    user_id: UUID
    role: str = "owner"


class WorkspaceMemberCreate(WorkspaceMemberBase):
    pass


class WorkspaceMemberUpdate(BaseModel):
    role: str | None = None


class WorkspaceMemberResponse(WorkspaceMemberBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    joined_at: datetime
