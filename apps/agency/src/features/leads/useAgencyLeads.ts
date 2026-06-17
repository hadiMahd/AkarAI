import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/query-client";

interface Lead {
  id: string;
  agency_tenant_id: string;
  listing_id: string;
  user_id: string | null;
  status: string;
  processing_status: string | null;
  spam_label: string | null;
  spam_score: number | null;
  lead_level: string | null;
  level_score: number | null;
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

async function fetchSpamLeads(page = 1, pageSize = 20): Promise<PaginatedLeadsResponse> {
  return apiClient<PaginatedLeadsResponse>("/agency/leads", {
    params: { page, page_size: pageSize, spam_label: "spam" },
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
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data?.items) return false;
      const hasPending = data.items.some(
        (lead) => lead.processing_status === "pending_spam" || lead.processing_status === "pending_level" || lead.processing_status === "pending"
      );
      return hasPending ? 5000 : false;
    },
  });
}

export function useReviewedLeads() {
  return useQuery({
    queryKey: queryKeys.leads.reviewed({}),
    queryFn: () => fetchReviewedLeads(),
  });
}

export function useSpamLeads() {
  return useQuery({
    queryKey: ["leads", "spam"],
    queryFn: () => fetchSpamLeads(),
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data?.items) return false;
      const hasPending = data.items.some(
        (lead) => lead.processing_status === "pending_spam" || lead.processing_status === "pending_level" || lead.processing_status === "pending"
      );
      return hasPending ? 5000 : false;
    },
  });
}

export function useLeadDetail(leadId: string) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: queryKeys.leads.detail(leadId),
    queryFn: () => fetchLeadDetail(leadId),
    enabled: !!leadId,
    refetchInterval: (query) => {
      const lead = query.state.data;
      if (lead?.processing_status === "pending_spam" || lead?.processing_status === "pending_level" || lead?.processing_status === "pending") return 5000;
      return false;
    },
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
