import { TrendingUp } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

import { useTransactionsForecast } from "./useTransactionsForecast";

function formatValue(value: number): string {
  return value.toFixed(2);
}

function buildChartPath(points: Array<{ x: number; y: number }>): string {
  return points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`)
    .join(" ");
}

export function TransactionsForecastChart() {
  const { data, isLoading, error } = useTransactionsForecast(24);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <div className="h-5 w-48 animate-pulse rounded bg-muted" />
          <div className="h-4 w-64 animate-pulse rounded bg-muted" />
        </CardHeader>
        <CardContent>
          <div className="h-64 animate-pulse rounded bg-muted" />
        </CardContent>
      </Card>
    );
  }

  if (error || !data || data.series.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Transactions Forecast</CardTitle>
          <CardDescription>Next-month average transactions per agency</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border border-dashed p-6 text-sm text-muted-foreground">
            Forecast unavailable right now.
          </div>
        </CardContent>
      </Card>
    );
  }

  const width = 920;
  const height = 280;
  const padding = { top: 20, right: 20, bottom: 34, left: 44 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const values = data.series.map((point) => point.value);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const valueRange = Math.max(maxValue - minValue, 1);
  const denominator = Math.max(data.series.length - 1, 1);

  const plotted = data.series.map((point, index) => {
    const x = padding.left + (plotWidth * index) / denominator;
    const y =
      padding.top + plotHeight - ((point.value - minValue) / valueRange) * plotHeight;
    return { ...point, x, y };
  });

  const historical = plotted.filter((point) => point.point_type === "historical");
  const forecast = plotted[plotted.length - 1];
  const historicalPath = buildChartPath(historical);
  const connectorPath =
    historical.length > 0 ? buildChartPath([historical[historical.length - 1], forecast]) : "";

  const yAxisTicks = Array.from({ length: 4 }, (_, index) => {
    const ratio = index / 3;
    const value = maxValue - valueRange * ratio;
    const y = padding.top + plotHeight * ratio;
    return { value, y };
  });

  return (
    <Card>
      <CardHeader className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <CardTitle>Transactions Forecast</CardTitle>
          <CardDescription>
            Historical monthly average transactions with next month&apos;s model prediction
          </CardDescription>
        </div>
        <div className="rounded-md border bg-muted/30 px-3 py-2 text-right">
          <div className="text-xs text-muted-foreground">Next Month</div>
          <div className="flex items-center gap-2 text-lg font-semibold">
            <TrendingUp className="h-4 w-4 text-emerald-600" />
            <span>{formatValue(data.forecast_value)}</span>
          </div>
          <div className="text-xs text-muted-foreground">{forecast.label}</div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-md border p-3">
            <div className="text-xs text-muted-foreground">Latest Actual</div>
            <div className="text-xl font-semibold">{formatValue(data.latest_actual_value)}</div>
          </div>
          <div className="rounded-md border p-3">
            <div className="text-xs text-muted-foreground">Model</div>
            <div className="text-xl font-semibold uppercase">{data.model_name}</div>
          </div>
          <div className="rounded-md border p-3">
            <div className="text-xs text-muted-foreground">Window</div>
            <div className="text-xl font-semibold">
              {historical[0]?.label} - {historical[historical.length - 1]?.label}
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <svg
            aria-label="transactions forecast chart"
            className="min-w-[920px]"
            viewBox={`0 0 ${width} ${height}`}
            role="img"
          >
            {yAxisTicks.map((tick) => (
              <g key={tick.y}>
                <line
                  x1={padding.left}
                  x2={width - padding.right}
                  y1={tick.y}
                  y2={tick.y}
                  stroke="currentColor"
                  strokeOpacity="0.12"
                />
                <text
                  x={padding.left - 8}
                  y={tick.y + 4}
                  fontSize="11"
                  textAnchor="end"
                  className="fill-muted-foreground"
                >
                  {formatValue(tick.value)}
                </text>
              </g>
            ))}

            <path
              d={historicalPath}
              fill="none"
              stroke="rgb(37 99 235)"
              strokeWidth="3"
              strokeLinejoin="round"
              strokeLinecap="round"
            />

            <path
              d={connectorPath}
              fill="none"
              stroke="rgb(22 163 74)"
              strokeWidth="2.5"
              strokeDasharray="6 6"
              strokeLinejoin="round"
              strokeLinecap="round"
            />

            {historical.map((point, index) => (
              <circle
                key={`${point.month}-${index}`}
                cx={point.x}
                cy={point.y}
                r="3"
                fill="rgb(37 99 235)"
              />
            ))}

            <circle cx={forecast.x} cy={forecast.y} r="5" fill="rgb(22 163 74)" />

            {plotted
              .filter((_, index) => index % 3 === 0 || index === plotted.length - 1)
              .map((point) => (
                <text
                  key={point.month}
                  x={point.x}
                  y={height - 10}
                  fontSize="11"
                  textAnchor="middle"
                  className="fill-muted-foreground"
                >
                  {point.label}
                </text>
              ))}
          </svg>
        </div>
      </CardContent>
    </Card>
  );
}
