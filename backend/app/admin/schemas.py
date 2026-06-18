"""Schemas for the Phase 15 Platform Admin Dashboard read APIs.

These schemas model the response shapes exposed by:

- ``GET /api/v1/platform/dashboard/insights``
- ``GET /api/v1/platform/audit-logs``
- ``GET /api/v1/platform/roles/overview``

The schemas intentionally stay close to the OpenAPI contract at
``specs/015-platform-admin-streamlit/contracts/platform-admin.openapi.yaml``.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Shared filter scope
# ---------------------------------------------------------------------------


RANGE_PRESETS = ("last_7_days", "last_30_days", "last_90_days", "custom")


class DashboardFilterScope(BaseModel):
    date_from: date
    date_to: date
    range_preset: str
    city: Optional[str] = None
    property_type: Optional[str] = None
    listing_purpose: Optional[str] = None

    @model_validator(mode="after")
    def _check_window(self) -> "DashboardFilterScope":
        if self.date_from > self.date_to:
            raise ValueError("date_from must be on or before date_to")
        return self


# ---------------------------------------------------------------------------
# Insights (US1)
# ---------------------------------------------------------------------------


class SearchVolumeTrendPoint(BaseModel):
    bucket_start: datetime
    bucket_end: datetime
    search_count: int = Field(ge=0)


class RankedSegment(BaseModel):
    label: str
    search_count: int = Field(ge=0)
    share: float = Field(ge=0.0, le=1.0)
    rank: int = Field(ge=1)


class DemandGapEntry(BaseModel):
    dimension_type: str
    dimension_label: str
    demand_count: int = Field(ge=0)
    supply_count: int = Field(ge=0)
    gap_score: float
    gap_direction: str  # undersupplied | balanced | oversupplied


class DemandInsightSnapshot(BaseModel):
    generated_at: datetime
    scope: DashboardFilterScope
    search_volume_total: int = Field(ge=0)
    search_volume_trend: list[SearchVolumeTrendPoint] = Field(default_factory=list)
    top_areas: list[RankedSegment] = Field(default_factory=list)
    top_budget_bands: list[RankedSegment] = Field(default_factory=list)
    top_property_types: list[RankedSegment] = Field(default_factory=list)
    demand_gaps: list[DemandGapEntry] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Audit log viewer (US2)
# ---------------------------------------------------------------------------


class PlatformAuditLogView(BaseModel):
    id: str
    created_at: datetime
    actor_role: str
    feature_area: str
    action: str
    result: str
    redacted_metadata: dict[str, Any] = Field(default_factory=dict)
    actor_user_id: Optional[str] = None
    tenant_scope_label: Optional[str] = None


class PaginatedAuditLogResponse(BaseModel):
    items: list[PlatformAuditLogView]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    has_next: bool
    has_previous: bool


# ---------------------------------------------------------------------------
# Role overview (US3)
# ---------------------------------------------------------------------------


class RoleAccessSummary(BaseModel):
    role_slug: str
    display_name: str
    granted_permissions: list[str] = Field(default_factory=list)
    surface_access: list[str] = Field(default_factory=list)
    restricted_surfaces: list[str] = Field(default_factory=list)


class RoleOverviewResponse(BaseModel):
    items: list[RoleAccessSummary]


# ---------------------------------------------------------------------------
# RAG evals
# ---------------------------------------------------------------------------


class RagEvalRunListItem(BaseModel):
    run_id: str
    run_label: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    mode: str
    total_examples: int = Field(ge=0)
    passed_examples: int = Field(ge=0)
    failed_examples: int = Field(ge=0)
    faithfulness: Optional[float] = None
    context_precision: Optional[float] = None
    context_recall: Optional[float] = None
    answer_relevancy: Optional[float] = None
    hit_at_1: Optional[float] = None
    hit_at_5: Optional[float] = None
    tenant_leakage_count: int = Field(ge=0, default=0)
    p95_latency_ms: Optional[float] = None
    judge_failures: int = Field(ge=0, default=0)
    threshold_failures: list[str] = Field(default_factory=list)
    passed: bool


class RagEvalExampleView(BaseModel):
    example_id: str
    query: str
    tenant_fixture: str
    expected_behavior: str
    passed: bool
    answer_status: Optional[str] = None
    faithfulness: Optional[float] = None
    context_precision: Optional[float] = None
    context_recall: Optional[float] = None
    answer_relevancy: Optional[float] = None
    hit_at_1: Optional[bool] = None
    hit_at_5: Optional[bool] = None
    expected_source_match: Optional[bool] = None
    leaked_sources: list[str] = Field(default_factory=list)
    latency_ms: Optional[float] = None
    failure_reasons: list[str] = Field(default_factory=list)


class RagEvalRunDetail(BaseModel):
    run: RagEvalRunListItem
    examples: list[RagEvalExampleView] = Field(default_factory=list)


class PaginatedRagEvalRunsResponse(BaseModel):
    items: list[RagEvalRunListItem] = Field(default_factory=list)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    has_next: bool
    has_previous: bool


__all__ = [
    "RANGE_PRESETS",
    "DashboardFilterScope",
    "SearchVolumeTrendPoint",
    "RankedSegment",
    "DemandGapEntry",
    "DemandInsightSnapshot",
    "PlatformAuditLogView",
    "PaginatedAuditLogResponse",
    "RoleAccessSummary",
    "RoleOverviewResponse",
    "RagEvalRunListItem",
    "RagEvalExampleView",
    "RagEvalRunDetail",
    "PaginatedRagEvalRunsResponse",
]
