import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/query-client";

interface ListingMediaItem {
  id: string;
  listing_id: string;
  caption: string | null;
  alt_text: string | null;
  display_order: number;
  width: number | null;
  height: number | null;
  media_url: string;
  format: string;
  status: string;
}

export function useListingMedia(listingId: string | undefined) {
  return useQuery<ListingMediaItem[], Error>({
    queryKey: queryKeys.listings.media(listingId!),
    queryFn: () => apiClient<ListingMediaItem[]>(`/listings/${listingId}/media`),
    enabled: !!listingId,
  });
}
