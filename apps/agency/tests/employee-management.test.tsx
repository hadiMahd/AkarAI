import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "./test-utils";
import { EmployeesPage } from "@/pages/employees/EmployeesPage";

describe("Employee Management", () => {
  it("renders employee page with add form", async () => {
    renderWithProviders(<EmployeesPage />);
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /employees/i })).toBeInTheDocument();
    });
  });

  it("shows employee invite form inputs", async () => {
    renderWithProviders(<EmployeesPage />);
    await waitFor(() => {
      expect(screen.getByLabelText(/work email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/display name/i)).toBeInTheDocument();
    });
  });
});
