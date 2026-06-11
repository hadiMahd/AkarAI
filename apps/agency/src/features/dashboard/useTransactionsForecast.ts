import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/query-client";

export interface ForecastPoint {
  month: string;
  label: string;
  value: number;
  point_type: "historical" | "forecast";
}

export interface TransactionsForecastResponse {
  metric: string;
  model_name: string;
  history_start_month: string;
  history_end_month: string;
  forecast_month: string;
  latest_actual_value: number;
  forecast_value: number;
  series: ForecastPoint[];
}

async function fetchTransactionsForecast(historyMonths: number): Promise<TransactionsForecastResponse> {
  return apiClient<TransactionsForecastResponse>("/agency/dashboard/transactions-forecast", {
    params: { history_months: historyMonths },
  });
}

export function useTransactionsForecast(historyMonths = 24) {
  return useQuery({
    queryKey: queryKeys.dashboard.transactionsForecast(historyMonths),
    queryFn: () => fetchTransactionsForecast(historyMonths),
  });
}
