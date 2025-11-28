import { test, expect } from "@playwright/test";

function setupDemoTest(name: string, location: string, heading: string, renderingFinishedIndicator: string, successIndicators?: string[], successIndicatorTimeout: number = 30000) {
  test.describe(name, () => {
    test.beforeEach(async ({ page }) => {
      // Navigate to the demo page
      await page.goto(location);

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
      await expect(page).toHaveTitle(new RegExp(heading));

      // Check that the main heading is visible
      await expect(
        page.getByRole("heading", { name: heading })
      ).toBeVisible();

      // Wait for the shinylive iframe to be present and get its frame context
      const iframeLocator = page.locator("iframe");
      await expect(iframeLocator).toBeVisible();

      // Get the frame content - shinylive renders its content inside the iframe
      const frame = page.frameLocator("iframe");

      // The shinylive app shows "Error starting app!" if it fails to load
      // Note: The error message appears on the main page, not inside the iframe
      const errorMessage = page.getByText("Error starting app!");

      // An element that appears when the app has fully rendered successfully
      // This element appears inside the iframe
      const renderingFinished = frame.getByText(renderingFinishedIndicator);

      // Race between success and error conditions
      // This ensures we fail fast when an error occurs instead of waiting for timeout
      const result = await Promise.race([
        // Success condition: wait for the rendering finished indicator to appear
        renderingFinished
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

      if (result === "error") {
        throw new Error("Demo failed to load: Error starting app!");
      }

      await expect(async () => {
        for (const indicator of successIndicators || []) {
          // Verify the demo rendered successfully by checking for key UI elements inside the iframe
          await expect(frame.getByText(indicator)).toBeVisible();
        }
      }).toPass({ timeout: successIndicatorTimeout });
    });
  });
}

setupDemoTest(
  "PAROS Demo",
  "/paros/index.html",
  "Calculate the central magnification of an eye - camera system",
  "Eye model parameters",
  ["Magnification"]
);

setupDemoTest(
  "Visisipy Demo",
  "/visisipy/index.html",
  "Ocular ray tracing simulations",
  "Raytrace result",
  ["Central spherical equivalent"]
);
