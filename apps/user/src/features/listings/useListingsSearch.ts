import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../../lib/api/client";
import { queryKeys } from "../../lib/query/query-client";
import type { SearchFilters } from "../search/useSearchFilters";

export interface Listing {
  id: string;
  title: string;
  price: number | null;
  currency: string | null;
  location_text: string;
  property_type: string;
  listing_purpose: string;
  bedrooms: number;
  bathrooms: number;
  area_size: number;
  furnishing: string;
}

export interface PaginatedListingsResponse {
  items: Listing[];
  page: number;
  page_size: number;
  total: number;
  has_next: boolean;
  has_previous: boolean;
  next_cursor: string | null;
}

export function useListingsSearch(filters: SearchFilters) {
  return useQuery<PaginatedListingsResponse, Error>({
    queryKey: [...queryKeys.listings.lists(filters as Record<string, unknown>), filters],
    staleTime: 0,
    refetchOnMount: "always",
    queryFn: async () => {
      const params = new URLSearchParams();

      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.set(key, String(value));
        }
      });

      return apiClient<PaginatedListingsResponse>(`/listings?${params.toString()}`);
    },
  });
}
