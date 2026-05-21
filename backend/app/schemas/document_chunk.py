from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentChunkBase(BaseModel):
    document_id: UUID
    workspace_id: UUID
    channel_id: UUID | None = None
    chunk_index: int
    content: str
    token_count: int | None = None
    meta_data: dict[str, Any] | None = None


class DocumentChunkCreate(DocumentChunkBase):
    pass


class DocumentChunkUpdate(BaseModel):
    content: str | None = None
    token_count: int | None = None
    meta_data: dict[str, Any] | None = None


class DocumentChunkResponse(DocumentChunkBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
