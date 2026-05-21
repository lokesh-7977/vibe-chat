import re

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.channel import Channel
from app.db.models.user import User
from app.db.models.workspace import Workspace
from app.db.models.workspace_member import WorkspaceMember
from app.db.schemas.common import ApiResponse
from app.db.schemas.workspace import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate
from app.repositories.channel_repository import ChannelRepository
from app.repositories.workspace_member_repository import WorkspaceMemberRepository
from app.repositories.workspace_repository import WorkspaceRepository


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\\s-]", "", value)
    value = re.sub(r"[\\s_-]+", "-", value)
    return value.strip("-") or "workspace"


class WorkspaceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.workspace_repository = WorkspaceRepository(db)
        self.workspace_member_repository = WorkspaceMemberRepository(db)
        self.channel_repository = ChannelRepository(db)

    def create_workspace(
        self,
        current_user: User,
        payload: WorkspaceCreate,
    ) -> ApiResponse[WorkspaceResponse]:
        slug_base = _slugify(payload.name)
        slug = slug_base
        suffix = 2
        while self.workspace_repository.get_by_slug(slug) is not None:
            slug = f"{slug_base}-{suffix}"
            suffix += 1

        workspace = Workspace(
            name=payload.name,
            slug=slug,
            description=payload.description,
            owner_id=current_user.id,
        )
        self.workspace_repository.create(workspace)
        self.db.flush()

        membership = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=current_user.id,
            role="owner",
        )
        self.workspace_member_repository.create(membership)

        default_channel = Channel(
            workspace_id=workspace.id,
            name="general",
            slug="general",
            description="Default channel",
            channel_type="general",
            created_by_id=current_user.id,
        )
        self.channel_repository.create(default_channel)

        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to create workspace",
            ) from exc

        self.db.refresh(workspace)
        return ApiResponse(
            success=True,
            message="Workspace created successfully",
            data=WorkspaceResponse.model_validate(workspace),
        )

    def list_workspaces(self, current_user: User) -> ApiResponse[list[WorkspaceResponse]]:
        workspaces = self.workspace_repository.list_for_user(current_user.id)
        return ApiResponse(
            success=True,
            message="Workspaces retrieved successfully",
            data=[WorkspaceResponse.model_validate(ws) for ws in workspaces],
        )

    def get_workspace(
        self,
        current_user: User,
        workspace_id,
    ) -> ApiResponse[WorkspaceResponse]:
        workspace = self.workspace_repository.get_by_id(workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found",
            )

        # Basic access: must be a member (owner membership is created at workspace creation).
        allowed = any(m.user_id == current_user.id for m in getattr(workspace, "members", []))
        if not allowed and workspace.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this workspace",
            )

        return ApiResponse(
            success=True,
            message="Workspace retrieved successfully",
            data=WorkspaceResponse.model_validate(workspace),
        )

    def update_workspace(
        self,
        current_user: User,
        workspace_id,
        payload: WorkspaceUpdate,
    ) -> ApiResponse[WorkspaceResponse]:
        workspace = self.workspace_repository.get_by_id(workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found",
            )

        if workspace.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the workspace owner can update this workspace",
            )

        if payload.name is not None:
            workspace.name = payload.name
        if payload.description is not None:
            workspace.description = payload.description

        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to update workspace",
            ) from exc

        self.db.refresh(workspace)
        return ApiResponse(
            success=True,
            message="Workspace updated successfully",
            data=WorkspaceResponse.model_validate(workspace),
        )

    def delete_workspace(
        self,
        current_user: User,
        workspace_id,
    ) -> ApiResponse[None]:
        workspace = self.workspace_repository.get_by_id(workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found",
            )

        if workspace.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the workspace owner can delete this workspace",
            )

        self.workspace_repository.delete(workspace)
        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to delete workspace",
            ) from exc

        return ApiResponse(
            success=True,
            message="Workspace deleted successfully",
            data=None,
        )
