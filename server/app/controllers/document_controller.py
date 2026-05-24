from uuid import UUID

from app.db.models.user import User
from app.db.schemas.common import ApiResponse
from app.db.schemas.document import DocumentResponse
from fastapi import Request

from app.db.schemas.upload import DocumentSummaryResponse, ImageSummaryResponse, ImageUrlResponse, PresignUploadRequest, PresignUploadResponse
from app.services.document_service import DocumentService


class DocumentController:
    def __init__(self, document_service: DocumentService) -> None:
        self.document_service = document_service

    def presign_upload(
        self,
        current_user: User,
        payload: PresignUploadRequest,
    ) -> ApiResponse[PresignUploadResponse]:
        return self.document_service.presign_upload(
            current_user=current_user,
            payload=payload,
        )

    def complete_upload(
        self,
        current_user: User,
        document_id,
    ) -> ApiResponse[DocumentResponse]:
        return self.document_service.complete_upload(
            current_user=current_user,
            document_id=document_id,
        )

    def presign_image_url(
        self,
        current_user: User,
        object_key: str,
    ) -> ApiResponse[ImageUrlResponse]:
        return self.document_service.presign_image_url(
            current_user=current_user,
            object_key=object_key,
        )

    async def summarize_image(
        self,
        current_user: User,
        object_key: str,
        user_prompt: str | None,
    ) -> ApiResponse[ImageSummaryResponse]:
        return await self.document_service.summarize_image(
            current_user=current_user,
            object_key=object_key,
            user_prompt=user_prompt,
        )

    def stream_summarize_image(
        self,
        *,
        current_user: User,
        object_key: str,
        user_prompt: str | None,
        request: Request,
    ):
        return self.document_service.stream_summarize_image(
            current_user=current_user,
            object_key=object_key,
            user_prompt=user_prompt,
            request=request,
        )

    async def summarize_document(
        self,
        current_user: User,
        object_key: str,
        user_prompt: str | None,
    ) -> ApiResponse[DocumentSummaryResponse]:
        return await self.document_service.summarize_document(
            current_user=current_user,
            object_key=object_key,
            user_prompt=user_prompt,
        )

    def stream_summarize_document(
        self,
        *,
        current_user: User,
        object_key: str,
        user_prompt: str | None,
        request: Request,
    ):
        return self.document_service.stream_summarize_document(
            current_user=current_user,
            object_key=object_key,
            user_prompt=user_prompt,
            request=request,
        )

    def stream_document_qa(
        self,
        *,
        current_user: User,
        object_key: str,
        question: str,
        request: Request,
    ):
        return self.document_service.stream_document_qa(
            current_user=current_user,
            object_key=object_key,
            question=question,
            request=request,
        )

    def list_channel_documents(
        self,
        current_user: User,
        channel_id,
        limit: int,
        offset: int,
    ) -> ApiResponse[list[DocumentResponse]]:
        return self.document_service.list_channel_documents(
            current_user=current_user,
            channel_id=channel_id,
            limit=limit,
            offset=offset,
        )
