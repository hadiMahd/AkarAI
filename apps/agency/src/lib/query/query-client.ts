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
    me: ["agency", "user", "me"] as const,
  },
  tenant: {
    context: ["agency", "tenant", "context"] as const,
  },
  dashboard: {
    summary: ["agency", "dashboard", "summary"] as const,
    transactionsForecast: (historyMonths: number) =>
      ["agency", "dashboard", "transactions-forecast", historyMonths] as const,
  },
  profile: {
    agency: ["agency", "profile"] as const,
  },
  employees: {
    all: ["agency", "employees"] as const,
    list: (filters: Record<string, unknown>) => ["agency", "employees", "list", filters] as const,
  },
  listings: {
    all: ["agency", "listings"] as const,
    list: (filters: Record<string, unknown>) => ["agency", "listings", "list", filters] as const,
    cities: ["agency", "listings", "cities"] as const,
    detail: (id: string) => ["agency", "listings", "detail", id] as const,
    photos: (listingId: string) => ["agency", "listings", listingId, "photos"] as const,
    slots: (listingId: string) => ["agency", "listings", listingId, "slots"] as const,
  },
  leads: {
    all: ["agency", "leads"] as const,
    active: (filters: Record<string, unknown>) => ["agency", "leads", "active", filters] as const,
    reviewed: (filters: Record<string, unknown>) => ["agency", "leads", "reviewed", filters] as const,
    detail: (id: string) => ["agency", "leads", "detail", id] as const,
  },
  viewings: {
    all: ["agency", "viewings"] as const,
    list: (filters: Record<string, unknown>) => ["agency", "viewings", "list", filters] as const,
  },
  rag: {
    all: ["agency", "rag"] as const,
    list: (filters: Record<string, unknown>) => ["agency", "rag", "list", filters] as const,
    detail: (id: string) => ["agency", "rag", "detail", id] as const,
    retrievalLogs: (filters: Record<string, unknown>) => ["agency", "rag", "retrieval-logs", filters] as const,
    policyQuery: (filters: Record<string, unknown>) => ["agency", "rag", "policy-query", filters] as const,
    chatThreads: (filters: Record<string, unknown>) => ["agency", "rag", "chat-threads", filters] as const,
    chatThread: (id: string) => ["agency", "rag", "chat-thread", id] as const,
  },
  agencyAi: {
    all: ["agency", "ai"] as const,
    listingDraft: (payload: Record<string, unknown>) =>
      ["agency", "ai", "listing-draft", payload] as const,
    specExtraction: (jobId: string) =>
      ["agency", "ai", "spec-extraction", jobId] as const,
    leadReplyDraft: (leadId: string, channel: string) =>
      ["agency", "ai", "lead-reply-draft", leadId, channel] as const,
    jobStatus: (jobId: string) => ["agency", "ai", "job", jobId] as const,
  },
} as const;
