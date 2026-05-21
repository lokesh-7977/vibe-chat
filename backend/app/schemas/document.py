from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentBase(BaseModel):
    workspace_id: UUID
    channel_id: UUID | None = None
    uploaded_by_id: UUID | None = None
    file_name: str
    file_url: str
    mime_type: str
    file_size: int | None = None
    status: str = "uploaded"


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    status: str | None = None


class DocumentResponse(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
