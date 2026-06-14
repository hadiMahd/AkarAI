"""Add text column to rag_chunks for retrieval text_preview

Revision ID: 0013
Revises: 0012
Create Date: 2026-06-12
"""

from alembic import op
import sqlalchemy as sa


revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column("rag_chunks", sa.Column("text", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("rag_chunks", "text")
