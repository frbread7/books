# Testing

## Local commands

~~~sh
python3 -m pip install -r requirements.txt
npm ci
npx playwright install chromium
npm run validate
npm run test:e2e
~~~

npx playwright install --with-deps chromium installs browser system dependencies on Linux when they are absent. `npm run validate` runs offline Python checks and then compares every derived site/data index with canonical manifests, maps, roadmap, learning paths, and Learning Journey without writing files. A stale or missing index fails the command before deployment. `python3 tools/book_factory.py generate` is the explicit index-writing command. Tests cover routes/assets, base-path centralization, dynamic catalog data, roadmap/catalog separation, the published-book count, PMICBook/WATBook/ProcessIntegrationBook/FabControlBook/ThinFilmBook records, recorded live evidence, and absence of upstream domain/identity/infrastructure from deployed files. The Learning Journey checks complete stage/strand coverage, unique stable IDs, bilingual fields, acyclic prerequisites, revisit depth, source metadata, and honest planned/published material references. Book Factory tests exercise publication evidence, duplicate chapter IDs, required live experiment evidence, discovery cross-references, bilingual map labels and topic tags, roadmap separation, second-book expansion, successful register/update generation, drift detection without mutation, and protection against implicit overwrite.

npm run test:e2e starts tests/serve.py, which serves the exact site artifact beneath /books/. Playwright covers mobile (390×844), tablet (768×1024), and desktop (1440×1000). The canonical catalog contains five published books and 20 verified experiment anchors:

- Home to PMICBook details and its 25 chapters/four experiments.
- FabControlBook's bilingual detail, localized manufacturing-control knowledge map, eight-step learning path, and four experiments.
- ProcessIntegrationBook's bilingual detail, map/path links, and three experiments.
- ThinFilmBook's published release evidence, bilingual chapter routes, cover, repository, language entry points, and three verified experiment anchors.
- Search, empty results, reset, and planned-status filtering.
- Subject knowledge maps, Learning Journey stage/strand selection, concept relations, material-status honesty, legacy learning paths, and experiment discovery.
- A synthetic second published book, aggregate statistics, and a registered in-progress detail with no top-level public destinations or external actions.
- A nested unknown route with project-base stylesheet, script, JSON, and navigation resolution.
- English/Korean controls and saved theme preference.
- Main views, image alternative-text attributes, keyboard skip-link focus styling, named links, and horizontal overflow.

The Pages deploy job separately runs `tests/e2e/production-smoke.spec.js` after deployment to check the published ThinFilmBook card and cover; that check is skipped during local validation when no production base URL is set. The suite captures homepage and book-detail screenshots for each viewport. Traces and failure screenshots are written to ignored test-results/.

## Scope

These portal checks validate metadata and outbound URL structure; they do not rerun PMICBook's complete textbook suite. PMICBook is external and remains unmodified. Only simulator/experiment links receive automated live reachability checks: `tools/verify_experiments.py` performs bounded HTTPS requests, pins each validated public destination IP while preserving configured proxy and CA behavior, checks HTTP status and the fragment in returned HTML, and records evidence. Repository, language-entry, chapter, and other outbound links are not automatically live-checked; manually smoke-test them after deployment. `npm test` checks recorded experiment evidence structurally and remains offline/deterministic.

Automated accessibility basics check semantic landmarks, keyboard focus visibility for the skip link, labels, presence of `alt` attributes (including empty decorative alternatives), and named links. These checks do not establish WCAG conformance and are not a substitute for a dedicated assistive-technology audit.
