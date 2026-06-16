import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/query-client";

async function fetchListingCities(): Promise<string[]> {
  return apiClient<string[]>("/listings/cities", { skipAuth: true });
}

export function useListingCities() {
  return useQuery({
    queryKey: queryKeys.listings.cities,
    queryFn: fetchListingCities,
    staleTime: 1000 * 60 * 10,
  });
}
