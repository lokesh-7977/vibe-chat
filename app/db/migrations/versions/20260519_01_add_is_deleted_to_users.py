"""add is_deleted to users

Revision ID: 20260519_01
Revises: 20260512_01
Create Date: 2026-05-19 18:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260519_01"
down_revision = "20260512_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "is_deleted")
