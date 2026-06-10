from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ViewingSlotCreateRequest(BaseModel):
    starts_at: datetime
    ends_at: datetime
    capacity: int = Field(default=1, ge=1)

    @field_validator("ends_at")
    @classmethod
    def ends_must_be_after_starts(cls, v: datetime, info) -> datetime:
        if "starts_at" in info.data and v <= info.data["starts_at"]:
            raise ValueError("ends_at must be after starts_at")
        return v


class ViewingSlotUpdateRequest(BaseModel):
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    capacity: Optional[int] = Field(default=None, ge=1)
    status: Optional[str] = None


class ViewingSlotResponse(BaseModel):
    id: UUID
    listing_id: UUID
    agency_tenant_id: UUID
    starts_at: datetime
    ends_at: datetime
    capacity: int
    reserved_count: int
    status: str
    created_by_user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PublicViewingSlotResponse(BaseModel):
    id: UUID
    starts_at: datetime
    ends_at: datetime
    capacity: int
    reserved_count: int
    status: str

    model_config = {"from_attributes": True}


class ViewingBookingRequest(BaseModel):
    viewing_slot_id: UUID
    notes: Optional[str] = None


class ScheduledViewingResponse(BaseModel):
    id: UUID
    agency_tenant_id: UUID
    listing_id: UUID
    viewing_slot_id: UUID
    user_id: Optional[UUID] = None
    status: str
    scheduled_start_at: datetime
    scheduled_end_at: datetime
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedScheduledViewingsResponse(BaseModel):
    items: list[ScheduledViewingResponse]
    page: int
    page_size: int
    total: int
    has_next: bool
    has_previous: bool


class ViewingStatusUpdateRequest(BaseModel):
    status: str
    reason: Optional[str] = None
