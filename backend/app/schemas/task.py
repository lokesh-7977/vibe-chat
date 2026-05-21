from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TaskBase(BaseModel):
    workspace_id: UUID
    channel_id: UUID | None = None
    title: str
    description: str | None = None
    status: str = "todo"
    priority: str = "medium"
    assignee_id: UUID | None = None
    created_by_id: UUID | None = None
    source_activity_id: UUID | None = None
    due_date: datetime | None = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    assignee_id: UUID | None = None
    due_date: datetime | None = None


class TaskResponse(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
