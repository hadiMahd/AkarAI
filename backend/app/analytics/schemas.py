from pydantic import BaseModel


class ForecastChartPoint(BaseModel):
    month: str
    label: str
    value: float
    point_type: str


class AgencyTransactionsForecastResponse(BaseModel):
    metric: str
    model_name: str
    history_start_month: str
    history_end_month: str
    forecast_month: str
    latest_actual_value: float
    forecast_value: float
    series: list[ForecastChartPoint]
