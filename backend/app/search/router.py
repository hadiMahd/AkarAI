from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_tenant_context
from app.common.dependencies import get_db_session
from app.common.pagination import PaginationRequest
from app.common.tenant import TenantContext
from app.search.schemas import (
    SearchLogResponse,
    PaginatedSearchLogsResponse,
    DomainEventLogResponse,
    PaginatedDomainLogsResponse,
)
from app.search.service import SearchService

router = APIRouter(prefix="/agency", tags=["Operational Logs"])


@router.get("/search-logs", response_model=PaginatedSearchLogsResponse)
async def list_search_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    pp = PaginationRequest(page=page, page_size=page_size)
    svc = SearchService(db, tenant)
    result = await svc.list_search_logs(pp)
    return PaginatedSearchLogsResponse(
        items=result.items, page=result.page, page_size=result.page_size,
        total=result.total, has_next=result.has_next, has_previous=result.has_previous,
    )


@router.get("/domain-logs", response_model=PaginatedDomainLogsResponse)
async def list_domain_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    pp = PaginationRequest(page=page, page_size=page_size)
    svc = SearchService(db, tenant)
    result = await svc.list_domain_logs(pp)
    return PaginatedDomainLogsResponse(
        items=result.items, page=result.page, page_size=result.page_size,
        total=result.total, has_next=result.has_next, has_previous=result.has_previous,
    )
