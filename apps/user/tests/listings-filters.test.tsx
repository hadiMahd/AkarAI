import { describe, it, expect, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { ListingsPage } from "@/pages/listings/ListingsPage";

const apiClientMock = vi.fn();

vi.mock("@/lib/api/client", () => ({
  apiClient: (...args: unknown[]) => apiClientMock(...args),
}));

vi.mock("@/features/saved-listings/useSavedListings", () => ({
  useSavedListings: () => ({
    savedListings: [],
    isSaved: () => false,
    toggleSaved: vi.fn(),
  }),
  useSavedListingsFull: () => ({ savedListings: [] }),
}));

function renderPage(initialEntry: string) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route path="/listings" element={<ListingsPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const response = {
  items: [
    {
      id: "listing-1",
      title: "Listing 1",
      description: "Desc",
      property_type: "apartment",
      listing_purpose: "sale",
      price: 100000,
      currency: "USD",
      bedrooms: 2,
      bathrooms: 1,
      area_size: 90,
      area_unit: "sqm",
      city: "Beirut",
      address: "Address",
      status: "active",
      thumbnail_url: null,
    },
  ],
  total: 1,
  page: 1,
  page_size: 12,
  has_next: false,
  has_previous: false,
};

describe("ListingsPage filters and sorting", () => {
  beforeEach(() => {
    apiClientMock.mockReset();
    apiClientMock.mockResolvedValue(response);
  });

  it("passes q and city separately with furnishing and area filters", async () => {
    renderPage("/listings?q=target&city=Beirut&furnishing=furnished&min_area_size=80&max_area_size=120");

    await waitFor(() => expect(apiClientMock).toHaveBeenCalled());

    const [, options] = apiClientMock.mock.calls.at(-1)!;
    expect(options.params.location).toBe("target");
    expect(options.params.city).toBe("Beirut");
    expect(options.params.furnishing).toBe("furnished");
    expect(options.params.min_area_size).toBe(80);
    expect(options.params.max_area_size).toBe(120);
  });

  it("maps oldest sort params to backend oldest sort", async () => {
    renderPage("/listings?sort_by=created_at&sort_order=asc");

    await waitFor(() => expect(apiClientMock).toHaveBeenCalled());

    const [, options] = apiClientMock.mock.calls.at(-1)!;
    expect(options.params.sort).toBe("oldest");
  });

  it("renders the extra filter controls exposed by the backend contract", async () => {
    renderPage("/listings");

    await waitFor(() => expect(apiClientMock).toHaveBeenCalled());

    expect(screen.getByLabelText(/furnishing/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/min area/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/max area/i)).toBeInTheDocument();
  });
});
