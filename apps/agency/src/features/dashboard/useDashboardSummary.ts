import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/query-client";

interface DashboardSummary {
  listings_total: number;
  active_leads_total: number;
  reviewed_leads_total: number;
  scheduled_viewings_total: number;
}

async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const [listingsRes, activeLeadsRes, reviewedLeadsRes, viewingsRes] = await Promise.all([
    apiClient<{ total: number }>("/agency/listings", { params: { page: 1, page_size: 1 } }),
    apiClient<{ total: number }>("/agency/leads", { params: { page: 1, page_size: 1, reviewed: false } }),
    apiClient<{ total: number }>("/agency/leads", { params: { page: 1, page_size: 1, status: "reviewed" } }),
    apiClient<{ total: number }>("/agency/viewings", { params: { page: 1, page_size: 1 } }),
  ]);

  return {
    listings_total: listingsRes.total,
    active_leads_total: activeLeadsRes.total,
    reviewed_leads_total: reviewedLeadsRes.total,
    scheduled_viewings_total: viewingsRes.total,
  };
}

export function useDashboardSummary() {
  return useQuery({
    queryKey: queryKeys.dashboard.summary,
    queryFn: fetchDashboardSummary,
  });
}
