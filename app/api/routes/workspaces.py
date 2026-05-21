from uuid import UUID

from fastapi import APIRouter, Request, status

from app.api.dependencies.user import CurrentUserDep
from app.api.dependencies.workspace import WorkspaceControllerDep
from app.db.schemas.common import ApiResponse
from app.db.schemas.workspace import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate

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
