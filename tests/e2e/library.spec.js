const { test, expect } = require("@playwright/test");

test("home, featured textbook, chapter links and structure work at the /books/ base", async ({ page }, testInfo) => {
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto("./");
  await expect(page.locator("h1")).toContainText("Ideas worth exploring");
  await expect(page.locator(".hero-stats strong").first()).toHaveText("01");
  await expect(page.locator(".featured-shelf .book-card")).toHaveCount(1);
  await expect(page.locator(".featured-shelf a[href^='https://frbread7.github.io/pmicbook/']")).toHaveCount(2);
  await page.screenshot({ path: testInfo.outputPath("home.png"), fullPage: true });
  await page.goto("book.html?slug=pmicbook");
  await expect(page.locator("h1")).toHaveText("PMICBook");
  await expect(page.locator(".chapter-list li")).toHaveCount(25);
  await expect(page.locator(".mini-experiment")).toHaveCount(4);
  await expect(page.locator(".book-facts dd").nth(2)).toHaveText("English · Korean");
  await expect(page.locator(".detail-actions a").filter({ hasText: "Open the textbook" })).toHaveAttribute("href", "https://frbread7.github.io/pmicbook/");
  await page.screenshot({ path: testInfo.outputPath("book-detail.png"), fullPage: true });
  expect(errors).toEqual([]);
  expect(new URL(page.url()).pathname).toMatch(/^\/books\//);
  const unnamed = await page.locator("a").evaluateAll(links => links.filter(link => !link.innerText.trim() && !link.getAttribute("aria-label")).length);
  expect(unnamed).toBe(0);
});

test("search and filters work and keep unstarted roadmap ideas out of the catalog", async ({ page }) => {
  await page.goto("library.html");
  await expect(page.locator(".book-card")).toHaveCount(1);
  await page.getByLabel("Search books").fill("BCD");
  await expect(page.locator(".book-card")).toHaveCount(1);
  await page.getByLabel("Search books").fill("not-a-real-topic");
  await expect(page.locator(".empty-grid")).toBeVisible();
  await page.getByRole("button", { name: "Clear filters" }).click();
  await expect(page.locator(".book-card")).toHaveCount(1);
  await page.getByLabel("Publication status").selectOption("planned");
  await expect(page.locator(".empty-grid")).toBeVisible();
});

test("subjects, paths and experiment discovery use published content only", async ({ page }) => {
  await page.goto("categories.html?id=semiconductor");
  await expect(page.locator(".knowledge-map .map-node")).toHaveCount(7);
  await expect(page.locator(".knowledge-map a").first()).toHaveAttribute("href", /^https:\/\/frbread7\.github\.io\/pmicbook\//);
  await page.goto("paths.html");
  await expect(page.locator(".path-card")).toHaveCount(2);
  expect(await page.locator(".path-step a").count()).toBeGreaterThan(8);
  await page.goto("experiments.html");
  await expect(page.locator(".experiment-card")).toHaveCount(4);
  await expect(page.locator(".experiment-card a").first()).toHaveAttribute("href", "https://frbread7.github.io/pmicbook/chapters/fundamentals.html#pm-fund-sim");
});

test("language and theme controls change state and persist", async ({ page }) => {
  await page.goto("./");
  await page.getByRole("button", { name: "Switch language" }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "ko");
  await expect(page.locator(".primary-nav").getByRole("link", { name: "도서관" })).toBeVisible();
  await page.goto("book.html?slug=pmicbook");
  await expect(page.locator(".book-facts dd").nth(2)).toHaveText("영어 · 한국어");
  await page.goto("./");
  await page.getByRole("button", { name: "다크 모드로 전환" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("lang", "ko");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.getByRole("button", { name: "언어 전환" }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
});

test("all primary views fit the viewport without horizontal overflow", async ({ page }) => {
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  page.on("console", message => { if (message.type() === "error") errors.push(message.text()); });
  for (const route of ["./", "library.html", "categories.html", "roadmap.html", "paths.html", "experiments.html", "book.html?slug=pmicbook", "feedback.html"]) {
    await page.goto(route);
    await expect(page.locator("h1").first()).toBeVisible();
    const dimensions = await page.evaluate(() => ({ viewport: document.documentElement.clientWidth, content: document.documentElement.scrollWidth }));
    expect(dimensions.content, route + " overflowed at " + dimensions.viewport + "px").toBeLessThanOrEqual(dimensions.viewport + 1);
    const navigation = await page.locator(".primary-nav").evaluate(element => ({ visible: element.clientWidth, content: element.scrollWidth }));
    expect(navigation.content, route + " hides part of the primary navigation").toBeLessThanOrEqual(navigation.visible);
    const unnamedControls = await page.locator("button, input, select").evaluateAll(elements => elements.filter(element => {
      if (element.matches("input, select")) return element.labels.length === 0 && !element.getAttribute("aria-label");
      return !element.textContent.trim() && !element.getAttribute("aria-label");
    }).length);
    expect(unnamedControls, route + " has unnamed controls").toBe(0);
  }
  expect(errors).toEqual([]);
});
