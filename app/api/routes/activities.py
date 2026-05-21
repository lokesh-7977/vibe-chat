from uuid import UUID

from fastapi import APIRouter, Query, Request, status

from app.api.dependencies.activity import ActivityControllerDep
from app.api.dependencies.user import CurrentUserDep
from app.db.schemas.activity import ActivityCreateRequest, ActivityResponse, ActivityUpdate
from app.db.schemas.common import ApiResponse

router = APIRouter(tags=["activities"])


@router.post(
    "/channels/{channel_id}/activities",
    response_model=ApiResponse[ActivityResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_channel_activity(
    channel_id: UUID,
    payload: ActivityCreateRequest,
    _request: Request,
    current_user: CurrentUserDep,
    controller: ActivityControllerDep,
):
    return controller.create_activity(
        current_user=current_user,
        channel_id=channel_id,
        payload=payload,
    )


@router.get(
    "/channels/{channel_id}/activities",
    response_model=ApiResponse[list[ActivityResponse]],
    status_code=status.HTTP_200_OK,
)
def list_channel_activities(
    channel_id: UUID,
    _request: Request,
    current_user: CurrentUserDep,
    controller: ActivityControllerDep,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return controller.list_channel_activities(
        current_user=current_user,
        channel_id=channel_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/activities/{activity_id}",
    response_model=ApiResponse[ActivityResponse],
    status_code=status.HTTP_200_OK,
)
def get_activity(
    activity_id: UUID,
    _request: Request,
    current_user: CurrentUserDep,
    controller: ActivityControllerDep,
):
    return controller.get_activity(current_user=current_user, activity_id=activity_id)


@router.patch(
    "/activities/{activity_id}",
    response_model=ApiResponse[ActivityResponse],
    status_code=status.HTTP_200_OK,
)
def update_activity(
    activity_id: UUID,
    payload: ActivityUpdate,
    _request: Request,
    current_user: CurrentUserDep,
    controller: ActivityControllerDep,
):
    return controller.update_activity(
        current_user=current_user,
        activity_id=activity_id,
        payload=payload,
    )


@router.delete(
    "/activities/{activity_id}",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
)
def delete_activity(
    activity_id: UUID,
    _request: Request,
    current_user: CurrentUserDep,
    controller: ActivityControllerDep,
):
    return controller.delete_activity(current_user=current_user, activity_id=activity_id)

