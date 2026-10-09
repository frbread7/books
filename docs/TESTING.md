# Testing

## Local commands

~~~sh
python3 -m pip install -r requirements.txt
npm ci
npm run validate
npm run test:e2e
~~~

npm run validate runs Python unittest checks, validates every registered manifest, and regenerates browser JSON indexes. It checks routes/assets, base-path centralization, catalog counts, roadmap/catalog separation, PMICBook experiment anchors, and absence of upstream domain/identity/infrastructure from deployed files. Book Factory tests exercise publication evidence, duplicate chapter IDs, anchor requirements, discovery-index cross-references, successful register/update generation, and protection against implicit overwrite.

npm run test:e2e starts tests/serve.py, which serves the exact site artifact beneath /books/. Playwright covers mobile (390×844), tablet (768×1024), and desktop (1440×1000):

- Home to PMICBook details and its 25 chapters/four experiments.
- Search, empty results, reset, and planned-status filtering.
- Subject knowledge map, learning paths, and experiment discovery.
- English/Korean controls and saved theme preference.
- Main views, named links, and horizontal overflow.

The suite captures homepage and book-detail screenshots for each viewport. Traces and failure screenshots are written to ignored test-results/.

## Scope

These portal checks validate metadata and outbound links; they do not rerun PMICBook's complete textbook suite. PMICBook is external and remains unmodified. The audit verified stable-tag chapter/experiment declarations and representative production routes. A production smoke test should repeat link and asset checks after deployment.

Automated accessibility checks cover semantic landmarks, focus styles, labels, alt text, and named links. They are a baseline, not a dedicated assistive-technology audit.
