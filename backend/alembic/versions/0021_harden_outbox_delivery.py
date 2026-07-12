"""Harden outbox claims and consumer idempotency.

Revision ID: 0021
Revises: 0020
Create Date: 2026-07-12
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "0021"
down_revision: str | None = "0020"
branch_labels: str | None = None
depends_on: str | None = None

LEASE_SECONDS = 900


def upgrade() -> None:
    op.add_column(
        "outbox_events", sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "outbox_events", sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("outbox_events", sa.Column("claim_token", UUID(as_uuid=True), nullable=True))
    op.add_column(
        "inbox_events", sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("inbox_events", sa.Column("claim_token", UUID(as_uuid=True), nullable=True))
    op.add_column(
        "media_audit_logs",
        sa.Column(
            "outbox_event_id",
            UUID(as_uuid=True),
            sa.ForeignKey("outbox_events.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Preserve a live worker's ownership while making genuinely abandoned work reclaimable.
    op.execute(
        sa.text(
            "UPDATE outbox_events "
            "SET claimed_at = updated_at, lease_expires_at = updated_at + (:lease * INTERVAL '1 second') "
            "WHERE status = 'processing'"
        ).bindparams(lease=LEASE_SECONDS)
    )
    op.execute(
        sa.text(
            "UPDATE inbox_events "
            "SET lease_expires_at = updated_at + (:lease * INTERVAL '1 second') "
            "WHERE status = 'processing'"
        ).bindparams(lease=LEASE_SECONDS)
    )

    op.create_index("ix_outbox_events_claimable", "outbox_events", ["status", "available_at"])
    op.create_index("ix_outbox_events_processing_lease", "outbox_events", ["lease_expires_at"])
    op.create_index("ix_inbox_events_processing_lease", "inbox_events", ["lease_expires_at"])
    op.create_index(
        "uq_media_audit_logs_outbox_event",
        "media_audit_logs",
        ["outbox_event_id", "event_name"],
        unique=True,
        postgresql_where=sa.text("outbox_event_id IS NOT NULL"),
    )
    op.execute(
        """
        DELETE FROM listing_photo_derivatives AS duplicate
        USING (
            SELECT id,
                   row_number() OVER (
                       PARTITION BY listing_photo_metadata_id, variant_name
                       ORDER BY created_at DESC, id DESC
                   ) AS duplicate_rank
            FROM listing_photo_derivatives
        ) AS ranked
        WHERE duplicate.id = ranked.id AND ranked.duplicate_rank > 1
        """
    )
    op.create_unique_constraint(
        "uq_listing_photo_derivative_variant",
        "listing_photo_derivatives",
        ["listing_photo_metadata_id", "variant_name"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_listing_photo_derivative_variant", "listing_photo_derivatives", type_="unique"
    )
    op.drop_index("uq_media_audit_logs_outbox_event", table_name="media_audit_logs")
    op.drop_index("ix_inbox_events_processing_lease", table_name="inbox_events")
    op.drop_index("ix_outbox_events_processing_lease", table_name="outbox_events")
    op.drop_index("ix_outbox_events_claimable", table_name="outbox_events")
    op.drop_column("inbox_events", "claim_token")
    op.drop_column("inbox_events", "lease_expires_at")
    op.drop_column("media_audit_logs", "outbox_event_id")
    op.drop_column("outbox_events", "claim_token")
    op.drop_column("outbox_events", "lease_expires_at")
    op.drop_column("outbox_events", "claimed_at")
