#!/usr/bin/env node
/* Local rendered evidence capture for the static Books site. */
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { chromium } = require('@playwright/test');
const collectViewportMetrics = require('../tests/viewport-metrics');
const { fixtureCatalog } = require('../tests/visual-catalog-fixtures');
const family = require('../site/data/kids-family.json');

const repo = path.resolve(__dirname, '..');
const base = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:18473/books/';
const output = path.resolve(process.argv[2] || '/tmp/books-visual-quality');
const detailSlugs = ['pmicbook', 'watbook', 'fabcontrolbook', 'processintegrationbook', 'thinfilmbook'];
const story = family.stories[0];
const theme = family.themes.find(item => item.storyId === story.id);
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
const assets = ['css/style.css', 'css/renaissance.css', 'js/app.js', 'data/books.json'];
const languages = ['en', 'ko'];
const themes = ['light', 'dark'];

function makeCases() {
  const cases = [];
  const add = (label, route, width = 390, lang = 'en', colorTheme = 'light', action = null, familyState = 'screen', syntheticBookCount = null) => {
    const group = label.startsWith('synthetic-library') ? 'Synthetic libraries'
      : label.startsWith('synthetic-detail') ? 'Synthetic details'
        : label.startsWith('detail-') ? 'Book details'
          : label.startsWith('explorers-') ? 'Little Explorers'
            : label.startsWith('library') ? 'Library'
          : label.startsWith('subject') ? 'Subjects'
            : label.startsWith('home') ? 'Home'
              : label.startsWith('paths') ? 'Learning paths'
                : label.startsWith('roadmap') ? 'Roadmap'
                  : label.startsWith('journey') ? 'Learning journey'
                    : label.startsWith('experiments') ? 'Experiments'
                      : label.startsWith('feedback') ? 'Feedback' : '404';
    cases.push({ label, group, route, width, lang, theme: colorTheme, action, familyState, syntheticBookCount });
  };
  // Full bilingual/theme coverage at the primary mobile width for all non-detail routes.
  const routes = [
    ['home', ''], ['library', 'library.html'], ['subjects', 'categories.html'],
    ['subject-selected', 'categories.html?id=semiconductor'], ['experiments', 'experiments.html'],
    ['paths', 'paths.html'], ['journey', 'learning-journey.html'], ['roadmap', 'roadmap.html'],
    ['explorers-browse', `kids-family.html?theme=${theme.id}&stage=preschool#family-browse`],
    ['feedback', 'feedback.html'], ['not-found', '404.html'],
    ['library-search', 'library.html?q=BCD'], ['library-filter', 'library.html?category=semiconductor'],
    ['library-empty', 'library.html?q=zzzz-no-matching-book-visual-capture&category=semiconductor']
  ];
  for (const [label, route] of routes) for (const lang of languages) for (const colorTheme of themes)
    add(`${label}-${lang}-${colorTheme}-390`, route, 390, lang, colorTheme);

  // Detail pages get bilingual/theme coverage at mobile widths and broader viewport checks.
  for (const slug of detailSlugs) {
    for (const lang of languages) for (const colorTheme of themes)
      add(`detail-${slug}-${lang}-${colorTheme}-390`, `book.html?slug=${slug}`, 390, lang, colorTheme);
    for (const lang of languages) for (const colorTheme of themes)
      add(`detail-${slug}-${lang}-${colorTheme}-320`, `book.html?slug=${slug}`, 320, lang, colorTheme);
    for (const lang of languages) for (const colorTheme of themes)
      add(`detail-${slug}-${lang}-${colorTheme}-360`, `book.html?slug=${slug}`, 360, lang, colorTheme);
    for (const width of [768, 1024, 1440, 1920]) add(`detail-${slug}-en-light-${width}`, `book.html?slug=${slug}`, width);
  }

  // Story, an actual next spread, and print media each capture a real rendered state.
  const storyRoute = `kids-family.html?theme=${theme.id}&stage=preschool`;
  for (const lang of languages) for (const colorTheme of themes) {
    add(`explorers-story-${lang}-${colorTheme}-390`, storyRoute, 390, lang, colorTheme, 'open-story');
    add(`explorers-spread-${lang}-${colorTheme}-390`, storyRoute, 390, lang, colorTheme, 'next-spread');
    add(`explorers-print-${lang}-${colorTheme}-390`, storyRoute, 390, lang, colorTheme, 'open-story', 'print');
  }
  // A small set of non-detail responsive checks at narrow, tablet, and desktop widths.
  for (const width of [320, 768, 1440]) {
    for (const [label, route] of [['home', ''], ['library', 'library.html']])
      add(`${label}-en-light-${width}`, route, width);
  }
  for (const width of [360, 1024, 1920]) {
    for (const [label, route] of [['home', ''], ['library', 'library.html']])
      add(`${label}-en-light-${width}`, route, width);
  }
  for (const width of [320, 360, 768, 1024, 1920]) {
    add(`journey-en-light-${width}`, 'learning-journey.html', width);
    add(`journey-ko-dark-${width}`, 'learning-journey.html', width, 'ko', 'dark');
    add(`roadmap-en-light-${width}`, 'roadmap.html', width);
    add(`roadmap-ko-dark-${width}`, 'roadmap.html', width, 'ko', 'dark');
  }
  add('journey-en-light-195-zoom-proxy', 'learning-journey.html', 195);
  add('journey-calculus-en-light-390', 'learning-journey.html?stage=university-advanced&strand=mathematics', 390);
  add('journey-concept-only-ko-dark-390', 'learning-journey.html?stage=early-elementary&strand=english-language', 390, 'ko', 'dark');
  add('roadmap-ko-dark-1440', 'roadmap.html', 1440, 'ko', 'dark');
  for (const width of [320, 360, 768, 1024, 1920]) {
    add(`explorers-browse-en-light-${width}`, `kids-family.html?theme=${theme.id}&stage=preschool#family-browse`, width);
    add(`explorers-browse-ko-dark-${width}`, `kids-family.html?theme=${theme.id}&stage=preschool#family-browse`, width, 'ko', 'dark');
  }
  for (const width of [768, 1024, 1440, 1920]) {
    for (const [label, route] of [['subjects', 'categories.html'], ['subject-selected', 'categories.html?id=semiconductor'], ['experiments', 'experiments.html'], ['paths', 'paths.html'], ['feedback', 'feedback.html'], ['not-found', '404.html']])
      add(`${label}-en-light-${width}`, route, width);
  }
  for (const count of [5, 10, 25, 50])
    add(`synthetic-library-${count}-en-light-390`, 'library.html', 390, 'en', 'light', null, 'screen', count);
  for (const lang of languages) for (const colorTheme of themes)
    add(`synthetic-detail-50-${lang}-${colorTheme}-390`, 'book.html?slug=visual-fixture-50', 390, lang, colorTheme, null, 'screen', 50);
  if (cases.length > 240) throw new Error(`Capture matrix exceeded 240 states (${cases.length})`);
  return cases;
}

