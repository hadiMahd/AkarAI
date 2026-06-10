import { useMutation } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";

export interface BookingRequest {
  viewing_slot_id: string;
  notes?: string;
}

export interface BookingResponse {
  id: string;
  listing_id: string;
  viewing_slot_id: string;
  status: string;
  scheduled_start_at: string;
  scheduled_end_at: string;
}

export function useBookViewing(listingId: string) {
  return useMutation<BookingResponse, Error, BookingRequest>({
    mutationFn: (data) =>
      apiClient<BookingResponse>(`/listings/${listingId}/viewings`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
  });
}
