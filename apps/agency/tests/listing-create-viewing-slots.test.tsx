import { fireEvent, screen } from "@testing-library/react";
import { vi } from "vitest";
import { renderWithProviders } from "./test-utils";
import { ListingForm } from "@/features/listings/ListingForm";
import type { DraftViewingSlot } from "@/features/listings/viewing-slot-draft";

vi.mock("@/features/listings/useAgencyListings", () => ({
  useAgencyListings: () => ({
    createListing: vi.fn(),
    isCreating: false,
    createError: null,
    publishListing: vi.fn(),
    isPublishing: false,
  }),
  useListingDetail: () => ({
    listing: null,
    isLoading: false,
    error: null,
    updateListing: vi.fn(),
    isUpdating: false,
    updateError: null,
  }),
  uploadListingPhoto: vi.fn(),
}));

vi.mock("@/features/listings/useListingCities", () => ({
  useListingCities: () => ({
    data: ["Beirut"],
    isLoading: false,
  }),
}));

vi.mock("@/features/listings/useViewingSlots", () => ({
  createViewingSlot: vi.fn(),
}));

describe("listing create viewing slots", () => {
  it("lets the user stage viewing dates while creating a listing", () => {
    const handleChange = vi.fn();
    const stagedSlots: DraftViewingSlot[] = [];

    renderWithProviders(
      <ListingForm
        listingId={null}
        stagedPhotos={[]}
        stagedViewingSlots={stagedSlots}
        onStagedViewingSlotsChange={handleChange}
        draftHydrated
      />,
    );

    expect(screen.getByText(/viewing availability/i)).toBeInTheDocument();
    expect(screen.getByText(/they will be saved when you submit the listing/i)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/start time/i), {
      target: { value: "2026-06-20T10:00" },
    });
    fireEvent.change(screen.getByLabelText(/end time/i), {
      target: { value: "2026-06-20T11:00" },
    });
    fireEvent.change(screen.getByLabelText(/capacity/i), {
      target: { value: "2" },
    });
    fireEvent.click(screen.getByRole("button", { name: /add viewing date/i }));

    expect(handleChange).toHaveBeenCalledTimes(1);
    expect(handleChange.mock.calls[0][0]).toEqual([
      expect.objectContaining({
        starts_at: "2026-06-20T10:00",
        ends_at: "2026-06-20T11:00",
        capacity: "2",
      }),
    ]);
  });
});
