import { render, screen } from "@testing-library/react";
import { renderWithProviders } from "./test-utils";
import { SpamLeadsPage } from "@/pages/placeholders/SpamLeadsPage";
import { PolicyDocumentsPage } from "@/pages/placeholders/PolicyDocumentsPage";

describe("Placeholder Routes & Navigation", () => {
  it("renders spam leads placeholder page", () => {
    renderWithProviders(<SpamLeadsPage />);
    expect(screen.getByRole("heading", { name: /spam leads/i })).toBeInTheDocument();
    expect(screen.getByText(/feature coming soon/i)).toBeInTheDocument();
  });

  it("renders policy documents placeholder page", () => {
    renderWithProviders(<PolicyDocumentsPage />);
    expect(screen.getByRole("heading", { name: /policy documents/i })).toBeInTheDocument();
    expect(screen.getByText(/feature coming soon/i)).toBeInTheDocument();
  });
});
