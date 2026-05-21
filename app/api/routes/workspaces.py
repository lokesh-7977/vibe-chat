from fastapi import APIRouter, Request, status

from app.api.dependencies.user import CurrentUserDep
from app.api.dependencies.workspace import WorkspaceControllerDep
from app.db.schemas.common import ApiResponse
from app.db.schemas.workspace import WorkspaceCreate, WorkspaceResponse

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

