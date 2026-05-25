"""make documents.file_url nullable

Revision ID: 3b4c2d1e9f10
Revises: 2a1f0d7c1a2b
Create Date: 2026-05-24
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "3b4c2d1e9f10"
down_revision = "2a1f0d7c1a2b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Legacy column. New code stores only object_key.
    op.alter_column("documents", "file_url", existing_type=sa.String(length=1000), nullable=True)


def downgrade() -> None:
    op.alter_column("documents", "file_url", existing_type=sa.String(length=1000), nullable=False)

