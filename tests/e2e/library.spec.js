const { test, expect } = require("@playwright/test");
const catalogBooks = require("../../site/data/books.json");
const catalogCategories = require("../../site/data/categories.json").categories;
const catalogRoadmap = require("../../site/data/roadmap.json");
const catalogPaths = require("../../site/data/learning-paths.json").paths;
const catalogJourney = require("../../site/data/learning-journey.json");
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
  await expect(page).toHaveTitle("My Library — Interactive Engineering & Knowledge Books");
  await expect(page.locator('meta[property="og:title"]')).toHaveAttribute("content", "My Library — Interactive Engineering & Knowledge Books");
  await expect(page.locator(".hero-stats strong").nth(0)).toHaveText(String(publishedBooks.length).padStart(2, "0"));
  const plannedIdeas = [...catalogRoadmap.books, ...catalogRoadmap.mathematicsBooks, ...catalogRoadmap.familyProjects].length;
  await expect(page.locator(".hero-stats strong").nth(1)).toHaveText(String(plannedIdeas).padStart(2, "0"));
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

test("WATBook detail exposes its bilingual chapters and six verified experiments", async ({ page }) => {
  const watbook = catalogBooks.find(book => book.id === "watbook");
  expect(watbook).toBeTruthy();
  await page.goto("book.html?slug=watbook");
  await expect(page.locator("h1")).toHaveText("WATBook");
  await expect(page.locator(".chapter-list li")).toHaveCount(10);
  await expect(page.locator(".mini-experiment")).toHaveCount(6);
  await expect(page.locator(".book-facts dd").nth(0)).toHaveText(watbook.version);
  await expect(page.locator(".book-facts dd").nth(2)).toHaveText("English · Korean");
  await expect(page.locator(`.detail-actions a[href="${watbook.productionUrl}"]`)).toBeVisible();
  await expect(page.locator(`.detail-actions a[href="${watbook.languageUrls.ko}"]`)).toBeVisible();
  await expect(page.locator(`.detail-actions a[href="${watbook.repositoryUrl}"]`)).toBeVisible();
  expect(await page.locator(".chapter-list a").evaluateAll(links => links.map(link => link.href)))
    .toEqual(watbook.chapters.map(chapter => chapter.urls.en));
  expect(await page.locator(".mini-experiment").evaluateAll(links => links.map(link => link.href)))
    .toEqual(watbook.experiments.map(experiment => experiment.url));

  await page.getByRole("button", { name: "Switch language" }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "ko");
  await expect(page.locator(".book-facts dd").nth(2)).toHaveText("영어 · 한국어");
  expect(await page.locator(".chapter-list a").evaluateAll(links => links.map(link => link.href)))
    .toEqual(watbook.chapters.map(chapter => chapter.urls.ko));

  await page.goto("experiments.html");
  const watExperiments = page.locator(".experiment-card").filter({ hasText: "WATBook" });
  await expect(watExperiments).toHaveCount(6);
  expect(await watExperiments.locator("a").evaluateAll(links => links.map(link => link.href)))
    .toEqual(watbook.experiments.map(experiment => experiment.url));
});

