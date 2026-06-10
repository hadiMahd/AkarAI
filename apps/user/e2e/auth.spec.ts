import { expect, test } from "@playwright/test";

function uniqueEmail() {
  return `playwright-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.com`;
}

test("redirects signed-out users from protected routes", async ({ page }) => {
  await page.goto("/home");

  await expect(page).toHaveURL(/\/sign-in$/);
  await expect(page.getByText("Sign In").first()).toBeVisible();
});

test("sign-up creates account and redirects", async ({ page }) => {
  const email = uniqueEmail();
  const password = "Playwright123!";
  const name = "Playwright User";

  await page.goto("/sign-up");
  await page.getByLabel("Full Name").fill(name);
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByLabel("Confirm Password").fill(password);
  await page.getByRole("button", { name: "Sign Up" }).click();

  await page.waitForURL(/\/home$/, { timeout: 10000 });
});

test("sign-in with valid credentials authenticates user", async ({ page }) => {
  const email = uniqueEmail();
  const password = "Playwright123!";
  const name = "Sign In Test User";

  // First sign up
  await page.goto("/sign-up");
  await page.getByLabel("Full Name").fill(name);
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByLabel("Confirm Password").fill(password);
  await page.getByRole("button", { name: "Sign Up" }).click();
  
  await page.waitForURL(/\/home$/, { timeout: 10000 });

  // Clear all storage and cookies to simulate sign-out
  await page.evaluate(() => {
    sessionStorage.clear();
    localStorage.clear();
  });
  
  // Clear cookies
  const context = page.context();
  await context.clearCookies();

  // Reload to clear React state and query cache
  await page.reload();

  // Navigate to sign-in page
  await page.goto("/sign-in");
  
  // Wait for the form to be visible
  await expect(page.getByLabel("Email")).toBeVisible({ timeout: 5000 });
  
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign In" }).click();

  await page.waitForURL(/\/home$/, { timeout: 10000 });
});

test("refresh keeps authenticated session on protected route", async ({ page }) => {
  const email = uniqueEmail();
  const password = "Playwright123!";

  await page.goto("/sign-up");
  await page.getByLabel("Full Name").fill("Refresh Session User");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByLabel("Confirm Password").fill(password);
  await page.getByRole("button", { name: "Sign Up" }).click();

  await page.waitForURL(/\/home$/, { timeout: 10000 });
  await page.reload();
  await page.waitForLoadState("networkidle");

  await expect(page).toHaveURL(/\/home$/);
  await expect(page.getByText(/welcome back/i)).toBeVisible();
});

test("sign-in with invalid credentials shows error", async ({ page }) => {
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill("nonexistent@example.com");
  await page.getByLabel("Password").fill("WrongPassword123!");
  await page.getByRole("button", { name: "Sign In" }).click();

  // Should show error message
  await expect(page.getByText(/Invalid email or password/i)).toBeVisible({ timeout: 5000 });
  
  // Should stay on sign-in page
  await expect(page).toHaveURL(/\/sign-in$/);
});

test("protected routes redirect to sign-in when not authenticated", async ({ page }) => {
  // Try to access protected routes
  await page.goto("/listings");
  await expect(page).toHaveURL(/\/sign-in$/);

  await page.goto("/profile");
  await expect(page).toHaveURL(/\/sign-in$/);

  await page.goto("/comparison");
  await expect(page).toHaveURL(/\/sign-in$/);
});
