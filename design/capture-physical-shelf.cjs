const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { execFileSync } = require('node:child_process');
const { chromium } = require('@playwright/test');

const repo = path.resolve(__dirname, '..');
const base = process.env.BOOKS_SHELF_BASE_URL || 'http://127.0.0.1:4173/books/';
const outputRoot = process.env.BOOKS_SHELF_CAPTURE_DIR || '/tmp/books-renaissance-shelf-final';
const git = (...args) => execFileSync('git', args, { cwd: repo, encoding: 'utf8' }).trim();
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');

async function main() {
  const head = git('rev-parse', 'HEAD');
  const tree = git('rev-parse', 'HEAD^{tree}');
  const dirty = Boolean(git('status', '--porcelain'));
  if (dirty && process.env.BOOKS_SHELF_ALLOW_DIRTY !== '1') throw new Error('Candidate worktree is not clean');

  const assetHashes = {};
  for (const asset of ['js/app.js', 'css/renaissance.css', 'data/books.json']) {
    const localHash = sha(fs.readFileSync(path.join(repo, 'site', asset)));
    const response = await fetch(new URL(asset, base));
    if (!response.ok) throw new Error(`${asset}: served HTTP ${response.status}`);
    const servedHash = sha(Buffer.from(await response.arrayBuffer()));
    if (servedHash !== localHash) throw new Error(`${asset}: served bytes differ from candidate`);
    assetHashes[asset] = localHash;
  }

  const output = path.join(outputRoot, dirty ? `${head}-precommit` : head);
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const records = [];
  const failures = [];
  try {
    const combinations = [];
    for (const width of [390, 1440]) {
      for (const lang of ['en', 'ko']) {
        for (const theme of ['light', 'dark']) {
          for (const route of ['home', 'library']) combinations.push({ width, lang, theme, route, core: true });
        }
      }
    }
    for (const width of [320, 360, 768, 1024, 1920]) {
      for (const route of ['home', 'library']) combinations.push({ width, lang: 'en', theme: 'light', route, core: false });
    }

    for (const item of combinations) {
      const context = await browser.newContext({ viewport: { width: item.width, height: item.width <= 390 ? 844 : 1000 }, reducedMotion: 'reduce' });
      await context.addInitScript(theme => localStorage.setItem('my-library-theme', theme), item.theme);
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      page.on('console', message => {
        if (message.type() === 'error') errors.push(message.text());
      });
      page.on('requestfailed', request => errors.push(`${request.method()} ${request.url()}: ${request.failure()?.errorText || 'request failed'}`));
      page.on('response', response => {
        if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`);
      });
      const suffix = item.route === 'home' ? '' : 'library.html';
      await page.goto(new URL(`${suffix}?lang=${item.lang}`, base).href, { waitUntil: 'networkidle' });
      await page.evaluate(() => document.fonts.ready);
      const shelf = page.locator('.bookcase[data-bookcase]');
      await shelf.waitFor({ state: 'visible' });
      const count = await shelf.locator('.shelf-book').count();
      const state = await page.locator('img').evaluateAll(async images => {
        for (const image of images) {
          image.loading = 'eager';
          try { await image.decode(); } catch { /* Report missing images below. */ }
        }
        return {
          brokenImages: images.filter(image => image.naturalWidth === 0).map(image => image.getAttribute('src')),
          documentWidth: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth),
          viewportWidth: innerWidth,
          theme: document.documentElement.dataset.theme,
          lang: document.documentElement.lang
        };
      });
      const name = `${item.route}-${item.width}-${item.lang}-${item.theme}`;
      const full = `${name}-full.png`;
      const close = `${name}-shelf.png`;
      await page.screenshot({ path: path.join(output, full), fullPage: true, animations: 'disabled' });
      await shelf.screenshot({ path: path.join(output, close), animations: 'disabled' });
      if (count !== 5 || state.brokenImages.length || state.documentWidth > state.viewportWidth + 1 || state.theme !== item.theme || state.lang !== item.lang || errors.length) {
        failures.push({ name, count, state, errors });
      }
      records.push({ ...item, name, count, state, errors, full, close });
      await context.close();
    }
  } finally {
    await browser.close();
  }

  const manifest = { head, tree, dirty, base, assetHashes, coreStates: records.filter(item => item.core).length, responsiveStates: records.filter(item => !item.core).length, records, failures };
  fs.writeFileSync(path.join(output, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
  process.stdout.write(`HEAD ${head}\nTREE ${tree}\nCAPTURES ${records.length} pairs\nFAILURES ${failures.length}\nMANIFEST ${path.join(output, 'manifest.json')}\n`);
  if (failures.length) process.exitCode = 1;
}

main().catch(error => { process.stderr.write(`${error.stack || error}\n`); process.exitCode = 1; });
