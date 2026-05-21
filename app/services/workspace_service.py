import re

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.channel import Channel
from app.db.models.user import User
from app.db.models.workspace import Workspace
from app.db.models.workspace_member import WorkspaceMember
from app.db.schemas.common import ApiResponse
from app.db.schemas.workspace import WorkspaceCreate, WorkspaceResponse
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

