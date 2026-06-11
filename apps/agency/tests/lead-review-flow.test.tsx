import { render, screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "./test-utils";
import { LeadsPage } from "@/pages/leads/LeadsPage";

describe("Lead Review Flow", () => {
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
});
