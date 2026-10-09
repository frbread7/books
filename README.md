# My Library

**Interactive Engineering & Knowledge Books**

My Library is a static, bilingual bookshelf for independently maintained textbooks. PMICBook is the first published book. Future semiconductor titles are editorial proposals on the roadmap; they are not listed as published books.

- Live target: https://frbread7.github.io/books/
- Source: https://github.com/frbread7/books
- First book: [PMICBook](https://frbread7.github.io/pmicbook/)

## Work locally

Requirements: Python 3.12+, Node.js 20+, npm.

~~~sh
python3 -m pip install -r requirements.txt
npm ci
npm run validate
npm run test:e2e
~~~

The browser tests exercise the actual GitHub Pages project prefix (/books/) at mobile, tablet, and desktop sizes. They use Playwright and Chromium. The local preview server starts automatically by Playwright.

To preview directly:

~~~sh
python3 tests/serve.py
~~~

Open http://127.0.0.1:4173/books/.

## Add a book

Each textbook stays in its own repository and deploys independently. Start with docs/BOOK_FACTORY.md, then follow docs/ADDING_A_NEW_BOOK.md. A manifest alone never marks a book as published: its live site, content review, and release evidence must pass and be recorded.

## Project map

- site/ — deployable static Pages artifact; flat HTML routes share one data-driven app.
- catalog/books/ — one validated record per book explicitly registered with the portal.
- catalog/ — subject maps, learning paths, and the editorial roadmap.
- schemas/book.schema.json — manifest schema.
- tools/book_factory.py — validation and safe register/update command.
- book-starter/ and tools/scaffold_book.py — independent textbook starter.
- tests/ — data/static checks and project-prefix Playwright journeys.

See docs/PRODUCT_VISION.md, docs/ARCHITECTURE.md, docs/ROADMAP.md, docs/USER_MANUAL.md, docs/DEPLOYMENT.md, and docs/BOOK_FACTORY.md.

## License and reference

Portal implementation code is MIT-licensed. My Library-authored catalog descriptions, editorial roadmap, and documentation are offered under CC BY 4.0 unless an individual record states otherwise. Individual textbook content retains the license in its independent repository.

My Library was implemented independently after auditing geniuskey/books. No upstream catalog records, prose, covers, screenshots, analytics, or backend configuration are copied. See docs/UPSTREAM_ATTRIBUTION.md.
