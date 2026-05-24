from uuid import UUID

from fastapi import APIRouter, Request, status

from app.api.dependencies.document import DocumentControllerDep
from app.api.dependencies.user import CurrentUserDep
from app.db.schemas.common import ApiResponse
from app.db.schemas.document import DocumentResponse
from fastapi import Query
from fastapi.responses import StreamingResponse

from pydantic import BaseModel

from app.db.schemas.upload import DocumentSummaryResponse, ImageSummaryResponse, ImageUrlResponse, PresignUploadRequest, PresignUploadResponse

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


@router.get(
    "/image-url",
    response_model=ApiResponse[ImageUrlResponse],
    status_code=status.HTTP_200_OK,
)
def image_url(
    _request: Request,
    current_user: CurrentUserDep,
    controller: DocumentControllerDep,
    key: str = Query(..., min_length=1),
):
    return controller.presign_image_url(current_user=current_user, object_key=key)


class SummarizeImageRequest(BaseModel):
    prompt: str | None = None


class DocumentQaRequest(BaseModel):
    question: str


@router.post(
    "/image-summary",
    response_model=ApiResponse[ImageSummaryResponse],
    status_code=status.HTTP_200_OK,
)
async def image_summary(
    payload: SummarizeImageRequest,
    _request: Request,
    current_user: CurrentUserDep,
    controller: DocumentControllerDep,
    key: str = Query(..., min_length=1),
):
    return await controller.summarize_image(current_user=current_user, object_key=key, user_prompt=payload.prompt)


@router.post(
    "/document-summary",
    response_model=ApiResponse[DocumentSummaryResponse],
    status_code=status.HTTP_200_OK,
)
async def document_summary(
    payload: SummarizeImageRequest,
    _request: Request,
    current_user: CurrentUserDep,
    controller: DocumentControllerDep,
    key: str = Query(..., min_length=1),
):
    return await controller.summarize_document(current_user=current_user, object_key=key, user_prompt=payload.prompt)


@router.post(
    "/image-summary/stream",
    status_code=status.HTTP_200_OK,
)
async def image_summary_stream(
    payload: SummarizeImageRequest,
    request: Request,
    current_user: CurrentUserDep,
    controller: DocumentControllerDep,
    key: str = Query(..., min_length=1),
):
    async def event_generator():
        async for chunk in controller.stream_summarize_image(
            current_user=current_user,
            object_key=key,
            user_prompt=payload.prompt,
            request=request,
        ):
            if await request.is_disconnected():
                continue
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/document-summary/stream",
    status_code=status.HTTP_200_OK,
)
async def document_summary_stream(
    payload: SummarizeImageRequest,
    request: Request,
    current_user: CurrentUserDep,
    controller: DocumentControllerDep,
    key: str = Query(..., min_length=1),
):
    async def event_generator():
        async for chunk in controller.stream_summarize_document(
            current_user=current_user,
            object_key=key,
            user_prompt=payload.prompt,
            request=request,
        ):
            if await request.is_disconnected():
                continue
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/document-qa/stream",
    status_code=status.HTTP_200_OK,
)
async def document_qa_stream(
    payload: DocumentQaRequest,
    request: Request,
    current_user: CurrentUserDep,
    controller: DocumentControllerDep,
    key: str = Query(..., min_length=1),
):
    async def event_generator():
        async for chunk in controller.stream_document_qa(
            current_user=current_user,
            object_key=key,
            question=payload.question,
            request=request,
        ):
            if await request.is_disconnected():
                continue
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
