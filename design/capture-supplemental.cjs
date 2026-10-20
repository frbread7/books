const { chromium } = require('@playwright/test');
const fs = require('node:fs');
const path = require('node:path');

const output = process.argv[2] || '/tmp/books-renaissance-qa-supplemental';
const base = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:4173/books/';
const routes = {
  journey: 'learning-journey.html',
  roadmap: 'roadmap.html',
  paths: 'paths.html',
  experiments: 'experiments.html'
};

(async () => {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const anomalies = [];
  const errors = [];
  let captures = 0;

  for (const [lang, theme] of [['en', 'light'], ['ko', 'dark']]) {
    const context = await browser.newContext({ viewport: { width: 390, height: 950 } });
    await context.addInitScript(({ lang, theme }) => {
      localStorage.setItem('my-library-language', lang);
      localStorage.setItem('my-library-theme', theme);
    }, { lang, theme });
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(`${page.url()}: ${error.message}`));
    page.on('console', message => {
      if (message.type() === 'error') errors.push(`${page.url()}: ${message.text()}`);
    });

    for (const [route, routePath] of Object.entries(routes)) {
      for (const width of [390, 1440]) {
        await page.setViewportSize({ width, height: 950 });
        await page.goto(new URL(routePath, base).href, { waitUntil: 'domcontentloaded' });
        await page.locator('main h1').first().waitFor({ timeout: 10000 });
        await page.evaluate(() => document.fonts.ready);
        const state = await page.evaluate(async () => {
          const images = [...document.querySelectorAll('img')];
          await Promise.all(images.map(async image => {
            image.loading = 'eager';
            try { await image.decode(); } catch { /* Recorded below. */ }
          }));
          window.scrollTo(0, 0);
          return {
            lang: document.documentElement.lang,
            theme: document.documentElement.dataset.theme,
            scrollWidth: document.documentElement.scrollWidth,
            missingImages: images.filter(image => image.naturalWidth === 0).map(image => image.src)
          };
        });
        if (state.lang !== lang || state.theme !== theme ||
            state.scrollWidth > width || state.missingImages.length) {
          anomalies.push({ route, width, lang, theme, ...state });
        }
        await page.screenshot({
          path: path.join(output, `${route}-${width}-${lang}-${theme}.png`),
          fullPage: true
        });
        captures += 1;
      }
    }
    await context.close();
  }

  await browser.close();
  console.log(JSON.stringify({ captures, output, anomalies, errors }, null, 2));
  if (anomalies.length || errors.length) process.exitCode = 1;
})().catch(error => {
  console.error(error);
  process.exit(1);
});
