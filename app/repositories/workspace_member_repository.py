from sqlalchemy.orm import Session

from app.db.models.workspace_member import WorkspaceMember


class WorkspaceMemberRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, membership: WorkspaceMember) -> WorkspaceMember:
        self.db.add(membership)
        return membership

