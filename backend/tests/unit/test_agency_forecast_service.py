from datetime import date
from uuid import uuid4

import pytest

from app.common.tenant import TenantContext


def test_agency_forecast_service_returns_history_plus_forecast(monkeypatch: pytest.MonkeyPatch):
    from app.analytics.service import AgencyForecastService, MonthlyObservation

    tenant = TenantContext(
        tenant_id=uuid4(),
        actor_id=uuid4(),
        role="agency_admin",
        permissions=[],
    )
    history = [
        MonthlyObservation(month=date(2025, month, 1), value=float(month), prediction=float(month))
        for month in range(1, 13)
    ]
    # Add the forecast-month entry that _load_predictions would include
    history.append(MonthlyObservation(month=date(2026, 1, 1), value=12.0, prediction=13.4))

    class DummyDate(date):
        @classmethod
        def today(cls) -> "DummyDate":
            return cls(2025, 12, 18)

    monkeypatch.setattr("app.analytics.service._load_predictions", lambda: history)
    monkeypatch.setattr("app.analytics.service.date", DummyDate)

    response = AgencyForecastService(tenant).get_transactions_forecast(history_months=12)

    assert response.forecast_month == "2026-01-01"
    assert response.forecast_value == 13.4
    assert response.latest_actual_value == 12.0
    assert response.series[-1].point_type == "forecast"
    assert len(response.series) == 13


def test_agency_forecast_service_blocks_support_employee():
    from app.analytics.service import AgencyForecastService
    from app.common.exceptions import ForbiddenError

    tenant = TenantContext(
        tenant_id=uuid4(),
        actor_id=uuid4(),
        role="support_employee",
        permissions=[],
    )

    with pytest.raises(ForbiddenError):
        AgencyForecastService(tenant).get_transactions_forecast()