test("ProcessIntegrationBook is published across its bilingual detail, map, path, and experiment views", async ({ page }) => {
  const integration = catalogBooks.find(book => book.id === "processintegrationbook");
  expect(integration).toBeTruthy();
  expect(integration.status).toBe("published");
  expect(integration.publicationEvidence.productionRevision).toMatch(/^[0-9a-f]{40}$/);
  expect(catalogRoadmap.books.some(book => book.id === integration.id)).toBe(false);
  expect(catalogRoadmap.books[0].id).toBe("fabcontrolbook");

  await page.goto("book.html?slug=processintegrationbook");
  await expect(page.locator("h1")).toHaveText("ProcessIntegrationBook");
  await expect(page.locator(".chapter-list li")).toHaveCount(13);
  await expect(page.locator(".mini-experiment")).toHaveCount(3);
  await expect(page.locator(".book-facts dd").nth(0)).toHaveText("1.0.0");
  await expect(page.locator(".detail-actions a[href^='https://frbread7.github.io/processintegrationbook/']")).toHaveCount(2);
  await expect(page.locator(`.detail-actions a[href="${integration.repositoryUrl}"]`)).toBeVisible();
  expect(await page.locator(".chapter-list a").evaluateAll(links => links.map(link => link.href)))
    .toEqual(integration.chapters.map(chapter => chapter.urls.en));
  expect(await page.locator(".mini-experiment").evaluateAll(links => links.map(link => link.href)))
    .toEqual(integration.experiments.map(experiment => experiment.url));

  await page.getByRole("button", { name: "Switch language" }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "ko");
  await expect(page.locator(".chapter-list li").first()).toContainText("기술 의사결정으로서의 공정 통합");
  expect(await page.locator(".chapter-list a").evaluateAll(links => links.map(link => link.href)))
    .toEqual(integration.chapters.map(chapter => chapter.urls.ko));

  await page.getByRole("button", { name: "언어 전환" }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await page.goto("categories.html?id=semiconductor");
  await expect(page.locator('.knowledge-map a[href^="https://frbread7.github.io/processintegrationbook/"]')).toHaveCount(10);
  await page.goto("paths.html");
  const integrationPath = page.locator(".path-card").filter({ has: page.getByRole("heading", { name: "Cross-module choices to measured evidence" }) });
  await expect(integrationPath.locator(".path-step")).toHaveCount(10);
  await expect(integrationPath).toContainText("ProcessIntegrationBook");
  await page.goto("experiments.html");
  const experiments = page.locator(".experiment-card").filter({ hasText: "ProcessIntegrationBook" });
  await expect(experiments).toHaveCount(3);
  expect(await experiments.locator("a").evaluateAll(links => links.map(link => link.href)))
    .toEqual(integration.experiments.map(experiment => experiment.url));
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
  await page.goto("categories.html?id=mathematics");
  await expect(page.locator(".knowledge-section")).toContainText("This subject has no published books yet.");
  await expect(page.locator(".knowledge-section .empty-state a")).toHaveAttribute("href", /learning-journey\.html\?strand=mathematics$/);
});

test("Learning Journey explores stages, strands, prerequisites, planned and concept-only states", async ({ page }) => {
  await page.goto("learning-journey.html");
  await expect(page.locator("h1")).toHaveText("A lifelong learning journey");
  await expect(page.locator("[data-stage-select]")).toHaveCount(6);
  await expect(page.locator("[data-strand-select]")).toHaveCount(11);
  await expect(page.locator(".journey-concept > h3")).toHaveText("Quantity, shape, and pattern through play");
  await expect(page.locator(".journey-material-planned")).toContainText("CuriosityBook");
  await expect(page.locator(".journey-material-planned")).toContainText("Planned book · not published");
  await expect(page.locator(".journey-concept-description")).toContainText("animal-friends story");

  const tabUntilFocused = async (locator, key = "Tab") => {
    for (let step = 0; step < 50; step += 1) {
      await page.keyboard.press(key);
      if (await locator.evaluate(element => element === document.activeElement)) return;
    }
    throw new Error(`Keyboard traversal did not reach ${await locator.getAttribute("data-stage-select") || await locator.getAttribute("data-strand-select")}`);
  };
  const englishStrand = page.locator('[data-strand-select="english-language"]');
  await tabUntilFocused(englishStrand);
  await page.keyboard.press("Enter");
  await expect(englishStrand).toBeFocused();
  await expect(englishStrand).toHaveAttribute("aria-pressed", "true");
  await expect(page).toHaveURL(/learning-journey\.html\?strand=english-language$/);
  const earlyElementary = page.locator('[data-stage-select="early-elementary"]');
  await tabUntilFocused(earlyElementary, "Shift+Tab");
  await page.keyboard.press("Space");
  await expect(earlyElementary).toBeFocused();
  await expect(earlyElementary).toHaveAttribute("aria-pressed", "true");
  await expect(page).toHaveURL(/learning-journey\.html\?strand=english-language&stage=early-elementary$/);
  await expect(page.locator("#journey-announcer")).toContainText("Now showing:");
  await expect(page.locator("#journey-announcer")).toContainText("Early elementary");
  await expect(page.locator("#journey-announcer")).toContainText("English");
  await expect(page.locator(".journey-material-concept")).toContainText("Curriculum concept · no authored book yet");
  await expect(page.locator(".journey-material-planned, .journey-material-available")).toHaveCount(0);

  await page.locator('[data-stage-select="preschool"]').click();
  await expect(page.locator('[data-stage-select="preschool"]')).toBeFocused();
  await page.locator('[data-strand-select="mathematics"]').click();
  await expect(page.locator('[data-strand-select="mathematics"]')).toBeFocused();
  await page.locator('[data-stage-select="university-advanced"]').click();
  await expect(page.locator('[data-stage-select="university-advanced"]')).toBeFocused();
  await expect(page.locator(".journey-concept > h3")).toHaveText("Calculus, linear structures, and mathematical models");
  await expect(page.locator(".journey-material-planned").filter({ hasText: "CalculusBook" })).toContainText("CalculusBook");
  await expect(page.locator(".journey-relations h4")).toHaveText("Revisits an earlier idea");
  await expect(page.locator(".journey-relations a")).toHaveAttribute("href", /learning-journey\.html\?stage=high-school&strand=mathematics$/);
  await expect(page.getByRole("navigation", { name: "Primary navigation" })).toBeVisible();
  await expect(page).toHaveURL(/learning-journey\.html\?strand=mathematics&stage=university-advanced$/);
  await page.goBack();
  await expect(page.locator(".journey-concept > h3")).toHaveText("Quantity, shape, and pattern through play");
  await page.goForward();
  await expect(page.locator(".journey-concept > h3")).toHaveText("Calculus, linear structures, and mathematical models");
  await expect(page.locator(".journey-links a").filter({ hasText: "Explore verified book reading paths" })).toHaveAttribute("href", /\/books\/paths\.html$/);

  await page.getByRole("button", { name: "Switch language" }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "ko");
  await expect(page.getByRole("button", { name: "언어 전환" })).toBeVisible();
  await expect(page.locator(".primary-nav").getByRole("link", { name: "배움 여정" })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "주요 탐색" })).toBeVisible();
  await expect(page.locator("#stage-selector-title")).toHaveText("학습 단계 선택");
  await expect(page.locator("#strand-selector-title")).toHaveText("주제 영역 선택");
  await expect(page.locator(".journey-concept > h3")).toHaveText("미적분·선형 구조와 수학적 모형");
  await expect(page.locator(".journey-material-planned").filter({ hasText: "CalculusBook" })).toContainText("계획된 교재 · 미출판");
  await expect(page.locator(".journey-sources summary")).toHaveText("출처와 이 지도의 활용 방식");
  await expect(page.locator(".journey-links a").filter({ hasText: "검증된 도서별 학습 경로 보기" })).toBeVisible();
  expect(catalogJourney.concepts).toHaveLength(66);
  await page.locator("details.journey-sources summary").click();
  await expect(page.locator(".journey-sources li")).toHaveCount(catalogJourney.references.length);
});

