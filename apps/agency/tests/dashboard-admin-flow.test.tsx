import { vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "./test-utils";
import { DashboardPage } from "@/pages/dashboard/DashboardPage";

vi.mock("@/lib/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api/client")>();
  return {
    ...actual,
    restoreSession: vi.fn().mockResolvedValue(false),
    apiClient: vi.fn(async (endpoint: string) => {
      if (endpoint === "/agency/dashboard/transactions-forecast") {
        return {
          metric: "average_transactions_per_agency",
          model_name: "lightgbm",
          history_start_month: "2025-01-01",
          history_end_month: "2025-12-01",
          forecast_month: "2026-01-01",
          latest_actual_value: 12,
          forecast_value: 13.4,
          series: [
            { month: "2025-11-01", label: "Nov 2025", value: 11.2, point_type: "historical" },
            { month: "2025-12-01", label: "Dec 2025", value: 12, point_type: "historical" },
            { month: "2026-01-01", label: "Jan 2026", value: 13.4, point_type: "forecast" },
          ],
        };
      }
      if (endpoint === "/agency/dashboard/lead-processing-trends") {
        return {
          tenant_id: "tenant-1",
          summary: {
            total_leads: 20,
            spam_count: 4,
            not_spam_count: 16,
            hot_count: 6,
            normal_count: 10,
            pending_count: 2,
            reviewed_count: 12,
          },
          spam_rate: 0.2,
          hot_rate: 0.375,
          review_rate: 0.6,
          fallback_count: 1,
        };
      }
      return { total: 0, items: [], has_next: false, has_previous: false, page: 1, page_size: 1 };
    }),
  };
});

vi.mock("@/lib/session/auth-session", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/session/auth-session")>();
  return {
    ...actual,
    getSession: () => ({
      accessToken: "token",
      user: {
        id: "user-1",
        email: "admin@agency.test",
        name: "Admin",
        is_active: true,
        created_at: "",
        updated_at: "",
        role: "agency_admin",
        permissions: [],
        tenant_id: "tenant-1",
      },
    }),
    getTenantSession: () => ({
      userId: "user-1",
      tenantId: "tenant-1",
      role: "agency_admin",
      permissions: [],
      isActive: true,
    }),
  };
});

vi.mock("@/features/auth/useTenantSession", () => ({
  useTenantSession: () => ({
    session: {
      userId: "user-1",
      tenantId: "tenant-1",
      role: "agency_admin",
      permissions: [],
      isActive: true,
    },
    isLoading: false,
    error: null,
  }),
}));

describe("Agency Admin Dashboard", () => {
  it("renders dashboard title", async () => {
    renderWithProviders(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /dashboard/i })).toBeInTheDocument();
    });
  });

  it("shows summary cards section", async () => {
    renderWithProviders(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText(/overview of your agency/i)).toBeInTheDocument();
    });
  });

  it("renders the transactions forecast chart for agency admins", async () => {
    renderWithProviders(<DashboardPage />);
    expect(await screen.findByLabelText(/transactions forecast chart/i)).toBeInTheDocument();
    expect(screen.getByText(/latest actual/i)).toBeInTheDocument();
    expect(screen.getAllByText(/transactions forecast/i).length).toBeGreaterThan(0);
  });
});
