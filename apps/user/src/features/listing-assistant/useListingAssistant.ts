import { useMutation } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";

export type ListingAssistantRole = "user" | "assistant";

export interface ListingAssistantMessage {
  role: ListingAssistantRole;
  content: string;
}

export interface ListingAssistantPendingAction {
  type: "lead_inquiry" | "viewing_booking";
  payload: {
    message?: string;
    viewing_slot_id?: string;
    scheduled_start_at?: string;
    scheduled_end_at?: string;
    scheduled_label?: string;
    notes?: string;
  };
}

export interface ListingAssistantResponse {
  assistant_message: string;
  pending_action: ListingAssistantPendingAction | null;
  metadata: Record<string, unknown>;
}

export interface ListingAssistantRequest {
  message: string;
  conversation_messages: ListingAssistantMessage[];
}

export function useListingAssistant(listingId: string) {
  return useMutation<ListingAssistantResponse, Error, ListingAssistantRequest>({
    mutationFn: (data) =>
      apiClient<ListingAssistantResponse>(`/api/v1/listings/${listingId}/assistant/messages`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
  });
}
