import csv
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path

from app.analytics.schemas import AgencyTransactionsForecastResponse, ForecastChartPoint
from app.common.exceptions import ForbiddenError, ServiceUnavailableError, ValidationError
from app.common.tenant import TenantContext, require_tenant

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts" / "agency_sales_forecast"
PREDICTIONS_PATH = ARTIFACTS_DIR / "model_predictions.csv"
MODEL_NAME = "lightgbm"


@dataclass(frozen=True)
class MonthlyObservation:
    month: date
    value: float
    prediction: float


@lru_cache(maxsize=1)
def _load_predictions() -> list[MonthlyObservation]:
    if not PREDICTIONS_PATH.exists():
        raise ServiceUnavailableError(detail="Forecast history artifact is missing")

    rows: list[MonthlyObservation] = []
    with PREDICTIONS_PATH.open(newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if row.get("model") != MODEL_NAME:
                continue
            raw_date = row.get("date")
            raw_actual = row.get("actual")
            raw_prediction = row.get("prediction")
            if not raw_date or raw_actual is None:
                continue
            rows.append(
                MonthlyObservation(
                    month=date.fromisoformat(raw_date),
                    value=float(raw_actual),
                    prediction=float(raw_prediction) if raw_prediction is not None else float(raw_actual),
                )
            )

    if not rows:
        raise ServiceUnavailableError(detail="Forecast history artifact is empty")
    return rows


def _month_start(value: date) -> date:
    return value.replace(day=1)


def _next_month(value: date) -> date:
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


class AgencyForecastService:
    def __init__(self, tenant: TenantContext | None):
        self._tenant = tenant

    def get_transactions_forecast(self, history_months: int = 24) -> AgencyTransactionsForecastResponse:
        ctx = require_tenant(self._tenant)
        if ctx.role != "agency_admin":
            raise ForbiddenError(detail="Only agency admins can view transaction forecasts")

        all_history = _load_predictions()
        current_month = _month_start(date.today())
        filtered_history = [item for item in all_history if item.month <= current_month]
        if len(filtered_history) < 12:
            raise ServiceUnavailableError(detail="Not enough historical data is available for forecasting")

        target_month = _next_month(filtered_history[-1].month)
        forecast_row = next((item for item in all_history if item.month == target_month), None)
        if forecast_row is None:
            future_rows = [item for item in all_history if item.month >= target_month]
            if future_rows:
                forecast_row = min(future_rows, key=lambda item: item.month)
        if forecast_row is None:
            raise ServiceUnavailableError(detail="Forecast month is missing from the artifact predictions")
        prediction = forecast_row.prediction

        history_window = filtered_history[-history_months:]
        series = [
            ForecastChartPoint(
                month=item.month.isoformat(),
                label=item.month.strftime("%b %Y"),
                value=round(item.value, 2),
                point_type="historical",
            )
            for item in history_window
        ]
        series.append(
            ForecastChartPoint(
                month=target_month.isoformat(),
                label=target_month.strftime("%b %Y"),
                value=round(prediction, 2),
                point_type="forecast",
            )
        )

        return AgencyTransactionsForecastResponse(
            metric="average_transactions_per_agency",
            model_name=MODEL_NAME,
            history_start_month=history_window[0].month.isoformat(),
            history_end_month=history_window[-1].month.isoformat(),
            forecast_month=target_month.isoformat(),
            latest_actual_value=round(filtered_history[-1].value, 2),
            forecast_value=round(prediction, 2),
            series=series,
        )
