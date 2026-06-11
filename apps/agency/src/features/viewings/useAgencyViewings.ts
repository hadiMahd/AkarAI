import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/query-client";

interface ScheduledViewing {
  id: string;
  agency_tenant_id: string;
  listing_id: string;
  viewing_slot_id: string;
  user_id: string | null;
  status: string;
  scheduled_start_at: string;
  scheduled_end_at: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

interface PaginatedViewingsResponse {
  items: ScheduledViewing[];
  page: number;
  page_size: number;
  total: number;
  has_next: boolean;
  has_previous: boolean;
}

interface ViewingFilters {
  status?: string;
  listing_id?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

async function fetchViewings(filters: ViewingFilters = {}): Promise<PaginatedViewingsResponse> {
  const params: Record<string, string | number> = {};
  if (filters.status) params.status = filters.status;
  if (filters.listing_id) params.listing_id = filters.listing_id;
  if (filters.date_from) params.date_from = filters.date_from;
  if (filters.date_to) params.date_to = filters.date_to;
  if (filters.page) params.page = filters.page;
  if (filters.page_size) params.page_size = filters.page_size;

  return apiClient<PaginatedViewingsResponse>("/agency/viewings", { params });
}

export function useAgencyViewings(filters: ViewingFilters = {}) {
  return useQuery({
    queryKey: queryKeys.viewings.list(filters as Record<string, unknown>),
    queryFn: () => fetchViewings(filters),
  });
}

export type { ScheduledViewing, ViewingFilters };
