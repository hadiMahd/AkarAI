"""Platform Admin Dashboard read-only router.

All endpoints are gated by ``require_platform_dashboard_access`` which
enforces BOTH the existing ``platform_admin`` role and the new
``platform:dashboard_read`` permission.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.schemas import (
    DemandInsightSnapshot,
    PaginatedAuditLogResponse,
    PaginatedRagEvalRunsResponse,
    RagEvalRunDetail,
    RoleOverviewResponse,
)
from app.admin.service import PlatformAdminService
from app.auth.dependencies import require_platform_dashboard_access
from app.common.dependencies import get_db_session


router = APIRouter(prefix="/api/v1/platform", tags=["Platform Admin"])


def _parse_iso_date(value: Optional[str]) -> Optional[date]:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return value if isinstance(value, date) else None


def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _default_insights_window(range_preset: Optional[str]) -> tuple[date, date]:
    today = date.today()
    preset = range_preset or "last_30_days"
    if preset == "last_7_days":
        return today - timedelta(days=7), today
    if preset == "last_90_days":
        return today - timedelta(days=90), today
    if preset == "custom":
        return today - timedelta(days=30), today
    return today - timedelta(days=30), today


@router.get("/dashboard/insights", response_model=DemandInsightSnapshot)
async def get_dashboard_insights(
    date_from: Optional[str] = Query(None, description="ISO date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="ISO date (YYYY-MM-DD)"),
    range_preset: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    property_type: Optional[str] = Query(None),
    listing_purpose: Optional[str] = Query(None),
    actor: dict = Depends(require_platform_dashboard_access()),
    db: AsyncSession = Depends(get_db_session),
):
    parsed_from = _parse_iso_date(date_from)
    parsed_to = _parse_iso_date(date_to)
    if parsed_from is None and parsed_to is None:
        parsed_from, parsed_to = _default_insights_window(range_preset)
    elif parsed_from is None or parsed_to is None:
        fallback_from, fallback_to = _default_insights_window(range_preset)
        parsed_from = parsed_from or fallback_from
        parsed_to = parsed_to or fallback_to

    service = PlatformAdminService(db)
    return await service.get_demand_insights(
        date_from=parsed_from,
        date_to=parsed_to,
        range_preset=range_preset,
        city=city,
        property_type=property_type,
        listing_purpose=listing_purpose,
        actor_id=actor.get("user_id"),
    )


@router.get("/audit-logs", response_model=PaginatedAuditLogResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    feature_area: Optional[str] = Query(None),
    actor_role: Optional[str] = Query(None),
    result: Optional[str] = Query(None),
    actor: dict = Depends(require_platform_dashboard_access()),
    db: AsyncSession = Depends(get_db_session),
):
    service = PlatformAdminService(db)
    return await service.list_audit_logs(
        page=page,
        page_size=page_size,
        date_from=_parse_iso_datetime(date_from),
        date_to=_parse_iso_datetime(date_to),
        feature_area=feature_area,
        actor_role=actor_role,
        result=result,
        actor_id=actor.get("user_id"),
    )


@router.get("/roles/overview", response_model=RoleOverviewResponse)
async def get_role_overview(
    actor: dict = Depends(require_platform_dashboard_access()),
    db: AsyncSession = Depends(get_db_session),
):
    service = PlatformAdminService(db)
    return await service.get_role_overview(actor_id=actor.get("user_id"))


@router.get("/rag-evals/runs", response_model=PaginatedRagEvalRunsResponse)
async def list_rag_eval_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    actor: dict = Depends(require_platform_dashboard_access()),
    db: AsyncSession = Depends(get_db_session),
):
    service = PlatformAdminService(db)
    return await service.list_rag_eval_runs(
        page=page,
        page_size=page_size,
        actor_id=actor.get("user_id"),
    )


@router.get("/rag-evals/runs/{run_id}", response_model=RagEvalRunDetail)
async def get_rag_eval_run_detail(
    run_id: UUID,
    actor: dict = Depends(require_platform_dashboard_access()),
    db: AsyncSession = Depends(get_db_session),
):
    service = PlatformAdminService(db)
    return await service.get_rag_eval_run_detail(
        run_id=run_id,
        actor_id=actor.get("user_id"),
    )


__all__ = ["router"]
