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
    // We need to wait for the demo to fully load before checking for errors

    // Check that the page title is correct
    await expect(page).toHaveTitle(/Ocular ray tracing simulations/);

    // Check that the main heading is visible
    await expect(
      page.getByRole("heading", { name: "Ocular ray tracing simulations" })
    ).toBeVisible();

    // Wait for the shinylive iframe to be present
    const iframe = page.locator("iframe");
    await expect(iframe).toBeVisible();

    // Wait for the demo to fully load by waiting for UI elements that only appear
    // when the shinylive app has successfully rendered
    // The "Model settings" sidebar title appears when the app is loaded
    const modelSettingsTitle = page.getByText("Model settings");

    // Wait for either the demo to load successfully OR an error to appear
    // Timeout is set high because shinylive apps can take a while to load dependencies
    const errorMessage = page.getByText("Error starting app!");

    // Poll until either success or failure condition is met
    // This is more reliable than Promise.race as it checks the state at each poll
    await expect(async () => {
      const errorVisible = await errorMessage.isVisible();
      if (errorVisible) {
        throw new Error("Demo failed to load: Error starting app!");
      }

      const settingsVisible = await modelSettingsTitle.isVisible();
      expect(settingsVisible).toBe(true);
    }).toPass({ timeout: 180000, intervals: [1000, 2000, 5000] });

    // Final verification: error message should not be visible
    await expect(errorMessage).not.toBeVisible();

    // Verify the demo rendered successfully by checking for key UI elements
    await expect(page.getByText("Raytrace result")).toBeVisible();
    await expect(page.getByText("Central spherical equivalent")).toBeVisible();
  });
});
