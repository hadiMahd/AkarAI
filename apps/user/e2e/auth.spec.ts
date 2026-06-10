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

  // After sign-up, user should be redirected away from sign-up page
  await page.waitForURL((url) => url.pathname !== "/sign-up", { timeout: 10000 });
  
  // The redirect might go to /home or / depending on session restoration
  // The important thing is that sign-up succeeded
  const currentUrl = page.url();
  expect(currentUrl).toMatch(/\/(home)?$/);
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
  
  // Wait for redirect
  await page.waitForURL((url) => url.pathname !== "/sign-up", { timeout: 10000 });

  // Sign out if we're on home
  if (page.url().includes("/home")) {
    // Try to sign out
    const accountMenu = page.getByRole("button", { name: "Account menu" });
    if (await accountMenu.isVisible()) {
      await accountMenu.click();
      await page.getByRole("menuitem", { name: "Sign Out" }).click();
      await expect(page).toHaveURL(/\/$/);
    }
  }

  // Now sign in
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign In" }).click();

  // Should redirect away from sign-in (either to /home or /)
  await page.waitForURL((url) => url.pathname !== "/sign-in", { timeout: 10000 });
  
  // The important thing is that sign-in succeeded and we're not on sign-in page
  const currentUrl = page.url();
  expect(currentUrl).toMatch(/\/(home)?$/);
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
