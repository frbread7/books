const { test, expect } = require("@playwright/test");
const catalogBooks = require("../../site/data/books.json");
const catalogCategories = require("../../site/data/categories.json").categories;

const publishedBooks = catalogBooks.filter(book => book.status === "published");
const templateBook = publishedBooks[0];
const categoryFixture = {
  id: "shelf-fixture",
  name: { en: "Shelf Fixture Subject", ko: "책장 테스트 주제" },
  description: { en: "Synthetic subject for isolated shelf tests.", ko: "책장 테스트용 가상 주제입니다." },
  color: "#315d6d",
  map: []
};

function fixtureBook(number, status = "published") {
  const book = structuredClone(templateBook);
  const slug = `shelf-fixture-${number}`;
  const title = `Shelf Fixture ${number}`;
  Object.assign(book, {
    id: slug,
    slug,
    title: { en: title, ko: `책장 테스트 ${number}` },
    subtitle: { en: `Synthetic fixture ${number}`, ko: `가상 테스트 ${number}` },
    description: { en: `Synthetic shelf test record ${number}.`, ko: `가상 책장 테스트 항목 ${number}입니다.` },
    category: "shelf-fixture",
    status,
    tags: [`shelf-fixture-${number}`]
  });
  if (status !== "published") {
    delete book.publicationEvidence;
    delete book.productionUrl;
    delete book.repositoryUrl;
    delete book.languageUrls;
  }
  return book;
}

function catalogFixture(size, { plannedNumbers = [], allPlanned = false } = {}) {
  const baseBooks = allPlanned
    ? catalogBooks.map((book, index) => fixtureBook(index + 1, "planned"))
    : catalogBooks;
  const additions = [];
  for (let number = catalogBooks.length + 1; number <= size; number += 1) {
    additions.push(fixtureBook(number, plannedNumbers.includes(number) || allPlanned ? "planned" : "published"));
  }
  return [...baseBooks, ...additions];
}

async function installCatalogFixture(page, books) {
  await page.route("**/data/books.json", route => route.fulfill({
    contentType: "application/json",
    body: JSON.stringify(books)
  }));
  await page.route("**/data/categories.json", route => route.fulfill({
    contentType: "application/json",
    body: JSON.stringify({ categories: [...catalogCategories, categoryFixture] })
  }));
}

function bookcase(page) {
  return page.locator(".bookcase[data-bookcase]");
}

async function expectFixtureRecords(page, expectedBooks) {
  const shelf = bookcase(page);
  const items = shelf.locator(".shelf-book");
  await expect(items).toHaveCount(expectedBooks.length);
  for (const book of expectedBooks) {
    const item = items.filter({ hasText: book.title.en });
    await expect(item).toHaveCount(1);
    await expect(item.getByRole("heading", { name: book.title.en, exact: true })).toHaveCount(1);
    const detailHref = new RegExp(`book\\.html\\?slug=${book.slug}$`);
    await expect(item.locator(".shelf-book-meta h3 a")).toHaveAttribute("href", detailHref);
    const coverLink = item.locator(".shelf-book-object .cover-link");
    await expect(coverLink).toHaveAttribute("href", detailHref);
    const image = item.locator(".shelf-book-object .book-cover");
    await expect(image).toHaveAttribute("alt", `${book.title.en} cover`);
    expect(await image.evaluate(element => new URL(element.src).pathname)).toMatch(new RegExp(`/${book.cover}$`));
  }
}

async function expectBookcaseContactGeometry(shelf) {
  const track = shelf.locator(".bookcase-track");
  const geometry = await track.evaluate(element => {
    const bounds = element.getBoundingClientRect();
    const support = getComputedStyle(element, "::before");
    const lip = getComputedStyle(element, "::after");
    return {
      trackWidth: bounds.width,
      supportTop: parseFloat(support.top),
      supportHeight: parseFloat(support.height),
      supportWidth: parseFloat(support.width),
      lipTop: parseFloat(lip.top),
      lipWidth: parseFloat(lip.width),
      contactY: bounds.top + parseFloat(support.top) + 8
    };
  });
  expect(geometry.supportHeight).toBeGreaterThan(0);
  expect(Math.abs(geometry.supportWidth - geometry.trackWidth)).toBeLessThanOrEqual(1);
  expect(Math.abs(geometry.lipWidth - geometry.trackWidth)).toBeLessThanOrEqual(1);
  expect(Math.abs(geometry.lipTop - geometry.supportTop - geometry.supportHeight + 3)).toBeLessThanOrEqual(1);

  const coverBottoms = await shelf.locator(".shelf-book-object .cover-link").evaluateAll(links =>
    links.map(link => link.getBoundingClientRect().bottom)
  );
  for (const bottom of coverBottoms) {
    expect(Math.abs(bottom - geometry.contactY), "each original cover must meet the measured continuous shelf contact boundary").toBeLessThanOrEqual(3);
  }
}

