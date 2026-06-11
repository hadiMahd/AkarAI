import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/query-client";

interface Lead {
  id: string;
  agency_tenant_id: string;
  listing_id: string;
  user_id: string | null;
  status: string;
  name: string | null;
  email: string | null;
  phone: string | null;
  message: string | null;
  source: string | null;
  created_at: string;
  updated_at: string;
}

interface PaginatedLeadsResponse {
  items: Lead[];
  page: number;
  page_size: number;
  total: number;
  has_next: boolean;
  has_previous: boolean;
}

interface LeadReviewRequest {
  outcome?: string;
  notes?: string;
}

interface ReviewedLeadRecord {
  id: string;
  lead_id: string;
  agency_tenant_id: string;
  reviewed_by_user_id: string | null;
  outcome: string | null;
  notes: string | null;
  created_at: string;
}

async function fetchActiveLeads(page = 1, pageSize = 20): Promise<PaginatedLeadsResponse> {
  return apiClient<PaginatedLeadsResponse>("/agency/leads", {
    params: { page, page_size: pageSize, reviewed: false },
  });
}

async function fetchReviewedLeads(page = 1, pageSize = 20): Promise<PaginatedLeadsResponse> {
  return apiClient<PaginatedLeadsResponse>("/agency/leads", {
    params: { page, page_size: pageSize, status: "reviewed" },
  });
}

async function fetchLeadDetail(leadId: string): Promise<Lead> {
  return apiClient<Lead>(`/agency/leads/${leadId}`);
}

async function reviewLead(leadId: string, data: LeadReviewRequest): Promise<ReviewedLeadRecord> {
  return apiClient<ReviewedLeadRecord>(`/agency/leads/${leadId}/review`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function useActiveLeads() {
  return useQuery({
    queryKey: queryKeys.leads.active({}),
    queryFn: () => fetchActiveLeads(),
  });
}

export function useReviewedLeads() {
  return useQuery({
    queryKey: queryKeys.leads.reviewed({}),
    queryFn: () => fetchReviewedLeads(),
  });
}

export function useLeadDetail(leadId: string) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: queryKeys.leads.detail(leadId),
    queryFn: () => fetchLeadDetail(leadId),
    enabled: !!leadId,
  });

  const reviewMutation = useMutation({
    mutationFn: (data: LeadReviewRequest) => reviewLead(leadId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.leads.active({}) });
      queryClient.invalidateQueries({ queryKey: queryKeys.leads.reviewed({}) });
      queryClient.invalidateQueries({ queryKey: queryKeys.leads.detail(leadId) });
    },
  });

  return {
    lead: query.data,
    isLoading: query.isLoading,
    error: query.error,
    reviewLead: reviewMutation.mutateAsync,
    isReviewing: reviewMutation.isPending,
  };
}

export type { Lead, LeadReviewRequest, ReviewedLeadRecord };
