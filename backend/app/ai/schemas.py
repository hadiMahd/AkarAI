"""Schemas for the Phase 12 Agency AI Workflows endpoints.

These cover:
- Temporary spec-sheet OCR extraction + listing draft generation
- Lead reply draft generation
- User comparison summary generation
- Shared job status envelope
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


JOB_TYPE_OCR_EXTRACTION = "ocr_extraction"
JOB_TYPE_LISTING_DRAFT = "listing_draft"
JOB_TYPE_LEAD_REPLY_DRAFT = "lead_reply_draft"
JOB_TYPE_COMPARISON_SUMMARY = "comparison_summary"

JOB_STATUS_QUEUED = "queued"
JOB_STATUS_PROCESSING = "processing"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_BLOCKED = "blocked"
JOB_STATUS_FAILED = "failed"

LEAD_REPLY_CHANNEL_WHATSAPP = "whatsapp"
LEAD_REPLY_CHANNEL_EMAIL = "email"


class ExtractedListingSpecs(BaseModel):
    property_type: Optional[str] = None
    listing_purpose: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    parking: Optional[int] = None
    floor: Optional[int] = None
    area_size: Optional[Decimal] = None
    area_unit: Optional[str] = None
    furnishing: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    location_text: Optional[str] = None
    raw_text_excerpt: Optional[str] = Field(default=None, max_length=2000)
    field_confidence: dict[str, str] = Field(default_factory=dict)
    source_snippets: dict[str, str] = Field(default_factory=dict)


class SpecExtractionJobAcceptedResponse(BaseModel):
    job_id: UUID
    status: str
    provider: str


class SpecExtractionResultResponse(BaseModel):
    job_id: UUID
    status: str
    provider: str
    warnings: list[str] = Field(default_factory=list)
    fallback_reason: Optional[str] = None
    extracted_specs: Optional[ExtractedListingSpecs] = None


class ListingDraftRequest(BaseModel):
    listing_id: Optional[UUID] = None
    listing_context: dict[str, Any]
    extracted_specs: Optional[ExtractedListingSpecs] = None


class ListingDraftResponse(BaseModel):
    job_id: UUID
    status: str
    title: Optional[str] = None
    description: Optional[str] = None
    highlights: list[str] = Field(default_factory=list)
    guardrail_status: Optional[str] = None
    generation_provider: Optional[str] = None
    blocked_reason: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)


class LeadReplyDraftRequest(BaseModel):
    channel: Literal["email", "whatsapp"]


class LeadReplyDraftResponse(BaseModel):
    job_id: UUID
    status: str
    channel: str
    subject: Optional[str] = None
    body: Optional[str] = None
    guardrail_status: Optional[str] = None
    generation_provider: Optional[str] = None
    blocked_reason: Optional[str] = None


class ComparisonSummaryRequest(BaseModel):
    listing_ids: list[UUID] = Field(..., min_length=2, max_length=4)

    @field_validator("listing_ids")
    @classmethod
    def deduplicate_listing_ids(cls, value: list[UUID]) -> list[UUID]:
        seen: set[UUID] = set()
        deduped: list[UUID] = []
        for listing_id in value:
            if listing_id in seen:
                continue
            seen.add(listing_id)
            deduped.append(listing_id)
        return deduped


class ComparisonSummaryResponse(BaseModel):
    job_id: UUID
    status: str
    summary: Optional[str] = None
    key_differences: list[str] = Field(default_factory=list)
    best_fit_notes: list[str] = Field(default_factory=list)
    guardrail_status: Optional[str] = None
    generation_provider: Optional[str] = None
    blocked_reason: Optional[str] = None


class AgencyAIJobRead(BaseModel):
    id: UUID
    job_id: UUID
    job_type: str
    status: str
    tenant_id: Optional[UUID] = None
    actor_user_id: Optional[UUID] = None
    source_reference_id: Optional[UUID] = None
    result_payload: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        if hasattr(obj, "id") and not isinstance(obj, dict):
            data = {
                "id": obj.id,
                "job_id": obj.id,
                "job_type": obj.job_type,
                "status": obj.status,
                "tenant_id": getattr(obj, "tenant_id", None),
                "actor_user_id": getattr(obj, "actor_user_id", None),
                "source_reference_id": getattr(obj, "source_reference_id", None),
                "result_payload": getattr(obj, "result_payload", None),
                "error_message": getattr(obj, "error_message", None),
                "created_at": obj.created_at,
                "started_at": getattr(obj, "started_at", None),
                "completed_at": getattr(obj, "completed_at", None),
                "expires_at": getattr(obj, "expires_at", None),
            }
            return super().model_validate(data, *args, **kwargs)
        return super().model_validate(obj, *args, **kwargs)


class ListingAssistantConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def trim_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("content cannot be blank")
        return value


class ListingAssistantMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_messages: list[ListingAssistantConversationMessage] = Field(default_factory=list)

    @field_validator("message")
    @classmethod
    def trim_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message cannot be blank")
        return value


class ListingAssistantPendingAction(BaseModel):
    type: Literal["lead_inquiry", "viewing_booking"]
    payload: dict[str, Any]


class ListingAssistantResponse(BaseModel):
    assistant_message: str
    pending_action: ListingAssistantPendingAction | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
