"""Add RAG chat threads and messages

Revision ID: 0015
Revises: 0014
Create Date: 2026-06-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM, UUID


revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    rag_chat_message_role = ENUM(
        "user",
        "assistant",
        name="rag_chat_message_role",
        create_type=False,
    )
    rag_chat_message_role.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "rag_chat_threads",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False, server_default="New conversation"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_rag_chat_threads_tenant_owner", "rag_chat_threads", ["tenant_id", "owner_user_id"])
    op.create_index("ix_rag_chat_threads_last_message_at", "rag_chat_threads", ["last_message_at"])

    op.create_table(
        "rag_chat_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("thread_id", UUID(as_uuid=True), sa.ForeignKey("rag_chat_threads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", rag_chat_message_role, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("retrieval_log_id", UUID(as_uuid=True), sa.ForeignKey("rag_retrieval_logs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("answer_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_rag_chat_messages_thread_id", "rag_chat_messages", ["thread_id"])
    op.create_index("ix_rag_chat_messages_tenant_owner", "rag_chat_messages", ["tenant_id", "owner_user_id"])
    op.create_index("ix_rag_chat_messages_thread_sequence", "rag_chat_messages", ["thread_id", "sequence_number"], unique=True)

    op.execute("ALTER TABLE rag_chat_threads ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE rag_chat_messages ENABLE ROW LEVEL SECURITY")

    op.execute("""
        CREATE POLICY rag_chat_threads_owner_isolation ON rag_chat_threads
        FOR ALL
        USING (rls_tenant_check(tenant_id) AND rls_user_check(owner_user_id))
        WITH CHECK (rls_tenant_check(tenant_id) AND rls_user_check(owner_user_id));
    """)
    op.execute("""
        CREATE POLICY rag_chat_messages_owner_isolation ON rag_chat_messages
        FOR ALL
        USING (rls_tenant_check(tenant_id) AND rls_user_check(owner_user_id))
        WITH CHECK (rls_tenant_check(tenant_id) AND rls_user_check(owner_user_id));
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS rag_chat_messages_owner_isolation ON rag_chat_messages")
    op.execute("DROP POLICY IF EXISTS rag_chat_threads_owner_isolation ON rag_chat_threads")

    op.drop_table("rag_chat_messages")
    op.drop_table("rag_chat_threads")

    rag_chat_message_role = sa.Enum(name="rag_chat_message_role")
    rag_chat_message_role.drop(op.get_bind(), checkfirst=True)
