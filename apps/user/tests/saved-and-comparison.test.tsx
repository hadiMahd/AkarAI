import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
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

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
}

function Wrapper({ children }: { children: React.ReactNode }) {
  const queryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

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

describe("useSavedListings", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("starts with empty saved listings", () => {
    const { result } = renderHook(() => useSavedListings(), { wrapper: Wrapper });
    expect(result.current.savedListings).toHaveLength(0);
  });

  it("can add a listing to saved", () => {
    const { result } = renderHook(() => useSavedListings(), { wrapper: Wrapper });
    act(() => {
      result.current.toggleSaved(mockListing);
    });
    expect(result.current.savedListings).toHaveLength(1);
    expect(result.current.savedListings[0].id).toBe("1");
  });

  it("can remove a listing from saved", () => {
    const { result } = renderHook(() => useSavedListings(), { wrapper: Wrapper });
    act(() => {
      result.current.toggleSaved(mockListing);
    });
    expect(result.current.savedListings).toHaveLength(1);
    act(() => {
      result.current.toggleSaved(mockListing);
    });
    expect(result.current.savedListings).toHaveLength(0);
  });

  it("persists saved listings to localStorage", () => {
    const { result } = renderHook(() => useSavedListings(), { wrapper: Wrapper });
    act(() => {
      result.current.toggleSaved(mockListing);
    });
    const stored = localStorage.getItem("akarai_saved_listings");
    expect(stored).toBeTruthy();
    const parsed = JSON.parse(stored!);
    expect(parsed).toHaveLength(1);
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