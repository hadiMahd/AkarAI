from datetime import datetime
from uuid import uuid4

try:
    from pgvector.sqlalchemy import Vector
except ImportError:  # pragma: no cover - dependency is installed in runtime image
    from sqlalchemy import Text as Vector

from sqlalchemy import ARRAY, Column, DateTime, ForeignKey, Integer, String, Text
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
    embedding = Column(Vector(1536), nullable=True)
    status = Column(rag_chunk_status_enum, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class RagRetrievalLog(Base):
    __tablename__ = "rag_retrieval_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("rag_documents.id", ondelete="CASCADE"), nullable=False)
    query = Column(Text, nullable=False)
    retrieved_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
