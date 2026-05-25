from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.workspace_member import WorkspaceMember


class WorkspaceMemberRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, membership: WorkspaceMember) -> WorkspaceMember:
        self.db.add(membership)
        return membership

    def list_for_workspace(self, workspace_id: UUID) -> list[WorkspaceMember]:
        return list(
            self.db.execute(
                select(WorkspaceMember).where(
                    WorkspaceMember.workspace_id == workspace_id
                )
            ).scalars().all()
        )

    def get_by_workspace_and_user(
        self, workspace_id: UUID, user_id: UUID
    ) -> WorkspaceMember | None:
        return self.db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        ).scalar_one_or_none()

    def delete(self, member: WorkspaceMember) -> None:
        self.db.delete(member)

