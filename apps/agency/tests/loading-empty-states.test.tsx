import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "./test-utils";
import { LeadsPage } from "@/pages/leads/LeadsPage";
import { ViewingsPage } from "@/pages/viewings/ViewingsPage";

describe("Loading & Empty States", () => {
  it("shows empty state for active leads when no data", async () => {
    renderWithProviders(<LeadsPage />);
    await waitFor(() => {
      expect(screen.getByText(/no active leads/i)).toBeInTheDocument();
    });
  });

  it("shows empty state for viewings when no data", async () => {
    renderWithProviders(<ViewingsPage />);
    await waitFor(() => {
      expect(screen.getByText(/no viewings match/i)).toBeInTheDocument();
    });
  });
});
