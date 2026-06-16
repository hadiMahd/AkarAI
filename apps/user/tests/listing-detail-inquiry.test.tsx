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
    const { ApiError } = await import("@/lib/api/client");
    mockApiClient.mockRejectedValue(new ApiError("API request failed: Not Found", 404, { detail: "Listing not found", error_code: "NOT_FOUND" }));
    renderWithProviders(<ListingDetailPage />);

    await waitFor(() => {
      expect(screen.getByText(/no longer available/i)).toBeInTheDocument();
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
    const { ApiError } = await import("@/lib/api/client");
    mockApiClient.mockImplementation((endpoint: string) => {
      if (endpoint.includes("/inquiries")) {
        return Promise.reject(
          new ApiError("API request failed: Too Many Requests", 429, {
            detail: "Too many inquiries. Please try again later.",
            error_code: "RATE_LIMIT_EXCEEDED",
          }),
        );
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
      expect(screen.getByText(/lot of inquiries/i)).toBeInTheDocument();
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

  describe("media rendering", () => {
    it("renders images from media endpoint when items are returned", async () => {
      const mockListingWithThumbnail = {
        ...mockListing,
        thumbnail_url: null,
      };
      const mockMediaItems = [
        {
          id: "media-1",
          listing_id: "test-listing-id",
          caption: "Living room",
          alt_text: null,
          display_order: 1,
          width: 800,
          height: 600,
          media_url: "http://example.com/photo1.jpg",
          format: "webp",
          status: "accepted",
        },
        {
          id: "media-2",
          listing_id: "test-listing-id",
          caption: "Kitchen",
          alt_text: null,
          display_order: 2,
          width: 800,
          height: 600,
          media_url: "http://example.com/photo2.jpg",
          format: "webp",
          status: "accepted",
        },
      ];

      mockApiClient.mockImplementation((endpoint: string) => {
        if (endpoint.includes("/media")) {
          return Promise.resolve(mockMediaItems);
        }
        if (endpoint.includes("/viewing-slots")) {
          return Promise.resolve([]);
        }
        return Promise.resolve(mockListingWithThumbnail as any);
      });

      renderWithProviders(<ListingDetailPage />);

      await waitFor(() => {
        expect(screen.getAllByText("Test Property").length).toBeGreaterThan(0);
      });

      expect(screen.getByText(/photos/i)).toBeInTheDocument();
      const images = screen.getAllByRole("img");
      expect(images.length).toBeGreaterThanOrEqual(2);
      expect(images[0]).toHaveAttribute("src", "http://example.com/photo1.jpg");
    });

    it("renders thumbnail when media endpoint returns empty", async () => {
      const mockListingWithThumbnail = {
        ...mockListing,
        thumbnail_url: "http://example.com/thumb.jpg",
      };

      let mediaCallCount = 0;
      mockApiClient.mockImplementation((endpoint: string) => {
        if (endpoint.includes("/media")) {
          mediaCallCount++;
          return Promise.resolve([]);
        }
        if (endpoint.includes("/viewing-slots")) {
          return Promise.resolve([]);
        }
        return Promise.resolve(mockListingWithThumbnail as any);
      });

      renderWithProviders(<ListingDetailPage />);

      await waitFor(() => {
        expect(screen.getAllByText("Test Property").length).toBeGreaterThan(0);
      });

      expect(mediaCallCount).toBeGreaterThanOrEqual(1);
      const images = screen.getAllByRole("img");
      expect(images.length).toBeGreaterThanOrEqual(1);
      expect(images[0]).toHaveAttribute("src", "http://example.com/thumb.jpg");
    });

    it("renders placeholder when both media and thumbnail are absent", async () => {
      const mockListingNoImage = {
        ...mockListing,
        thumbnail_url: null,
      };

      mockApiClient.mockImplementation((endpoint: string) => {
        if (endpoint.includes("/media")) {
          return Promise.resolve([]);
        }
        if (endpoint.includes("/viewing-slots")) {
          return Promise.resolve([]);
        }
        return Promise.resolve(mockListingNoImage as any);
      });

      renderWithProviders(<ListingDetailPage />);

      await waitFor(() => {
        expect(screen.getAllByText("Test Property").length).toBeGreaterThan(0);
      });

      expect(screen.getByText(/no images available/i)).toBeInTheDocument();
    });

    it("shows error state when media endpoint fails", async () => {
      const { ApiError } = await import("@/lib/api/client");
      const mockListingNoImage = {
        ...mockListing,
        thumbnail_url: null,
      };

      mockApiClient.mockImplementation((endpoint: string) => {
        if (endpoint.includes("/media")) {
          return Promise.reject(
            new ApiError("API request failed: Internal Server Error", 500, { detail: "boom" }),
          );
        }
        if (endpoint.includes("/viewing-slots")) {
          return Promise.resolve([]);
        }
        return Promise.resolve(mockListingNoImage as any);
      });

      renderWithProviders(<ListingDetailPage />);

      await waitFor(() => {
        expect(screen.getAllByText("Test Property").length).toBeGreaterThan(0);
      });

      expect(screen.getByText(/couldn't load the photos/i)).toBeInTheDocument();
    });
  });
});
