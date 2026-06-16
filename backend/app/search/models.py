import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.common.database import Base


class SearchLog(Base):
    __tablename__ = "search_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    agency_tenant_id = Column(UUID(as_uuid=True), ForeignKey("agency_tenants.id", ondelete="SET NULL"), nullable=True)
    source_mode = Column(String(16), nullable=False, default="manual")  # manual, ai_text, voice
    event_type = Column(String(32), nullable=False, default="manual_search")
    raw_query_redacted = Column(Text, nullable=True)
    transcript_redacted = Column(Text, nullable=True)
    intent = Column(JSON, nullable=True)
    filters = Column(JSON, nullable=True)
    sort = Column(String(32), nullable=True)
    result_count = Column(Integer, default=0, nullable=False)
    provider = Column(String(64), nullable=True)
    fallback_reason = Column(String(256), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
