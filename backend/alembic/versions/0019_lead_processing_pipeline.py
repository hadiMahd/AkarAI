"""Add lead processing pipeline fields: retry_count, last_error, idempotency_key, analytics indexes

Revision ID: 0019
Revises: 0018
Create Date: 2026-06-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID


revision: str = "0019"
down_revision: str | None = "0018"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # LeadSpamResult: add retry_count, last_error, idempotency_key
    op.add_column("lead_spam_results", sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("lead_spam_results", sa.Column("last_error", sa.Text(), nullable=True))
    op.add_column("lead_spam_results", sa.Column("idempotency_key", sa.String(128), nullable=True))

    # LeadLevelResult: add retry_count, last_error, idempotency_key
    op.add_column("lead_level_results", sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("lead_level_results", sa.Column("last_error", sa.Text(), nullable=True))
    op.add_column("lead_level_results", sa.Column("idempotency_key", sa.String(128), nullable=True))

    # Lead: add processing_status for auto-repoll support
    op.add_column("leads", sa.Column("processing_status", sa.String(32), nullable=False, server_default="pending"))

    # Analytics indexes
    op.create_index("ix_lead_spam_results_tenant_status", "lead_spam_results", ["agency_tenant_id", "status"])
    op.create_index("ix_lead_spam_results_tenant_label", "lead_spam_results", ["agency_tenant_id", "label"])
    op.create_index("ix_lead_level_results_tenant_status", "lead_level_results", ["agency_tenant_id", "status"])
    op.create_index("ix_lead_level_results_tenant_level", "lead_level_results", ["agency_tenant_id", "level"])
    op.create_index("ix_leads_processing_status", "leads", ["processing_status"])
    op.create_index("ix_lead_spam_results_idempotency", "lead_spam_results", ["idempotency_key"], unique=False)
    op.create_index("ix_lead_level_results_idempotency", "lead_level_results", ["idempotency_key"], unique=False)

    # Unique constraint on idempotency key per lead_id+stage for idempotent callbacks
    op.create_index("ix_lead_spam_results_lead_stage", "lead_spam_results", ["lead_id", "idempotency_key"], unique=False)
    op.create_index("ix_lead_level_results_lead_stage", "lead_level_results", ["lead_id", "idempotency_key"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_lead_level_results_lead_stage", table_name="lead_level_results")
    op.drop_index("ix_lead_spam_results_lead_stage", table_name="lead_spam_results")
    op.drop_index("ix_lead_level_results_idempotency", table_name="lead_level_results")
    op.drop_index("ix_lead_spam_results_idempotency", table_name="lead_spam_results")
    op.drop_index("ix_leads_processing_status", table_name="leads")
    op.drop_index("ix_lead_level_results_tenant_level", table_name="lead_level_results")
    op.drop_index("ix_lead_level_results_tenant_status", table_name="lead_level_results")
    op.drop_index("ix_lead_spam_results_tenant_label", table_name="lead_spam_results")
    op.drop_index("ix_lead_spam_results_tenant_status", table_name="lead_spam_results")

    op.drop_column("leads", "processing_status")
    op.drop_column("lead_level_results", "idempotency_key")
    op.drop_column("lead_level_results", "last_error")
    op.drop_column("lead_level_results", "retry_count")
    op.drop_column("lead_spam_results", "idempotency_key")
    op.drop_column("lead_spam_results", "last_error")
    op.drop_column("lead_spam_results", "retry_count")
