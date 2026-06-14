from datetime import datetime
from uuid import uuid4

try:
    from pgvector.sqlalchemy import Vector
except ImportError:  # pragma: no cover - dependency is installed in runtime image
    from sqlalchemy import Text as Vector

from sqlalchemy import ARRAY, Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID

from app.common.database import Base


rag_document_status_enum = ENUM(
    "pending",
    "processing",
    "processed",
    "failed",
    name="rag_document_status",
    create_type=False,
)
rag_chunk_status_enum = ENUM("active", "orphaned", name="rag_chunk_status", create_type=False)
rag_retrieval_scope_enum = ENUM("agency_policy", name="rag_retrieval_scope", create_type=False)
rag_confidence_status_enum = ENUM(
    "sufficient",
    "insufficient",
    "fallback",
    name="rag_confidence_status",
    create_type=False,
)
rag_chat_message_role_enum = ENUM(
    "user",
    "assistant",
    name="rag_chat_message_role",
    create_type=False,
)


class RagDocument(Base):
    __tablename__ = "rag_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(512), nullable=False)
    status = Column(rag_document_status_enum, default="pending", nullable=False)
    blob_path = Column(String(1024), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class RagPage(Base):
    __tablename__ = "rag_pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("rag_documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False)
    blob_path = Column(String(1024), nullable=False)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class RagChunk(Base):
    __tablename__ = "rag_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("rag_documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False)
    page_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)
    content_hash = Column(String(64), nullable=False)
    text = Column(Text, nullable=True)
    embedding = Column(Vector(1536), nullable=True)
    status = Column(rag_chunk_status_enum, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class RagRetrievalLog(Base):
    __tablename__ = "rag_retrieval_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("rag_documents.id", ondelete="CASCADE"), nullable=True)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_role = Column(String(64), nullable=False)
    query = Column(Text, nullable=False)
    retrieval_scope = Column(rag_retrieval_scope_enum, default="agency_policy", nullable=False)
    selected_document_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False, default=list)
    selected_chunk_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False, default=list)
    selected_page_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False, default=list)
    reranker_used = Column(Boolean, default=False, nullable=False)
    reranker_provider = Column(String(128), nullable=True)
    fallback_reason = Column(String(256), nullable=True)
    confidence_status = Column(rag_confidence_status_enum, default="sufficient", nullable=False)
    retrieved_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class RagEvaluationRun(Base):
    __tablename__ = "rag_evaluation_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_label = Column(String(128), nullable=False)
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    total_examples = Column(Integer, nullable=False, default=0)
    passed_examples = Column(Integer, nullable=False, default=0)
    failed_examples = Column(Integer, nullable=False, default=0)
    summary = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class RagEvaluationExample(Base):
    __tablename__ = "rag_evaluation_examples"

    id = Column(String(128), primary_key=True)
    run_id = Column(UUID(as_uuid=True), ForeignKey("rag_evaluation_runs.id", ondelete="CASCADE"), nullable=False)
    query = Column(Text, nullable=False)
    tenant_fixture = Column(String(128), nullable=False)
    expected_behavior = Column(String(64), nullable=False)
    expected_source_labels = Column(ARRAY(Text), nullable=False, default=list)
    notes = Column(Text, nullable=True)
    passed = Column(Boolean, default=False, nullable=False)
    summary = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class RagChatThread(Base):
    __tablename__ = "rag_chat_threads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(160), nullable=False, default="New conversation")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_message_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class RagChatMessage(Base):
    __tablename__ = "rag_chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("rag_chat_threads.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(rag_chat_message_role_enum, nullable=False)
    content = Column(Text, nullable=False)
    sequence_number = Column(Integer, nullable=False)
    retrieval_log_id = Column(UUID(as_uuid=True), ForeignKey("rag_retrieval_logs.id", ondelete="SET NULL"), nullable=True)
    answer_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
