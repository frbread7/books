# Contributing

My Library is the discovery portal for independently maintained books. Textbook chapters, simulators, releases, and book deployments belong in each book's own repository; this repository registers their verified metadata and links.

## Before making a change

- Read [the architecture](docs/ARCHITECTURE.md), [book series contract](docs/BOOK_SERIES_CONTRACT.md), and [upstream attribution](docs/UPSTREAM_ATTRIBUTION.md).
- For a new or updated textbook, follow [the Book Factory workflow](docs/BOOK_FACTORY.md) and [Adding a New Book](docs/ADDING_A_NEW_BOOK.md).
- Keep roadmap proposals in `catalog/roadmap.json`. A proposal becomes a registered in-progress book only when work actually starts, and a book becomes published only after its deployed content and release evidence are verified.
- Use original or properly licensed artwork and content. Preserve each book's own license and attribution.
- Do not add credentials or private user data. Feedback is submitted through public GitHub Issues; issue authors and content are visible publicly.

## Change catalog or navigation data

Edit the canonical files in `catalog/` and `catalog/books/`. Do not hand-edit generated browser indexes in `site/data/`. Regenerate them, then validate:

~~~sh
python3 tools/book_factory.py generate
npm test
~~~

Use `register` for a new book record and `update` to replace an existing record with the same stable ID. The command validates the manifest and updates derived indexes. It does not publish a book or change its status. Run `tools/verify_experiments.py` only for real deployed experiments; it makes bounded HTTPS requests and records successful live checks.

## Run checks and open a pull request

Install the project requirements and run the same validation and browser suite used by CI:

~~~sh
python3 -m pip install -r requirements.txt
npm ci
npx playwright install chromium
npm test
~~~

Playwright covers mobile, tablet, and desktop viewports and the `/books/` project-site prefix. Describe the user-visible change, catalog/schema impact, and checks run in the pull request. Pull requests run validation but do not deploy. A validated push to `main` deploys `site/` to GitHub Pages.

The feedback form creates public issues. Do not include sensitive or confidential information in a report.
