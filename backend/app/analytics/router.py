from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.schemas import AgencyTransactionsForecastResponse
from app.analytics.service import AgencyForecastService
from app.auth.dependencies import get_tenant_context
from app.common.dependencies import get_db_session
from app.common.tenant import TenantContext
from app.leads.query_service import LeadProcessingQueryService
from app.leads.schemas import LeadProcessingTrendsResponse, LeadProcessingSummary

router = APIRouter(prefix="/agency/dashboard", tags=["Agency Dashboard"])


@router.get("/transactions-forecast", response_model=AgencyTransactionsForecastResponse)
async def get_transactions_forecast(
    history_months: int = Query(24, ge=12, le=60),
    tenant: TenantContext = Depends(get_tenant_context),
):
    service = AgencyForecastService(tenant)
    return service.get_transactions_forecast(history_months=history_months)


@router.get("/lead-processing-trends", response_model=LeadProcessingTrendsResponse)
async def get_lead_processing_trends(
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db_session),
):
    query_svc = LeadProcessingQueryService(db)
    trends = await query_svc.get_trend_summary(tenant.tenant_id)
    return LeadProcessingTrendsResponse(
        tenant_id=tenant.tenant_id,
        summary=LeadProcessingSummary(
            total_leads=trends["total_leads"],
            spam_count=trends["spam_count"],
            not_spam_count=trends["not_spam_count"],
            hot_count=trends["hot_count"],
            normal_count=trends["normal_count"],
            pending_count=trends["pending_count"],
            reviewed_count=trends["reviewed_count"],
        ),
        spam_rate=trends["spam_rate"],
        hot_rate=trends["hot_rate"],
        review_rate=trends["review_rate"],
        fallback_count=trends["fallback_count"],
    )
