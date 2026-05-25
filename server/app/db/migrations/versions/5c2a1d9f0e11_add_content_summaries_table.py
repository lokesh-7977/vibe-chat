"""add content_summaries table

Revision ID: 5c2a1d9f0e11
Revises: 4f0e7c9b6a2d
Create Date: 2026-05-24
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "5c2a1d9f0e11"
down_revision = "4f0e7c9b6a2d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "content_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("key", sa.String(length=1200), nullable=False),
        sa.Column("prompt", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("workspace_id", "kind", "key", "prompt", name="uq_content_summaries_workspace_kind_key_prompt"),
    )
    op.create_index(op.f("ix_content_summaries_workspace_id"), "content_summaries", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_content_summaries_kind"), "content_summaries", ["kind"], unique=False)
    op.create_index(op.f("ix_content_summaries_key"), "content_summaries", ["key"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_content_summaries_key"), table_name="content_summaries")
    op.drop_index(op.f("ix_content_summaries_kind"), table_name="content_summaries")
    op.drop_index(op.f("ix_content_summaries_workspace_id"), table_name="content_summaries")
    op.drop_table("content_summaries")

