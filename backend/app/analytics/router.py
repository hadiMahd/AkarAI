from fastapi import APIRouter, Depends, Query

from app.analytics.schemas import AgencyTransactionsForecastResponse
from app.analytics.service import AgencyForecastService
from app.auth.dependencies import get_tenant_context
from app.common.tenant import TenantContext

router = APIRouter(prefix="/agency/dashboard", tags=["Agency Dashboard"])


@router.get("/transactions-forecast", response_model=AgencyTransactionsForecastResponse)
async def get_transactions_forecast(
    history_months: int = Query(24, ge=12, le=60),
    tenant: TenantContext = Depends(get_tenant_context),
):
    service = AgencyForecastService(tenant)
    return service.get_transactions_forecast(history_months=history_months)
