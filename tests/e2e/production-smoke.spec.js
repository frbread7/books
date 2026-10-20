const { test, expect } = require("@playwright/test");

test.skip(!process.env.PLAYWRIGHT_BASE_URL, "Runs only against the deployed Pages site.");

test("deployed ThinFilmBook card and cover load", async ({ page }) => {
  await page.goto("library.html");

  const card = page.locator(".book-card").filter({ has: page.locator('img[src$="thinfilmbook.svg"]') });
  await expect(card).toHaveCount(1);
  await expect(card.locator(".badge-published")).toHaveCount(1);

  const cover = card.locator("img");
  await expect(cover).toHaveAttribute("alt", "ThinFilmBook cover");
  await cover.scrollIntoViewIfNeeded();
  await expect.poll(() => cover.evaluate(image => image.complete && image.naturalWidth > 0)).toBe(true);

  await card.locator("h3 a").click();
  await expect(page.getByRole("heading", { level: 1, name: "ThinFilmBook" })).toBeVisible();
  const detailCover = page.locator(".detail-cover-wrap img");
  await expect.poll(() => detailCover.evaluate(image => image.complete && image.naturalWidth > 0)).toBe(true);
});
