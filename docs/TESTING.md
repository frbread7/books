# Testing

## Local commands

~~~sh
python3 -m pip install -r requirements.txt
npm ci
npx playwright install chromium
npm run validate
npm run test:e2e
~~~

npx playwright install --with-deps chromium installs browser system dependencies on Linux when they are absent. `npm run validate` runs offline Python checks and then compares every derived site/data index with canonical manifests, maps, roadmap, and paths without writing files. A stale or missing index fails the command before deployment. `python3 tools/book_factory.py generate` is the explicit index-writing command. Tests cover routes/assets, base-path centralization, dynamic catalog data, roadmap/catalog separation, PMICBook's stable chapter and experiment facts, recorded live evidence, and absence of upstream domain/identity/infrastructure from deployed files. Book Factory tests exercise publication evidence, duplicate chapter IDs, required live experiment evidence, discovery cross-references, second-book expansion, successful register/update generation, drift detection without mutation, and protection against implicit overwrite.

npm run test:e2e starts tests/serve.py, which serves the exact site artifact beneath /books/. Playwright covers mobile (390×844), tablet (768×1024), and desktop (1440×1000):

- Home to PMICBook details and its 25 chapters/four experiments.
- Search, empty results, reset, and planned-status filtering.
- Subject knowledge map, learning paths, and experiment discovery using catalog-driven expected totals.
- A synthetic second published book, aggregate statistics, and a registered in-progress detail state with no false reading link.
- A nested unknown route with project-base stylesheet, script, JSON, and navigation resolution.
- English/Korean controls and saved theme preference.
- Main views, image alternative-text attributes, keyboard skip-link focus styling, named links, and horizontal overflow.

The suite captures homepage and book-detail screenshots for each viewport. Traces and failure screenshots are written to ignored test-results/.

## Scope

These portal checks validate metadata and outbound links; they do not rerun PMICBook's complete textbook suite. PMICBook is external and remains unmodified. Experiment verification is separate from ordinary tests: `tools/verify_experiments.py` performs a bounded live HTTPS request, checks the HTTP status and fragment in the returned HTML, and records evidence. `npm test` checks those stored records structurally and remains offline/deterministic. A production smoke test should repeat link and asset checks after deployment.

Automated accessibility basics check semantic landmarks, keyboard focus visibility for the skip link, labels, presence of `alt` attributes (including empty decorative alternatives), and named links. These checks do not establish WCAG conformance and are not a substitute for a dedicated assistive-technology audit.
