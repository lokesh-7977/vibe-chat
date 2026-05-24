from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()

    def get_active_by_email(self, email: str) -> User | None:
        return self.db.execute(
            select(User).where(User.email == email, User.is_deleted.is_(False))
        ).scalar_one_or_none()

    def get_by_id(self, user_id: UUID) -> User | None:
        return self.db.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()

    def get_active_by_id(self, user_id: UUID) -> User | None:
        return self.db.execute(
            select(User).where(User.id == user_id, User.is_deleted.is_(False))
        ).scalar_one_or_none()

    def create(self, **user_data: object) -> User:
        db_user = User(**user_data)
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def list_active(self) -> list[User]:
        return list(
            self.db.execute(
                select(User).where(User.is_deleted.is_(False))
            ).scalars().all()
        )

    def save(self) -> None:
        self.db.commit()
