from datetime import date
from uuid import uuid4
from unittest.mock import MagicMock

import pytest

from app.common.tenant import TenantContext


def test_build_feature_row_contains_expected_inputs():
    from app.analytics.service import MonthlyObservation, _build_feature_row

    history = [
        MonthlyObservation(month=date(2025, month, 1), value=float(month))
        for month in range(1, 13)
    ]

    row = _build_feature_row(history, date(2026, 1, 1))

    assert row["year"] == 2026
    assert row["month"] == 1
    assert row["quarter"] == 1
    assert row["trend"] == 12
    assert row["Avg Transactions per Agency_lag_1"] == 12.0
    assert row["Avg Transactions per Agency_lag_12"] == 1.0
    assert row["Avg Transactions per Agency_roll_mean_3"] == pytest.approx(11.0)
    assert row["Avg Transactions per Agency_roll_min_12"] == 1.0
    assert row["Avg Transactions per Agency_roll_max_12"] == 12.0


def test_agency_forecast_service_returns_history_plus_forecast(monkeypatch: pytest.MonkeyPatch):
    from app.analytics.service import AgencyForecastService, MonthlyObservation

    tenant = TenantContext(
        tenant_id=uuid4(),
        actor_id=uuid4(),
        role="agency_admin",
        permissions=[],
    )
    history = [
        MonthlyObservation(month=date(2025, month, 1), value=float(month))
        for month in range(1, 13)
    ]

    class DummyDate(date):
        @classmethod
        def today(cls) -> "DummyDate":
            return cls(2025, 12, 18)

    dummy_model = MagicMock()
    dummy_model.predict.return_value = [13.4]

    monkeypatch.setattr("app.analytics.service._load_history", lambda: history)
    monkeypatch.setattr("app.analytics.service._load_model", lambda: dummy_model)
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
