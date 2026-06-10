import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      gcTime: 1000 * 60 * 30,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export const queryKeys = {
  user: {
    me: ["user", "me"] as const,
  },
  listings: {
    all: ["listings"] as const,
    lists: (filters: Record<string, unknown>) => ["listings", "list", filters] as const,
    details: (id: string) => ["listings", "detail", id] as const,
    saved: ["listings", "saved"] as const,
    slots: (listingId: string) => ["listings", listingId, "slots"] as const,
  },
  profile: {
    inquiries: ["profile", "inquiries"] as const,
    viewings: ["profile", "viewings"] as const,
  },
} as const;