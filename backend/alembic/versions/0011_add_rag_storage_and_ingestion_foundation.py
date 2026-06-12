"""Add RAG storage and ingestion foundation tables

Revision ID: 0011
Revises: 0010
Create Date: 2026-06-12
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import ARRAY, ENUM, UUID


revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    rag_document_status = ENUM(
        "pending",
        "processing",
        "processed",
        "failed",
        name="rag_document_status",
        create_type=False,
    )
    rag_document_status.create(op.get_bind(), checkfirst=True)

    rag_chunk_status = ENUM("active", "orphaned", name="rag_chunk_status", create_type=False)
    rag_chunk_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "rag_documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("status", rag_document_status, nullable=False, server_default="pending"),
        sa.Column("blob_path", sa.String(1024), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_rag_documents_tenant_id", "rag_documents", ["tenant_id"])
    op.create_index("ix_rag_documents_tenant_status", "rag_documents", ["tenant_id", "status"])

    op.create_table(
        "rag_pages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("rag_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("blob_path", sa.String(1024), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_rag_pages_document_id", "rag_pages", ["document_id"])
    op.create_index("ix_rag_pages_tenant_id", "rag_pages", ["tenant_id"])
    op.create_index("ix_rag_pages_document_page_number", "rag_pages", ["document_id", "page_number"], unique=True)

    op.create_table(
        "rag_chunks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("rag_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("page_ids", ARRAY(UUID(as_uuid=True)), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("status", rag_chunk_status, nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_rag_chunks_document_id", "rag_chunks", ["document_id"])
    op.create_index("ix_rag_chunks_tenant_id", "rag_chunks", ["tenant_id"])
    op.create_index("ix_rag_chunks_status", "rag_chunks", ["status"])
    op.create_index("ix_rag_chunks_tenant_content_hash", "rag_chunks", ["tenant_id", "content_hash"])

    op.create_table(
        "rag_retrieval_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("rag_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_rag_retrieval_logs_tenant_id", "rag_retrieval_logs", ["tenant_id"])
    op.create_index("ix_rag_retrieval_logs_document_id", "rag_retrieval_logs", ["document_id"])

    op.execute("ALTER TABLE rag_documents ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE rag_pages ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE rag_chunks ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE rag_retrieval_logs ENABLE ROW LEVEL SECURITY")

    op.execute("""
        CREATE POLICY rag_documents_tenant_isolation ON rag_documents
        FOR ALL
        USING (rls_tenant_check(tenant_id))
        WITH CHECK (rls_tenant_check(tenant_id));
    """)
    op.execute("""
        CREATE POLICY rag_pages_tenant_isolation ON rag_pages
        FOR ALL
        USING (rls_tenant_check(tenant_id))
        WITH CHECK (rls_tenant_check(tenant_id));
    """)
    op.execute("""
        CREATE POLICY rag_chunks_tenant_isolation ON rag_chunks
        FOR ALL
        USING (rls_tenant_check(tenant_id))
        WITH CHECK (rls_tenant_check(tenant_id));
    """)
    op.execute("""
        CREATE POLICY rag_retrieval_logs_tenant_isolation ON rag_retrieval_logs
        FOR ALL
        USING (rls_tenant_check(tenant_id))
        WITH CHECK (rls_tenant_check(tenant_id));
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS rag_retrieval_logs_tenant_isolation ON rag_retrieval_logs")
    op.execute("DROP POLICY IF EXISTS rag_chunks_tenant_isolation ON rag_chunks")
    op.execute("DROP POLICY IF EXISTS rag_pages_tenant_isolation ON rag_pages")
    op.execute("DROP POLICY IF EXISTS rag_documents_tenant_isolation ON rag_documents")

    op.drop_table("rag_retrieval_logs")
    op.drop_table("rag_chunks")
    op.drop_table("rag_pages")
    op.drop_table("rag_documents")

    rag_document_status = sa.Enum(name="rag_document_status")
    rag_document_status.drop(op.get_bind(), checkfirst=True)
    rag_chunk_status = sa.Enum(name="rag_chunk_status")
    rag_chunk_status.drop(op.get_bind(), checkfirst=True)
