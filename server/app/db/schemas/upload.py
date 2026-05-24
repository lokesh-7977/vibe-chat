from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class PresignUploadRequest(BaseModel):
    workspace_id: UUID
    channel_id: UUID
    file_name: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=1, max_length=200)
    file_size: int | None = Field(default=None, ge=0)


class PresignUploadResponse(BaseModel):
    document_id: UUID
    object_key: str
    upload_url: str


class ImageUrlResponse(BaseModel):
    key: str
    url: str
    mime_type: str
    file_name: str


class ImageSummaryResponse(BaseModel):
    key: str
    summary: str


class DocumentSummaryResponse(BaseModel):
    key: str
    summary: str


class DocumentQaResponse(BaseModel):
    key: str
    question: str
    answer: str
