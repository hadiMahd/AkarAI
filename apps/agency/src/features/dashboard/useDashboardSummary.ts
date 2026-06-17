import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/query-client";

interface DashboardSummary {
  listings_total: number;
  active_leads_total: number;
  reviewed_leads_total: number;
  scheduled_viewings_total: number;
}

interface LeadProcessingTrends {
  tenant_id: string;
  summary: {
    total_leads: number;
    spam_count: number;
    not_spam_count: number;
    hot_count: number;
    normal_count: number;
    pending_count: number;
    reviewed_count: number;
  };
  spam_rate: number;
  hot_rate: number;
  review_rate: number;
  fallback_count: number;
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

async function fetchLeadProcessingTrends(): Promise<LeadProcessingTrends> {
  return apiClient<LeadProcessingTrends>("/agency/dashboard/lead-processing-trends");
}

export function useDashboardSummary() {
  return useQuery({
    queryKey: queryKeys.dashboard.summary,
    queryFn: fetchDashboardSummary,
  });
}

export function useLeadProcessingTrends() {
  return useQuery({
    queryKey: ["dashboard", "lead-processing-trends"],
    queryFn: fetchLeadProcessingTrends,
    refetchInterval: 15000,
  });
}

export type { DashboardSummary, LeadProcessingTrends };
