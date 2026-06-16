import { useMutation, useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/query-client";

export interface ComparisonSummaryRequest {
  listing_ids: string[];
}

export interface ComparisonSummaryResponse {
  job_id: string;
  status: string;
  summary?: string | null;
  key_differences: string[];
  best_fit_notes: string[];
  guardrail_status?: string | null;
  generation_provider?: string | null;
  blocked_reason?: string | null;
}

async function requestComparisonSummary(
  payload: ComparisonSummaryRequest,
): Promise<ComparisonSummaryResponse> {
  return apiClient<ComparisonSummaryResponse>(
    "/api/v1/me/comparison-summary",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function useComparisonSummaryMutation() {
  return useMutation({
    mutationFn: requestComparisonSummary,
  });
}

async function fetchLatestComparisonSummary(
  listingIds: string[],
): Promise<ComparisonSummaryResponse | null> {
  if (!listingIds.length) return null;
  return apiClient<ComparisonSummaryResponse | null>(
    `/api/v1/me/comparison-summary/${listingIds.join(",")}`,
  );
}

export function useComparisonSummary(listingIds: string[]) {
  return useQuery({
    queryKey: queryKeys.comparison.summary(listingIds),
    queryFn: () => fetchLatestComparisonSummary(listingIds),
    enabled: listingIds.length >= 2,
  });
}
