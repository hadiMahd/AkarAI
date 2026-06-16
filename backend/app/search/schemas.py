from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


class SearchLogResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    agency_tenant_id: Optional[UUID] = None
    filters: Optional[dict] = None
    sort: Optional[str] = None
    result_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedSearchLogsResponse(BaseModel):
    items: list[SearchLogResponse]
    page: int
    page_size: int
    total: int
    has_next: bool
    has_previous: bool


class DomainEventLogResponse(BaseModel):
    id: UUID
    agency_tenant_id: Optional[UUID] = None
    actor_user_id: Optional[UUID] = None
    event_name: str
    aggregate_type: Optional[str] = None
    aggregate_id: Optional[str] = None
    payload: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedDomainLogsResponse(BaseModel):
    items: list[DomainEventLogResponse]
    page: int
    page_size: int
    total: int
    has_next: bool
    has_previous: bool


class ConfirmedSearchFilters(BaseModel):
    q: Optional[str] = None
    city: Optional[str] = None
    location: Optional[str] = None
    property_type: Optional[str] = None
    listing_purpose: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    parking: Optional[int] = None
    floor: Optional[int] = None
    furnishing: Optional[str] = None
    min_area_size: Optional[float] = None
    max_area_size: Optional[float] = None
    sort: Optional[str] = None
    page: int = 1
    page_size: int = 20

    @field_validator("min_price", "max_price", "min_area_size", "max_area_size", mode="before")
    @classmethod
    def reject_negative_numerics(cls, v):
        if v is not None and v < 0:
            raise ValueError("Value must not be negative")
        return v

    @field_validator("bedrooms", "bathrooms", "parking", "floor", "page", "page_size", mode="before")
    @classmethod
    def reject_negative_integers(cls, v):
        if v is not None and v < 0:
            raise ValueError("Value must not be negative")
        return v


class UnclearLocationIntent(BaseModel):
    phrase: str
    reason: str
    suggested_action: Optional[str] = None
    resolved_city: Optional[str] = None


class SearchIntent(BaseModel):
    source_mode: str  # manual, ai_text, voice
    filters: ConfirmedSearchFilters
    confidence: str  # high, medium, low, fallback
    raw_query: Optional[str] = None
    transcript: Optional[str] = None
    provider: Optional[str] = None
    fallback_reason: Optional[str] = None
    unclear_location: Optional[UnclearLocationIntent] = None


class VoiceSearchTranscript(BaseModel):
    transcript: str
    provider: str
    confidence: str  # usable, unclear, empty, failed
    fallback_reason: Optional[str] = None


class AISearchIntentRequest(BaseModel):
    q: str


class AISearchIntentResponse(BaseModel):
    intent: SearchIntent
    unclear_location: Optional[UnclearLocationIntent] = None


class VoiceSearchResponse(BaseModel):
    transcript: VoiceSearchTranscript
    intent: SearchIntent


class ConfirmationLogRequest(BaseModel):
    source_mode: str
    confirmed_filters: ConfirmedSearchFilters
    edits: Optional[list[str]] = None
