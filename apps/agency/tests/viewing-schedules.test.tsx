import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "./test-utils";
import { ViewingsPage } from "@/pages/viewings/ViewingsPage";

describe("Viewing Schedules", () => {
  it("renders viewings page with filters", async () => {
    renderWithProviders(<ViewingsPage />);
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /viewing schedules/i })).toBeInTheDocument();
      expect(screen.getByLabelText(/status/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/listing id/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/from date/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/to date/i)).toBeInTheDocument();
    });
  });

  it("shows apply filters button", async () => {
    renderWithProviders(<ViewingsPage />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /apply filters/i })).toBeInTheDocument();
    });
  });
});