test("CuriosityBook picture-book ideas stay planned and enrich the Learning Journey", async ({ page }) => {
  await page.goto("learning-journey.html?stage=preschool&strand=mathematics");
  await expect(page.locator(".journey-concept-description")).toContainText("animal-friends story");
  await expect(page.locator(".journey-material-planned")).toContainText("CuriosityBook");
  await expect(page.locator(".journey-material-planned")).toContainText("Planned book · not published");

  await page.goto("learning-journey.html?stage=preschool&strand=science");
  await expect(page.locator(".journey-concept-description")).toContainText("Where Does Rain Come From?");
  await expect(page.locator(".journey-material-planned")).toContainText("CuriosityBook");

  await page.goto("learning-journey.html?stage=preschool&strand=korean-history");
  await expect(page.locator(".journey-concept-description")).toContainText("King Sejong");
  await expect(page.locator(".journey-material-planned")).toContainText("CuriosityBook");

  await page.goto("learning-journey.html?stage=preschool&strand=korean-language-literature");
  await expect(page.locator(".journey-concept-description")).toContainText("Parent Read-Aloud Mode");
  await expect(page.locator(".journey-material-planned")).toContainText("CuriosityBook");
});

test("Learning Journey keeps a stable bilingual announcement and labels depth as editorial map order", async ({ page }) => {
  await page.goto("learning-journey.html");
  const announcer = page.locator("#journey-announcer");
  await expect(announcer).toHaveAttribute("aria-live", "polite");
  await expect(announcer).toHaveAttribute("aria-atomic", "true");
  await expect(page.locator(".journey-depth")).toContainText("Map depth");
  await expect(page.locator(".journey-depth")).toContainText("not learner progress or level");
  await page.evaluate(() => { window.journeyAnnouncerBeforeUpdate = document.querySelector("#journey-announcer"); });

  await page.locator('[data-strand-select="science"]').click();
  await expect(announcer).toContainText("Now showing:");
  expect(await announcer.evaluate(element => element === window.journeyAnnouncerBeforeUpdate)).toBe(true);

  await page.getByRole("button", { name: "Switch language" }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "ko");
  await expect(page.locator(".journey-depth")).toContainText("지도 깊이");
  await expect(page.locator(".journey-depth")).toContainText("편집상 순서 · 학습 진도나 수준이 아님");
  const koreanAnnouncer = page.locator("#journey-announcer");
  await page.evaluate(() => { window.journeyAnnouncerBeforeUpdate = document.querySelector("#journey-announcer"); });
  await page.locator('[data-strand-select="korean-history"]').click();
  await expect(koreanAnnouncer).toContainText("현재 보기:");
  expect(await koreanAnnouncer.evaluate(element => element === window.journeyAnnouncerBeforeUpdate)).toBe(true);
});

