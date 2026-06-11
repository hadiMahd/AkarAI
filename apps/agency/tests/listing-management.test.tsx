import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "./test-utils";
import { ListingsPage } from "@/pages/listings/ListingsPage";

describe("Listing Management", () => {
  it("renders listings page", async () => {
    renderWithProviders(<ListingsPage />);
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /listings/i })).toBeInTheDocument();
    });
  });

  it("shows create listing link", async () => {
    renderWithProviders(<ListingsPage />);
    await waitFor(() => {
      expect(screen.getByText(/create listing/i)).toBeInTheDocument();
    });
  });
});
