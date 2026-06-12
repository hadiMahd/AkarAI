"""Add media processing fields, derivatives, and audit log for listing photos

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add media processing fields to listing_photo_metadata
    op.add_column(
        "listing_photo_metadata",
        sa.Column("content_type", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "listing_photo_metadata",
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
    )
    op.add_column(
        "listing_photo_metadata",
        sa.Column("width", sa.Integer(), nullable=True),
    )
    op.add_column(
        "listing_photo_metadata",
        sa.Column("height", sa.Integer(), nullable=True),
    )
    op.add_column(
        "listing_photo_metadata",
        sa.Column("moderation_label", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "listing_photo_metadata",
        sa.Column("moderation_score", sa.Numeric(4, 3), nullable=True),
    )
    op.add_column(
        "listing_photo_metadata",
        sa.Column("quality_score", sa.Numeric(10, 4), nullable=True),
    )

    # Create listing_photo_derivatives table
    op.create_table(
        "listing_photo_derivatives",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("listing_photo_metadata_id", UUID(as_uuid=True), sa.ForeignKey("listing_photo_metadata.id", ondelete="CASCADE"), nullable=False),
        sa.Column("variant_name", sa.String(length=64), nullable=False),
        sa.Column("object_key", sa.String(length=512), nullable=False),
        sa.Column("format", sa.String(length=16), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("is_public_safe", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_listing_photo_derivatives_photo_id", "listing_photo_derivatives", ["listing_photo_metadata_id"])

    # Create media_audit_logs table
    op.create_table(
        "media_audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agency_tenant_id", UUID(as_uuid=True), sa.ForeignKey("agency_tenants.id", ondelete="SET NULL"), nullable=False),
        sa.Column("actor_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("listing_photo_metadata_id", UUID(as_uuid=True), sa.ForeignKey("listing_photo_metadata.id", ondelete="SET NULL"), nullable=False),
        sa.Column("event_name", sa.String(length=128), nullable=False),
        sa.Column("result", sa.String(length=32), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_media_audit_logs_tenant_id", "media_audit_logs", ["agency_tenant_id"])
    op.create_index("ix_media_audit_logs_photo_id", "media_audit_logs", ["listing_photo_metadata_id"])
    op.create_index("ix_media_audit_logs_event_name", "media_audit_logs", ["event_name"])


def downgrade() -> None:
    op.drop_index("ix_media_audit_logs_event_name", "media_audit_logs")
    op.drop_index("ix_media_audit_logs_photo_id", "media_audit_logs")
    op.drop_index("ix_media_audit_logs_tenant_id", "media_audit_logs")
    op.drop_table("media_audit_logs")

    op.drop_index("ix_listing_photo_derivatives_photo_id", "listing_photo_derivatives")
    op.drop_table("listing_photo_derivatives")

    op.drop_column("listing_photo_metadata", "quality_score")
    op.drop_column("listing_photo_metadata", "moderation_score")
    op.drop_column("listing_photo_metadata", "moderation_label")
    op.drop_column("listing_photo_metadata", "height")
    op.drop_column("listing_photo_metadata", "width")
    op.drop_column("listing_photo_metadata", "file_size_bytes")
    op.drop_column("listing_photo_metadata", "content_type")