import { render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { renderWithProviders } from "./test-utils";
import { LeadsPage } from "@/pages/leads/LeadsPage";
import { apiClient } from "@/lib/api/client";

vi.mock("@/lib/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api/client")>();
  return {
    ...actual,
    apiClient: vi.fn(),
  };
});

describe("Lead Review Flow", () => {
  const mockApiClient = vi.mocked(apiClient);

  it("renders active leads page", async () => {
    renderWithProviders(<LeadsPage />);
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /active leads/i })).toBeInTheDocument();
    });
  });

  it("shows empty state when no data", async () => {
    renderWithProviders(<LeadsPage />);
    await waitFor(() => {
      expect(screen.getByText(/no active leads/i)).toBeInTheDocument();
    });
  });

  it("shows rank skipped when a lead is classified as spam", async () => {
    mockApiClient.mockResolvedValueOnce({
      items: [
        {
          id: "lead-1",
          agency_tenant_id: "tenant-1",
          listing_id: "listing-1",
          user_id: "user-1",
          status: "new",
          processing_status: "completed",
          spam_label: "spam",
          spam_score: 0.98,
          lead_level: null,
          level_score: null,
          name: "Spam Lead",
          email: "spam@example.com",
          phone: null,
          message: "Buy now",
          source: "web",
          created_at: "2026-06-17T10:00:00Z",
          updated_at: "2026-06-17T10:00:00Z",
        },
      ],
      page: 1,
      page_size: 20,
      total: 1,
      has_next: false,
      has_previous: false,
    } as never);

    renderWithProviders(<LeadsPage />);

    await waitFor(() => {
      expect(screen.getByText("Spam")).toBeInTheDocument();
    });
    expect(screen.getByText(/rank skipped/i)).toBeInTheDocument();
  });
});
