from uuid import UUID

from fastapi import APIRouter, Request, status

from app.api.dependencies.document import DocumentControllerDep
from app.api.dependencies.user import CurrentUserDep
from app.db.schemas.common import ApiResponse
from app.db.schemas.document import DocumentResponse
from app.db.schemas.upload import PresignUploadRequest, PresignUploadResponse

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post(
    "/presign",
    response_model=ApiResponse[PresignUploadResponse],
    status_code=status.HTTP_201_CREATED,
)
def presign_upload(
    payload: PresignUploadRequest,
    _request: Request,
    current_user: CurrentUserDep,
    controller: DocumentControllerDep,
):
    return controller.presign_upload(current_user=current_user, payload=payload)


@router.post(
    "/{document_id}/complete",
    response_model=ApiResponse[DocumentResponse],
    status_code=status.HTTP_200_OK,
)
def complete_upload(
    document_id: UUID,
    _request: Request,
    current_user: CurrentUserDep,
    controller: DocumentControllerDep,
):
    return controller.complete_upload(current_user=current_user, document_id=document_id)