async function expectFirstBookAtStart(shelf) {
  const viewport = await shelf.locator(".bookcase-viewport").boundingBox();
  const first = await shelf.locator(".shelf-book").first().boundingBox();
  const leadingInset = await shelf.locator(".bookcase-track").evaluate(track => parseFloat(getComputedStyle(track).paddingLeft));
  expect(viewport).toBeTruthy();
  expect(first).toBeTruthy();
  expect(first.x - viewport.x, "the first matching book should be back within the shelf's leading inset").toBeGreaterThanOrEqual(-1);
  expect(first.x - viewport.x, "the first matching book should be back within the shelf's leading inset").toBeLessThanOrEqual(leadingInset + 1);
  await expect(shelf.locator("[data-shelf-prev]")).toBeDisabled();
}

async function waitForShelfControls(shelf) {
  const viewport = shelf.locator(".bookcase-viewport");
  const previous = shelf.locator("[data-shelf-prev]");
  const next = shelf.locator("[data-shelf-next]");
  await expect.poll(async () => {
    const position = await viewport.evaluate(element => {
      const first = element.querySelector(".shelf-book");
      const max = Math.max(0, element.scrollWidth - element.clientWidth);
      const start = Math.min(max, first?.offsetLeft || 0);
      return {
        atStart: element.scrollLeft <= start + 1,
        atEnd: element.scrollLeft >= max - 1
      };
    });
    return (await previous.isDisabled()) === position.atStart
      && (await next.isDisabled()) === position.atEnd;
  }).toBe(true);
}

async function advanceToEnd(page) {
  const shelf = bookcase(page);
  const viewport = shelf.locator(".bookcase-viewport");
  const next = shelf.locator("[data-shelf-next]");
  const previous = shelf.locator("[data-shelf-prev]");
  await waitForShelfControls(shelf);
  const canScroll = !(await next.isDisabled());
  await expect(previous).toBeDisabled();
  for (let step = 0; step < 20 && !(await next.isDisabled()); step += 1) {
    const previousOffset = await viewport.evaluate(element => element.scrollLeft);
    await next.click();
    await expect.poll(() => viewport.evaluate(element => element.scrollLeft)).toBeGreaterThan(previousOffset);
    await waitForShelfControls(shelf);
  }
  await expect(next).toBeDisabled();
  const last = shelf.locator(".shelf-book").last();
  const viewportBox = await viewport.boundingBox();
  const lastBox = await last.boundingBox();
  expect(viewportBox).toBeTruthy();
  expect(lastBox).toBeTruthy();
  expect(lastBox.x, "the last catalog record must be reachable inside its shelf viewport").toBeGreaterThanOrEqual(viewportBox.x - 1);
  expect(lastBox.x + lastBox.width, "the final record must not remain stranded beyond the shelf viewport").toBeLessThanOrEqual(viewportBox.x + viewportBox.width + 1);
  if (canScroll) {
    await expect(previous).toBeEnabled();
    for (let step = 0; step < 20 && !(await previous.isDisabled()); step += 1) {
      const previousOffset = await viewport.evaluate(element => element.scrollLeft);
      await previous.click();
      await expect.poll(() => viewport.evaluate(element => element.scrollLeft)).toBeLessThan(previousOffset);
      await waitForShelfControls(shelf);
    }
    await expectFirstBookAtStart(shelf);
    await expect(next).toBeEnabled();
  }
}

for (const size of [5, 6, 11]) {
  test(`home and Library keep all ${size}-record fixture books reachable on physical shelves`, async ({ page }, testInfo) => {
    const books = catalogFixture(size);
    await installCatalogFixture(page, books);
    await page.emulateMedia({ reducedMotion: "reduce" });

    await page.goto("./");
    const published = books.filter(book => book.status === "published");
    await expectFixtureRecords(page, published);
    await expectBookcaseContactGeometry(bookcase(page));
    await expect(bookcase(page).locator(".shelf-book .badge-published")).toHaveCount(published.length);
    await expect(bookcase(page).locator(".bookcase-viewport")).toHaveAttribute("tabindex", "0");
    if (testInfo.project.name === "mobile") await expectMobilePreview(page);
    await advanceToEnd(page);

    await page.goto("library.html");
    await expectFixtureRecords(page, books);
    await expectBookcaseContactGeometry(bookcase(page));
    await expect(page.locator("#result-count")).toContainText(String(books.length));
    if (testInfo.project.name === "mobile") await expectMobilePreview(page);
    await advanceToEnd(page);
  });
}

