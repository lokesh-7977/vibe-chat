from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.workspace import Workspace
from app.db.models.workspace_member import WorkspaceMember


class WorkspaceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, workspace_id) -> Workspace | None:
        return self.db.execute(
            select(Workspace).where(Workspace.id == workspace_id)
        ).scalar_one_or_none()

    def get_by_slug(self, slug: str) -> Workspace | None:
        return self.db.execute(
            select(Workspace).where(Workspace.slug == slug)
        ).scalar_one_or_none()

    def list_for_user(self, user_id) -> list[Workspace]:
        return list(
            self.db.execute(
                select(Workspace)
                .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
                .where(WorkspaceMember.user_id == user_id)
                .order_by(Workspace.created_at.desc())
            ).scalars().all()
        )

    def create(self, workspace: Workspace) -> Workspace:
        self.db.add(workspace)
        return workspace

    def delete(self, workspace: Workspace) -> None:
        self.db.delete(workspace)
