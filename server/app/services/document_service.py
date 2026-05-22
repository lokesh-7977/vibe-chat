from __future__ import annotations

import os
import uuid
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.document import Document
from app.db.models.user import User
from app.db.schemas.common import ApiResponse
from app.db.schemas.document import DocumentResponse
from app.db.schemas.upload import PresignUploadRequest, PresignUploadResponse
from app.repositories.channel_member_repository import ChannelMemberRepository
from app.repositories.channel_repository import ChannelRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.storage.r2 import presign_put_object


class DocumentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.document_repository = DocumentRepository(db)
        self.channel_repository = ChannelRepository(db)
        self.channel_member_repository = ChannelMemberRepository(db)
        self.workspace_repository = WorkspaceRepository(db)

    def _require_channel_member(self, current_user: User, channel_id):
        channel = self.channel_repository.get_by_id(channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")

        workspaces = self.workspace_repository.list_for_user(current_user.id)
        if not any(ws.id == channel.workspace_id for ws in workspaces):
            raise HTTPException(status_code=403, detail="You do not have access to this workspace")

        membership = self.channel_member_repository.get(channel_id, current_user.id)
        if not membership:
            raise HTTPException(status_code=403, detail="You are not a member of this channel")

        return channel

    def _validate_presign_payload(self, payload: PresignUploadRequest) -> None:
        settings = get_settings()

        if payload.file_size is not None:
            if payload.file_size > settings.uploads_max_file_size_bytes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File too large (max {settings.uploads_max_file_size_bytes} bytes)",
                )

        allowed = set(settings.uploads_allowed_mime_types or [])
        if allowed and payload.mime_type not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported mime_type",
            )

    def presign_upload(
        self,
        current_user: User,
        payload: PresignUploadRequest,
    ) -> ApiResponse[PresignUploadResponse]:
        self._validate_presign_payload(payload)
        channel = self._require_channel_member(current_user=current_user, channel_id=payload.channel_id)
        if channel.workspace_id != payload.workspace_id:
            raise HTTPException(status_code=400, detail="workspace_id does not match channel")

        # Object key layout allows later workspace/channel scoping.
        safe_name = os.path.basename(payload.file_name).replace("\\", "_").replace("/", "_")
        object_key = f"workspaces/{channel.workspace_id}/channels/{payload.channel_id}/documents/{uuid.uuid4()}_{safe_name}"

        presigned = presign_put_object(object_key=object_key, content_type=payload.mime_type)

        document = Document(
            workspace_id=channel.workspace_id,
            channel_id=payload.channel_id,
            uploaded_by_id=current_user.id,
            file_name=safe_name,
            file_url=presigned.file_url,
            mime_type=payload.mime_type,
            file_size=payload.file_size,
            status="pending_upload",
        )
        self.document_repository.create(document)

        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="Unable to create upload") from exc

        self.db.refresh(document)
        return ApiResponse(
            success=True,
            message="Upload URL created successfully",
            data=PresignUploadResponse(
                document_id=document.id,
                object_key=presigned.object_key,
                upload_url=presigned.upload_url,
                file_url=presigned.file_url,
            ),
        )

    def complete_upload(
        self,
        current_user: User,
        document_id: UUID,
    ) -> ApiResponse[DocumentResponse]:
        document = self.document_repository.get_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        if document.channel_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document is not associated with a channel",
            )

        self._require_channel_member(current_user=current_user, channel_id=document.channel_id)

        if document.uploaded_by_id and document.uploaded_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the uploader can complete this upload",
            )

        if document.status != "uploaded":
            document.status = "uploaded"
            try:
                self.db.commit()
            except Exception as exc:
                self.db.rollback()
                raise HTTPException(status_code=400, detail="Unable to complete upload") from exc
            self.db.refresh(document)

        return ApiResponse(
            success=True,
            message="Upload completed successfully",
            data=DocumentResponse.model_validate(document),
        )

    def list_channel_documents(
        self,
        current_user: User,
        channel_id,
        limit: int,
        offset: int,
    ) -> ApiResponse[list[DocumentResponse]]:
        self._require_channel_member(current_user=current_user, channel_id=channel_id)
        docs = self.document_repository.list_for_channel(channel_id, limit=limit, offset=offset)
        return ApiResponse(
            success=True,
            message="Documents retrieved successfully",
            data=[DocumentResponse.model_validate(d) for d in docs],
        )