async function expectMobilePreview(page) {
  const shelf = bookcase(page);
  const viewport = shelf.locator(".bookcase-viewport");
  await expect(shelf.locator(".bookcase-hint")).toBeVisible();
  await expect(shelf.locator(".bookcase-hint")).not.toBeEmpty();
  expect(await page.evaluate(() => navigator.maxTouchPoints), "the mobile project should provide a touch-capable browsing context").toBeGreaterThan(0);
  const visibleCovers = await shelf.locator(".shelf-book-object").evaluateAll((objects, viewportElement) => {
    const bounds = viewportElement.getBoundingClientRect();
    return objects.filter(object => {
      const box = object.getBoundingClientRect();
      return box.left >= bounds.left - 1 && box.right <= bounds.right + 1;
    }).length;
  }, await viewport.elementHandle());
  expect(visibleCovers, "a narrow shelf should present about two complete covers at once").toBeGreaterThanOrEqual(2);
}

test("Library shelf resets to the first matching item and updates controls for filters and empty results", async ({ page }) => {
  const books = catalogFixture(11, { plannedNumbers: [6, 11] });
  await installCatalogFixture(page, books);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("library.html");

  const shelf = bookcase(page);
  const viewport = shelf.locator(".bookcase-viewport");
  const previous = shelf.locator("[data-shelf-prev]");
  const next = shelf.locator("[data-shelf-next]");
  await advanceToEnd(page);

  await page.locator("#category-filter").selectOption("shelf-fixture");
  const subjectBooks = books.filter(book => book.category === "shelf-fixture");
  await expectFixtureRecords(page, subjectBooks);
  await expectFirstBookAtStart(shelf);
  await advanceToEnd(page);

  await page.locator("#status-filter").selectOption("planned");
  const plannedBooks = subjectBooks.filter(book => book.status === "planned");
  await expectFixtureRecords(page, plannedBooks);
  await expectFirstBookAtStart(shelf);
  await expect(next).toBeDisabled();

  await page.locator("#book-search").fill("Shelf Fixture 11");
  await expectFixtureRecords(page, plannedBooks.filter(book => book.slug === "shelf-fixture-11"));
  await expectBookcaseContactGeometry(shelf);
  await expect(previous).toBeDisabled();
  await expect(next).toBeDisabled();

  await page.locator("#book-search").fill("no-such-shelf-book");
  await expect(shelf.locator(".shelf-book")).toHaveCount(0);
  await expect(page.locator(".empty-state.empty-grid")).toBeVisible();
  await expect(previous).toBeDisabled();
  await expect(next).toBeDisabled();

  await page.locator('[data-action="clear-filters"]').click();
  await expectFixtureRecords(page, books);
  await expectFirstBookAtStart(shelf);
});

test("home shelf keeps planned-only catalog records off the published shelf", async ({ page }) => {
  const books = catalogFixture(5, { allPlanned: true });
  await installCatalogFixture(page, books);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("./");

  const shelf = bookcase(page);
  await expect(shelf.locator(".shelf-book")).toHaveCount(0);
  await expect(shelf.locator("[data-shelf-prev]")).toBeDisabled();
  await expect(shelf.locator("[data-shelf-next]")).toBeDisabled();

  await page.goto("library.html");
  await expectFixtureRecords(page, books);
  await expect(shelf.locator(".badge-planned")).toHaveCount(books.length);
});

test("bookcase controls have accessible labels, keyboard focus, and honor reduced motion", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  const books = catalogFixture(11);
  await installCatalogFixture(page, books);
  await page.goto("library.html");

  const shelf = bookcase(page);
  const viewport = shelf.locator(".bookcase-viewport");
  const previous = shelf.locator("[data-shelf-prev]");
  const next = shelf.locator("[data-shelf-next]");
  await expect(viewport).toHaveAttribute("aria-label", /.+/);
  for (const control of [previous, next]) {
    await expect(control).toHaveAttribute("aria-label", /.+/);
    await expect(control).toHaveAttribute("aria-controls", /.+/);
  }
  await expect(viewport).toHaveAttribute("role", "region");
  await expect(viewport).toHaveAttribute("tabindex", "0");
  await expect(viewport).toHaveCSS("scroll-behavior", "auto");

  await next.focus();
  await expect(next).toBeFocused();
  await page.keyboard.press("Enter");
  await expect.poll(() => viewport.evaluate(element => element.scrollLeft)).toBeGreaterThan(0);
  await expect(previous).toBeEnabled();

  const initialTheme = await page.locator("html").getAttribute("data-theme");
  await page.locator(".theme-button").click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", initialTheme === "dark" ? "light" : "dark");
  await expectBookcaseContactGeometry(shelf);

  await page.getByRole("button", { name: "Switch language" }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "ko");
  await expect(shelf.locator(".shelf-book")).toHaveCount(books.length);
  await expect(shelf.locator(".shelf-book h3").first()).toHaveText(books[0].title.ko);
  await expect(shelf.locator("[data-shelf-next]")).toHaveAttribute("aria-label", /.+/);
  await expectBookcaseContactGeometry(shelf);
});
