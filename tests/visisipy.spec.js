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

    // Race between success and error conditions
    // This ensures we fail fast when an error occurs instead of waiting for timeout
    const result = await Promise.race([
      // Success condition: wait for the raytrace result to appear
      raytraceResultTitle
        .waitFor({ state: "visible", timeout: 180000 })
        .then(() => "success")
        .catch(() => null), // Ignore timeout, let the other promise win
      // Error condition: wait for the error message to appear
      errorMessage
        .waitFor({ state: "visible", timeout: 180000 })
        .then(() => "error")
        .catch(() => null), // Ignore timeout, let the other promise win
    ]);

    // If neither condition was met (both timed out), fail the test
    if (result === null) {
      throw new Error(
        "Demo did not load: neither success nor error state detected within timeout"
      );
    }

    // If error was detected, fail the test immediately with a clear message
    if (result === "error") {
      throw new Error("Demo failed to load: Error starting app!");
    }

    // Verify the demo rendered successfully by checking for key UI elements inside the iframe
    await expect(frame.getByText("Central spherical equivalent")).toBeVisible();
  });
});
