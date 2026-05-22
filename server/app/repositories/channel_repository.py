from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.channel import Channel


class ChannelRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, channel_id) -> Channel | None:
        return self.db.execute(
            select(Channel).where(Channel.id == channel_id)
        ).scalar_one_or_none()

    def list_for_workspace(self, workspace_id) -> list[Channel]:
        return list(
            self.db.execute(
                select(Channel)
                .where(Channel.workspace_id == workspace_id)
                .order_by(Channel.created_at.asc())
            ).scalars().all()
        )

    def create(self, channel: Channel) -> Channel:
        self.db.add(channel)
        return channel

    def delete(self, channel: Channel) -> None:
        self.db.delete(channel)
