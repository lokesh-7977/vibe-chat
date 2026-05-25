"""add channel_summaries table

Revision ID: 4f0e7c9b6a2d
Revises: 3b4c2d1e9f10
Create Date: 2026-05-24
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "4f0e7c9b6a2d"
down_revision = "3b4c2d1e9f10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "channel_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "channel_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("channels.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("last_message_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("channel_id", name="uq_channel_summaries_channel_id"),
    )
    op.create_index(op.f("ix_channel_summaries_channel_id"), "channel_summaries", ["channel_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_channel_summaries_channel_id"), table_name="channel_summaries")
    op.drop_table("channel_summaries")

