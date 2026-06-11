import { expect, test, type Page } from "@playwright/test";
import { ADMIN_STORAGE_STATE, SUPPORT_STORAGE_STATE } from "./auth-state";

const ADMIN_EMAIL = "agency.admin@akarai.test";

test("redirects signed-out users from protected routes", async ({ page }) => {
  await page.goto("/dashboard");

  await expect(page).toHaveURL(/\/sign-in$/);
  await expect(page.getByText("Sign in to access your agency workspace")).toBeVisible();
});

test.describe("admin session", () => {
  test.use({ storageState: ADMIN_STORAGE_STATE });

  test("restores dashboard session, reaches admin pages, and signs out", async ({ page }) => {
    await page.goto("/dashboard");

    await expect(page.getByRole("heading", { name: "Dashboard", exact: true })).toBeVisible();
    await expect(page.getByRole("link", { name: "Employees" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Listings" })).toBeVisible();

    await page.reload();
    await page.waitForLoadState("networkidle");

    await expect(page).toHaveURL(/\/dashboard$/);
    await expect(page.getByRole("heading", { name: "Dashboard", exact: true })).toBeVisible();
    await expect(page.getByRole("link", { name: "Employees" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Listings" })).toBeVisible();

    await page.goto("/spam-leads");
    await expect(page.getByRole("heading", { name: "Spam Leads" })).toBeVisible();
    await expect(page.getByText(/coming soon/i)).toBeVisible();

    await page.goto("/policy-documents");
    await expect(page.getByRole("heading", { name: "Policy Documents" })).toBeVisible();
    await expect(page.getByText(/coming soon/i)).toBeVisible();

    await page.getByRole("button", { name: ADMIN_EMAIL }).click();
    await page.getByRole("menuitem", { name: "Sign Out" }).click();

    await expect(page).toHaveURL(/\/sign-in$/);
  });
});

test.describe("support session", () => {
  test.use({ storageState: SUPPORT_STORAGE_STATE });

  test("sees restricted navigation, shared pages, and admin-route blocking", async ({ page }) => {
    await page.goto("/dashboard");

    await expect(page.getByRole("link", { name: "Active Leads" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Reviewed Leads" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Viewings" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Spam Leads" })).toBeVisible();

    await expect(page.getByRole("link", { name: "Employees" })).toHaveCount(0);
    await expect(page.getByRole("link", { name: "Listings" })).toHaveCount(0);
    await expect(page.getByRole("link", { name: "Profile" })).toHaveCount(0);
    await expect(page.getByRole("link", { name: "Policy Documents" })).toHaveCount(0);

    await page.goto("/leads");
    await expect(page.getByRole("heading", { name: "Active Leads" })).toBeVisible();

    await page.goto("/leads/reviewed");
    await expect(page.getByRole("heading", { name: "Reviewed Leads" })).toBeVisible();

    await page.goto("/viewings");
    await expect(page.getByRole("heading", { name: "Viewing Schedules" })).toBeVisible();

    await page.goto("/employees");
    await expect(page).toHaveURL(/\/dashboard$/);

    await page.goto("/profile");
    await expect(page).toHaveURL(/\/dashboard$/);

    await page.goto("/listings");
    await expect(page).toHaveURL(/\/dashboard$/);

    await page.goto("/policy-documents");
    await expect(page).toHaveURL(/\/dashboard$/);
  });
});
