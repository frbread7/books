# My Library

**Interactive Engineering & Knowledge Books**

My Library is a static, bilingual bookshelf for independently maintained textbooks. PMICBook, WATBook, ProcessIntegrationBook, and FabControlBook are published books. The Mathematics collection and Family Learning Journey add editorial maps and proposals without treating plans as publications.

- Live target: https://frbread7.github.io/books/
- Source: https://github.com/frbread7/books
- Published books: [PMICBook](https://frbread7.github.io/pmicbook/), [WATBook](https://frbread7.github.io/watbook/), [ProcessIntegrationBook](https://frbread7.github.io/processintegrationbook/), and [FabControlBook](https://frbread7.github.io/fabcontrolbook/)

## Work locally

Requirements: Python 3.12+, Node.js 20+, npm.

~~~sh
python3 -m pip install -r requirements.txt
npm ci
npx playwright install chromium
npm run validate
npm run test:e2e
~~~

The browser tests exercise the actual GitHub Pages project prefix (/books/) at mobile, tablet, and desktop sizes. They use Playwright and Chromium. On Linux systems missing browser libraries, run `npx playwright install --with-deps chromium`. The local preview server starts automatically by Playwright.

`npm run validate` is read-only and fails if committed generated indexes do not match the catalog. After editing catalog inputs, run `python3 tools/book_factory.py generate` before validation.

To preview directly:

~~~sh
python3 tests/serve.py
~~~

Open http://127.0.0.1:4173/books/.

## Add a book

Each textbook stays in its own repository and deploys independently. Start with docs/BOOK_FACTORY.md, then follow docs/ADDING_A_NEW_BOOK.md. A manifest alone never marks a book as published: its live site, content review, and release evidence must pass and be recorded.

Contributions to the portal follow [CONTRIBUTING.md](CONTRIBUTING.md).

## Project map

- site/ — deployable static Pages artifact; flat HTML routes share one data-driven app.
- catalog/books/ — one validated record per book explicitly registered with the portal.
- catalog/ — subject maps, reading paths, editorial roadmaps, the versioned concept map, and the separate Kids & Family story collection.
- schemas/book.schema.json — manifest schema.
- schemas/learning-journey.schema.json — curriculum-source, stage, strand, and concept-map schema.
- schemas/kids-family.schema.json — bilingual family theme, story draft, proposal, and source-note schema.
- tools/book_factory.py — read-only validation, index generation, and safe register/update command.
- tools/reference_intelligence.py — incremental, deterministic upstream source inventory and differentiation/provenance checks.
- tools/verify_experiments.py — bounded live HTTPS checks for published experiment links and fragments.
- book-starter/ and tools/scaffold_book.py — independent textbook starter.
- tests/ — data/static checks and project-prefix Playwright journeys.

See docs/PRODUCT_VISION.md, docs/ARCHITECTURE.md, docs/ROADMAP.md, docs/USER_MANUAL.md, docs/DEPLOYMENT.md, and docs/BOOK_FACTORY.md.
For lifelong learning sources and specifications, see docs/LEARNING_JOURNEY.md, docs/CURRICULUM_SOURCES.md, docs/MATHEMATICS_ROADMAP.md, docs/CURIOSITYBOOK_SPEC.md, docs/KIDS_FAMILY_PORTAL_SPEC.md, and docs/HEAVYVEHICLEBOOK_PILOT.md.
For upstream change monitoring, differentiation, and file-level rights handling, see docs/REFERENCE_INTELLIGENCE.md, docs/REFERENCE_OVERLAP_FRAMEWORK.md, docs/COPYRIGHT_AND_PROVENANCE.md, and docs/PROVENANCE_AUDIT.md.

## License and reference

Portal implementation code is MIT-licensed. My Library-authored catalog descriptions, editorial roadmap, and documentation are offered under CC BY 4.0 unless an individual record states otherwise. The bilingual story prose in `catalog/kids-family.json` is a public editorial preview with no reuse license granted; its SVG preview art follows the separate software license. A content license must be selected before publication. Individual textbook content retains the license in its independent repository.

My Library was implemented independently after auditing geniuskey/books. No upstream catalog records, prose, covers, screenshots, analytics, or backend configuration are copied. See docs/UPSTREAM_ATTRIBUTION.md.
