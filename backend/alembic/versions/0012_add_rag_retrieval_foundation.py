"""Add RAG retrieval foundation tables

Revision ID: 0012
Revises: 0011
Create Date: 2026-06-12
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, ENUM, UUID


revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    rag_scope = ENUM("agency_policy", name="rag_retrieval_scope", create_type=False)
    rag_scope.create(op.get_bind(), checkfirst=True)
    rag_confidence = ENUM(
        "sufficient",
        "insufficient",
        "fallback",
        name="rag_confidence_status",
        create_type=False,
    )
    rag_confidence.create(op.get_bind(), checkfirst=True)

    op.alter_column("rag_retrieval_logs", "document_id", existing_type=UUID(as_uuid=True), nullable=True)

    op.add_column("rag_retrieval_logs", sa.Column("actor_user_id", UUID(as_uuid=True), nullable=True))
    op.add_column("rag_retrieval_logs", sa.Column("actor_role", sa.String(length=64), nullable=False, server_default="agency_admin"))
    op.add_column("rag_retrieval_logs", sa.Column("retrieval_scope", rag_scope, nullable=False, server_default="agency_policy"))
    op.add_column("rag_retrieval_logs", sa.Column("selected_document_ids", ARRAY(UUID(as_uuid=True)), nullable=False, server_default="{}"))
    op.add_column("rag_retrieval_logs", sa.Column("selected_chunk_ids", ARRAY(UUID(as_uuid=True)), nullable=False, server_default="{}"))
    op.add_column("rag_retrieval_logs", sa.Column("selected_page_ids", ARRAY(UUID(as_uuid=True)), nullable=False, server_default="{}"))
    op.add_column("rag_retrieval_logs", sa.Column("reranker_used", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("rag_retrieval_logs", sa.Column("reranker_provider", sa.String(length=128), nullable=True))
    op.add_column("rag_retrieval_logs", sa.Column("fallback_reason", sa.String(length=256), nullable=True))
    op.add_column("rag_retrieval_logs", sa.Column("confidence_status", rag_confidence, nullable=False, server_default="sufficient"))
    op.add_column("rag_retrieval_logs", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))

    op.create_table(
        "rag_evaluation_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("run_label", sa.String(length=128), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_examples", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("passed_examples", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_examples", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("summary", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "rag_evaluation_examples",
        sa.Column("id", sa.String(length=128), primary_key=True),
        sa.Column("run_id", UUID(as_uuid=True), sa.ForeignKey("rag_evaluation_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("tenant_fixture", sa.String(length=128), nullable=False),
        sa.Column("expected_behavior", sa.String(length=64), nullable=False),
        sa.Column("expected_source_labels", ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("summary", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.alter_column("rag_retrieval_logs", "document_id", existing_type=UUID(as_uuid=True), nullable=False)

    op.drop_table("rag_evaluation_examples")
    op.drop_table("rag_evaluation_runs")

    op.drop_column("rag_retrieval_logs", "created_at")
    op.drop_column("rag_retrieval_logs", "confidence_status")
    op.drop_column("rag_retrieval_logs", "fallback_reason")
    op.drop_column("rag_retrieval_logs", "reranker_provider")
    op.drop_column("rag_retrieval_logs", "reranker_used")
    op.drop_column("rag_retrieval_logs", "selected_page_ids")
    op.drop_column("rag_retrieval_logs", "selected_chunk_ids")
    op.drop_column("rag_retrieval_logs", "selected_document_ids")
    op.drop_column("rag_retrieval_logs", "retrieval_scope")
    op.drop_column("rag_retrieval_logs", "actor_role")
    op.drop_column("rag_retrieval_logs", "actor_user_id")

    rag_confidence = sa.Enum(name="rag_confidence_status")
    rag_confidence.drop(op.get_bind(), checkfirst=True)
    rag_scope = sa.Enum(name="rag_retrieval_scope")
    rag_scope.drop(op.get_bind(), checkfirst=True)