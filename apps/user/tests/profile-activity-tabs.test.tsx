import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ProfilePage } from "../src/pages/profile/ProfilePage";
import { useAuth } from "../src/features/auth/useAuth";

vi.mock("../src/features/auth/useAuth");

const mockUseAuth = vi.mocked(useAuth);

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
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

describe("Profile Activity Tabs", () => {
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

  it("renders profile page with tabs", async () => {
    renderWithProviders(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: /saved listings/i })).toBeInTheDocument();
    });

    expect(screen.getByRole("tab", { name: /submitted inquiries/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /scheduled viewings/i })).toBeInTheDocument();
  });

  it("shows saved listings tab by default", async () => {
    renderWithProviders(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: /saved listings/i })).toBeInTheDocument();
    });

    const savedTab = screen.getByRole("tab", { name: /saved listings/i });
    expect(savedTab).toHaveAttribute("aria-selected", "true");
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
