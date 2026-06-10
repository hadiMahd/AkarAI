import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ProtectedRoute, PublicOnlyRoute } from "@/app/guards";
import { useAuth } from "@/features/auth/useAuth";

vi.mock("@/features/auth/useAuth", () => ({
  useAuth: vi.fn(),
}));

const mockUseAuth = vi.mocked(useAuth);

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
}

function renderWithProviders(ui: React.ReactElement, { route = "/" } = {}) {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route path="/protected" element={<div>Protected Content</div>} />
          </Route>
          <Route element={<PublicOnlyRoute />}>
            <Route path="/public" element={<div>Public Content</div>} />
          </Route>
          <Route path="/sign-in" element={<div>Sign In Page</div>} />
          <Route path="/home" element={<div>Home Page</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("ProtectedRoute", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("redirects to sign-in when user is not authenticated", () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: false,
      error: null,
      isAuthenticated: false,
      signIn: vi.fn(),
      signUp: vi.fn(),
      logout: vi.fn(),
      isSigningIn: false,
      isSigningUp: false,
      signInError: null,
      signUpError: null,
    });

    renderWithProviders(<div />, { route: "/protected" });

    expect(screen.getByText("Sign In Page")).toBeInTheDocument();
  });

  it("shows loading skeleton when auth is loading", () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: true,
      error: null,
      isAuthenticated: false,
      signIn: vi.fn(),
      signUp: vi.fn(),
      logout: vi.fn(),
      isSigningIn: false,
      isSigningUp: false,
      signInError: null,
      signUpError: null,
    });

    renderWithProviders(<div />, { route: "/protected" });

    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("renders protected content when user is authenticated", () => {
    mockUseAuth.mockReturnValue({
      user: { id: "1", email: "test@test.com", name: "Test User", is_active: true, created_at: "", updated_at: "" },
      isLoading: false,
      error: null,
      isAuthenticated: true,
      signIn: vi.fn(),
      signUp: vi.fn(),
      logout: vi.fn(),
      isSigningIn: false,
      isSigningUp: false,
      signInError: null,
      signUpError: null,
    });

    renderWithProviders(<div />, { route: "/protected" });

    expect(screen.getByText("Protected Content")).toBeInTheDocument();
  });
});

describe("PublicOnlyRoute", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("redirects to home when user is authenticated", () => {
    mockUseAuth.mockReturnValue({
      user: { id: "1", email: "test@test.com", name: "Test User", is_active: true, created_at: "", updated_at: "" },
      isLoading: false,
      error: null,
      isAuthenticated: true,
      signIn: vi.fn(),
      signUp: vi.fn(),
      logout: vi.fn(),
      isSigningIn: false,
      isSigningUp: false,
      signInError: null,
      signUpError: null,
    });

    renderWithProviders(<div />, { route: "/public" });

    expect(screen.getByText("Home Page")).toBeInTheDocument();
  });

  it("renders public content when user is not authenticated", () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: false,
      error: null,
      isAuthenticated: false,
      signIn: vi.fn(),
      signUp: vi.fn(),
      logout: vi.fn(),
      isSigningIn: false,
      isSigningUp: false,
      signInError: null,
      signUpError: null,
    });

    renderWithProviders(<div />, { route: "/public" });

    expect(screen.getByText("Public Content")).toBeInTheDocument();
  });
});
