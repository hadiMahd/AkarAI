import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ProfilePage } from "../src/pages/profile/ProfilePage";
import { useAuth } from "../src/features/auth/useAuth";

vi.mock("../src/features/auth/useAuth");

const mockUseAuth = vi.mocked(useAuth);

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
    mockUseAuth.mockReturnValue({
      user: { id: "user-1", email: "test@example.com" },
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
      expect(screen.getByRole("tab", { name: /saved listings/i })).toBeInTheDocument();
    });

    expect(screen.getByRole("tab", { name: /submitted inquiries/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /scheduled viewings/i })).toBeInTheDocument();
  });

  it("shows saved listings tab content by default", async () => {
    renderWithProviders(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByText(/you haven't saved any listings yet/i)).toBeInTheDocument();
    });
  });

  it("does not show account settings or profile edit", async () => {
    renderWithProviders(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: /saved listings/i })).toBeInTheDocument();
    });

    expect(screen.queryByText(/account settings/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/edit profile/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/profile edit/i)).not.toBeInTheDocument();
  });
});
