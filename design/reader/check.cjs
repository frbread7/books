const { chromium } = require('@playwright/test');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

const output = process.argv[2] || '/tmp/books-renaissance-reader-capture';
const specimen = pathToFileURL(path.join(__dirname, 'index.html')).href;

(async () => {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const findings = [];
  let captures = 0;

  for (const width of [390, 1440]) {
    const context = await browser.newContext({ viewport: { width, height: 900 } });
    const page = await context.newPage();
    page.on('pageerror', error => findings.push(error.message));
    await page.goto(specimen);

    for (const lang of ['en', 'ko']) {
      await page.locator(`[data-language="${lang}"]`).click();
      for (const theme of ['light', 'dark']) {
        if (await page.locator('html').getAttribute('data-theme') !== theme) {
          await page.locator('.theme-button').click();
        }
        await page.waitForTimeout(260);
        const state = await page.evaluate(() => ({
          lang: document.documentElement.lang,
          theme: document.documentElement.dataset.theme,
          overflow: document.documentElement.scrollWidth > innerWidth,
          anchors: [...document.querySelectorAll('.contents a')]
            .every(link => !!document.getElementById(link.hash.slice(1))),
          pressed: document.querySelector(`[data-language="${document.documentElement.lang}"]`)
            .getAttribute('aria-pressed'),
          formula: document.querySelector('.equation').textContent.replace(/\s+/g, ' ').trim(),
          mathName: document.querySelector('.equation').getAttribute('aria-label'),
          diagramName: document.querySelector('#circuit-title').textContent,
          diagramDescription: document.querySelector('#circuit-desc').textContent,
          caption: document.querySelector('.circuit-figure figcaption').textContent,
          settingsName: document.querySelector('.reader-controls').getAttribute('aria-label'),
          railName: document.querySelector('.contents-rail').getAttribute('aria-label'),
          questionName: document.querySelector('.callout-question').getAttribute('aria-label'),
          reminderName: document.querySelector('.callout-guidance').getAttribute('aria-label'),
          navName: document.querySelector('.contents nav').getAttribute('aria-label'),
          diagramVisible: document.querySelector('.circuit-figure svg').getBoundingClientRect().width > 200
        }));
        if (state.lang !== lang || state.theme !== theme || state.overflow ||
            !state.anchors || state.pressed !== 'true' ||
            !state.formula.includes('6 V / 1.0 kΩ') || !state.formula.includes('6 mA') ||
            !state.mathName || !state.diagramName || !state.diagramDescription ||
            !state.caption || !state.diagramVisible ||
            (lang === 'ko' && (!state.diagramDescription.includes('시계 방향') ||
              [state.settingsName, state.railName, state.questionName, state.reminderName, state.navName]
                .some(name => !/[가-힣]/.test(name)))) ||
            (lang === 'en' && !state.diagramDescription.includes('clockwise'))) {
          findings.push({ width, lang, theme, state });
        }
        await page.screenshot({
          path: path.join(output, `reader-${width}-${lang}-${theme}.png`),
          fullPage: true
        });
        captures += 1;
      }
    }
    await context.close();
  }

  await browser.close();
  console.log(JSON.stringify({ captures, output, findings }, null, 2));
  if (findings.length) process.exitCode = 1;
})().catch(error => {
  console.error(error);
  process.exit(1);
});
