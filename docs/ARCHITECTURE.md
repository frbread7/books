# Architecture

## Shape

My Library is a static site with no server-side runtime. The site/ directory is the complete Pages artifact. Flat route shells (index.html, library.html, categories.html, roadmap.html, paths.html, experiments.html, book.html, and feedback.html) share one small vanilla-JavaScript renderer and stylesheet. Catalog JSON is fetched at runtime from site/data/.

site/js/paths.js derives the site base from `document.baseURI` and resolves every internal route and data request from that base. The 404 shell declares the `/books/` project base explicitly so a nested invalid URL can still load assets and catalog data. Other flat pages keep relative paths. This supports the GitHub Pages project prefix without maintaining a second set of routes.

Canonical and Open Graph URLs are set at runtime; book details retain a normalized slug in their canonical URL and use book-specific title/description metadata. Flat pages keep relative stylesheet, script, favicon, and cover paths at the same base. The site does not depend on a framework, bundler, database, or remote font host.

## Sources of truth

- catalog/books/<id>.json — normalized records for explicitly registered books.
- catalog/categories.json — extensible categories and published knowledge-map connections.
- catalog/roadmap.json — future editorial proposals, separate from the published catalog.
- catalog/learning-paths.json — ordered references to published book and chapter IDs.
- schemas/book.schema.json and tools/book_factory.py — manifest shape and semantic validation.
- site/data/*.json — generated runtime indexes; regenerate with `python3 tools/book_factory.py generate`, then confirm with the read-only `validate` command.

The browser never treats roadmap entries as book records. Published totals derive only from registered records with status published.

## Boundaries

Each textbook remains independently authored, reviewed, released, licensed, and deployed. The portal stores descriptive metadata and outbound URLs, not chapter content. Published experiments carry evidence from a separate bounded live verifier that checks HTTPS status and the target fragment; the normal test suite validates that evidence offline. Learning-path steps resolve through a published book and an existing chapter, never a future-roadmap slug.

## Runtime and dependencies

Production is static GitHub Pages. Runtime has no third-party JavaScript or network calls other than fetching its own JSON and a reader's intentional outbound navigation. Browser automation is a development-only Playwright dependency. Feedback uses the repository's public GitHub Issues.

## Adding routes

Use a flat shell with data-page, ./css/style.css, ./js/paths.js, ./js/i18n.js, and ./js/app.js. Add interface copy in both dictionaries. Resolve internal links and data with MyLibraryPaths.siteUrl; never hardcode a leading slash. Add the route to the route-contract tests.
