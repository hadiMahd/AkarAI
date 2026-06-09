from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class LeadInquiryRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    message: Optional[str] = None

    @field_validator("email")
    @classmethod
    def email_must_contain_at(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and "@" not in v:
            raise ValueError("Email must contain '@'")
        return v


class LeadResponse(BaseModel):
    id: UUID
    agency_tenant_id: UUID
    listing_id: UUID
    user_id: Optional[UUID] = None
    status: str
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
