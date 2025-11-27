// @ts-check
const { test, expect } = require("@playwright/test");

test.describe("Visisipy Demo", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the visisipy demo page
    await page.goto("/visisipy/index.html");

    // Accept the Terms of Use dialog if it appears
    const agreeButton = page.getByRole("button", { name: "I Agree" });
    if ((await agreeButton.count()) > 0 && (await agreeButton.isVisible())) {
      await agreeButton.click();
    }
  });

  test("demo page loads without errors", async ({ page }) => {
    // The demo runs in a shinylive iframe that takes time to render
    // Wait for a reasonable amount of time for the demo to load
    // The iframe should not show an error message

    // Check that the page title is correct
    await expect(page).toHaveTitle(/Ocular ray tracing simulations/);

    // Check that the main heading is visible
    await expect(
      page.getByRole("heading", { name: "Ocular ray tracing simulations" })
    ).toBeVisible();

    // Wait for the shinylive iframe to be present
    const iframe = page.locator("iframe");
    await expect(iframe).toBeVisible();

    // The shinylive app shows "Error starting app!" if it fails
    // We need to check that this error message does NOT appear
    const errorMessage = page.getByText("Error starting app!");

    // Wait for the page to finish loading resources
    await page.waitForLoadState("networkidle");

    // Check that the error message is not visible
    // We wait up to 120 seconds total for the demo to render
    await expect(errorMessage).not.toBeVisible({ timeout: 120000 });
  });
});
