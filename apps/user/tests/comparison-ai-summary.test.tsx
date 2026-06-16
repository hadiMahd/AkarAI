import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState, type ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import {
  useComparisonSummaryMutation,
  type ComparisonSummaryResponse,
} from "@/features/comparison/useComparisonSummary";

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        {ui}
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

vi.mock("@/features/comparison/useComparisonSummary", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/features/comparison/useComparisonSummary")>();
  return {
    ...actual,
    useComparisonSummaryMutation: () => ({
      mutateAsync: vi.fn(
        async (payload: { listing_ids: string[] }): Promise<ComparisonSummaryResponse> => ({
          job_id: "job-cmp-1",
          status: "completed",
          summary: "Listing A is a 2BR in Beirut, Listing B is a 1BR. Both are furnished.",
          key_differences: [
            "Listing A has 2 bedrooms, Listing B has 1",
            "Listing A is more expensive at $1500 vs $900",
          ],
          best_fit_notes: [
            "Listing A is better for families",
            "Listing B is better for single occupants",
          ],
          guardrail_status: "passed",
        }),
      ),
      isPending: false,
    }),
    useComparisonSummary: () => ({ data: null, isLoading: false }),
  };
});

function Harness() {
  const [result, setResult] = useState<ComparisonSummaryResponse | null>(null);
  const mutation = useComparisonSummaryMutation();
  return (
    <div>
      <button
        type="button"
        onClick={() =>
          mutation
            .mutateAsync({ listing_ids: ["listing-1", "listing-2"] })
            .then((r) => setResult(r))
        }
      >
        Generate summary
      </button>
      {result && (
        <div data-testid="summary-card">
          <p data-testid="summary-text">{result.summary}</p>
          <ul data-testid="differences">
            {result.key_differences.map((d, i) => (
              <li key={i}>{d}</li>
            ))}
          </ul>
          <ul data-testid="best-fit">
            {result.best_fit_notes.map((n, i) => (
              <li key={i}>{n}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

describe("user comparison AI summary", () => {
  it("renders the generated summary, differences, and best-fit notes", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Harness />);

    await user.click(screen.getByRole("button", { name: /generate summary/i }));

    await waitFor(() => {
      expect(screen.getByTestId("summary-text")).toHaveTextContent(
        /Listing A is a 2BR in Beirut/,
      );
      expect(screen.getByTestId("differences")).toHaveTextContent(/2 bedrooms/);
      expect(screen.getByTestId("best-fit")).toHaveTextContent(/better for families/);
    });
  });

  it("sends the listing ids to the mutation", async () => {
    const user = userEvent.setup();
    // Build a separate harness with a recording mutateAsync
    const mutate = vi.fn(
      async (payload: { listing_ids: string[] }): Promise<ComparisonSummaryResponse> => ({
        job_id: "job-x",
        status: "completed",
        summary: "ok",
        key_differences: [],
        best_fit_notes: [],
        guardrail_status: "passed",
      }),
    );
    function RecordingHarness() {
      return (
        <div>
          <button
            type="button"
            onClick={() => mutate({ listing_ids: ["listing-1", "listing-2"] })}
          >
            generate
          </button>
        </div>
      );
    }
    renderWithProviders(<RecordingHarness />);
    await user.click(screen.getByRole("button", { name: /generate/i }));
    expect(mutate).toHaveBeenCalledWith(
      expect.objectContaining({ listing_ids: ["listing-1", "listing-2"] }),
    );
  });
});
