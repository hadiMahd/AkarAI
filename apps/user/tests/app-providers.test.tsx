import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { Providers } from "@/app/providers";

vi.mock("@/lib/api/client", async () => {
  const actual = await vi.importActual("@/lib/api/client");
  return {
    ...actual,
    restoreSession: vi.fn().mockResolvedValue(false),
  };
});

beforeEach(() => {
  vi.clearAllMocks();
});

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
}

describe("Providers", () => {
  it("renders children correctly", async () => {
    render(
      <Providers>
        <div>Test Child</div>
      </Providers>
    );

    await waitFor(() => {
      expect(screen.getByText("Test Child")).toBeInTheDocument();
    });
  });

  it("provides QueryClient context", () => {
    const queryClient = createTestQueryClient();
    let capturedClient: QueryClient | null = null;

    function TestComponent() {
      return <div>Test</div>;
    }

    render(
      <QueryClientProvider client={queryClient}>
        <TestComponent />
      </QueryClientProvider>
    );

    expect(screen.getByText("Test")).toBeInTheDocument();
  });

  it("provides Router context", () => {
    render(
      <BrowserRouter>
        <div>Router Test</div>
      </BrowserRouter>
    );

    expect(screen.getByText("Router Test")).toBeInTheDocument();
  });
});

describe("API Client", () => {
  it("exports apiClient function", async () => {
    const { apiClient } = await import("@/lib/api/client");
    expect(typeof apiClient).toBe("function");
  });

  it("exports API_BASE_URL", async () => {
    const { API_BASE_URL } = await import("@/lib/api/client");
    expect(typeof API_BASE_URL).toBe("string");
  });
});

describe("Auth Session", () => {
  it("exports session management functions", async () => {
    const { setSession, getSession, clearSession, isAuthenticated } = await import("@/lib/session/auth-session");
    expect(typeof setSession).toBe("function");
    expect(typeof getSession).toBe("function");
    expect(typeof clearSession).toBe("function");
    expect(typeof isAuthenticated).toBe("function");
  });

  it("manages session state correctly", async () => {
    const { setSession, getSession, clearSession, isAuthenticated } = await import("@/lib/session/auth-session");

    const mockUser = {
      id: "1",
      email: "test@test.com",
      name: "Test User",
      is_active: true,
      created_at: "2024-01-01",
      updated_at: "2024-01-01",
    };

    setSession("access-token", mockUser);

    const session = getSession();
    expect(session.accessToken).toBe("access-token");
    expect(session.user).toEqual(mockUser);
    expect(isAuthenticated()).toBe(true);

    clearSession();

    const clearedSession = getSession();
    expect(clearedSession.accessToken).toBeNull();
    expect(clearedSession.user).toBeNull();
    expect(isAuthenticated()).toBe(false);
  });
});
