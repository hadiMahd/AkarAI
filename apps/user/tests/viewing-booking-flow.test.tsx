import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ListingDetailPage } from "../src/pages/listing-detail/ListingDetailPage";
import { useAuth } from "../src/features/auth/useAuth";
import { apiClient } from "../src/lib/api/client";

vi.mock("../src/features/auth/useAuth");
vi.mock("../src/lib/api/client", async () => {
  const actual: any = await vi.importActual("../src/lib/api/client");
  return { ...actual, apiClient: vi.fn() };
});

const mockUseAuth = vi.mocked(useAuth);
const mockApiClient = vi.mocked(apiClient);

function renderWithProviders(ui: React.ReactElement, { route = "/listings/test-listing-id" } = {}) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: 0,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route path="/listings/:id" element={ui} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

const mockListing = {
  id: "test-listing-id",
  title: "Test Property",
  description: "A beautiful test property",
  price: 250000,
  currency: "USD",
  location_text: "Test City",
  address: "123 Test St",
  city: "Test City",
  property_type: "apartment",
  listing_purpose: "sale" as const,
  bedrooms: 2,
  bathrooms: 1,
  area_size: 85,
  area_unit: "sqm",
  furnishing: "furnished",
  status: "active",
  created_at: "2024-01-01T00:00:00Z",
};

const mockSlots = [
  {
    id: "slot-1",
    starts_at: "2026-06-15T10:00:00Z",
    ends_at: "2026-06-15T11:00:00Z",
    capacity: 5,
    reserved_count: 0,
    status: "active",
  },
  {
    id: "slot-2",
    starts_at: "2026-06-16T14:00:00Z",
    ends_at: "2026-06-16T15:00:00Z",
    capacity: 3,
    reserved_count: 1,
    status: "active",
  },
];

describe("Viewing Booking Flow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAuth.mockReturnValue({
      user: { id: "user-1", email: "test@example.com" },
      isAuthenticated: true,
      isLoading: false,
      signIn: vi.fn(),
      signUp: vi.fn(),
      signOut: vi.fn(),
    } as any);
  });

  it("renders viewing slot picker when slots are available", async () => {
    mockApiClient.mockImplementation((endpoint: string) => {
      if (endpoint.includes("/viewing-slots")) {
        return Promise.resolve(mockSlots as any);
      }
      return Promise.resolve(mockListing as any);
    });

    renderWithProviders(<ListingDetailPage />);

    await waitFor(() => {
      expect(screen.getByText(/available viewing slots/i)).toBeInTheDocument();
    });
  });

  it("allows selecting a viewing slot", async () => {
    mockApiClient.mockImplementation((endpoint: string) => {
      if (endpoint.includes("/viewing-slots")) {
        return Promise.resolve(mockSlots as any);
      }
      return Promise.resolve(mockListing as any);
    });

    renderWithProviders(<ListingDetailPage />);

    await waitFor(() => {
      expect(screen.getByText(/available viewing slots/i)).toBeInTheDocument();
    });

    const slotButtons = screen.getAllByRole("button").filter((btn) =>
      btn.textContent?.includes("spots filled")
    );
    expect(slotButtons.length).toBeGreaterThan(0);

    await userEvent.click(slotButtons[0]);

    expect(screen.getByRole("button", { name: /book viewing/i })).toBeInTheDocument();
  });

  it("submits booking form successfully", async () => {
    const mockBookingResponse = {
      id: "booking-1",
      listing_id: "test-listing-id",
      viewing_slot_id: "slot-1",
      status: "scheduled",
      scheduled_start_at: "2026-06-15T10:00:00Z",
      scheduled_end_at: "2026-06-15T11:00:00Z",
    };

    mockApiClient.mockImplementation((endpoint: string, options?: any) => {
      if (endpoint.includes("/viewings") && options?.method === "POST") {
        return Promise.resolve(mockBookingResponse as any);
      }
      if (endpoint.includes("/viewing-slots")) {
        return Promise.resolve(mockSlots as any);
      }
      return Promise.resolve(mockListing as any);
    });

    renderWithProviders(<ListingDetailPage />);

    await waitFor(() => {
      expect(screen.getByText(/available viewing slots/i)).toBeInTheDocument();
    });

    const slotButtons = screen.getAllByRole("button").filter((btn) =>
      btn.textContent?.includes("spots filled")
    );
    await userEvent.click(slotButtons[0]);

    const bookButton = screen.getByRole("button", { name: /book viewing/i });
    await userEvent.click(bookButton);

    await waitFor(() => {
      expect(screen.getByText(/booked successfully/i)).toBeInTheDocument();
    });
  });

  it("shows error for invalid slot selection", async () => {
    const fullSlots = [
      {
        id: "slot-1",
        starts_at: "2026-06-15T10:00:00Z",
        ends_at: "2026-06-15T11:00:00Z",
        capacity: 5,
        reserved_count: 5,
        status: "active",
      },
    ];

    mockApiClient.mockImplementation((endpoint: string) => {
      if (endpoint.includes("/viewing-slots")) {
        return Promise.resolve(fullSlots as any);
      }
      return Promise.resolve(mockListing as any);
    });

    renderWithProviders(<ListingDetailPage />);

    await waitFor(() => {
      expect(screen.getByText(/available viewing slots/i)).toBeInTheDocument();
    });

    const fullSlotButtons = screen.getAllByRole("button").filter(
      (btn) => btn.textContent?.includes("spots filled") && btn.hasAttribute("disabled")
    );
    expect(fullSlotButtons.length).toBeGreaterThan(0);
  });

  it("shows rate limit error for too many bookings", async () => {
    const { ApiError } = await import("@/lib/api/client");
    mockApiClient.mockImplementation((endpoint: string, options?: any) => {
      if (endpoint.includes("/viewings") && options?.method === "POST") {
        return Promise.reject(
          new ApiError("API request failed: Too Many Requests", 429, {
            detail: "Too many viewing bookings. Please try again later.",
            error_code: "RATE_LIMIT_EXCEEDED",
          }),
        );
      }
      if (endpoint.includes("/viewing-slots")) {
        return Promise.resolve(mockSlots as any);
      }
      return Promise.resolve(mockListing as any);
    });

    renderWithProviders(<ListingDetailPage />);

    await waitFor(() => {
      expect(screen.getByText(/available viewing slots/i)).toBeInTheDocument();
    });

    const slotButtons = screen.getAllByRole("button").filter((btn) =>
      btn.textContent?.includes("spots filled")
    );
    await userEvent.click(slotButtons[0]);

    const bookButton = await screen.findByRole("button", { name: /book viewing/i });
    await userEvent.click(bookButton);

    await waitFor(() => {
      expect(screen.getByText(/booked a lot of viewings|wait a moment/i)).toBeInTheDocument();
    });
  });
});
