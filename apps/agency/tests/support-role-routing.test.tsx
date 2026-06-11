import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "./test-utils";
import { ReviewedLeadsPage } from "@/pages/leads/ReviewedLeadsPage";

describe("Support Role Routing", () => {
  it("allows access to reviewed leads", async () => {
    renderWithProviders(<ReviewedLeadsPage />);
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /reviewed leads/i })).toBeInTheDocument();
    });
  });

  it("shows empty state for reviewed leads", async () => {
    renderWithProviders(<ReviewedLeadsPage />);
    await waitFor(() => {
      expect(screen.getByText(/no reviewed leads yet/i)).toBeInTheDocument();
    });
  });
});