test("primary navigation wraps without clipping at 320 pixels in both languages", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 820 });
  await page.goto("learning-journey.html");
  const nav = page.getByRole("navigation", { name: "Primary navigation" });
  const assertLinksFit = async (navigation) => {
    await expect(navigation.getByRole("link")).toHaveCount(6);
    for (const link of await navigation.getByRole("link").all()) await expect(link).toBeVisible();
    const geometry = await navigation.evaluate(element => {
      const bounds = element.getBoundingClientRect();
      return {
        clientWidth: element.clientWidth,
        scrollWidth: element.scrollWidth,
        left: bounds.left,
        right: bounds.right,
        links: [...element.querySelectorAll("a")].map(link => {
          const rect = link.getBoundingClientRect();
          return { left: rect.left, right: rect.right };
        })
      };
    });
    expect(geometry.scrollWidth).toBeLessThanOrEqual(geometry.clientWidth);
    for (const link of geometry.links) {
      expect(link.left).toBeGreaterThanOrEqual(geometry.left);
      expect(link.right).toBeLessThanOrEqual(geometry.right);
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(320);
  };
  await assertLinksFit(nav);

  await page.getByRole("button", { name: "Switch language" }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "ko");
  await assertLinksFit(page.getByRole("navigation", { name: "주요 탐색" }));
});

test("mathematics roadmap exposes planned textbook preparation links", async ({ page }) => {
  await page.goto("roadmap.html#idea-differentialequationsbook");
  const differentialEquations = page.locator("#idea-differentialequationsbook");
  await expect(differentialEquations.locator(".badge-planned")).toHaveText("Planned");
  await expect(differentialEquations.locator(".roadmap-prerequisite-links a")).toHaveCount(2);
  await expect(differentialEquations.locator(".roadmap-prerequisite-links a").filter({ hasText: "CalculusBook" })).toHaveAttribute("href", /roadmap\.html#idea-calculusbook$/);
  await expect(differentialEquations.locator(".roadmap-prerequisite-links a").filter({ hasText: "AlgebraBook" })).toHaveAttribute("href", /roadmap\.html#idea-algebrabook$/);
  await expect(page.locator("#roadmap-mathematics")).toContainText("Links show suggested preparation, not age gates");

  await page.goto("roadmap.html#idea-curiositybook");
  const curiosity = page.locator("#idea-curiositybook");
  await expect(curiosity.getByRole("heading", { level: 4, name: "Pilot story and experience ideas" })).toBeVisible();
  await expect(curiosity).not.toContainText("Proposed chapter groups");
  await page.getByRole("button", { name: "Switch language" }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "ko");
  await expect(page.locator("#idea-curiositybook").getByRole("heading", { level: 4, name: "파일럿 이야기와 경험 아이디어" })).toBeVisible();
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
  await expect(page.locator(".book-progress-detail")).toHaveAttribute("data-book-status", "in-progress");
  await expect(page.locator(".book-progress-detail .detail-description")).toContainText("catalog expansion");
  await expect(page.locator(".progress-repository")).toHaveAttribute("href", "https://github.com/example/futurefixture");
  await expect(page.locator(".detail-actions a")).toHaveCount(2);
  await expect(page.locator(".detail-actions a").filter({ hasText: "Open the textbook" })).toHaveCount(0);
  await expect(page.locator(`.detail-actions a[href="${draft.productionUrl}"]`)).toHaveCount(0);
  await expect(page.locator(".chapter-list, .mini-experiment")).toHaveCount(0);
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
  const missingPath = new URL(page.url()).pathname;
  await expect(page.locator(".skip-link")).toHaveAttribute("href", `${page.url()}#main`);
  await page.keyboard.press("Tab");
  await expect(page.locator(".skip-link")).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#main")).toBeFocused();
  const afterSkip = new URL(page.url());
  expect(afterSkip.pathname).toBe(missingPath);
  expect(afterSkip.hash).toBe("#main");
  expect(failedRequests).toEqual([]);
  expect(failedSubresources).toEqual([]);
});

test("404 skip link stays on the error page when catalog startup fails", async ({ page }) => {
  await page.route("**/books/data/books.json", route => route.abort());
  const response = await page.goto("unknown/startup-failure");
  expect(response.status()).toBe(404);
  await expect(page.locator("h1")).toBeVisible();
  const missingPath = new URL(page.url()).pathname;
  await expect(page.locator(".skip-link")).toHaveAttribute("href", `${page.url()}#main`);
  await page.keyboard.press("Tab");
  await expect(page.locator(".skip-link")).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#main")).toBeFocused();
  const afterSkip = new URL(page.url());
  expect(afterSkip.pathname).toBe(missingPath);
  expect(afterSkip.hash).toBe("#main");
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
  for (const route of ["./", "library.html", "categories.html", "roadmap.html", "learning-journey.html", "paths.html", "experiments.html", "book.html?slug=pmicbook", "feedback.html", "unknown/path"]) {
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
