const { test, expect } = require("@playwright/test");
const books = require("../../site/data/books.json");
const family = require("../../site/data/kids-family.json");

test("redesigned home connects the featured book, chapter, collection, and subjects", async ({ page }) => {
  const featured = books.find(book => book.id === "pmicbook");
  const overview = featured.chapters.find(chapter => chapter.id === "overview");

  await page.goto("./");
  await expect(page.locator(".room-hero")).toBeVisible();
  await expect(page.locator(".room-hero h1")).toHaveText("Good ideas deserve to be opened.");
  await expect(page.locator(".room-hero-art img")).toHaveAttribute("alt", "PMICBook cover");
  await expect(page.locator(".room-book-card h3").filter({ hasText: new RegExp(`^${featured.title.en}$`) })).toHaveCount(1);
  await expect(page.locator(".room-feature .room-chapter-entry a")).toHaveAttribute("href", overview.urls.en);
  await expect(page.locator(".room-book-card")).toHaveCount(books.length);

  const subject = page.locator('.room-subject-card[data-subject="semiconductor"]');
  await expect(subject).toBeVisible();
  await expect(subject).toHaveAttribute("href", /\/books\/library\.html\?category=semiconductor$/);
  await subject.click();
  await expect(page).toHaveURL(/library\.html\?category=semiconductor$/);
  await expect(page.locator("#category-filter")).toHaveValue("semiconductor");
  await expect(page.locator(".book-card").filter({ hasText: "PMICBook" })).toBeVisible();
});

test("redesigned home keeps navigation and discovery usable at a narrow width in English and Korean", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 820 });
  await page.goto("./");

  const assertFits = async () => {
    const widths = await page.evaluate(() => ({
      viewport: document.documentElement.clientWidth,
      document: document.documentElement.scrollWidth,
      nav: document.querySelector(".primary-nav").scrollWidth,
      navClient: document.querySelector(".primary-nav").clientWidth,
      overflow: [...document.querySelectorAll("body *")].map(element => ({
        selector: `${element.tagName.toLowerCase()}${element.id ? `#${element.id}` : ""}${[...element.classList].map(name => `.${name}`).join("")}`,
        right: Math.round(element.getBoundingClientRect().right),
        width: Math.round(element.getBoundingClientRect().width)
      })).filter(element => element.right > document.documentElement.clientWidth + 1).slice(0, 8)
    }));
    expect(widths.document, JSON.stringify(widths)).toBeLessThanOrEqual(widths.viewport);
    expect(widths.nav).toBeLessThanOrEqual(widths.navClient);
    await expect(page.locator(".room-hero h1")).toBeVisible();
    await expect(page.locator(".room-subject-card").first()).toBeVisible();
  };

  await assertFits();
  await page.getByRole("button", { name: "Switch language" }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "ko");
  await expect(page.locator(".room-hero h1")).toContainText("좋은 아이디어");
  await expect(page.locator(".room-subject-card").first()).toHaveAttribute("href", /\/books\/(library|learning-journey|roadmap)\.html/);
  await assertFits();
});

test("chapter detail preserves bilingual chapter destinations and theme preference", async ({ page }) => {
  const watbook = books.find(book => book.id === "watbook");
  await page.goto("book.html?slug=watbook");
  await expect(page.locator(".chapter-list a")).toHaveCount(watbook.chapters.length);
  expect(await page.locator(".chapter-list a").evaluateAll(links => links.map(link => link.href)))
    .toEqual(watbook.chapters.map(chapter => chapter.urls.en));

  await page.getByRole("button", { name: "Switch language" }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "ko");
  expect(await page.locator(".chapter-list a").evaluateAll(links => links.map(link => link.href)))
    .toEqual(watbook.chapters.map(chapter => chapter.urls.ko));

  await page.getByRole("button", { name: "다크 모드로 전환" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.goto("library.html?q=BCD");
  await expect(page.locator("#book-search")).toHaveValue("BCD");
  await expect(page.locator(".book-card").filter({ hasText: "PMICBook" })).toBeVisible();
  await expect(page.locator("html")).toHaveAttribute("lang", "ko");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
});

test("language switching uses the URL when browser storage is unavailable", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, "localStorage", {
      configurable: true,
      get() { throw new DOMException("Storage access denied", "SecurityError"); }
    });
  });

  await page.goto("book.html?slug=watbook");
  await page.getByRole("button", { name: "Switch language" }).click();
  await expect(page).toHaveURL(/book\.html\?slug=watbook&lang=ko$/);
  await expect(page.locator("html")).toHaveAttribute("lang", "ko");
  await expect(page.locator("h1")).toHaveText("WATBook");
  await expect(page.locator(".book-facts dd").nth(2)).toHaveText("영어 · 한국어");

  await page.goto("library.html?lang=ko&category=semiconductor");
  await expect(page.locator("html")).toHaveAttribute("lang", "ko");
  await expect(page).toHaveURL(/library\.html\?lang=ko&category=semiconductor$/);
  await page.locator("#book-search").fill("PMIC");
  await expect(page).toHaveURL(/library\.html\?lang=ko&q=pmic&category=semiconductor$/);
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("lang", "ko");
  await expect(page.locator("#book-search")).toHaveValue("pmic");
});

test("family story deep links restore the selected theme, stage, and spread", async ({ page }) => {
  const theme = family.themes[0];
  const story = family.stories.find(item => item.id === theme.storyId);
  const requestedPage = 2;
  await page.goto(`kids-family.html?theme=${theme.id}&stage=middle-school&story=${story.id}&page=${requestedPage}#family-reader`);

  await expect(page.locator("#family-reader")).toBeVisible();
  await expect(page.locator("#family-reader-title")).toHaveText(story.title.en);
  await expect(page.locator(`[data-theme-select="${theme.id}"]`)).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator('[data-family-stage-select="middle-school"]')).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator(".family-page-count")).toHaveText(`Spread ${requestedPage + 1} / ${story.pages.length}`);
  await expect(page.locator(".family-story-copy")).toContainText(story.pages[requestedPage].text.en);
  await expect(page).toHaveURL(new RegExp(`theme=${theme.id}.*stage=middle-school.*story=${story.id}.*page=${requestedPage}#family-reader$`));
});
