const { test, expect } = require("@playwright/test");
const collectViewportMetrics = require("../viewport-metrics");
const { fixtureCatalog } = require("../visual-catalog-fixtures");

const detailSlugs = ["pmicbook", "watbook", "fabcontrolbook", "processintegrationbook", "thinfilmbook"];

function contrastRatio(first, second) {
  const luminance = color => {
    const normalized = color.startsWith("color(srgb");
    const channels = color.match(/[\d.]+/g).slice(0, 3).map(Number).map(value => {
      const channel = normalized ? value : value / 255;
      return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
    });
    return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
  };
  const values = [luminance(first), luminance(second)].sort((a, b) => b - a);
  return (values[0] + 0.05) / (values[1] + 0.05);
}

test("detail covers decode uncropped and leave the full title visible across responsive widths", async ({ page }) => {
  for (const width of [320, 360, 390, 600, 768, 1024, 1440, 1920]) {
    await page.setViewportSize({ width, height: 1000 });
    for (const slug of detailSlugs) for (const lang of ["en", "ko"]) {
      await page.goto(`book.html?slug=${slug}&lang=${lang}`);
      const cover = page.locator(".detail-cover");
      const title = page.locator(".book-detail-hero h1");
      await expect.poll(() => cover.evaluate(image => image.complete && image.naturalWidth > 0)).toBe(true);
      await expect(cover).toHaveCSS("object-fit", "contain");
      await expect(title).toBeVisible();
      await title.scrollIntoViewIfNeeded();
      const geometry = await page.evaluate(() => {
        const image = document.querySelector(".detail-cover");
        const heading = document.querySelector(".book-detail-hero h1");
        const imageBox = image.getBoundingClientRect();
        const titleBox = heading.getBoundingClientRect();
        const wordRects = [];
        const walker = document.createTreeWalker(heading, NodeFilter.SHOW_TEXT);
        while (walker.nextNode()) {
          const text = walker.currentNode;
          for (const match of text.textContent.matchAll(/\S+/g)) {
            const range = document.createRange();
            range.setStart(text, match.index);
            range.setEnd(text, match.index + match[0].length);
            const rects = [...range.getClientRects()];
            wordRects.push({ count: rects.length, left: Math.min(...rects.map(rect => rect.left)), right: Math.max(...rects.map(rect => rect.right)) });
          }
        }
        return { imageBottom: imageBox.bottom, imageRight: imageBox.right, titleLeft: titleBox.left, titleTop: titleBox.top, titleRight: titleBox.right, titleHeight: titleBox.height, wordRects };
      });
      const viewport = await page.evaluate(collectViewportMetrics);
      expect(geometry.titleHeight).toBeGreaterThan(0);
      if (width <= 600) expect(geometry.titleTop).toBeGreaterThanOrEqual(geometry.imageBottom - 1);
      else expect(geometry.titleLeft).toBeGreaterThanOrEqual(geometry.imageRight - 1);
      expect(geometry.titleRight).toBeLessThanOrEqual(viewport.layoutWidth);
      expect(geometry.wordRects.length).toBeGreaterThan(0);
      expect(geometry.wordRects.every(rect => rect.count === 1 && rect.left >= 0 && rect.right <= viewport.layoutWidth)).toBe(true);
      expect(viewport.layoutWidth).toBeLessThanOrEqual(width);
      expect(viewport.documentWidth).toBeLessThanOrEqual(viewport.layoutWidth);
    }
  }
});

