const { chromium } = require('@playwright/test');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

const base = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:4173/books/';
const output = process.argv[2] || '/tmp/books-renaissance-readiness.json';
const routes = {
  home: '', library: 'library.html', detail: 'book.html?slug=pmicbook',
  family: 'kids-family.html', journey: 'learning-journey.html'
};
const states = [['en', 'light'], ['ko', 'dark']];
const widths = [320, 390, 720, 1440];

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.floor(sorted.length / 2)];
}

function rgb(color) {
  if (color.startsWith('rgb(')) return color.match(/[\d.]+/g).slice(0, 3).map(Number);
  if (color.startsWith('color(srgb ')) {
    return color.slice('color(srgb '.length).match(/[\d.]+/g).slice(0, 3).map(value => Number(value) * 255);
  }
  return null;
}

function contrast(foreground, background) {
  const luminance = color => {
    const channels = rgb(color)?.map(value => {
      const normal = value / 255;
      return normal <= 0.04045 ? normal / 12.92 : ((normal + 0.055) / 1.055) ** 2.4;
    });
    return channels && channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
  };
  const a = luminance(foreground);
  const b = luminance(background);
  return a === null || b === null ? null : Math.round(((Math.max(a, b) + 0.05) /
    (Math.min(a, b) + 0.05)) * 100) / 100;
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const findings = [];
  const report = { base, states: [], motion: {}, keyboard: {}, contrast: [], touch: {}, errors: {}, performance: {} };

  for (const [lang, theme] of states) {
    const context = await browser.newContext();
    await context.addInitScript(({ lang, theme }) => {
      localStorage.setItem('my-library-language', lang);
      localStorage.setItem('my-library-theme', theme);
    }, { lang, theme });
    const page = await context.newPage();
    page.on('pageerror', error => findings.push(`pageerror: ${error.message}`));
    for (const [route, routePath] of Object.entries(routes)) {
      for (const width of widths) {
        await page.setViewportSize({ width, height: 900 });
        await page.goto(new URL(routePath, base).href, { waitUntil: 'domcontentloaded' });
        await page.locator('main h1').first().waitFor({ timeout: 10000 });
        const state = await page.evaluate(() => ({
          lang: document.documentElement.lang,
          theme: document.documentElement.dataset.theme,
          viewport: document.documentElement.clientWidth,
          scrollWidth: document.documentElement.scrollWidth,
          heading: document.querySelector('main h1')?.textContent.trim()
        }));
        const result = { route, width, expected: `${lang}/${theme}`, ...state };
        report.states.push(result);
        if (state.lang !== lang || state.theme !== theme ||
            state.scrollWidth > state.viewport + 1 || !state.heading) findings.push(result);
      }
    }
    await context.close();
  }

  const reduced = await browser.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
  const motionPage = await reduced.newPage();
  await motionPage.goto(base);
  await motionPage.locator('main h1').waitFor();
  await motionPage.locator('.room-book-card').first().hover();
  report.motion.portal = await motionPage.evaluate(() => ({
    preference: matchMedia('(prefers-reduced-motion: reduce)').matches,
    scrollBehavior: getComputedStyle(document.documentElement).scrollBehavior,
    buttonTransition: getComputedStyle(document.querySelector('.button')).transitionDuration,
    cardTransition: getComputedStyle(document.querySelector('.room-book-card')).transitionDuration,
    hoveredCardTransform: getComputedStyle(document.querySelector('.room-book-card')).transform
  }));
  const reader = pathToFileURL(path.join(__dirname, 'reader', 'index.html')).href;
  await motionPage.goto(reader);
  report.motion.reader = await motionPage.evaluate(() => ({
    preference: matchMedia('(prefers-reduced-motion: reduce)').matches,
    scrollBehavior: getComputedStyle(document.documentElement).scrollBehavior,
    bodyTransition: getComputedStyle(document.body).transitionDuration
  }));
  if (!report.motion.portal.preference || report.motion.portal.scrollBehavior !== 'auto' ||
      report.motion.portal.buttonTransition !== '0s' ||
      report.motion.portal.cardTransition !== '0s' ||
      report.motion.portal.hoveredCardTransform !== 'none' ||
      !report.motion.reader.preference || report.motion.reader.scrollBehavior !== 'auto' ||
      parseFloat(report.motion.reader.bodyTransition) > 0.001) findings.push({ motion: report.motion });
  await reduced.close();

  const interaction = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await interaction.newPage();
  await page.goto(base);
  await page.locator('main h1').waitFor();
  await page.keyboard.press('Tab');
  report.keyboard.skipFocused = await page.locator('.skip-link').evaluate(element =>
    document.activeElement === element && getComputedStyle(element).outlineStyle === 'solid');
  await page.keyboard.press('Enter');
  report.keyboard.skipDestination = await page.evaluate(() => ({ hash: location.hash, activeId: document.activeElement.id }));
  await page.goto(new URL('library.html', base).href);
  await page.locator('#book-search').waitFor();
  const focusOrder = [];
  for (let i = 0; i < 28; i += 1) {
    await page.keyboard.press('Tab');
    focusOrder.push(await page.evaluate(() => ({
      tag: document.activeElement.tagName,
      id: document.activeElement.id,
      order: [...document.querySelectorAll('a, button, input, select, summary')]
        .indexOf(document.activeElement),
      outline: getComputedStyle(document.activeElement).outlineStyle
    })));
  }
  report.keyboard.library = {
    sampleLength: focusOrder.length,
    searchReached: focusOrder.some(item => item.id === 'book-search'),
    categoryReached: focusOrder.some(item => item.id === 'category-filter'),
    noFocusTrap: new Set(focusOrder.map(item => item.order)).size > 8,
    invisibleFocused: focusOrder.filter(item => item.outline === 'none').slice(0, 5)
  };
  await page.goto(new URL('kids-family.html', base).href);
  await page.locator('.family-interest').first().waitFor();
  const interests = page.locator('.family-interest');
  if (await interests.count() > 1) {
    await interests.nth(1).focus();
    await page.keyboard.press('Enter');
    report.keyboard.familyInterestOperable = await interests.nth(1).getAttribute('aria-pressed') === 'true';
  }
  if (!report.keyboard.skipFocused || report.keyboard.skipDestination.hash !== '#main' ||
      !report.keyboard.library.searchReached || !report.keyboard.library.categoryReached ||
      !report.keyboard.library.noFocusTrap || report.keyboard.library.invisibleFocused.length ||
      !report.keyboard.familyInterestOperable) {
    findings.push({ keyboard: report.keyboard });
  }

  for (const [lang, theme] of states) {
    await page.addInitScript(({ lang, theme }) => {
      localStorage.setItem('my-library-language', lang);
      localStorage.setItem('my-library-theme', theme);
    }, { lang, theme });
    await page.goto(base);
    await page.locator('.room-book-card').first().waitFor();
    const samples = await page.evaluate(() => {
      const selectors = [
        '.primary-nav a', '.button-primary', '.room-book-card h3',
        '.room-book-card .book-subtitle', '.room-book-card .badge-published',
        '.room-subject-card:not(.room-subject-card-featured) .room-subject-name'
      ];
      return selectors.map(selector => {
        const element = document.querySelector(selector);
        if (!element) return { selector, missing: true };
        const style = getComputedStyle(element);
        let surface = element;
        while (surface && getComputedStyle(surface).backgroundColor === 'rgba(0, 0, 0, 0)') {
          surface = surface.parentElement;
        }
        const background = surface ? getComputedStyle(surface).backgroundColor : getComputedStyle(document.body).backgroundColor;
        return { selector, text: element.textContent.trim().slice(0, 40),
          color: style.color, background, fontSize: style.fontSize, fontWeight: style.fontWeight };
      });
    });
    report.contrast.push({ lang, theme, route: 'home', samples });
    await page.goto(new URL('kids-family.html', base).href);
    await page.locator('.family-interest').first().waitFor();
    report.contrast.push({ lang, theme, route: 'family', samples: await page.evaluate(() => {
      return ['.family-interest', '.family-story-card h3', '.family-privacy p'].map(selector => {
        const element = document.querySelector(selector);
        if (!element) return { selector, missing: true };
        const style = getComputedStyle(element);
        let surface = element;
        while (surface && getComputedStyle(surface).backgroundColor === 'rgba(0, 0, 0, 0)') surface = surface.parentElement;
        return { selector, text: element.textContent.trim().slice(0, 40), color: style.color,
          background: surface ? getComputedStyle(surface).backgroundColor : getComputedStyle(document.body).backgroundColor,
          fontSize: style.fontSize, fontWeight: style.fontWeight };
      });
    }) });
  }
  report.touch = await page.evaluate(() => {
    const selectors = ['.primary-nav a', '.icon-button', '.family-interest', '.family-stage', '.family-theme-card'];
    const targets = [...document.querySelectorAll(selectors.join(', '))]
      .filter(element => getComputedStyle(element).display !== 'none')
      .map(element => ({ element, rect: element.getBoundingClientRect() }));
    return selectors.map(selector => {
      const elements = [...document.querySelectorAll(selector)].filter(element => getComputedStyle(element).display !== 'none');
      const sizes = elements.map(element => element.getBoundingClientRect());
      return { selector, count: sizes.length,
        minWidth: sizes.length ? Math.round(Math.min(...sizes.map(item => item.width))) : null,
        minHeight: sizes.length ? Math.round(Math.min(...sizes.map(item => item.height))) : null,
        undersized: elements.filter(element => {
          const rect = element.getBoundingClientRect();
          if (rect.width >= 24 && rect.height >= 24) return false;
          const center = { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
          const nearest = Math.min(...targets.filter(item => item.element !== element)
            .map(item => Math.hypot(center.x - item.rect.left - item.rect.width / 2,
              center.y - item.rect.top - item.rect.height / 2)));
          return nearest < 24;
        }).length };
    });
  });
  if (report.touch.some(item => !item.count || item.minHeight < 40 || item.undersized)) {
    findings.push({ touch: report.touch });
  }
  for (const state of report.contrast) {
    for (const sample of state.samples) {
      if (sample.missing) {
        findings.push({ contrast: { lang: state.lang, theme: state.theme,
          route: state.route, selector: sample.selector, missing: true } });
        continue;
      }
      sample.ratio = contrast(sample.color, sample.background);
      if (sample.ratio === null || sample.ratio < 4.5) {
        findings.push({ contrast: { lang: state.lang, theme: state.theme,
          route: state.route, selector: sample.selector, ratio: sample.ratio } });
      }
    }
  }
  await interaction.close();

  const errorsContext = await browser.newContext();
  const errorPage = await errorsContext.newPage();
  await errorPage.route('**/data/kids-family.json', route => route.fulfill({ status: 503, body: '{}' }));
  await errorPage.goto(base);
  await errorPage.locator('main h1').waitFor();
  report.errors.optionalFamilyHome = await errorPage.locator('.room-hero h1').count() === 1;
  await errorPage.goto(new URL('kids-family.html', base).href);
  await errorPage.locator('[data-action="retry"]').waitFor();
  report.errors.requiredFamilyRetry = await errorPage.locator('[data-action="retry"]').count() === 1;
  await errorPage.unroute('**/data/kids-family.json');
  await errorPage.locator('[data-action="retry"]').click();
  await errorPage.locator('.family-interest').first().waitFor();
  report.errors.familyRetryRestored = true;
  await errorPage.goto(new URL('book.html?slug=missing-book', base).href);
  await errorPage.locator('main h1').waitFor();
  report.errors.missingBookReturn = await errorPage.locator('.not-found a[href*="library.html"]').count() === 1;
  if (Object.values(report.errors).some(value => !value)) findings.push({ errors: report.errors });
  await errorsContext.close();

  for (const [route, routePath] of Object.entries({ home: '', library: 'library.html', family: 'kids-family.html' })) {
    const runs = [];
    for (let i = 0; i < 3; i += 1) {
      const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
      await context.addInitScript(() => {
        window.__layoutShiftSum = null;
        try {
          window.__layoutShiftSum = 0;
          new PerformanceObserver(list => {
            for (const entry of list.getEntries()) {
              if (!entry.hadRecentInput) window.__layoutShiftSum += entry.value;
            }
          }).observe({ type: 'layout-shift', buffered: true });
        } catch { window.__layoutShiftSum = null; }
      });
      const p = await context.newPage();
      const requests = [];
      p.on('request', request => requests.push(request.url()));
      const start = Date.now();
      await p.goto(new URL(routePath, base).href, { waitUntil: 'domcontentloaded' });
      await p.locator('main h1').first().waitFor();
      const readyMs = Date.now() - start;
      await p.waitForLoadState('networkidle');
      const measurements = await p.evaluate(() => ({
        layoutShift: window.__layoutShiftSum,
        resources: performance.getEntriesByType('resource').map(item => ({
          url: item.name, bytes: item.transferSize, durationMs: Math.round(item.duration)
        }))
      }));
      runs.push({ readyMs, requests: requests.length,
        externalRequests: requests.filter(url => new URL(url).origin !== new URL(base).origin).length,
        browserTransferBytes: measurements.resources.reduce((sum, item) => sum + item.bytes, 0),
        observedLayoutShift: measurements.layoutShift === null ? null :
          Math.round(measurements.layoutShift * 1000) / 1000 });
      await context.close();
    }
    report.performance[route] = { runs, medianReadyMs: median(runs.map(run => run.readyMs)),
      medianTransferBytes: median(runs.map(run => run.browserTransferBytes)) };
  }

  await browser.close();
  report.findings = findings;
  fs.writeFileSync(output, JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ output, reflowStates: report.states.length, motion: report.motion,
    keyboard: report.keyboard, touch: report.touch, errors: report.errors,
    performance: report.performance, findings }, null, 2));
  if (findings.length) process.exitCode = 1;
})().catch(error => { console.error(error); process.exit(1); });
