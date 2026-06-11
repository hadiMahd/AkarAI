from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AgencyProfileResponse(BaseModel):
    id: UUID
    agency_tenant_id: UUID
    display_name: str
    legal_name: Optional[str] = None
    description: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website_url: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgencyProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    legal_name: Optional[str] = None
    description: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website_url: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    status: Optional[str] = None

    @field_validator("email")
    @classmethod
    def email_must_contain_at(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and "@" not in v:
            raise ValueError("Email must contain '@'")
        return v


class AgencyEmployeeResponse(BaseModel):
    id: UUID
    agency_tenant_id: UUID
    user_id: UUID
    role_id: UUID
    status: str
    display_name: Optional[str] = None
    work_email: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgencyEmployeeCreateRequest(BaseModel):
    user_id: Optional[UUID] = None
    role_id: Optional[UUID] = None
    display_name: Optional[str] = None
    work_email: Optional[str] = None
    role_slug: Optional[str] = None

    @field_validator("work_email")
    @classmethod
    def email_must_contain_at(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and "@" not in v:
            raise ValueError("Email must contain '@'")
        return v


class AgencyEmployeeUpdateRequest(BaseModel):
    role_id: Optional[UUID] = None
    display_name: Optional[str] = None
    work_email: Optional[str] = None

    @field_validator("work_email")
    @classmethod
    def email_must_contain_at(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and "@" not in v:
            raise ValueError("Email must contain '@'")
        return v


class PaginatedEmployeesResponse(BaseModel):
    items: list[AgencyEmployeeResponse]
    page: int
    page_size: int
    total: int
    has_next: bool
    has_previous: bool
