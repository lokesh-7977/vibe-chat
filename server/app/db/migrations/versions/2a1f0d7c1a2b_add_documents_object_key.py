"""add documents.object_key

Revision ID: 2a1f0d7c1a2b
Revises: 8538096e73ef
Create Date: 2026-05-24
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "2a1f0d7c1a2b"
down_revision = "8538096e73ef"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Existing databases created before we switched to storing only object_key
    # have a non-null documents.file_url. Add object_key and backfill.
    op.add_column("documents", sa.Column("object_key", sa.String(length=1000), nullable=True))

    # Best-effort backfill: store whatever was previously in file_url as the key.
    # This keeps old rows accessible and avoids breaking on NOT NULL immediately.
    op.execute("UPDATE documents SET object_key = file_url WHERE object_key IS NULL")

    op.alter_column("documents", "object_key", existing_type=sa.String(length=1000), nullable=False)


def downgrade() -> None:
    op.drop_column("documents", "object_key")

