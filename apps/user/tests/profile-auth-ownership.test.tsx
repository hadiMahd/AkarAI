import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ProfilePage } from "../src/pages/profile/ProfilePage";
import { useAuth } from "../src/features/auth/useAuth";
import { apiClient } from "../src/lib/api/client";

vi.mock("../src/features/auth/useAuth");
vi.mock("../src/lib/api/client", async () => {
  const actual: any = await vi.importActual("../src/lib/api/client");
  return { ...actual, apiClient: vi.fn() };
});

const mockUseAuth = vi.mocked(useAuth);
const mockApiClient = vi.mocked(apiClient);

function renderWithProviders(ui: React.ReactElement, { route = "/profile" } = {}) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route path="/profile" element={ui} />
          <Route path="/sign-in" element={<div>Sign In Page</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("Profile Auth and Ownership", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApiClient.mockImplementation((endpoint: string) => {
      if (endpoint === "/me/profile") {
        return Promise.resolve({
          id: "user-1",
          email: "test@example.com",
          name: "Test User",
          phone: null,
          is_complete_for_leads: true,
          missing_fields: [],
        } as any);
      }
      if (endpoint === "/me/inquiries" || endpoint === "/me/viewings") {
        return Promise.resolve({
          items: [],
          page: 1,
          page_size: 20,
          total: 0,
          has_next: false,
          has_previous: false,
        } as any);
      }
      return Promise.resolve({ items: [], page: 1, page_size: 20, total: 0, has_next: false, has_previous: false } as any);
    });
    mockUseAuth.mockReturnValue({
      user: { id: "user-1", email: "test@example.com", name: "Test User" },
      isAuthenticated: true,
      isLoading: false,
      signIn: vi.fn(),
      signUp: vi.fn(),
      signOut: vi.fn(),
    } as any);
  });

  it("shows profile page with tabs when rendered", async () => {
    renderWithProviders(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: /^profile$/i })).toBeInTheDocument();
    });

    expect(screen.getByRole("tab", { name: /saved listings/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /submitted inquiries/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /scheduled viewings/i })).toBeInTheDocument();
  });

  it("shows profile form by default", async () => {
    renderWithProviders(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /save profile/i })).toBeInTheDocument();
    });
  });

  it("respects tab deep links", async () => {
    renderWithProviders(<ProfilePage />, { route: "/profile?tab=viewings" });

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: /scheduled viewings/i })).toHaveAttribute("aria-selected", "true");
    });

    expect(screen.queryByRole("button", { name: /save profile/i })).not.toBeInTheDocument();
  });
});
