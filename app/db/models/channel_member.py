import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ChannelMember(Base):
    __tablename__ = "channel_members"

    __table_args__ = (
        UniqueConstraint("channel_id", "user_id", name="uq_channel_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(String(30), default="member", nullable=False)

    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    channel = relationship("Channel", back_populates="members")
    user = relationship("User", back_populates="channel_memberships")