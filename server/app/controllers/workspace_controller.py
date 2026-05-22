from app.db.models.user import User
from app.db.schemas.common import ApiResponse
from app.db.schemas.workspace import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate
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

    def list_workspaces(self, current_user: User) -> ApiResponse[list[WorkspaceResponse]]:
        return self.workspace_service.list_workspaces(current_user=current_user)

    def get_workspace(
        self,
        current_user: User,
        workspace_id,
    ) -> ApiResponse[WorkspaceResponse]:
        return self.workspace_service.get_workspace(
            current_user=current_user,
            workspace_id=workspace_id,
        )

    def update_workspace(
        self,
        current_user: User,
        workspace_id,
        payload: WorkspaceUpdate,
    ) -> ApiResponse[WorkspaceResponse]:
        return self.workspace_service.update_workspace(
            current_user=current_user,
            workspace_id=workspace_id,
            payload=payload,
        )

    def delete_workspace(
        self,
        current_user: User,
        workspace_id,
    ) -> ApiResponse[None]:
        return self.workspace_service.delete_workspace(
            current_user=current_user,
            workspace_id=workspace_id,
        )
