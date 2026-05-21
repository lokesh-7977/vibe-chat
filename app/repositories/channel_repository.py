from sqlalchemy.orm import Session

from app.db.models.channel import Channel


class ChannelRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, channel: Channel) -> Channel:
        self.db.add(channel)
        return channel

