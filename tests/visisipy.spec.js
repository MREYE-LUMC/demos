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

    // Wait for the shinylive iframe to be present and get its frame context
    const iframeLocator = page.locator("iframe");
    await expect(iframeLocator).toBeVisible();

    // Get the frame content - shinylive renders its content inside the iframe
    const frame = page.frameLocator("iframe");

    // The shinylive app shows "Error starting app!" if it fails to load
    // Note: The error message appears on the main page, not inside the iframe
    const errorMessage = page.getByText("Error starting app!");

    // The "Raytrace result" card header appears when the app has fully rendered successfully
    // This element appears inside the iframe
    const raytraceResultTitle = frame.getByText("Raytrace result");

    // Poll until either success or failure condition is met
    // Using 180 second timeout because shinylive apps can take a while to load dependencies
    await expect(async () => {
      const errorVisible = await errorMessage.isVisible();
      if (errorVisible) {
        throw new Error("Demo failed to load: Error starting app!");
      }

      const raytraceVisible = await raytraceResultTitle.isVisible();
      expect(raytraceVisible).toBe(true);
    }).toPass({ timeout: 180000, intervals: [1000, 2000, 5000] });

    // Final verification: error message should not be visible
    await expect(errorMessage).not.toBeVisible();

    // Verify the demo rendered successfully by checking for key UI elements inside the iframe
    await expect(frame.getByText("Central spherical equivalent")).toBeVisible();
  });
});
