from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# ── Lead processing stage constants ──
LEAD_PROCESSING_STAGE_SPAM = "spam"
LEAD_PROCESSING_STAGE_LEVEL = "level"

LEAD_PROCESSING_STATUS_PENDING = "pending"  # legacy; kept for backward compat
LEAD_PROCESSING_STATUS_PENDING_SPAM = "pending_spam"
LEAD_PROCESSING_STATUS_PENDING_LEVEL = "pending_level"
LEAD_PROCESSING_STATUS_COMPLETED = "completed"
LEAD_PROCESSING_STATUS_FAILED = "failed"

LEAD_PROCESSING_PENDING_STATES = {LEAD_PROCESSING_STATUS_PENDING, LEAD_PROCESSING_STATUS_PENDING_SPAM, LEAD_PROCESSING_STATUS_PENDING_LEVEL}

LEAD_SPAM_LABEL_SPAM = "spam"
LEAD_SPAM_LABEL_NOT_SPAM = "not_spam"

LEAD_LEVEL_HOT = "hot"
LEAD_LEVEL_NORMAL = "normal"


class LeadInquiryRequest(BaseModel):
    message: Optional[str] = None


class LeadResponse(BaseModel):
    id: UUID
    agency_tenant_id: UUID
    listing_id: UUID
    user_id: Optional[UUID] = None
    status: str
    processing_status: Optional[str] = None
    spam_label: Optional[str] = None
    spam_score: Optional[float] = None
    lead_level: Optional[str] = None
    level_score: Optional[float] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    message: Optional[str] = None
    source: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PaginatedLeadsResponse(BaseModel):
    items: list[LeadResponse]
    page: int
    page_size: int
    total: int
    has_next: bool
    has_previous: bool


class LeadStatusUpdateRequest(BaseModel):
    status: str


class LeadReviewRequest(BaseModel):
    outcome: Optional[str] = None
    notes: Optional[str] = None


class ReviewedLeadRecordResponse(BaseModel):
    id: UUID
    lead_id: UUID
    agency_tenant_id: UUID
    reviewed_by_user_id: Optional[UUID] = None
    outcome: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Lead Processing Callback Contracts ──

class LeadClassificationCallbackRequest(BaseModel):
    lead_id: UUID
    tenant_id: UUID
    stage: str
    status: str
    label: Optional[str] = None
    score: Optional[float] = None
    details: Optional[dict] = None
    retry_count: int = 0

    @field_validator("stage")
    @classmethod
    def validate_stage(cls, v: str) -> str:
        if v not in (LEAD_PROCESSING_STAGE_SPAM, LEAD_PROCESSING_STAGE_LEVEL):
            raise ValueError(f"stage must be '{LEAD_PROCESSING_STAGE_SPAM}' or '{LEAD_PROCESSING_STAGE_LEVEL}'")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in (LEAD_PROCESSING_STATUS_PENDING, LEAD_PROCESSING_STATUS_PENDING_SPAM, LEAD_PROCESSING_STATUS_PENDING_LEVEL, LEAD_PROCESSING_STATUS_COMPLETED, LEAD_PROCESSING_STATUS_FAILED):
            raise ValueError(f"status must be one of: pending, pending_spam, pending_level, completed, failed")
        return v


class LeadClassificationCallbackResponse(BaseModel):
    lead_id: UUID
    stage: str
    status: str
    label: Optional[str] = None


class LeadSpamResultResponse(BaseModel):
    id: UUID
    lead_id: UUID
    agency_tenant_id: UUID
    status: str
    label: Optional[str] = None
    score: Optional[float] = None
    details: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeadLevelResultResponse(BaseModel):
    id: UUID
    lead_id: UUID
    agency_tenant_id: UUID
    status: str
    level: Optional[str] = None
    score: Optional[float] = None
    details: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeadProcessingSummary(BaseModel):
    total_leads: int = 0
    spam_count: int = 0
    not_spam_count: int = 0
    hot_count: int = 0
    normal_count: int = 0
    pending_count: int = 0
    reviewed_count: int = 0


class LeadProcessingTrendsResponse(BaseModel):
    tenant_id: UUID
    summary: LeadProcessingSummary
    spam_rate: float = 0.0
    hot_rate: float = 0.0
    review_rate: float = 0.0
    fallback_count: int = 0
