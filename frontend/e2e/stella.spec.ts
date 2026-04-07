import { expect, test } from "@playwright/test";

test("critical path works across overview, analytics, chat, and reports", async ({ page }) => {
  await page.goto("/");

  await page.getByPlaceholder("Username").fill("stella");
  await page.getByPlaceholder("Password").fill("stella");
  await page.getByRole("button", { name: /enter workspace/i }).click();

  await expect(page.getByRole("heading", { name: /selected kpis, streaming insight, and trend depth/i })).toBeVisible();
  await expect(page.getByText(/health score/i)).toBeVisible();

  await page.getByRole("link", { name: /deep analytics/i }).click();
  await expect(page.getByRole("heading", { name: /metric relationships/i })).toBeVisible();

  await page.getByRole("link", { name: /chat/i }).click();
  await expect(page.getByText(/connected\. ask stella about the current data set/i)).toBeVisible();
  await page.getByPlaceholder(/why was my sleep score weak this week/i).fill("What changed this week?");
  await page.locator("form.chat-composer").evaluate((form) => {
    form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
  });
  await expect(page.locator(".bubble.user")).toContainText("What changed this week?");
  await expect(page.getByText(/stella stub response for browser validation/i)).toBeVisible();

  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("link", { name: /reports/i }).click();
  await expect(page.getByRole("heading", { name: /generate a portable health summary/i })).toBeVisible();
  await page.getByRole("button", { name: /download report/i }).click();
  const download = await downloadPromise;
  await expect(download.suggestedFilename()).toContain("stella-report");
});
