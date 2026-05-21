from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CallBase(BaseModel):
    workspace_id: UUID
    channel_id: UUID | None = None
    started_by_id: UUID | None = None
    title: str | None = None
    status: str = "active"
    started_at: datetime | None = None
    ended_at: datetime | None = None


class CallCreate(CallBase):
    pass


class CallUpdate(BaseModel):
    status: str | None = None
    title: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None


class CallResponse(CallBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    # Call has no updated_at column in the model


class CallParticipantBase(BaseModel):
    call_id: UUID
    user_id: UUID
    joined_at: datetime
    left_at: datetime | None = None
    is_muted: bool = False
    is_camera_on: bool = False
    is_screen_sharing: bool = False


class CallParticipantCreate(CallParticipantBase):
    pass


class CallParticipantUpdate(BaseModel):
    left_at: datetime | None = None
    is_muted: bool | None = None
    is_camera_on: bool | None = None
    is_screen_sharing: bool | None = None


class CallParticipantResponse(CallParticipantBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class CallTranscriptBase(BaseModel):
    call_id: UUID
    speaker_id: UUID | None = None
    content: str
    started_at: datetime | None = None
    ended_at: datetime | None = None


class CallTranscriptCreate(CallTranscriptBase):
    pass


class CallTranscriptUpdate(BaseModel):
    content: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None


class CallTranscriptResponse(CallTranscriptBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class CallSummaryBase(BaseModel):
    call_id: UUID
    summary: str
    decisions: dict[str, Any] | None = None
    action_items: dict[str, Any] | None = None


class CallSummaryCreate(CallSummaryBase):
    pass


class CallSummaryUpdate(BaseModel):
    summary: str | None = None
    decisions: dict[str, Any] | None = None
    action_items: dict[str, Any] | None = None


class CallSummaryResponse(CallSummaryBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
