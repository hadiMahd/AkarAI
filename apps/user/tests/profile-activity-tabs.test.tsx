import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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

function renderWithProviders(ui: React.ReactElement, route = "/profile") {
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
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("Profile Activity Tabs", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApiClient.mockImplementation((endpoint: string) => {
      if (endpoint === "/me/profile") {
        return Promise.resolve({
          id: "user-1",
          email: "test@example.com",
          name: "Test User",
          phone: "+96170000000",
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

  it("renders profile page with tabs", async () => {
    renderWithProviders(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: /^profile$/i })).toBeInTheDocument();
    });

    expect(screen.getByRole("tab", { name: /saved listings/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /submitted inquiries/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /scheduled viewings/i })).toBeInTheDocument();
  });

  it("shows profile tab by default", async () => {
    renderWithProviders(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: /^profile$/i })).toHaveAttribute("aria-selected", "true");
    });
  });

  it("switches to inquiries tab when clicked", async () => {
    renderWithProviders(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByText(/submitted inquiries/i)).toBeInTheDocument();
    });

    const inquiriesTab = screen.getByRole("tab", { name: /submitted inquiries/i });
    await userEvent.click(inquiriesTab);

    expect(inquiriesTab).toHaveAttribute("aria-selected", "true");
  });

  it("switches to viewings tab when clicked", async () => {
    renderWithProviders(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: /scheduled viewings/i })).toBeInTheDocument();
    });

    const viewingsTab = screen.getByRole("tab", { name: /scheduled viewings/i });
    await userEvent.click(viewingsTab);

    expect(viewingsTab).toHaveAttribute("aria-selected", "true");
  });

  it("keeps profile fields out of activity tabs", async () => {
    renderWithProviders(<ProfilePage />, "/profile?tab=inquiries");

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: /submitted inquiries/i })).toHaveAttribute("aria-selected", "true");
    });

    expect(screen.queryByRole("button", { name: /save profile/i })).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/^name$/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/^phone$/i)).not.toBeInTheDocument();
  });

  it("shows profile contact form inside the profile tab", async () => {
    renderWithProviders(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /save profile/i })).toBeInTheDocument();
    });

    expect(screen.getByLabelText(/^name$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^phone$/i)).toBeInTheDocument();
  });
});
