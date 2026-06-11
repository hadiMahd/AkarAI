import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "./test-utils";
import { SignInPage } from "@/pages/auth/SignInPage";

describe("Agency Auth Routing", () => {
  it("renders sign-in page when unauthenticated", async () => {
    renderWithProviders(<SignInPage />);
    await waitFor(() => {
      expect(screen.getByText(/agency dashboard/i)).toBeInTheDocument();
    });
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });
});
