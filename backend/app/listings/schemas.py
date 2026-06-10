from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ListingCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    property_type: Optional[str] = None
    listing_purpose: Optional[str] = None
    price: Optional[Decimal] = None
    currency: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area_size: Optional[Decimal] = None
    area_unit: Optional[str] = None
    furnishing: Optional[str] = None
    location_text: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    status: str = "inactive"


class ListingUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    property_type: Optional[str] = None
    listing_purpose: Optional[str] = None
    price: Optional[Decimal] = None
    currency: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area_size: Optional[Decimal] = None
    area_unit: Optional[str] = None
    furnishing: Optional[str] = None
    location_text: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    status: Optional[str] = None


class ListingResponse(BaseModel):
    id: UUID
    agency_tenant_id: UUID
    title: str
    description: Optional[str] = None
    property_type: Optional[str] = None
    listing_purpose: Optional[str] = None
    price: Optional[Decimal] = None
    currency: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area_size: Optional[Decimal] = None
    area_unit: Optional[str] = None
    furnishing: Optional[str] = None
    location_text: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    status: str
    created_by_user_id: Optional[UUID] = None
    updated_by_user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PublicListingResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    property_type: Optional[str] = None
    listing_purpose: Optional[str] = None
    price: Optional[Decimal] = None
    currency: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area_size: Optional[Decimal] = None
    area_unit: Optional[str] = None
    furnishing: Optional[str] = None
    location_text: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedPublicListingsResponse(BaseModel):
    items: list[PublicListingResponse]
    page: int
    page_size: int
    total: int
    has_next: bool
    has_previous: bool


class PaginatedListingsResponse(BaseModel):
    items: list[ListingResponse]
    page: int
    page_size: int
    total: int
    has_next: bool
    has_previous: bool


class ListingPhotoMetadataCreateRequest(BaseModel):
    object_key: str = Field(..., min_length=1, max_length=512)
    caption: Optional[str] = None
    alt_text: Optional[str] = None
    display_order: int = 0


class ListingPhotoMetadataUpdateRequest(BaseModel):
    caption: Optional[str] = None
    alt_text: Optional[str] = None
    display_order: Optional[int] = None


class ListingPhotoMetadataResponse(BaseModel):
    id: UUID
    listing_id: UUID
    agency_tenant_id: UUID
    object_key: str
    caption: Optional[str] = None
    alt_text: Optional[str] = None
    display_order: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PublicListingSearchParams(BaseModel):
    location: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    property_type: Optional[str] = None
    listing_purpose: Optional[str] = None
    furnishing: Optional[str] = None
    min_area_size: Optional[float] = None
    max_area_size: Optional[float] = None
    sort: Optional[str] = None


class SavedListingResponse(BaseModel):
    id: UUID
    user_id: UUID
    listing_id: UUID
    created_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SavedListingWithDetailsResponse(BaseModel):
    id: UUID
    user_id: UUID
    listing_id: UUID
    created_at: datetime
    deleted_at: Optional[datetime] = None
    listing: PublicListingResponse

    model_config = {"from_attributes": True}


class PaginatedSavedListingsResponse(BaseModel):
    items: list[SavedListingResponse]
    page: int
    page_size: int
    total: int
    has_next: bool
    has_previous: bool


class PaginatedSavedListingsWithDetailsResponse(BaseModel):
    items: list[SavedListingWithDetailsResponse]
    page: int
    page_size: int
    total: int
    has_next: bool
    has_previous: bool


class ComparisonSessionCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class ComparisonSessionUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)


class ComparisonSessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PaginatedComparisonSessionsResponse(BaseModel):
    items: list[ComparisonSessionResponse]
    page: int
    page_size: int
    total: int
    has_next: bool
    has_previous: bool


class ComparisonItemCreateRequest(BaseModel):
    listing_id: UUID


class ComparisonItemResponse(BaseModel):
    id: UUID
    comparison_session_id: UUID
    listing_id: UUID
    position: int
    created_at: datetime

    model_config = {"from_attributes": True}
