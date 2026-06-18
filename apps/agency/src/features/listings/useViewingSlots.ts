import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/query-client";

interface ViewingSlot {
  id: string;
  listing_id: string;
  agency_tenant_id: string;
  starts_at: string;
  ends_at: string;
  capacity: number;
  reserved_count: number;
  status: string;
  created_at: string;
  updated_at: string;
}

interface ViewingSlotCreateRequest {
  starts_at: string;
  ends_at: string;
  capacity: number;
}

async function fetchViewingSlots(listingId: string): Promise<ViewingSlot[]> {
  return apiClient<ViewingSlot[]>(`/agency/listings/${listingId}/viewing-slots`);
}

async function createViewingSlot(listingId: string, data: ViewingSlotCreateRequest): Promise<ViewingSlot> {
  return apiClient<ViewingSlot>(`/agency/listings/${listingId}/viewing-slots`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

async function deactivateViewingSlot(listingId: string, slotId: string): Promise<void> {
  return apiClient<void>(`/agency/listings/${listingId}/viewing-slots/${slotId}`, {
    method: "DELETE",
  });
}

export function useViewingSlots(listingId: string) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: queryKeys.listings.slots(listingId),
    queryFn: () => fetchViewingSlots(listingId),
    enabled: !!listingId,
  });

  const createMutation = useMutation({
    mutationFn: (data: ViewingSlotCreateRequest) => createViewingSlot(listingId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.listings.slots(listingId) });
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: (slotId: string) => deactivateViewingSlot(listingId, slotId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.listings.slots(listingId) });
    },
  });

  return {
    slots: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error,
    createSlot: createMutation.mutateAsync,
    isCreating: createMutation.isPending,
    deactivateSlot: deactivateMutation.mutateAsync,
    isDeactivating: deactivateMutation.isPending,
  };
}

export type { ViewingSlot, ViewingSlotCreateRequest };
export { createViewingSlot };
