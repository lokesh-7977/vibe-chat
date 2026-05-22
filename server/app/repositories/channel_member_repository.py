from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.channel_member import ChannelMember


class ChannelMemberRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, channel_id, user_id) -> ChannelMember | None:
        return self.db.execute(
            select(ChannelMember).where(
                ChannelMember.channel_id == channel_id,
                ChannelMember.user_id == user_id,
            )
        ).scalar_one_or_none()

    def list_for_channel(self, channel_id) -> list[ChannelMember]:
        return list(
            self.db.execute(
                select(ChannelMember).where(ChannelMember.channel_id == channel_id)
            ).scalars().all()
        )

    def create(self, member: ChannelMember) -> ChannelMember:
        self.db.add(member)
        return member

    def delete(self, member: ChannelMember) -> None:
        self.db.delete(member)

