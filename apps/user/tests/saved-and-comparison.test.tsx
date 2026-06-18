import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { renderHook, act } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useSavedListings } from "@/features/saved-listings/useSavedListings";
import { useSessionComparison } from "@/features/comparison/sessionComparison";

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
}

function Wrapper({ children }: { children: React.ReactNode }) {
  const queryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

const mockSavedListingItem = {
  id: "saved-1",
  user_id: "user-1",
  listing_id: "1",
  created_at: "2024-01-01T00:00:00Z",
  deleted_at: null,
};

const mockSavedListingWithDetails = {
  ...mockSavedListingItem,
  listing: {
    id: "1",
    title: "Test Listing",
    description: "Test description",
    property_type: "apartment",
    listing_purpose: "sale",
    price: 100000,
    currency: "USD",
    bedrooms: 2,
    bathrooms: 1,
    area_size: 80,
    area_unit: "sqm",
    furnishing: "furnished",
    location_text: "Test City",
    city: "Test City",
    country: "Test Country",
    status: "active",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
};

const mockApiResponse = {
  items: [mockSavedListingItem],
  page: 1,
  page_size: 100,
  total: 1,
  has_next: false,
  has_previous: false,
};

const mockApiResponseWithDetails = {
  items: [mockSavedListingWithDetails],
  page: 1,
  page_size: 100,
  total: 1,
  has_next: false,
  has_previous: false,
};

// Mock the API client
vi.mock("@/lib/api/client", () => ({
  apiClient: vi.fn(async (endpoint: string, options?: { method?: string; body?: string }) => {
    if (endpoint === "/me/saved-listings" && options?.method === undefined) {
      return Promise.resolve(mockApiResponse);
    }
    if (endpoint === "/me/saved-listings/with-details" && options?.method === undefined) {
      return Promise.resolve(mockApiResponseWithDetails);
    }
    if (endpoint.startsWith("/me/saved-listings/") && options?.method === "PUT") {
      return Promise.resolve(mockSavedListingItem);
    }
    if (endpoint.startsWith("/me/saved-listings/") && options?.method === "DELETE") {
      return Promise.resolve({});
    }
    return Promise.resolve({});
  }),
  API_BASE_URL: "http://localhost:8000",
  ApiError: class ApiError extends Error {
    constructor(message: string, public status: number, public data?: unknown) {
      super(message);
    }
  },
}));

vi.mock("@/lib/session/auth-session", () => ({
  getSession: () => ({
    accessToken: "mock-token",
    user: { id: "user-1", email: "test@example.com" },
  }),
  getAccessToken: () => "mock-token",
  setAccessToken: vi.fn(),
  setSession: vi.fn(),
  clearSession: vi.fn(),
  clearLegacyStorage: vi.fn(),
}));

describe("useSavedListings with backend API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches saved listings from backend on mount", async () => {
    const { result } = renderHook(() => useSavedListings(), { wrapper: Wrapper });

    // Should start loading
    expect(result.current.isLoading).toBe(true);
  });

  it("reflects backend saved state after data loads", async () => {
    const { result } = renderHook(() => useSavedListings(), { wrapper: Wrapper });

    // Wait for the query to complete
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Should have the saved listing
    expect(result.current.savedListings).toContain("1");
    expect(result.current.isSaved("1")).toBe(true);
  });

  it("does not persist to localStorage", async () => {
    const setItemSpy = vi.spyOn(Storage.prototype, "setItem");

    renderHook(() => useSavedListings(), { wrapper: Wrapper });

    // Should not write to localStorage for saved listings
    expect(setItemSpy).not.toHaveBeenCalledWith("akarai_saved_listings", expect.anything());
  });

  it("shows loading state initially", () => {
    const { result } = renderHook(() => useSavedListings(), { wrapper: Wrapper });
    expect(result.current.isLoading).toBe(true);
  });

  it("handles empty saved listings from backend", async () => {
    mockApiResponse.items = [];
    mockApiResponse.total = 0;

    const { result } = renderHook(() => useSavedListings(), { wrapper: Wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.savedListings).toHaveLength(0);
  });
});

describe("useSessionComparison", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("starts with empty comparison list", () => {
    const { result } = renderHook(() => useSessionComparison(), { wrapper: Wrapper });
    expect(result.current.comparisonListings).toHaveLength(0);
  });

  it("can add a listing to comparison", () => {
    const { result } = renderHook(() => useSessionComparison(), { wrapper: Wrapper });
    act(() => {
      result.current.addToComparison(mockListing);
    });
    expect(result.current.comparisonListings).toHaveLength(1);
  });

  it("limits comparison to 4 items", () => {
    const { result } = renderHook(() => useSessionComparison(), { wrapper: Wrapper });
    act(() => {
      for (let i = 0; i < 5; i++) {
        result.current.addToComparison({ ...mockListing, id: String(i) });
      }
    });
    expect(result.current.comparisonListings).toHaveLength(4);
  });

  it("can remove a listing from comparison", () => {
    const { result } = renderHook(() => useSessionComparison(), { wrapper: Wrapper });
    act(() => {
      result.current.addToComparison(mockListing);
    });
    expect(result.current.comparisonListings).toHaveLength(1);
    act(() => {
      result.current.removeFromComparison("1");
    });
    expect(result.current.comparisonListings).toHaveLength(0);
  });

  it("persists comparison to sessionStorage", () => {
    const { result } = renderHook(() => useSessionComparison(), { wrapper: Wrapper });
    act(() => {
      result.current.addToComparison(mockListing);
    });
    const stored = sessionStorage.getItem("akarai_comparison_listings");
    expect(stored).toBeTruthy();
    const parsed = JSON.parse(stored!);
    expect(parsed).toHaveLength(1);
  });
});

const mockListing = {
  id: "1",
  title: "Test Listing",
  description: "Test description",
  property_type: "apartment",
  listing_purpose: "sale" as const,
  price: 100000,
  currency: "USD",
  bedrooms: 2,
  bathrooms: 1,
  area_size: 80,
  area_unit: "sqm",
  city: "Test City",
  address: "123 Test St",
  status: "active",
};
