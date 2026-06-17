from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.types import DateTime

from app.common.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    agency_tenant_id = Column(UUID(as_uuid=True), ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(16), default="new", nullable=False)
    processing_status = Column(String(32), default="pending", nullable=False)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(64), nullable=True)
    message = Column(Text, nullable=True)
    source = Column(String(32), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)


class LeadSpamResult(Base):
    __tablename__ = "lead_spam_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    agency_tenant_id = Column(UUID(as_uuid=True), ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(16), default="pending", nullable=False)
    label = Column(String(64), nullable=True)
    score = Column(Numeric(5, 4), nullable=True)
    details = Column(JSON, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)
    idempotency_key = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class LeadLevelResult(Base):
    __tablename__ = "lead_level_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    agency_tenant_id = Column(UUID(as_uuid=True), ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(16), default="pending", nullable=False)
    level = Column(String(32), nullable=True)
    score = Column(Numeric(5, 4), nullable=True)
    details = Column(JSON, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)
    idempotency_key = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class LeadSuggestedReply(Base):
    __tablename__ = "lead_suggested_replies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    agency_tenant_id = Column(UUID(as_uuid=True), ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(16), default="draft", nullable=False)
    body = Column(Text, nullable=True)
    created_by = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ReviewedLeadRecord(Base):
    __tablename__ = "reviewed_lead_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    agency_tenant_id = Column(UUID(as_uuid=True), ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False)
    reviewed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    outcome = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
