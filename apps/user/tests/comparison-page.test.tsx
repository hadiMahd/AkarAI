import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { ComparisonPage } from "@/pages/comparison/ComparisonPage";

vi.mock("@/features/comparison/sessionComparison", () => ({
  useSessionComparison: () => ({
    comparisonListings: [
      {
        id: "listing-1",
        title: "Beirut Apartment",
        description: "Two bedroom apartment",
        property_type: "apartment",
        listing_purpose: "rent",
        price: 1200,
        currency: "USD",
        bedrooms: 2,
        bathrooms: 2,
        area_size: 140,
        area_unit: "sqm",
        city: "Beirut",
        address: "Hamra",
        status: "active",
      },
      {
        id: "listing-2",
        title: "Tripoli Flat",
        description: "One bedroom flat",
        property_type: "apartment",
        listing_purpose: "sale",
        price: 90000,
        currency: "USD",
        bedrooms: 1,
        bathrooms: 1,
        area_size: 95,
        area_unit: "sqm",
        city: "Tripoli",
        address: "El Mina",
        status: "active",
      },
    ],
    removeFromComparison: vi.fn(),
    clearComparison: vi.fn(),
  }),
}));

vi.mock("@/features/comparison/useComparisonSummary", () => ({
  useComparisonSummaryMutation: () => ({
    mutateAsync: vi.fn(async () => ({
      job_id: "cmp-1",
      status: "completed",
      summary: "Beirut is larger and better for families.",
      key_differences: ["Listing 1 has more space"],
      best_fit_notes: ["Listing 1 suits families", "Listing 2 suits smaller budgets"],
    })),
    isPending: false,
    error: null,
  }),
}));

describe("ComparisonPage", () => {
  it("shows an AI comparison button and renders the summary", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <ComparisonPage />
      </MemoryRouter>,
    );

    await user.click(screen.getByRole("button", { name: /compare with ai/i }));

    await waitFor(() => {
      expect(screen.getByText(/ai comparison/i)).toBeInTheDocument();
      expect(screen.getByText(/Beirut is larger/i)).toBeInTheDocument();
      expect(screen.getByText(/Listing 1 has more space/i)).toBeInTheDocument();
    });
  });
});
