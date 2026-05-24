from uuid import UUID

from fastapi import APIRouter, Request, status

from app.api.dependencies.user import CurrentUserDep
from app.api.dependencies.workspace import WorkspaceControllerDep
from app.db.schemas.common import ApiResponse
from app.db.schemas.workspace import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate
from app.db.schemas.workspace_member import (
    WorkspaceMemberCreate,
    WorkspaceMemberResponse,
)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

@router.post(
    "",
    response_model=ApiResponse[WorkspaceResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_workspace(
    payload: WorkspaceCreate,
    _request: Request,
    current_user: CurrentUserDep,
    controller: WorkspaceControllerDep,
):
    return controller.create_workspace(current_user=current_user, payload=payload)

@router.get(
    "",
    response_model=ApiResponse[list[WorkspaceResponse]],
    status_code=status.HTTP_200_OK,
)
def list_workspaces(
    _request: Request,
    current_user: CurrentUserDep,
    controller: WorkspaceControllerDep,
):
    return controller.list_workspaces(current_user=current_user)


@router.get(
    "/{workspace_id}",
    response_model=ApiResponse[WorkspaceResponse],
    status_code=status.HTTP_200_OK,
)
def get_workspace(
    workspace_id: UUID,
    _request: Request,
    current_user: CurrentUserDep,
    controller: WorkspaceControllerDep,
):
    return controller.get_workspace(current_user=current_user, workspace_id=workspace_id)


@router.patch(
    "/{workspace_id}",
    response_model=ApiResponse[WorkspaceResponse],
    status_code=status.HTTP_200_OK,
)
def update_workspace(
    workspace_id: UUID,
    payload: WorkspaceUpdate,
    _request: Request,
    current_user: CurrentUserDep,
    controller: WorkspaceControllerDep,
):
    return controller.update_workspace(
        current_user=current_user,
        workspace_id=workspace_id,
        payload=payload,
    )


@router.delete(
    "/{workspace_id}",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
)
def delete_workspace(
    workspace_id: UUID,
    _request: Request,
    current_user: CurrentUserDep,
    controller: WorkspaceControllerDep,
):
    return controller.delete_workspace(
        current_user=current_user,
        workspace_id=workspace_id,
    )


@router.get(
    "/{workspace_id}/members",
    response_model=ApiResponse[list[WorkspaceMemberResponse]],
    status_code=status.HTTP_200_OK,
)
def list_workspace_members(
    workspace_id: UUID,
    _request: Request,
    current_user: CurrentUserDep,
    controller: WorkspaceControllerDep,
):
    return controller.list_members(
        current_user=current_user,
        workspace_id=workspace_id,
    )


@router.post(
    "/{workspace_id}/members",
    response_model=ApiResponse[WorkspaceMemberResponse],
    status_code=status.HTTP_201_CREATED,
)
def add_workspace_member(
    workspace_id: UUID,
    payload: WorkspaceMemberCreate,
    _request: Request,
    current_user: CurrentUserDep,
    controller: WorkspaceControllerDep,
):
    return controller.add_member(
        current_user=current_user,
        workspace_id=workspace_id,
        payload=payload,
    )
