from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


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
