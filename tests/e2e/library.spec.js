const { test, expect } = require("@playwright/test");
const catalogBooks = require("../../site/data/books.json");
const catalogCategories = require("../../site/data/categories.json").categories;
const catalogRoadmap = require("../../site/data/roadmap.json");
const catalogPaths = require("../../site/data/learning-paths.json").paths;
const publishedBooks = catalogBooks.filter(book => book.status === "published");
const publishedExperimentCount = publishedBooks.reduce((count, book) => count + book.experiments.length, 0);
const bcdMatches = catalogBooks.filter(book => [
  book.title.en, book.subtitle.en, book.description.en, ...book.tags,
  ...book.chapters.flatMap(chapter => [chapter.title.en, ...chapter.topics])
].join(" ").toLowerCase().includes("bcd")).length;

test("home, featured textbook, chapter links and structure work at the /books/ base", async ({ page }, testInfo) => {
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto("./");
  await expect(page.locator("h1")).toContainText("Ideas worth exploring");
  await expect(page.locator(".hero-stats strong").nth(0)).toHaveText(String(publishedBooks.length).padStart(2, "0"));
  await expect(page.locator(".hero-stats strong").nth(1)).toHaveText(String(catalogRoadmap.books.length).padStart(2, "0"));
  await expect(page.locator(".hero-stats strong").nth(2)).toHaveText(String(publishedExperimentCount).padStart(2, "0"));
  await expect(page.locator(".featured-shelf .book-card")).toHaveCount(publishedBooks.length ? 1 : 0);
  await expect(page.locator(".featured-shelf a[href^='https://frbread7.github.io/pmicbook/']")).toHaveCount(2);
  await page.screenshot({ path: testInfo.outputPath("home.png"), fullPage: true });
  await page.goto("book.html?slug=pmicbook");
  await expect(page.locator("h1")).toHaveText("PMICBook");
  await expect(page.locator(".chapter-list li")).toHaveCount(25);
  await expect(page.locator(".mini-experiment")).toHaveCount(4);
  await expect(page.locator(".book-facts dd").nth(2)).toHaveText("English · Korean");
  await expect(page.locator(".detail-actions a").filter({ hasText: "Open the textbook" })).toHaveAttribute("href", "https://frbread7.github.io/pmicbook/");
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute("href", /\/books\/book\.html\?slug=pmicbook$/);
  await expect(page.locator('meta[property="og:title"]')).toHaveAttribute("content", "PMICBook — My Library");
  await expect(page.locator('meta[property="og:description"]')).toHaveAttribute("content", catalogBooks.find(book => book.id === "pmicbook").description.en);
  await page.screenshot({ path: testInfo.outputPath("book-detail.png"), fullPage: true });
  expect(errors).toEqual([]);
  expect(new URL(page.url()).pathname).toMatch(/^\/books\//);
  const unnamed = await page.locator("a").evaluateAll(links => links.filter(link => !link.innerText.trim() && !link.getAttribute("aria-label")).length);
  expect(unnamed).toBe(0);
  const imagesWithoutAlt = await page.locator("img").evaluateAll(images => images.filter(image => !image.hasAttribute("alt")).length);
  expect(imagesWithoutAlt).toBe(0);
  await page.goto("./");
  await page.keyboard.press("Tab");
  await expect(page.locator(".skip-link")).toBeFocused();
  expect(await page.evaluate(() => getComputedStyle(document.activeElement).outlineStyle)).toBe("solid");
});

test("search and filters work and keep unstarted roadmap ideas out of the catalog", async ({ page }) => {
  await page.goto("library.html");
  await expect(page.locator(".book-card")).toHaveCount(catalogBooks.length);
  await page.getByLabel("Search books").fill("BCD");
  await expect(page.locator(".book-card")).toHaveCount(bcdMatches);
  await page.getByLabel("Search books").fill("not-a-real-topic");
  await expect(page.locator(".empty-grid")).toBeVisible();
  await page.getByRole("button", { name: "Clear filters" }).click();
  await expect(page.locator(".book-card")).toHaveCount(catalogBooks.length);
  await page.getByLabel("Publication status").selectOption("planned");
  await expect(page.locator(".empty-grid")).toBeVisible();
});

test("subjects, paths and experiment discovery use published content only", async ({ page }) => {
  await page.goto("categories.html?id=semiconductor");
  const categoryCanonical = "http://127.0.0.1:4173/books/categories.html?id=semiconductor";
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute("href", categoryCanonical);
  await expect(page.locator('meta[property="og:url"]')).toHaveAttribute("content", categoryCanonical);
  await expect(page.locator(".knowledge-map .map-node")).toHaveCount(catalogCategories.find(category => category.id === "semiconductor").map.length);
  const plannedMemory = page.locator(".map-node").filter({ hasText: "Memory products (planned)" });
  await expect(plannedMemory).toContainText("Planned");
  await expect(plannedMemory.locator("a")).toHaveCount(0);
  await expect(page.locator(".knowledge-map a").first()).toHaveAttribute("href", /^https:\/\/frbread7\.github\.io\/pmicbook\//);
  await page.goto("paths.html");
  await expect(page.locator(".path-card")).toHaveCount(catalogPaths.length);
  expect(await page.locator(".path-step a").count()).toBeGreaterThan(8);
  await page.goto("experiments.html");
  await expect(page.locator(".experiment-card")).toHaveCount(publishedExperimentCount);
  await expect(page.locator(".experiment-card a").first()).toHaveAttribute("href", "https://frbread7.github.io/pmicbook/chapters/fundamentals.html#pm-fund-sim");
});

test("catalog expansion updates aggregate counts and registered drafts have an honest status page", async ({ page }) => {
  const pmicbook = catalogBooks.find(book => book.id === "pmicbook");
  const secondPublished = structuredClone(pmicbook);
  Object.assign(secondPublished, {
    id: "fixturebook", slug: "fixturebook", title: { en: "FixtureBook", ko: "FixtureBook" },
    subtitle: { en: "Synthetic second-book fixture", ko: "두 번째 책 테스트 픽스처" },
    description: { en: "A synthetic book used to verify catalog expansion.", ko: "카탈로그 확장 검증용 가상 도서입니다." },
    repositoryUrl: "https://github.com/example/fixturebook", productionUrl: "https://example.test/fixturebook/",
    languages: ["en"], languageUrls: { en: "https://example.test/fixturebook/" }, chapterCount: 1,
    chapters: [{ id: "intro", number: 1, title: { en: "Introduction", ko: "소개" }, urls: { en: "https://example.test/fixturebook/chapters/intro.html" }, topics: ["fixture"] }],
    experiments: [], prerequisites: [], relatedBooks: [],
    publicationEvidence: { releaseUrl: "https://github.com/example/fixturebook/releases/tag/v1.0.0", releasePublishedAt: "2026-01-01", contentReview: "Test fixture", siteVerification: "Test fixture", chapterVerification: "Test fixture" }
  });
  const draft = structuredClone(secondPublished);
  Object.assign(draft, {
    id: "futurefixture", slug: "futurefixture", title: { en: "Future Fixture", ko: "미래 픽스처" },
    status: "in-progress", chapterCount: 0, chapters: [], productionUrl: "https://example.test/futurefixture/",
    languageUrls: { en: "https://example.test/futurefixture/" }, repositoryUrl: "https://github.com/example/futurefixture"
  });
  delete draft.publicationEvidence;
  const fixture = [...catalogBooks, secondPublished, draft];
  await page.route("**/books/data/books.json", route => route.fulfill({ contentType: "application/json", body: JSON.stringify(fixture) }));
  await page.goto("./");
  const publishedCount = fixture.filter(book => book.status === "published").length;
  const experimentCount = fixture.filter(book => book.status === "published").reduce((count, book) => count + book.experiments.length, 0);
  await expect(page.locator(".hero-stats strong").nth(0)).toHaveText(String(publishedCount).padStart(2, "0"));
  await expect(page.locator(".hero-stats strong").nth(2)).toHaveText(String(experimentCount).padStart(2, "0"));
  await page.goto("library.html");
  await expect(page.locator(".book-card")).toHaveCount(fixture.length);
  await page.getByLabel("Publication status").selectOption("in-progress");
  await expect(page.locator(".book-card")).toHaveCount(fixture.filter(book => book.status === "in-progress").length);
  await page.getByRole("link", { name: "Future Fixture", exact: true }).click();
  await expect(page.locator("h1")).toHaveText("Future Fixture");
  await expect(page.locator(".unavailable-note")).toContainText("In progress");
  await expect(page.locator(".detail-actions a")).toHaveCount(0);
});

test("language and theme controls change state and persist", async ({ page }) => {
  await page.goto("./");
  await page.getByRole("button", { name: "Switch language" }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "ko");
  await expect(page.locator(".primary-nav").getByRole("link", { name: "도서관" })).toBeVisible();
  await page.goto("book.html?slug=pmicbook");
  await expect(page.locator(".book-facts dd").nth(2)).toHaveText("영어 · 한국어");
  await page.goto("feedback.html");
  await expect(page.locator("main")).toContainText("GitHub 사용자 이름은 공개");
  await page.goto("./");
  await page.getByRole("button", { name: "다크 모드로 전환" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("lang", "ko");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.getByRole("button", { name: "언어 전환" }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
});

test("search placeholder and published badge meet text contrast in both themes", async ({ page }) => {
  await page.goto("library.html");
  for (const theme of ["light", "dark"]) {
    await page.evaluate(value => {
      if (value === "dark") document.documentElement.dataset.theme = "dark";
      else document.documentElement.removeAttribute("data-theme");
    }, theme);
    const contrast = await page.evaluate(() => {
      const rgb = value => value.match(/[\d.]+/g).slice(0, 3).map(Number).map(channel => {
        channel /= 255;
        return channel <= .04045 ? channel / 12.92 : ((channel + .055) / 1.055) ** 2.4;
      });
      const ratio = (foreground, background) => {
        const luminance = value => {
          const [r, g, b] = rgb(value);
          return .2126 * r + .7152 * g + .0722 * b;
        };
        const values = [luminance(foreground), luminance(background)].sort((a, b) => b - a);
        return (values[0] + .05) / (values[1] + .05);
      };
      const input = document.querySelector("#book-search");
      const badge = document.querySelector(".badge-published");
      return {
        placeholder: ratio(getComputedStyle(input, "::placeholder").color, getComputedStyle(input).backgroundColor),
        badge: ratio(getComputedStyle(badge).color, getComputedStyle(badge).backgroundColor)
      };
    });
    expect(contrast.placeholder, `${theme} placeholder`).toBeGreaterThanOrEqual(4.5);
    expect(contrast.badge, `${theme} published badge`).toBeGreaterThanOrEqual(4.5);
  }
});

test("nested unknown routes keep their shell, scripts, styles, and navigation at the project base", async ({ page }) => {
  const failedRequests = [];
  const failedSubresources = [];
  page.on("requestfailed", request => failedRequests.push(request.url()));
  page.on("response", response => {
    if (response.status() >= 400 && !response.request().isNavigationRequest()) failedSubresources.push(response.url());
  });
  const response = await page.goto("unknown/path");
  expect(response.status()).toBe(404);
  await expect(page.locator("h1")).toHaveText("This shelf is empty");
  await expect(page.locator("base")).toHaveAttribute("href", "/books/");
  await expect(page.locator(".brand")).toHaveAttribute("href", "http://127.0.0.1:4173/books/");
  const resources = await page.evaluate(() => [...document.styleSheets].map(sheet => sheet.href).filter(Boolean));
  expect(resources).toContain("http://127.0.0.1:4173/books/css/style.css");
  expect(failedRequests).toEqual([]);
  expect(failedSubresources).toEqual([]);
});

test("all primary views fit the viewport without horizontal overflow", async ({ page }) => {
  const consoleErrors = [];
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  page.on("console", message => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("response", response => {
    if (response.status() >= 400 && !response.request().isNavigationRequest()) errors.push(`${response.url()} returned HTTP ${response.status()}`);
  });
  for (const route of ["./", "library.html", "categories.html", "roadmap.html", "paths.html", "experiments.html", "book.html?slug=pmicbook", "feedback.html", "unknown/path"]) {
    const consoleStart = consoleErrors.length;
    const response = await page.goto(route);
    if (route === "unknown/path") {
      expect(response.status()).toBe(404);
      expect(response.request().isNavigationRequest()).toBe(true);
      const knownDocument404 = "Failed to load resource: the server responded with a status of 404 (Not Found)";
      const knownErrorIndex = consoleErrors.findIndex((message, index) => index >= consoleStart && message === knownDocument404);
      if (knownErrorIndex >= 0) consoleErrors.splice(knownErrorIndex, 1);
    }
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
  expect([...errors, ...consoleErrors]).toEqual([]);
});
