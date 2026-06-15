import { useMutation } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";

export interface ConfirmedSearchFilters {
  q?: string;
  city?: string;
  location?: string;
  property_type?: string;
  listing_purpose?: string;
  min_price?: number;
  max_price?: number;
  bedrooms?: number;
  bathrooms?: number;
  parking?: number;
  floor?: number;
  furnishing?: string;
  min_area_size?: number;
  max_area_size?: number;
  sort?: string;
  page?: number;
  page_size?: number;
}

export interface UnclearLocationIntent {
  phrase: string;
  reason: string;
  suggested_action?: string;
  resolved_city?: string;
}

export interface SearchIntent {
  source_mode: string;
  filters: ConfirmedSearchFilters;
  confidence: string;
  raw_query?: string;
  transcript?: string;
  provider?: string;
  fallback_reason?: string;
  unclear_location?: UnclearLocationIntent;
}

export interface SearchIntentResponse {
  intent: SearchIntent;
  unclear_location?: UnclearLocationIntent;
  transcript?: {
    transcript?: string;
  };
}

export function useSearchIntent() {
  return useMutation({
    mutationFn: async (q: string): Promise<SearchIntentResponse> => {
      return await apiClient("/search/intent", {
        method: "POST",
        body: JSON.stringify({ q }),
      });
    },
  });
}

export function useConfirmationLog() {
  return useMutation({
    mutationFn: async (data: {
      source_mode: string;
      confirmed_filters: ConfirmedSearchFilters;
      edits?: string[];
    }): Promise<void> => {
      await apiClient("/search/logs/confirmation", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
  });
}
