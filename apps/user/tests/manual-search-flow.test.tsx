import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { HomePage } from "@/pages/home/HomePage";

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

describe("HomePage", () => {
  it("renders homepage with welcome message", () => {
    renderWithProviders(<HomePage />);
    expect(screen.getByText(/Welcome back/i)).toBeInTheDocument();
  });

  it("shows browse listings card", () => {
    renderWithProviders(<HomePage />);
    expect(screen.getByText(/Browse Listings/i)).toBeInTheDocument();
  });

  it("shows saved listings card", () => {
    renderWithProviders(<HomePage />);
    expect(screen.getByText(/Saved Listings/i)).toBeInTheDocument();
  });

  it("shows comparison card", () => {
    renderWithProviders(<HomePage />);
    expect(screen.getByText(/Compare Properties/i)).toBeInTheDocument();
  });
});