"""Expand search_logs for AI and voice search; add parking and floor to listings

Revision ID: 0016
Revises: 0015
Create Date: 2026-06-15
"""

from alembic import op
import sqlalchemy as sa


revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # Add parking and floor columns to listings
    op.add_column("listings", sa.Column("parking", sa.Integer(), nullable=True))
    op.add_column("listings", sa.Column("floor", sa.Integer(), nullable=True))

    # Expand search_logs with AI/voice search fields
    op.add_column(
        "search_logs",
        sa.Column("source_mode", sa.String(16), nullable=False, server_default="manual"),
    )
    op.add_column(
        "search_logs",
        sa.Column("event_type", sa.String(32), nullable=False, server_default="manual_search"),
    )
    op.add_column("search_logs", sa.Column("raw_query_redacted", sa.Text(), nullable=True))
    op.add_column("search_logs", sa.Column("transcript_redacted", sa.Text(), nullable=True))
    op.add_column("search_logs", sa.Column("intent", sa.JSON(), nullable=True))
    op.add_column("search_logs", sa.Column("provider", sa.String(64), nullable=True))
    op.add_column("search_logs", sa.Column("fallback_reason", sa.String(256), nullable=True))


def downgrade() -> None:
    # Remove search_logs columns
    op.drop_column("search_logs", "fallback_reason")
    op.drop_column("search_logs", "provider")
    op.drop_column("search_logs", "intent")
    op.drop_column("search_logs", "transcript_redacted")
    op.drop_column("search_logs", "raw_query_redacted")
    op.drop_column("search_logs", "event_type")
    op.drop_column("search_logs", "source_mode")

    # Remove listings columns
    op.drop_column("listings", "floor")
    op.drop_column("listings", "parking")
