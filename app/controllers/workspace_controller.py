from app.db.models.user import User
from app.db.schemas.common import ApiResponse
from app.db.schemas.workspace import WorkspaceCreate, WorkspaceResponse
from app.services.workspace_service import WorkspaceService


class WorkspaceController:
    def __init__(self, workspace_service: WorkspaceService) -> None:
        self.workspace_service = workspace_service

    def create_workspace(
        self,
        current_user: User,
        payload: WorkspaceCreate,
    ) -> ApiResponse[WorkspaceResponse]:
        return self.workspace_service.create_workspace(
            current_user=current_user,
            payload=payload,
        )

