from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models.activity import Activity


class ActivityRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, activity_id) -> Activity | None:
        return self.db.execute(
            select(Activity)
            .options(joinedload(Activity.actor))
            .where(Activity.id == activity_id)
        ).scalar_one_or_none()

    def list_for_channel(
        self,
        channel_id,
        limit: int,
        offset: int,
        include_deleted: bool = False,
    ) -> list[Activity]:
        stmt = (
            select(Activity)
            .options(joinedload(Activity.actor))
            .where(Activity.channel_id == channel_id)
            .where(Activity.activity_type != "ai_message")
        )
        if not include_deleted:
            stmt = stmt.where(Activity.deleted_at.is_(None))
        stmt = stmt.order_by(Activity.created_at.desc()).limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars().all())

    def create(self, activity: Activity) -> Activity:
        self.db.add(activity)
        return activity

    @staticmethod
    def soft_delete(activity: Activity, deleted_at: datetime) -> None:
        activity.deleted_at = deleted_at
