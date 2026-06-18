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
      queries: { retry: false, staleTime: 0, gcTime: 0 },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route path="/listings/:id" element={ui} />
          <Route path="/profile" element={<div>Profile Page</div>} />
          <Route path="/sign-in" element={<div>Sign In Page</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

const mockListing = {
  id: "test-listing-id",
  title: "Assistant Test Property",
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

const mockProfile = {
  id: "user-1",
  email: "test@example.com",
  name: "Test User",
  phone: "+96170000000",
  is_complete_for_leads: true,
  missing_fields: [],
};

describe("ListingAssistantWidget", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAuth.mockReturnValue({
      user: { id: "user-1", email: "test@example.com", name: "Test User" },
      isAuthenticated: true,
      isLoading: false,
      signIn: vi.fn(),
      signUp: vi.fn(),
      signOut: vi.fn(),
    } as any);
  });

  it("renders a factual assistant reply for the current listing", async () => {
    mockApiClient.mockImplementation((endpoint: string, options?: any) => {
      if (endpoint === "/me/profile") {
        return Promise.resolve(mockProfile as any);
      }
      if (endpoint.includes("/viewing-slots")) {
        return Promise.resolve([]);
      }
      if (endpoint.includes("/assistant/messages")) {
        return Promise.resolve({
          assistant_message: "The listing price is USD 250,000.",
          pending_action: null,
          metadata: { intent: "listing_facts" },
        } as any);
      }
      return Promise.resolve(mockListing as any);
    });

    renderWithProviders(<ListingDetailPage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /open listing assistant/i })).toBeInTheDocument();
    });

    expect(screen.queryByRole("dialog", { name: /listing assistant/i })).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /open listing assistant/i }));

    await waitFor(() => {
      expect(screen.getByRole("dialog", { name: /listing assistant/i })).toBeInTheDocument();
    });

    await userEvent.type(
      screen.getByLabelText(/^message$/i, { selector: "#listing_assistant_message" }),
      "What is the price?"
    );
    await userEvent.click(screen.getByRole("button", { name: /^send$/i }));

    await waitFor(() => {
      expect(screen.getByText(/USD 250,000/i)).toBeInTheDocument();
    });
  });

  it("prepares an inquiry and only submits after confirm", async () => {
    const submitSpy = vi.fn();

    mockApiClient.mockImplementation((endpoint: string, options?: any) => {
      if (endpoint === "/me/profile") {
        return Promise.resolve(mockProfile as any);
      }
      if (endpoint.includes("/viewing-slots")) {
        return Promise.resolve([]);
      }
      if (endpoint.includes("/assistant/messages")) {
        return Promise.resolve({
          assistant_message: "I prepared an inquiry draft for this listing.",
          pending_action: {
            type: "lead_inquiry",
            payload: { message: "Hello, I am interested in this property." },
          },
          metadata: { intent: "lead_inquiry" },
        } as any);
      }
      if (endpoint.includes("/inquiries") && options?.method === "POST") {
        submitSpy();
        return Promise.resolve({
          id: "lead-1",
          listing_id: "test-listing-id",
          status: "new",
          created_at: "2026-06-18T10:00:00Z",
        } as any);
      }
      return Promise.resolve(mockListing as any);
    });

    renderWithProviders(<ListingDetailPage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /open listing assistant/i })).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole("button", { name: /open listing assistant/i }));

    await userEvent.type(
      screen.getByLabelText(/^message$/i, { selector: "#listing_assistant_message" }),
      "Help me contact the agency"
    );
    await userEvent.click(screen.getByRole("button", { name: /^send$/i }));

    await waitFor(() => {
      expect(screen.getByText(/review inquiry draft/i)).toBeInTheDocument();
    });
    expect(submitSpy).not.toHaveBeenCalled();

    await userEvent.click(screen.getByRole("button", { name: /^confirm$/i }));

    await waitFor(() => {
      expect(submitSpy).toHaveBeenCalledTimes(1);
      expect(screen.getByText(/existing listing inquiry flow/i)).toBeInTheDocument();
    });
  });

  it("cancels a prepared viewing without mutating anything", async () => {
    const bookingSpy = vi.fn();

    mockApiClient.mockImplementation((endpoint: string, options?: any) => {
      if (endpoint === "/me/profile") {
        return Promise.resolve(mockProfile as any);
      }
      if (endpoint.includes("/viewing-slots")) {
        return Promise.resolve([]);
      }
      if (endpoint.includes("/assistant/messages")) {
        return Promise.resolve({
          assistant_message: "I found a viewing slot for tomorrow at 6:00 PM.",
          pending_action: {
            type: "viewing_booking",
            payload: {
              viewing_slot_id: "slot-1",
              scheduled_start_at: "2026-06-19T18:00:00Z",
              scheduled_end_at: "2026-06-19T18:30:00Z",
              notes: "tomorrow after 5",
            },
          },
          metadata: { intent: "viewing_booking" },
        } as any);
      }
      if (endpoint.includes("/viewings") && options?.method === "POST") {
        bookingSpy();
      }
      return Promise.resolve(mockListing as any);
    });

    renderWithProviders(<ListingDetailPage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /open listing assistant/i })).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole("button", { name: /open listing assistant/i }));

    await userEvent.type(
      screen.getByLabelText(/^message$/i, { selector: "#listing_assistant_message" }),
      "Book a viewing tomorrow after 5"
    );
    await userEvent.click(screen.getByRole("button", { name: /^send$/i }));

    await waitFor(() => {
      expect(screen.getByText(/review viewing proposal/i)).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole("button", { name: /^cancel$/i }));
    expect(bookingSpy).not.toHaveBeenCalled();
    expect(screen.queryByText(/review viewing proposal/i)).not.toBeInTheDocument();
  });
});