test("195 CSS px at DPR 2 checks the narrow-width zoom proxy for detail title and panels", async ({ browser }) => {
  const context = await browser.newContext({ viewport: { width: 195, height: 960 }, deviceScaleFactor: 2 });
  const zoomPage = await context.newPage();
  const baseURL = process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:4173/books/";
  await zoomPage.goto(new URL("book.html?slug=processintegrationbook", baseURL).href);
  const heading = zoomPage.getByRole("heading", { level: 1, name: "ProcessIntegrationBook" });
  await expect(heading).toBeVisible();
  const result = await zoomPage.evaluate(() => ({
    dpr: devicePixelRatio,
    text: document.querySelector(".book-detail-hero h1").textContent,
    breakpoints: [...document.querySelectorAll(".book-detail-hero h1 wbr")].length,
    panels: [...document.querySelectorAll(".detail-panel")].map(panel => {
      const bounds = panel.getBoundingClientRect();
      return { left: bounds.left, right: bounds.right };
    })
  }));
  const viewport = await zoomPage.evaluate(collectViewportMetrics);
  expect(result.dpr).toBe(2);
  expect(result.text).toBe("ProcessIntegrationBook");
  expect(result.breakpoints).toBe(2);
  expect(viewport.layoutWidth).toBeLessThanOrEqual(195);
  expect(viewport.documentWidth).toBeLessThanOrEqual(viewport.layoutWidth);
  expect(result.panels.every(panel => panel.left >= 0 && panel.right <= viewport.layoutWidth)).toBe(true);
  await context.close();
});

