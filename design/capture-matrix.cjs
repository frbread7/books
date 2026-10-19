const { chromium } = require('@playwright/test');
const fs = require('node:fs');
const pathModule = require('node:path');

(async () => {
  const output = process.argv[2] || '/tmp/books-renaissance-qa-final';
  const base = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:4173/books/';
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const routes = {
    home: '',
    library: 'library.html',
    detail: 'book.html?slug=pmicbook',
    categories: 'categories.html',
    kids: 'kids-family.html'
  };
  const errors = [];
  const anomalies = [];
  let captures = 0;

  for (const lang of ['en', 'ko']) {
    for (const theme of ['light', 'dark']) {
      const context = await browser.newContext({
        viewport: { width: 320, height: 950 },
        deviceScaleFactor: 1
      });
      await context.addInitScript(({ lang, theme }) => {
        localStorage.setItem('my-library-language', lang);
        localStorage.setItem('my-library-theme', theme);
      }, { lang, theme });

      const page = await context.newPage();
      page.on('pageerror', error => errors.push(`${page.url()}: ${error.message}`));
      page.on('console', message => {
        if (message.type() === 'error') errors.push(`${page.url()}: ${message.text()}`);
      });

      for (const [route, path] of Object.entries(routes)) {
        for (const width of [320, 360, 390, 768, 1024, 1440, 1920]) {
          await page.setViewportSize({ width, height: 950 });
          await page.goto(new URL(path, base).href, {
            waitUntil: 'domcontentloaded'
          });
          await page.locator('main h1').first().waitFor({ timeout: 10000 });
          await page.evaluate(() => document.fonts.ready);

          const state = await page.evaluate(() => ({
            lang: document.documentElement.lang,
            theme: document.documentElement.dataset.theme
          }));
          if (state.lang !== lang || state.theme !== theme) {
            anomalies.push({ route, width, expected: { lang, theme }, state });
          }

          const missingImages = await page.locator('img').evaluateAll(async images => {
            for (const image of images) {
              image.loading = 'eager';
              if (!image.complete) await new Promise(resolve => {
                image.addEventListener('load', resolve, { once: true });
                image.addEventListener('error', resolve, { once: true });
                setTimeout(resolve, 3000);
              });
              await image.decode().catch(() => {});
            }
            window.scrollTo(0, 0);
            return images.filter(image => image.naturalWidth === 0)
              .map(image => image.getAttribute('src'));
          });

          const overflow = await page.evaluate(() => {
            const width = innerWidth;
            const items = [...document.querySelectorAll('body *')]
              .map(element => {
                const rect = element.getBoundingClientRect();
                return {
                  selector: element.tagName.toLowerCase() +
                    (typeof element.className === 'string' && element.className
                      ? `.${element.className.trim().split(/\s+/).join('.')}`
                      : ''),
                  left: Math.round(rect.left),
                  right: Math.round(rect.right),
                  text: (element.innerText || '').trim().slice(0, 48)
                };
              })
              .filter(item => item.right > width + 0.5 || item.left < -0.5)
              .slice(0, 3);
            return { scrollWidth: document.documentElement.scrollWidth, items };
          });

          if (overflow.scrollWidth > width || overflow.items.length || missingImages.length) {
            anomalies.push({ route, width, lang, theme, overflow, missingImages });
          }

          await page.screenshot({
            path: pathModule.join(output, `${route}-${width}-${lang}-${theme}.png`),
            fullPage: true
          });
          captures += 1;
        }
      }
      await context.close();
    }
  }

  await browser.close();
  console.log(JSON.stringify({ captures, output, anomalies, errors }, null, 2));
  if (anomalies.length || errors.length) process.exitCode = 1;
})().catch(error => {
  console.error(error);
  process.exit(1);
});
