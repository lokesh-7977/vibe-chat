import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Call(Base):
    __tablename__ = "calls"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )

    channel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("channels.id", ondelete="SET NULL"),
        nullable=True,
    )

    started_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    participants = relationship("CallParticipant", back_populates="call", cascade="all, delete-orphan")
    transcripts = relationship("CallTranscript", back_populates="call", cascade="all, delete-orphan")
    summaries = relationship("CallSummary", back_populates="call", cascade="all, delete-orphan")


class CallParticipant(Base):
    __tablename__ = "call_participants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_muted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_camera_on: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_screen_sharing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    call = relationship("Call", back_populates="participants")


class CallTranscript(Base):
    __tablename__ = "call_transcripts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.id", ondelete="CASCADE"),
        nullable=False,
    )

    speaker_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    call = relationship("Call", back_populates="transcripts")


class CallSummary(Base):
    __tablename__ = "call_summaries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.id", ondelete="CASCADE"),
        nullable=False,
    )

    summary: Mapped[str] = mapped_column(Text, nullable=False)
    decisions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    action_items: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    call = relationship("Call", back_populates="summaries")