from uuid import UUID

from fastapi import APIRouter, Query, Request, status

from app.api.dependencies.channel import ChannelControllerDep
from app.api.dependencies.document import DocumentControllerDep
from app.api.dependencies.user import CurrentUserDep
from app.db.schemas.channel import ChannelCreate, ChannelResponse, ChannelUpdate
from app.db.schemas.channel_member import ChannelMemberCreate, ChannelMemberResponse
from app.db.schemas.common import ApiResponse
from app.db.schemas.document import DocumentResponse

router = APIRouter(prefix="/channels", tags=["channels"])


@router.get(
    "",
    response_model=ApiResponse[list[ChannelResponse]],
    status_code=status.HTTP_200_OK,
)
def list_channels(
    workspace_id: UUID,
    _request: Request,
    current_user: CurrentUserDep,
    controller: ChannelControllerDep,
):
    return controller.list_channels(current_user=current_user, workspace_id=workspace_id)


@router.post(
    "",
    response_model=ApiResponse[ChannelResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_channel(
    payload: ChannelCreate,
    _request: Request,
    current_user: CurrentUserDep,
    controller: ChannelControllerDep,
):
    return controller.create_channel(current_user=current_user, payload=payload)


@router.get(
    "/{channel_id}",
    response_model=ApiResponse[ChannelResponse],
    status_code=status.HTTP_200_OK,
)
def get_channel(
    channel_id: UUID,
    _request: Request,
    current_user: CurrentUserDep,
    controller: ChannelControllerDep,
):
    return controller.get_channel(current_user=current_user, channel_id=channel_id)


@router.patch(
    "/{channel_id}",
    response_model=ApiResponse[ChannelResponse],
    status_code=status.HTTP_200_OK,
)
def update_channel(
    channel_id: UUID,
    payload: ChannelUpdate,
    _request: Request,
    current_user: CurrentUserDep,
    controller: ChannelControllerDep,
):
    return controller.update_channel(
        current_user=current_user,
        channel_id=channel_id,
        payload=payload,
    )


@router.delete(
    "/{channel_id}",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
)
def delete_channel(
    channel_id: UUID,
    _request: Request,
    current_user: CurrentUserDep,
    controller: ChannelControllerDep,
):
    return controller.delete_channel(current_user=current_user, channel_id=channel_id)


@router.delete(
    "/{channel_id}/messages",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
)
def delete_channel_messages(
    channel_id: UUID,
    _request: Request,
    current_user: CurrentUserDep,
    controller: ChannelControllerDep,
):
    return controller.delete_channel_messages(current_user=current_user, channel_id=channel_id)


@router.get(
    "/{channel_id}/members",
    response_model=ApiResponse[list[ChannelMemberResponse]],
    status_code=status.HTTP_200_OK,
)
def list_channel_members(
    channel_id: UUID,
    _request: Request,
    current_user: CurrentUserDep,
    controller: ChannelControllerDep,
):
    return controller.list_channel_members(current_user=current_user, channel_id=channel_id)


@router.post(
    "/members",
    response_model=ApiResponse[ChannelMemberResponse],
    status_code=status.HTTP_201_CREATED,
)
def add_channel_member(
    payload: ChannelMemberCreate,
    _request: Request,
    current_user: CurrentUserDep,
    controller: ChannelControllerDep,
):
    return controller.add_channel_member(current_user=current_user, payload=payload)


@router.delete(
    "/{channel_id}/members/{user_id}",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
)
def remove_channel_member(
    channel_id: UUID,
    user_id: UUID,
    _request: Request,
    current_user: CurrentUserDep,
    controller: ChannelControllerDep,
):
    return controller.remove_channel_member(
        current_user=current_user,
        channel_id=channel_id,
        user_id=user_id,
    )


@router.get(
    "/{channel_id}/documents",
    response_model=ApiResponse[list[DocumentResponse]],
    status_code=status.HTTP_200_OK,
)
def list_channel_documents(
    channel_id: UUID,
    _request: Request,
    current_user: CurrentUserDep,
    document_controller: DocumentControllerDep,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return document_controller.list_channel_documents(
        current_user=current_user,
        channel_id=channel_id,
        limit=limit,
        offset=offset,
    )
