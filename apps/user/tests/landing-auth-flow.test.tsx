import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { LandingPage } from "@/pages/landing/LandingPage";

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
}

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("LandingPage", () => {
  it("renders landing page with title", () => {
    renderWithProviders(<LandingPage />);
    expect(screen.getByText(/Find Your Perfect Home/i)).toBeInTheDocument();
  });

  it("shows sign in and sign up buttons for unauthenticated users", () => {
    renderWithProviders(<LandingPage />);
    const signInButtons = screen.getAllByText(/Sign In/i);
    expect(signInButtons.length).toBeGreaterThan(0);
    expect(screen.getByText(/Sign Up/i)).toBeInTheDocument();
  });

  it("shows get started button", () => {
    renderWithProviders(<LandingPage />);
    expect(screen.getByText(/Get Started/i)).toBeInTheDocument();
  });
});