import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "./test-utils";
import { SignInPage } from "@/pages/auth/SignInPage";

describe("Agency App Providers & Session Restore", () => {
  it("renders sign-in page without loading state after session restore", async () => {
    renderWithProviders(<SignInPage />);
    await waitFor(() => {
      expect(screen.getByText(/agency dashboard/i)).toBeInTheDocument();
    });
    expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
  });
});
