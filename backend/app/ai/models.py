"""Models for the Phase 12 Agency AI Workflows surfaces.

Tables:
- agency_ai_jobs: OCR + generation job tracking
- lead_reply_drafts: saved reply draft records
- comparison_summaries: user-saved comparison summary records
- agency_assistant_tool_invocations: assistant tool audit trail
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID

from app.common.database import Base


JOB_TYPE_OCR_EXTRACTION = "ocr_extraction"
JOB_TYPE_LISTING_DRAFT = "listing_draft"
JOB_TYPE_LEAD_REPLY_DRAFT = "lead_reply_draft"
JOB_TYPE_COMPARISON_SUMMARY = "comparison_summary"

JOB_STATUS_QUEUED = "queued"
JOB_STATUS_PROCESSING = "processing"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_BLOCKED = "blocked"
JOB_STATUS_FAILED = "failed"


VALID_JOB_TYPES = {
    JOB_TYPE_OCR_EXTRACTION,
    JOB_TYPE_LISTING_DRAFT,
    JOB_TYPE_LEAD_REPLY_DRAFT,
    JOB_TYPE_COMPARISON_SUMMARY,
}


VALID_JOB_STATUSES = {
    JOB_STATUS_QUEUED,
    JOB_STATUS_PROCESSING,
    JOB_STATUS_COMPLETED,
    JOB_STATUS_BLOCKED,
    JOB_STATUS_FAILED,
}


class AgencyAIJob(Base):
    __tablename__ = "agency_ai_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, default=JOB_STATUS_QUEUED)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    actor_user_id = Column(UUID(as_uuid=True), nullable=True)
    source_reference_id = Column(UUID(as_uuid=True), nullable=True)
    result_payload = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)


class LeadReplyDraft(Base):
    __tablename__ = "lead_reply_drafts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    agency_tenant_id = Column(UUID(as_uuid=True), ForeignKey("agency_tenants.id", ondelete="CASCADE"), nullable=False)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    channel = Column(String(32), nullable=False)
    subject = Column(String(255), nullable=True)
    draft_text = Column(Text, nullable=False)
    guardrail_status = Column(String(32), nullable=True)
    generation_provider = Column(String(64), nullable=True)
    blocked_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class ComparisonSummary(Base):
    __tablename__ = "comparison_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    listing_ids = Column(JSON, nullable=False)
    summary = Column(Text, nullable=False)
    key_differences = Column(JSON, nullable=True)
    best_fit_notes = Column(JSON, nullable=True)
    guardrail_status = Column(String(32), nullable=True)
    generation_provider = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class AgencyAssistantToolInvocation(Base):
    __tablename__ = "agency_assistant_tool_invocations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    actor_user_id = Column(UUID(as_uuid=True), nullable=True)
    tool_name = Column(String(64), nullable=False)
    input_summary = Column(JSON, nullable=True)
    output_summary = Column(JSON, nullable=True)
    status = Column(String(32), nullable=False)
    failure_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
