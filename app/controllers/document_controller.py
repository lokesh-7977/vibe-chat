from uuid import UUID

from app.db.models.user import User
from app.db.schemas.common import ApiResponse
from app.db.schemas.document import DocumentResponse
from app.db.schemas.upload import PresignUploadRequest, PresignUploadResponse
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
