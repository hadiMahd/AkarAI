"""Add agency AI job tracking, lead reply, comparison summary tables, and tool invocation log

Revision ID: 0018
Revises: 0017
Create Date: 2026-06-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID


revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "agency_ai_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("job_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("actor_user_id", UUID(as_uuid=True), nullable=True),
        sa.Column("source_reference_id", UUID(as_uuid=True), nullable=True),
        sa.Column("result_payload", JSON, nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_agency_ai_jobs_tenant", "agency_ai_jobs", ["tenant_id"])
    op.create_index("ix_agency_ai_jobs_actor", "agency_ai_jobs", ["actor_user_id"])
    op.create_index("ix_agency_ai_jobs_status", "agency_ai_jobs", ["status"])
    op.create_index("ix_agency_ai_jobs_job_type", "agency_ai_jobs", ["job_type"])

    op.create_table(
        "lead_reply_drafts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("lead_id", UUID(as_uuid=True), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agency_tenant_id", UUID(as_uuid=True), sa.ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("subject", sa.String(255), nullable=True),
        sa.Column("draft_text", sa.Text(), nullable=False),
        sa.Column("guardrail_status", sa.String(32), nullable=True),
        sa.Column("generation_provider", sa.String(64), nullable=True),
        sa.Column("blocked_reason", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_lead_reply_drafts_lead", "lead_reply_drafts", ["lead_id"])
    op.create_index("ix_lead_reply_drafts_tenant", "lead_reply_drafts", ["agency_tenant_id"])

    op.create_table(
        "comparison_summaries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("listing_ids", JSON, nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("key_differences", JSON, nullable=True),
        sa.Column("best_fit_notes", JSON, nullable=True),
        sa.Column("guardrail_status", sa.String(32), nullable=True),
        sa.Column("generation_provider", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_comparison_summaries_user", "comparison_summaries", ["user_id"])

    op.create_table(
        "agency_assistant_tool_invocations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("actor_user_id", UUID(as_uuid=True), nullable=True),
        sa.Column("tool_name", sa.String(64), nullable=False),
        sa.Column("input_summary", JSON, nullable=True),
        sa.Column("output_summary", JSON, nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("failure_reason", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_agency_assistant_tool_invocations_tenant", "agency_assistant_tool_invocations", ["tenant_id"])
    op.create_index("ix_agency_assistant_tool_invocations_tool", "agency_assistant_tool_invocations", ["tool_name"])


def downgrade() -> None:
    op.drop_index("ix_agency_assistant_tool_invocations_tool", table_name="agency_assistant_tool_invocations")
    op.drop_index("ix_agency_assistant_tool_invocations_tenant", table_name="agency_assistant_tool_invocations")
    op.drop_table("agency_assistant_tool_invocations")

    op.drop_index("ix_comparison_summaries_user", table_name="comparison_summaries")
    op.drop_table("comparison_summaries")

    op.drop_index("ix_lead_reply_drafts_tenant", table_name="lead_reply_drafts")
    op.drop_index("ix_lead_reply_drafts_lead", table_name="lead_reply_drafts")
    op.drop_table("lead_reply_drafts")

    op.drop_index("ix_agency_ai_jobs_job_type", table_name="agency_ai_jobs")
    op.drop_index("ix_agency_ai_jobs_status", table_name="agency_ai_jobs")
    op.drop_index("ix_agency_ai_jobs_actor", table_name="agency_ai_jobs")
    op.drop_index("ix_agency_ai_jobs_tenant", table_name="agency_ai_jobs")
    op.drop_table("agency_ai_jobs")
