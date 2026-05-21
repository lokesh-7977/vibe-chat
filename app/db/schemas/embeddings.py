from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentEmbeddingBase(BaseModel):
    document_chunk_id: UUID
    embedding: list[float]
    embedding_model: str


class DocumentEmbeddingCreate(DocumentEmbeddingBase):
    pass


class DocumentEmbeddingUpdate(BaseModel):
    embedding: list[float] | None = None
    embedding_model: str | None = None


class DocumentEmbeddingResponse(DocumentEmbeddingBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


class ActivityEmbeddingBase(BaseModel):
    activity_id: UUID
    workspace_id: UUID
    channel_id: UUID | None = None
    embedding: list[float]
    embedding_model: str


class ActivityEmbeddingCreate(ActivityEmbeddingBase):
    pass


class ActivityEmbeddingUpdate(BaseModel):
    embedding: list[float] | None = None
    embedding_model: str | None = None


class ActivityEmbeddingResponse(ActivityEmbeddingBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime

