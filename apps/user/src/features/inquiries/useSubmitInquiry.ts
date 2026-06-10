import { useMutation } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";

export interface InquiryRequest {
  message: string;
  contact_phone?: string;
}

export interface InquiryResponse {
  id: string;
  listing_id: string;
  status: string;
  created_at: string;
}

export function useSubmitInquiry(listingId: string) {
  return useMutation<InquiryResponse, Error, InquiryRequest>({
    mutationFn: (data) =>
      apiClient<InquiryResponse>(`/listings/${listingId}/inquiries`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
  });
}
