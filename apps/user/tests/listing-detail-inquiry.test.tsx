import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ListingDetailPage } from "../src/pages/listing-detail/ListingDetailPage";
import { useAuth } from "../src/features/auth/useAuth";
import { apiClient } from "../src/lib/api/client";

vi.mock("../src/features/auth/useAuth");
vi.mock("../src/lib/api/client");

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

function setupListingMock() {
  mockApiClient.mockImplementation((endpoint: string) => {
    if (endpoint.includes("/viewing-slots")) {
      return Promise.resolve([]);
    }
    return Promise.resolve(mockListing as any);
  });
}

describe("ListingDetailPage", () => {
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

  it("renders loading state initially", () => {
    mockApiClient.mockImplementation(() => new Promise(() => {}));
    renderWithProviders(<ListingDetailPage />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders listing details when loaded", async () => {
    setupListingMock();
    renderWithProviders(<ListingDetailPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Test Property").length).toBeGreaterThan(0);
    });

    expect(screen.getByText(/\$250,000/)).toBeInTheDocument();
    expect(screen.getByText(/123 Test St/)).toBeInTheDocument();
  });

  it("renders unavailable state when listing not found", async () => {
    mockApiClient.mockRejectedValue(new Error("Not found"));
    renderWithProviders(<ListingDetailPage />);

    await waitFor(() => {
      expect(screen.getByText(/unavailable/i)).toBeInTheDocument();
    });
  });

  it("renders inquiry form", async () => {
    setupListingMock();
    renderWithProviders(<ListingDetailPage />);

    await waitFor(() => {
      const elements = screen.getAllByText(/submit inquiry/i);
      expect(elements.length).toBeGreaterThanOrEqual(1);
    });
  });

  it("shows inquiry failure feedback on error", async () => {
    mockApiClient.mockImplementation((endpoint: string) => {
      if (endpoint.includes("/inquiries")) {
        return Promise.reject(new Error("Rate limit exceeded"));
      }
      if (endpoint.includes("/viewing-slots")) {
        return Promise.resolve([]);
      }
      return Promise.resolve(mockListing as any);
    });

    renderWithProviders(<ListingDetailPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Test Property").length).toBeGreaterThan(0);
    });

    const messageTextarea = screen.getByLabelText(/message/i);
    await userEvent.type(messageTextarea, "I'm interested in this property");

    const submitButton = screen.getByRole("button", { name: /^submit inquiry$/i });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/rate limit/i)).toBeInTheDocument();
    });
  });

  it("does not render AI widget, chatbot, or match score", async () => {
    setupListingMock();
    renderWithProviders(<ListingDetailPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Test Property").length).toBeGreaterThan(0);
    });

    expect(screen.queryByText(/ai search/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/chatbot/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/match score/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/microphone/i)).not.toBeInTheDocument();
  });
});