test("home and library heroes and shelf covers decode without cropping or page overflow", async ({ page }) => {
  for (const width of [320, 360, 390, 768, 1024, 1440, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    for (const route of ["", "library.html"]) {
      await page.goto(route);
      const images = page.locator(route ? ".shelf-book .book-cover" : ".room-hero-cover, .shelf-book .book-cover");
      for (const image of await images.all()) {
        await image.scrollIntoViewIfNeeded();
        await expect.poll(() => image.evaluate(element => element.complete && element.naturalWidth > 0)).toBe(true);
        await expect(image).toHaveCSS("object-fit", "contain");
        const box = await image.boundingBox();
        expect(box.width).toBeGreaterThan(0);
        expect(box.height).toBeGreaterThan(0);
        expect(box.x + box.width).toBeLessThanOrEqual(width + 1);
      }
      const viewport = await page.evaluate(collectViewportMetrics);
      expect(viewport.layoutWidth).toBeLessThanOrEqual(width);
      expect(viewport.documentWidth).toBeLessThanOrEqual(viewport.layoutWidth);
    }
  }
});

test("topic chips remain readable and visibly bounded in English and Korean, light and dark", async ({ page }) => {
  test.setTimeout(180000);
  for (const width of [320, 360, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    for (const slug of detailSlugs) {
      for (const lang of ["en", "ko"]) {
        for (const theme of ["light", "dark"]) {
          await page.goto(`book.html?slug=${slug}&lang=${lang}`);
          const chips = page.locator(".tag-row-large .tag");
          await expect(chips.first()).toBeVisible();
          await page.evaluate(value => { document.documentElement.dataset.theme = value; }, theme);
          for (const chip of await chips.all()) {
            const style = await chip.evaluate(element => {
              const own = getComputedStyle(element);
              const parent = getComputedStyle(element.parentElement);
              let parentFill = parent.backgroundColor;
              for (let node = element.parentElement; node && getComputedStyle(node).backgroundColor === "rgba(0, 0, 0, 0)"; node = node.parentElement) parentFill = getComputedStyle(node.parentElement || document.body).backgroundColor;
              return { fontSize: parseFloat(own.fontSize), color: own.color, fill: own.backgroundColor, borderColor: own.borderTopColor, parentFill };
            });
            expect(style.fontSize).toBeGreaterThanOrEqual(12);
            expect(contrastRatio(style.color, style.fill)).toBeGreaterThanOrEqual(4.5);
            expect(contrastRatio(style.fill, style.parentFill)).toBeGreaterThanOrEqual(1.25);
            expect(contrastRatio(style.borderColor, style.parentFill)).toBeGreaterThanOrEqual(1.4);
          }
        }
      }
    }
  }
  for (const width of [320, 360, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    for (const lang of ["en", "ko"]) {
      for (const theme of ["light", "dark"]) {
        await page.goto(`roadmap.html?lang=${lang}`);
        const chips = page.locator(".roadmap-card .tag");
        await expect(chips.first()).toBeVisible();
        await page.evaluate(value => { document.documentElement.dataset.theme = value; }, theme);
        for (const chip of await chips.all()) {
          const style = await chip.evaluate(element => {
            const own = getComputedStyle(element);
            let parent = getComputedStyle(element.parentElement).backgroundColor;
            for (let node = element.parentElement; node && getComputedStyle(node).backgroundColor === "rgba(0, 0, 0, 0)"; node = node.parentElement) parent = getComputedStyle(node.parentElement || document.body).backgroundColor;
            return { size: parseFloat(own.fontSize), color: own.color, fill: own.backgroundColor, border: own.borderTopColor, parent };
          });
          expect(style.size).toBeGreaterThanOrEqual(12);
          expect(contrastRatio(style.color, style.fill)).toBeGreaterThanOrEqual(4.5);
          expect(contrastRatio(style.fill, style.parent)).toBeGreaterThanOrEqual(1.25);
          expect(contrastRatio(style.border, style.parent)).toBeGreaterThanOrEqual(1.4);
        }
      }
    }
  }
});

test("roadmap links and priority labels stay readable and tappable in both themes and languages", async ({ page }) => {
  test.setTimeout(180000);
  for (const width of [320, 360, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    for (const lang of ["en", "ko"]) for (const theme of ["light", "dark"]) {
      await page.goto(`roadmap.html?lang=${lang}`);
      await expect(page.locator(".roadmap-card").first()).toBeVisible();
      await page.evaluate(value => { document.documentElement.dataset.theme = value; }, theme);
      const reliability = page.locator(".roadmap-card h3").filter({ hasText: "ReliabilityEngineeringBook" });
      await expect(reliability).toHaveText("ReliabilityEngineeringBook");
      await expect(reliability.locator("wbr")).toHaveCount(2);
      const styles = await page.evaluate(() => {
        const contrastRatio = (first, second) => {
          const luminance = color => {
            const normalized = color.startsWith("color(srgb");
            return color.match(/[\d.]+/g).slice(0, 3).map(Number).map(value => {
              const channel = normalized ? value : value / 255;
              return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
            }).reduce((sum, channel, index) => sum + channel * [0.2126, 0.7152, 0.0722][index], 0);
          };
          const values = [luminance(first), luminance(second)].sort((a, b) => b - a);
          return (values[0] + 0.05) / (values[1] + 0.05);
        };
        const links = [...document.querySelectorAll(".roadmap-prerequisite-links a")].map(link => {
          const bounds = link.getBoundingClientRect();
          const color = getComputedStyle(link).color;
          const surface = getComputedStyle(link.closest(".roadmap-card")).backgroundColor;
          return { width: bounds.width, height: bounds.height, center: bounds.top + bounds.height / 2, contrast: contrastRatio(color, surface) };
        });
        const priority = [...document.querySelectorAll(".roadmap-priority span")].map(label => ({
          color: getComputedStyle(label).color,
          surface: getComputedStyle(label.closest(".roadmap-card")).backgroundColor
        }));
        return { links, priority };
      });
      expect(styles.links.length).toBeGreaterThan(0);
      expect(styles.links.every(link => link.width >= 24 && link.height >= 24 && link.contrast >= 4.5)).toBe(true);
      const centers = styles.links.map(link => link.center).sort((a, b) => a - b);
      for (let index = 1; index < centers.length; index += 1) expect(centers[index] - centers[index - 1]).toBeGreaterThanOrEqual(24);
      expect(styles.priority.every(label => contrastRatio(label.color, label.surface) >= 4.5)).toBe(true);
    }
  }
});

test("195px viewport reflows learning journey stages without clipping", async ({ page }) => {
  await page.setViewportSize({ width: 195, height: 960 });
  await page.goto("learning-journey.html");
  const stages = page.locator(".journey-stage-list .journey-stage");
  await expect(stages).toHaveCount(6);
  const geometry = await page.evaluate(() => ({
    stages: [...document.querySelectorAll(".journey-stage-list .journey-stage")].map(stage => {
      const bounds = stage.getBoundingClientRect();
      return { left: bounds.left, right: bounds.right, top: bounds.top };
    })
  }));
  const viewport = await page.evaluate(collectViewportMetrics);
  expect(viewport.layoutWidth).toBeLessThanOrEqual(195);
  expect(viewport.documentWidth).toBeLessThanOrEqual(viewport.layoutWidth);
  expect(geometry.stages.every(stage => stage.left >= 0 && stage.right <= viewport.layoutWidth)).toBe(true);
  await page.screenshot({ path: "/tmp/books-quality-journey-195.png", fullPage: true });
});

test("synthetic catalogs through 50 books keep shelf titles and detail actions reachable", async ({ page }) => {
  test.setTimeout(90000);
  await page.setViewportSize({ width: 390, height: 844 });
  let finalRecords;
  for (const count of [5, 10, 25, 50]) {
    const records = fixtureCatalog(count);
    finalRecords = records;
    await page.route("**/data/books.json", route => route.fulfill({ contentType: "application/json", body: JSON.stringify(records) }));
    await page.goto("library.html?lang=en");
    const items = page.locator(".bookcase .shelf-book");
    await expect(items).toHaveCount(count);
    for (const lang of ["en", "ko"]) {
      if (lang === "ko") await page.goto("library.html?lang=ko");
      await expect(items).toHaveCount(count);
      const visibility = await page.evaluate(() => {
        const viewport = document.querySelector(".bookcase-viewport");
        viewport.style.scrollSnapType = "none";
        viewport.style.scrollBehavior = "auto";
        const viewportBounds = viewport.getBoundingClientRect();
        return [...document.querySelectorAll(".bookcase .shelf-book")].map(item => {
          const link = item.querySelector(".shelf-book-meta h3 a");
          for (let attempt = 0; attempt < 8; attempt += 1) {
            const bounds = link.getBoundingClientRect();
            const delta = bounds.left < viewportBounds.left ? bounds.left - viewportBounds.left : bounds.right > viewportBounds.right ? bounds.right - viewportBounds.right : 0;
            if (!delta) break;
            viewport.scrollLeft += delta;
          }
          const visibleBounds = link.getBoundingClientRect();
          return {
            href: link.getAttribute("href"),
            text: link.textContent,
            reachable: visibleBounds.left >= viewportBounds.left - 1 && visibleBounds.right <= viewportBounds.right + 1,
            bounds: [visibleBounds.left, visibleBounds.right, viewportBounds.left, viewportBounds.right],
            action: item.querySelector(".shelf-book-meta .text-link")?.getAttribute("href"),
            fit: getComputedStyle(item.querySelector(".book-cover")).objectFit
          };
        });
      });
      expect(visibility).toHaveLength(count);
      for (const item of visibility) {
        expect(item.reachable, JSON.stringify(item)).toBe(true);
        expect(new URL(item.href).search).toMatch(/slug=visual-fixture-\d+$/);
        expect(item.action).toBe(item.href);
        expect(item.fit).toBe("contain");
        expect(item.text.length).toBeGreaterThan(0);
      }
    }
    await page.unroute("**/data/books.json");
  }
  await page.route("**/data/books.json", route => route.fulfill({ contentType: "application/json", body: JSON.stringify(finalRecords) }));
  await page.goto("library.html?lang=en");
  const longTitleLink = page.locator('.shelf-book[data-book-slug="visual-fixture-50"] .shelf-book-meta h3 a');
  await longTitleLink.click();
  const longTitle = page.locator(".book-detail-hero h1");
  await expect(longTitle).toHaveText("AnUnbrokenSyntheticEngineeringTitleThatMustWrapWithinTheAvailableMobileDetailWidth");
  await expect(longTitle).toBeVisible();
  const viewport = await page.evaluate(collectViewportMetrics);
  expect(viewport.layoutWidth).toBeLessThanOrEqual(390);
  expect(viewport.documentWidth).toBeLessThanOrEqual(viewport.layoutWidth);
  expect(await page.locator(".tag-row-large .tag").count()).toBe(3);
});
