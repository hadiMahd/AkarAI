import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/query-client";

export interface ListingDetail {
  id: string;
  title: string;
  description: string;
  property_type: string;
  listing_purpose: "sale" | "rent";
  price: number;
  currency: string;
  bedrooms: number | null;
  bathrooms: number | null;
  area_size: number | null;
  area_unit: string;
  furnishing: string | null;
  city: string;
  address: string;
  location_text: string;
  status: string;
  created_at: string;
}

export function useListingDetail(id: string | undefined) {
  return useQuery<ListingDetail, Error>({
    queryKey: queryKeys.listings.details(id!),
    queryFn: () => apiClient<ListingDetail>(`/listings/${id}`),
    enabled: !!id,
    staleTime: 1000 * 60 * 5,
  });
}
