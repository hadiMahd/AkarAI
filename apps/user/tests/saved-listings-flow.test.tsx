import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ProfilePage } from "../src/pages/profile/ProfilePage";
import { useAuth } from "../src/features/auth/useAuth";
import { apiClient } from "../src/lib/api/client";

vi.mock("../src/features/auth/useAuth");
vi.mock("../src/lib/api/client");

const mockUseAuth = vi.mocked(useAuth);
const mockApiClient = vi.mocked(apiClient);

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, staleTime: 0, gcTime: 0 },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/profile"]}>
        <Routes>
          <Route path="/profile" element={ui} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("Saved Listings Flow", () => {
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

  it("shows saved listings tab with saved items", async () => {
    const savedListing = {
      id: "saved-1",
      user_id: "user-1",
      listing_id: "listing-1",
      created_at: "2024-01-01T00:00:00Z",
      deleted_at: null,
      listing: {
        id: "listing-1",
        title: "Saved Property",
        description: "A saved property",
        property_type: "apartment",
        listing_purpose: "sale",
        price: 300000,
        currency: "USD",
        bedrooms: 3,
        bathrooms: 2,
        area_size: 120,
        area_unit: "sqm",
        furnishing: "furnished",
        location_text: "Test City",
        city: "Test City",
        country: "Test Country",
        status: "active",
        thumbnail_url: null,
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
      },
    };

    mockApiClient.mockImplementation((endpoint: string, options?: any) => {
      if (endpoint === "/me/saved-listings/with-details") {
        return Promise.resolve({
          items: [savedListing],
          page: 1,
          page_size: 100,
          total: 1,
          has_next: false,
          has_previous: false,
        });
      }
      if (endpoint === "/me/saved-listings") {
        return Promise.resolve({
          items: [{ id: "saved-1", user_id: "user-1", listing_id: "listing-1", created_at: "2024-01-01T00:00:00Z", deleted_at: null }],
          page: 1,
          page_size: 100,
          total: 1,
          has_next: false,
          has_previous: false,
        });
      }
      if (endpoint === "/auth/me") {
        return Promise.resolve({ actor: { id: "user-1", email: "test@example.com", role: "user", permissions: [], is_active: true } });
      }
      return Promise.reject(new Error("Unexpected endpoint: " + endpoint));
    });

    renderWithProviders(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: /saved listings/i })).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText("Saved Property")).toBeInTheDocument();
    });

    expect(screen.getByText(/\$300,000/)).toBeInTheDocument();
  });

  it("shows empty state when no saved listings", async () => {
    mockApiClient.mockImplementation((endpoint: string) => {
      if (endpoint === "/me/saved-listings/with-details") {
        return Promise.resolve({
          items: [],
          page: 1,
          page_size: 100,
          total: 0,
          has_next: false,
          has_previous: false,
        });
      }
      if (endpoint === "/me/saved-listings") {
        return Promise.resolve({
          items: [],
          page: 1,
          page_size: 100,
          total: 0,
          has_next: false,
          has_previous: false,
        });
      }
      if (endpoint === "/auth/me") {
        return Promise.resolve({ actor: { id: "user-1", email: "test@example.com", role: "user", permissions: [], is_active: true } });
      }
      return Promise.reject(new Error("Unexpected endpoint: " + endpoint));
    });

    renderWithProviders(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: /saved listings/i })).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText(/you haven't saved any listings yet/i)).toBeInTheDocument();
    });
  });

  it("shows loading state initially", async () => {
    mockApiClient.mockImplementation(() => new Promise(() => {}));

    renderWithProviders(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: /saved listings/i })).toBeInTheDocument();
    });

    expect(screen.getByText(/loading saved listings/i)).toBeInTheDocument();
  });
});
