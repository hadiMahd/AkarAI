from typing import Any, Optional

from pydantic import BaseModel


class APIResponse(BaseModel):
    """Standard success envelope for API responses."""

    status: str = "ok"
    data: Optional[Any] = None
    request_id: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error envelope for API error responses."""

    status: str = "error"
    detail: str
    error_code: Optional[str] = None
    request_id: Optional[str] = None


class PaginatedResponse(BaseModel):
    """Standard paginated list response."""

    status: str = "ok"
    data: list[Any]
    page: int
    page_size: int
    total: int
    has_next: bool
    has_previous: bool
    request_id: Optional[str] = None
