from __future__ import annotations

import os
import uuid
from uuid import UUID

from fastapi import HTTPException, Request, status
import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.document import Document
from app.db.models.user import User
from app.db.schemas.common import ApiResponse
from app.db.schemas.document import DocumentResponse
from app.ai.services.image_summary_service import ImageSummaryService
from app.repositories.content_summary_repository import ContentSummaryRepository
from app.ai.services.document_summary_service import DocumentSummaryService
from app.ai.services.document_qa_service import DocumentQaService
from app.db.schemas.upload import ImageSummaryResponse, ImageUrlResponse, PresignUploadRequest, PresignUploadResponse
from app.db.schemas.upload import DocumentSummaryResponse
from app.db.schemas.upload import DocumentQaResponse
from app.utils.text_extractors import extract_text_from_document_bytes
from app.repositories.channel_member_repository import ChannelMemberRepository
from app.repositories.channel_repository import ChannelRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.storage.r2 import presign_get_object, presign_put_object


class DocumentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.document_repository = DocumentRepository(db)
        self.channel_repository = ChannelRepository(db)
        self.channel_member_repository = ChannelMemberRepository(db)
        self.workspace_repository = WorkspaceRepository(db)
        self.image_summary_service = ImageSummaryService()
        self.document_summary_service = DocumentSummaryService()
        self.document_qa_service = DocumentQaService()

    def _require_channel_member(self, current_user: User, channel_id):
        channel = self.channel_repository.get_by_id(channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")

        workspaces = self.workspace_repository.list_for_user(current_user.id)
        if not any(ws.id == channel.workspace_id for ws in workspaces):
            raise HTTPException(status_code=403, detail="You do not have access to this workspace")

        return channel

    def _validate_presign_payload(self, payload: PresignUploadRequest) -> None:
        settings = get_settings()

        if payload.file_size is not None:
            if payload.file_size > settings.uploads_max_file_size_bytes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File too large (max {settings.uploads_max_file_size_bytes} bytes)",
                )

        allowed = set(settings.uploads_allowed_mime_types_list or [])
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
            object_key=presigned.object_key,
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

    def presign_image_url(self, current_user: User, object_key: str) -> ApiResponse[ImageUrlResponse]:
        # Enforce workspace access by parsing our object key convention.
        # Expected: workspaces/<workspace_id>/channels/<channel_id>/documents/<uuid>_<name>
        parts = object_key.split("/")
        if len(parts) < 6 or parts[0] != "workspaces" or parts[2] != "channels" or parts[4] != "documents":
            raise HTTPException(status_code=400, detail="Invalid key")

        try:
            workspace_id = UUID(parts[1])
            channel_id = UUID(parts[3])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid key") from None

        channel = self._require_channel_member(current_user=current_user, channel_id=channel_id)
        if channel.workspace_id != workspace_id:
            raise HTTPException(status_code=403, detail="You do not have access to this file")

        document = self.document_repository.get_by_object_key(object_key)
        if not document:
            raise HTTPException(status_code=404, detail="File not found")

        presigned = presign_get_object(object_key=object_key)
        return ApiResponse(
            success=True,
            message="View URL created successfully",
            data=ImageUrlResponse(
                key=presigned.object_key,
                url=presigned.view_url,
                mime_type=document.mime_type,
                file_name=document.file_name,
            ),
        )

    async def summarize_image(
        self,
        current_user: User,
        object_key: str,
        user_prompt: str | None,
    ) -> ApiResponse[ImageSummaryResponse]:
        # Reuse the same access rules as image-url.
        parts = object_key.split("/")
        if len(parts) < 6 or parts[0] != "workspaces" or parts[2] != "channels" or parts[4] != "documents":
            raise HTTPException(status_code=400, detail="Invalid key")

        try:
            workspace_id = UUID(parts[1])
            channel_id = UUID(parts[3])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid key") from None

        channel = self._require_channel_member(current_user=current_user, channel_id=channel_id)
        if channel.workspace_id != workspace_id:
            raise HTTPException(status_code=403, detail="You do not have access to this file")

        document = self.document_repository.get_by_object_key(object_key)
        if not document:
            raise HTTPException(status_code=404, detail="File not found")
        if not (document.mime_type or "").startswith("image/"):
            raise HTTPException(status_code=400, detail="Not an image")

        view = presign_get_object(object_key=object_key)
        prompt_key = ((user_prompt or "").strip() or "").lower()[:200]
        cache_repo = ContentSummaryRepository(self.db)
        cached = cache_repo.get(workspace_id=workspace_id, kind="image", key=object_key, prompt=prompt_key)
        if cached and (cached.summary or "").strip():
            return ApiResponse(success=True, message="Image summarized", data=ImageSummaryResponse(key=object_key, summary=cached.summary))

        summary = await self.image_summary_service.summarize(image_url=view.view_url, user_prompt=user_prompt)
        if summary.strip():
            cache_repo.upsert(workspace_id=workspace_id, kind="image", key=object_key, prompt=prompt_key, summary=summary.strip())
            self.db.commit()
        return ApiResponse(success=True, message="Image summarized", data=ImageSummaryResponse(key=object_key, summary=summary))

    async def stream_summarize_image(
        self,
        *,
        current_user: User,
        object_key: str,
        user_prompt: str | None,
        request: Request,
    ):
        import json

        def sse(event: str, data: dict) -> str:
            return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

        yield sse("generation_started", {"key": object_key})

        parts = object_key.split("/")
        if len(parts) < 6 or parts[0] != "workspaces" or parts[2] != "channels" or parts[4] != "documents":
            yield sse("error", {"message": "Invalid key"})
            return

        try:
            workspace_id = UUID(parts[1])
            channel_id = UUID(parts[3])
        except ValueError:
            yield sse("error", {"message": "Invalid key"})
            return

        channel = self._require_channel_member(current_user=current_user, channel_id=channel_id)
        if channel.workspace_id != workspace_id:
            yield sse("error", {"message": "You do not have access to this file"})
            return

        document = self.document_repository.get_by_object_key(object_key)
        if not document:
            yield sse("error", {"message": "File not found"})
            return
        if not (document.mime_type or "").startswith("image/"):
            yield sse("error", {"message": "Not an image"})
            return

        prompt_key = ((user_prompt or "").strip() or "").lower()[:200]
        cache_repo = ContentSummaryRepository(self.db)
        cached = cache_repo.get(workspace_id=workspace_id, kind="image", key=object_key, prompt=prompt_key)
        if cached and (cached.summary or "").strip():
            yield sse("token", {"content": cached.summary})
            yield sse("generation_completed", {"key": object_key})
            return

        yield sse("source_loading", {"message": "Analyzing image..."})
        view = presign_get_object(object_key=object_key)

        try:
            full = ""
            async for token in self.image_summary_service.stream(image_url=view.view_url, user_prompt=user_prompt):
                if await request.is_disconnected():
                    return
                full += token
                yield sse("token", {"content": token})
        except Exception as exc:
            yield sse("error", {"message": str(exc)[:200]})
            return

        if full.strip():
            cache_repo.upsert(workspace_id=workspace_id, kind="image", key=object_key, prompt=prompt_key, summary=full.strip())
            try:
                self.db.commit()
            except Exception:
                self.db.rollback()

        yield sse("generation_completed", {"key": object_key})

    async def summarize_document(
        self,
        current_user: User,
        object_key: str,
        user_prompt: str | None,
    ) -> ApiResponse[DocumentSummaryResponse]:
        parts = object_key.split("/")
        if len(parts) < 6 or parts[0] != "workspaces" or parts[2] != "channels" or parts[4] != "documents":
            raise HTTPException(status_code=400, detail="Invalid key")

        try:
            workspace_id = UUID(parts[1])
            channel_id = UUID(parts[3])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid key") from None

        channel = self._require_channel_member(current_user=current_user, channel_id=channel_id)
        if channel.workspace_id != workspace_id:
            raise HTTPException(status_code=403, detail="You do not have access to this file")

        document = self.document_repository.get_by_object_key(object_key)
        if not document:
            raise HTTPException(status_code=404, detail="File not found")

        allowed = {
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
            "text/markdown",
        }
        if (document.mime_type or "") not in allowed:
            raise HTTPException(status_code=400, detail="Unsupported document type for summarization")

        view = presign_get_object(object_key=object_key)
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
            resp = await client.get(view.view_url, follow_redirects=True)
            if resp.status_code == 404:
                raise HTTPException(status_code=404, detail="File missing in storage")
            resp.raise_for_status()
            data = resp.content

        try:
            text = extract_text_from_document_bytes(data, mime_type=document.mime_type)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)[:200]) from exc

        prompt_key = ((user_prompt or "").strip() or "").lower()[:200]
        cache_repo = ContentSummaryRepository(self.db)
        cached = cache_repo.get(workspace_id=workspace_id, kind="document", key=object_key, prompt=prompt_key)
        if cached and (cached.summary or "").strip():
            return ApiResponse(success=True, message="Document summarized", data=DocumentSummaryResponse(key=object_key, summary=cached.summary))

        summary = await self.document_summary_service.summarize(
            text=text,
            file_name=document.file_name,
            user_prompt=user_prompt,
        )
        if summary.strip():
            cache_repo.upsert(workspace_id=workspace_id, kind="document", key=object_key, prompt=prompt_key, summary=summary.strip())
            self.db.commit()
        return ApiResponse(success=True, message="Document summarized", data=DocumentSummaryResponse(key=object_key, summary=summary))

    async def stream_summarize_document(
        self,
        *,
        current_user: User,
        object_key: str,
        user_prompt: str | None,
        request: Request,
    ):
        import json

        def sse(event: str, data: dict) -> str:
            return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

        yield sse("generation_started", {"key": object_key})

        # Validate + access check (same as summarize_document).
        parts = object_key.split("/")
        if len(parts) < 6 or parts[0] != "workspaces" or parts[2] != "channels" or parts[4] != "documents":
            yield sse("error", {"message": "Invalid key"})
            return

        try:
            workspace_id = UUID(parts[1])
            channel_id = UUID(parts[3])
        except ValueError:
            yield sse("error", {"message": "Invalid key"})
            return

        channel = self._require_channel_member(current_user=current_user, channel_id=channel_id)
        if channel.workspace_id != workspace_id:
            yield sse("error", {"message": "You do not have access to this file"})
            return

        document = self.document_repository.get_by_object_key(object_key)
        if not document:
            yield sse("error", {"message": "File not found"})
            return

        allowed = {
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
            "text/markdown",
        }
        if (document.mime_type or "") not in allowed:
            yield sse("error", {"message": "Unsupported document type for summarization"})
            return

        prompt_key = ((user_prompt or "").strip() or "").lower()[:200]
        cache_repo = ContentSummaryRepository(self.db)
        cached = cache_repo.get(workspace_id=workspace_id, kind="document", key=object_key, prompt=prompt_key)
        if cached and (cached.summary or "").strip():
            yield sse("token", {"content": cached.summary})
            yield sse("generation_completed", {"key": object_key})
            return

        yield sse("source_loading", {"message": "Downloading document..."})
        view = presign_get_object(object_key=object_key)
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
                resp = await client.get(view.view_url, follow_redirects=True)
                if resp.status_code == 404:
                    yield sse("error", {"message": "File missing in storage"})
                    return
                resp.raise_for_status()
                data = resp.content
        except Exception as exc:
            yield sse("error", {"message": f"Download failed: {str(exc)[:200]}"})
            return

        yield sse("source_loading", {"message": "Extracting text..."})
        try:
            text = extract_text_from_document_bytes(data, mime_type=document.mime_type)
        except Exception as exc:
            yield sse("error", {"message": str(exc)[:200]})
            return

        # Stream model output.
        try:
            full = ""
            async for token in self.document_summary_service.stream(text=text, file_name=document.file_name, user_prompt=user_prompt):
                if await request.is_disconnected():
                    return
                full += token
                yield sse("token", {"content": token})
        except Exception as exc:
            yield sse("error", {"message": str(exc)[:200]})
            return

        if full.strip():
            cache_repo.upsert(workspace_id=workspace_id, kind="document", key=object_key, prompt=prompt_key, summary=full.strip())
            try:
                self.db.commit()
            except Exception:
                self.db.rollback()

        yield sse("generation_completed", {"key": object_key})

    async def stream_document_qa(
        self,
        *,
        current_user: User,
        object_key: str,
        question: str,
        request: Request,
    ):
        import json

        def sse(event: str, data: dict) -> str:
            return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

        if not (question or "").strip():
            yield sse("error", {"message": "Question is required"})
            return

        yield sse("generation_started", {"key": object_key})

        parts = object_key.split("/")
        if len(parts) < 6 or parts[0] != "workspaces" or parts[2] != "channels" or parts[4] != "documents":
            yield sse("error", {"message": "Invalid key"})
            return

        try:
            workspace_id = UUID(parts[1])
            channel_id = UUID(parts[3])
        except ValueError:
            yield sse("error", {"message": "Invalid key"})
            return

        channel = self._require_channel_member(current_user=current_user, channel_id=channel_id)
        if channel.workspace_id != workspace_id:
            yield sse("error", {"message": "You do not have access to this file"})
            return

        document = self.document_repository.get_by_object_key(object_key)
        if not document:
            yield sse("error", {"message": "File not found"})
            return

        allowed = {
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
            "text/markdown",
        }
        if (document.mime_type or "") not in allowed:
            yield sse("error", {"message": "Unsupported document type for Q&A"})
            return

        yield sse("source_loading", {"message": "Downloading document..."})
        view = presign_get_object(object_key=object_key)
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
                resp = await client.get(view.view_url, follow_redirects=True)
                if resp.status_code == 404:
                    yield sse("error", {"message": "File missing in storage"})
                    return
                resp.raise_for_status()
                data = resp.content
        except Exception as exc:
            yield sse("error", {"message": f"Download failed: {str(exc)[:200]}"})
            return

        yield sse("source_loading", {"message": "Extracting text..."})
        try:
            text = extract_text_from_document_bytes(data, mime_type=document.mime_type)
        except Exception as exc:
            yield sse("error", {"message": str(exc)[:200]})
            return

        answer = ""
        try:
            async for token in self.document_qa_service.stream(text=text, file_name=document.file_name, question=question):
                if await request.is_disconnected():
                    return
                answer += token
                yield sse("token", {"content": token})
        except Exception as exc:
            yield sse("error", {"message": str(exc)[:200]})
            return

        yield sse("generation_completed", {"key": object_key})
        # Final event with structured payload (optional for clients)
        yield sse("completed", DocumentQaResponse(key=object_key, question=question, answer=answer).model_dump())

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