async function waitReady(page, requireHeading = true) {
  if (requireHeading) await page.locator('main h1').first().waitFor({ state: 'visible', timeout: 15000 });
  await page.evaluate(async () => {
    await document.fonts.ready;
    for (const img of document.images) {
      img.loading = 'eager';
      if (!img.complete) await new Promise(resolve => {
        img.addEventListener('load', resolve, { once: true });
        img.addEventListener('error', resolve, { once: true });
        setTimeout(resolve, 5000);
      });
      if (img.complete && img.naturalWidth) await img.decode().catch(() => {});
    }
  });
}

async function main() {
  fs.mkdirSync(output, { recursive: true });
  const assetHashes = {};
  for (const asset of assets) {
    const local = hash(fs.readFileSync(path.join(repo, 'site', asset)));
    const response = await fetch(new URL(asset, base));
    if (!response.ok) throw new Error(`${asset}: served HTTP ${response.status}`);
    const served = hash(Buffer.from(await response.arrayBuffer()));
    if (served !== local) throw new Error(`${asset}: served bytes differ from local candidate (stale server?)`);
    assetHashes[asset] = { local, served };
  }

  const browser = await chromium.launch({ headless: true });
  const records = [];
  const failures = [];
  const cases = makeCases();
  try {
    for (const item of cases) {
      const context = await browser.newContext({
        viewport: { width: item.width, height: item.width <= 390 ? 900 : 1000 },
        deviceScaleFactor: 1, reducedMotion: 'reduce'
      });
      await context.addInitScript(({ lang, theme }) => {
        localStorage.setItem('my-library-language', lang);
        localStorage.setItem('my-library-theme', theme);
      }, { lang: item.lang, theme: item.theme });
      const page = await context.newPage();
      if (item.syntheticBookCount) {
        const syntheticBooks = fixtureCatalog(item.syntheticBookCount);
        await page.route('**/data/books.json', route => route.fulfill({
          contentType: 'application/json',
          body: JSON.stringify(syntheticBooks)
        }));
      }
      const errors = [];
      page.on('pageerror', error => errors.push(`pageerror: ${error.message}`));
      page.on('console', message => { if (message.type() === 'error') errors.push(`console: ${message.text()}`); });
      page.on('requestfailed', request => errors.push(`request: ${request.method()} ${request.url()} ${request.failure()?.errorText || ''}`));
      page.on('response', response => { if (response.status() >= 400) errors.push(`http ${response.status()}: ${response.url()}`); });

      await page.setViewportSize({ width: item.width, height: item.width <= 390 ? 900 : 1000 });
      const url = new URL(item.route, base);
      url.searchParams.set('lang', item.lang);
      await page.goto(url.href, { waitUntil: 'domcontentloaded', timeout: 20000 });
      await waitReady(page);
      if (item.action === 'open-story' || item.action === 'next-spread') {
        await page.locator('[data-story-open]').first().click();
        await page.locator('.family-spread').waitFor({ state: 'visible' });
        const expectedTitle = story.title[item.lang] || story.title.en;
        const actualTitle = await page.locator('#family-reader-title').innerText();
        if (actualTitle.trim() !== expectedTitle) throw new Error(`${item.label}: expected story ${expectedTitle}, got ${actualTitle}`);
      }
      if (item.action === 'next-spread') {
        await page.locator('[data-story-next]').click();
        if (new URL(page.url()).searchParams.get('page') !== '1') throw new Error(`${item.label}: next spread did not navigate to page=1`);
      }
      if (item.familyState === 'print') await page.emulateMedia({ media: 'print' });
      await waitReady(page, item.familyState !== 'print');

      const state = await page.evaluate(() => {
        const shelfRegions = [...document.querySelectorAll('.bookcase-viewport')];
        const overflowElements = [...document.querySelectorAll('body *')].map(el => {
          const rect = el.getBoundingClientRect();
          const style = getComputedStyle(el);
          return { tag: el.tagName.toLowerCase(), className: typeof el.className === 'string' ? el.className : '', left: Math.round(rect.left), right: Math.round(rect.right), overflowX: style.overflowX, inShelfScroller: Boolean(el.closest('.bookcase-viewport')), inSvg: Boolean(el.closest('svg')) };
        }).filter(el => !el.inShelfScroller && !el.inSvg && (el.right > document.documentElement.clientWidth + 1 || el.left < -1) && el.overflowX !== 'auto' && el.overflowX !== 'scroll')
          .slice(0, 8);
        return {
          h1: (document.querySelector('.family-print-story > h1') || document.querySelector('main h1'))?.innerText?.trim() || null,
          lang: document.documentElement.lang,
          theme: document.documentElement.dataset.theme,
          brokenImages: [...document.images].filter(img => !img.naturalWidth).map(img => img.getAttribute('src')),
          overflowElements,
          shelfScrollRegions: shelfRegions.map(el => ({ scrollWidth: el.scrollWidth, clientWidth: el.clientWidth }))
        };
      });
      const viewport = await page.evaluate(collectViewportMetrics);
      const problems = [];
      if (!state.h1) problems.push('missing main h1');
      if (state.lang !== item.lang) problems.push(`lang mismatch: ${state.lang}`);
      if (state.theme !== item.theme) problems.push(`theme mismatch: ${state.theme}`);
      if (viewport.layoutWidth > item.width + 1 || viewport.documentWidth > viewport.layoutWidth + 1 || state.overflowElements.length) problems.push('document horizontal overflow');
      if (state.brokenImages.length) problems.push(`broken images: ${state.brokenImages.join(', ')}`);
      if (errors.length) problems.push(...errors);

      const filename = `${item.label}.png`;
      await page.screenshot({ path: path.join(output, filename), fullPage: true, animations: 'disabled', timeout: 20000 });
      const record = { ...item, filename, h1: state.h1, viewport, state, errors, problems };
      records.push(record);
      if (problems.length) failures.push({ label: item.label, problems, state });
      await context.close();
    }
  } finally {
    await browser.close();
  }

  const manifest = {
    generatedAt: new Date().toISOString(), base, output, assetHashes,
    captureCount: records.length, captureLimit: cases.length,
    note: 'Capture and DOM diagnostics are evidence only; capture count does not constitute a visual pass.',
    records, failures
  };
  fs.writeFileSync(path.join(output, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
  const groups = new Map();
  for (const record of records) groups.set(record.group, [...(groups.get(record.group) || []), record]);
  const sections = [...groups].map(([name, items]) => `<section><h2>${escapeHtml(name)} <small>(${items.length})</small></h2><div class="grid">${items.map(record => `<article><a href="${record.filename}"><img loading="lazy" src="${record.filename}" alt="${escapeHtml(record.label)} capture"></a><div><a href="${record.filename}">${escapeHtml(record.label)}</a><br><small>${record.width}px · ${record.lang}/${record.theme}${record.familyState === 'print' ? ' · print' : ''} · ${escapeHtml(record.h1 || 'missing h1')}</small></div></article>`).join('')}</div></section>`).join('\n');
  fs.writeFileSync(path.join(output, 'index.html'), `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Books visual capture gallery</title><style>body{font:15px/1.5 system-ui;margin:2rem;max-width:90rem;color:#17202a}section{margin:2rem 0}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px}article{min-width:0;border:1px solid #ccd2d7;background:#fff;padding:8px}article img{display:block;width:100%;height:300px;object-fit:contain;background:#f0f2f3}small{color:#555}a{color:#064d75}</style><h1>Books visual capture gallery</h1><p>${records.length} captures. Captures and DOM diagnostics are not a visual pass. Click a thumbnail for the full PNG.</p>${sections}<p><a href="manifest.json">Evidence manifest</a></p></html>`);
  process.stdout.write(`CAPTURES ${records.length}\nFAILURES ${failures.length}\nGALLERY ${path.join(output, 'index.html')}\nMANIFEST ${path.join(output, 'manifest.json')}\n`);
  if (failures.length) process.exitCode = 1;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
}

if (require.main === module) main().catch(error => { process.stderr.write(`${error.stack || error}\n`); process.exitCode = 1; });

module.exports = { makeCases };
