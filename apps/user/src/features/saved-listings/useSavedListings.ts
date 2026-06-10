import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listSavedListings,
  listSavedListingsWithDetails,
  saveListing,
  unsaveListing,
  type SavedListingItem,
  type SavedListingWithDetails,
  type PaginatedSavedListingsResponse,
} from "@/lib/api/auth";

const SAVED_LISTINGS_QUERY_KEY = ["saved-listings"];
const SAVED_LISTINGS_FULL_QUERY_KEY = ["saved-listings", "full"];

export function useSavedListings() {
  const queryClient = useQueryClient();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: SAVED_LISTINGS_QUERY_KEY,
    queryFn: () => listSavedListings(1, 100),
    staleTime: 1000 * 60 * 5,
  });

  const savedListingIds = data?.items?.map((item) => item.listing_id) ?? [];

  const saveMutation = useMutation({
    mutationFn: (listingId: string) => saveListing(listingId),
    onMutate: async (listingId: string) => {
      await queryClient.cancelQueries({ queryKey: SAVED_LISTINGS_QUERY_KEY });
      const previous = queryClient.getQueryData<PaginatedSavedListingsResponse>(SAVED_LISTINGS_QUERY_KEY);
      queryClient.setQueryData<PaginatedSavedListingsResponse>(SAVED_LISTINGS_QUERY_KEY, (old) => {
        if (!old) return { items: [], page: 1, page_size: 100, total: 1, has_next: false, has_previous: false };
        if (old.items.some((i) => i.listing_id === listingId)) return old;
        const newItem: SavedListingItem = {
          id: crypto.randomUUID(),
          user_id: "",
          listing_id: listingId,
          created_at: new Date().toISOString(),
          deleted_at: null,
        };
        return { ...old, items: [newItem, ...old.items], total: old.total + 1 };
      });
      return { previous };
    },
    onError: (_err, _listingId, context) => {
      if (context?.previous) {
        queryClient.setQueryData(SAVED_LISTINGS_QUERY_KEY, context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: SAVED_LISTINGS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: SAVED_LISTINGS_FULL_QUERY_KEY });
    },
  });

  const unsaveMutation = useMutation({
    mutationFn: (listingId: string) => unsaveListing(listingId),
    onMutate: async (listingId: string) => {
      await queryClient.cancelQueries({ queryKey: SAVED_LISTINGS_QUERY_KEY });
      const previous = queryClient.getQueryData<PaginatedSavedListingsResponse>(SAVED_LISTINGS_QUERY_KEY);
      queryClient.setQueryData<PaginatedSavedListingsResponse>(SAVED_LISTINGS_QUERY_KEY, (old) => {
        if (!old) return { items: [], page: 1, page_size: 100, total: 0, has_next: false, has_previous: false };
        return { ...old, items: old.items.filter((i) => i.listing_id !== listingId), total: old.total - 1 };
      });
      return { previous };
    },
    onError: (_err, _listingId, context) => {
      if (context?.previous) {
        queryClient.setQueryData(SAVED_LISTINGS_QUERY_KEY, context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: SAVED_LISTINGS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: SAVED_LISTINGS_FULL_QUERY_KEY });
    },
  });

  const toggleSaved = (listingId: string) => {
    const isCurrentlySaved = savedListingIds.includes(listingId);
    if (isCurrentlySaved) {
      unsaveMutation.mutate(listingId);
    } else {
      saveMutation.mutate(listingId);
    }
  };

  const isSaved = (listingId: string) => {
    return savedListingIds.includes(listingId);
  };

  const clearAll = () => {
    queryClient.setQueryData(SAVED_LISTINGS_QUERY_KEY, {
      items: [],
      page: 1,
      page_size: 100,
      total: 0,
      has_next: false,
      has_previous: false,
    });
    queryClient.setQueryData(SAVED_LISTINGS_FULL_QUERY_KEY, {
      items: [],
      page: 1,
      page_size: 100,
      total: 0,
      has_next: false,
      has_previous: false,
    });
  };

  return {
    savedListings: savedListingIds,
    isLoading,
    error,
    toggleSaved,
    unsave: unsaveMutation.mutate,
    isSaved,
    clearAll,
    refetch,
  };
}

export function useSavedListingsFull() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: SAVED_LISTINGS_FULL_QUERY_KEY,
    queryFn: () => listSavedListingsWithDetails(1, 100),
    staleTime: 1000 * 60 * 5,
  });

  return {
    savedListings: (data?.items ?? []) as SavedListingWithDetails[],
    isLoading,
    error,
    refetch,
  };
}