# Architecture

## Shape

My Library is a static site with no server-side runtime. The site/ directory is the complete Pages artifact. Flat route shells (index.html, library.html, categories.html, roadmap.html, learning-journey.html, kids-family.html, paths.html, experiments.html, book.html, and feedback.html) share one small vanilla-JavaScript renderer and stylesheet. Catalog and editorial JSON is fetched at runtime from site/data/.

site/js/paths.js derives the site base from `document.baseURI` and resolves every internal route and data request from that base. The 404 shell declares the `/books/` project base explicitly so a nested invalid URL can still load assets and catalog data. Other flat pages keep relative paths. This supports the GitHub Pages project prefix without maintaining a second set of routes.

Canonical and Open Graph URLs are set at runtime; book details retain a normalized slug in their canonical URL and use book-specific title/description metadata. Flat pages keep relative stylesheet, script, favicon, and cover paths at the same base. The site does not depend on a framework, bundler, database, or remote font host.

## Sources of truth

- catalog/books/<id>.json — normalized records for explicitly registered books.
- catalog/categories.json — extensible categories and published knowledge-map connections. Map node labels and topic tags support bilingual `{en, ko}` values; legacy single-language strings remain valid where appropriate.
- catalog/roadmap.json — future editorial proposals, separate from the published catalog.
- The seven proposed mathematics titles in catalog/roadmap.json have a typed prerequisiteIds graph. These suggested-preparation edges are validated for known IDs and acyclicity, then rendered as roadmap links; they do not create book records or gates.
- catalog/learning-paths.json — ordered references to published book and chapter IDs.
- catalog/learning-journey.json — versioned references, bilingual guidance stages/strands, and stable prerequisite/revisit concept IDs. Concepts stay separate from books.
- catalog/kids-family.json — separate bilingual interest taxonomy, family story drafts, scoped editorial proposals, source notes, and links to existing preschool Learning Journey concepts. It is not a book manifest or roadmap record.
- schemas/book.schema.json and tools/book_factory.py — manifest shape and semantic validation.
- schemas/learning-journey.schema.json — learning-map shape. The Book Factory validates sources, graph edges, stage/strand coverage, roadmap targets, and published chapter references before generating indexes.
- schemas/kids-family.schema.json — strict family collection shape; the Book Factory checks concept IDs, existing explicit revisit continuations, cited sources, proposal boundaries, and unpublished pilot status.
- site/data/*.json — generated runtime indexes; regenerate with `python3 tools/book_factory.py generate`, then confirm with the read-only `validate` command.

The browser never treats roadmap entries as book records. Published totals derive only from registered records with status published.

The roadmap has separate semiconductor, mathematics, and family-project arrays. Active editorial work can remain `status: planned` until it is registered, at which point its proposal is removed. Homepage proposal totals include all roadmap sections; published counts derive only from registered manifests with completed publication evidence. Kids & Family themes, drafts, and its five scoping cards stay in the separate family collection and do not change either count.

## Boundaries

Each textbook remains independently authored, reviewed, released, licensed, and deployed. The portal stores descriptive metadata and outbound URLs, not chapter content. Published experiments carry evidence from a separate bounded live verifier that pins validated public addresses, honors configured proxy and CA behavior, and checks HTTPS status and the target fragment; the normal test suite validates that evidence offline. Learning-path steps resolve through a published book and an existing chapter, never a future-roadmap slug.

## Runtime and dependencies

Production is static GitHub Pages. Runtime has no third-party JavaScript or network calls other than fetching its own JSON and a reader's intentional outbound navigation. Browser automation is a development-only Playwright dependency. Feedback uses the repository's public GitHub Issues.

## Adding routes

Use a flat shell with data-page, ./css/style.css, ./js/paths.js, ./js/i18n.js, and ./js/app.js. Add interface copy in both dictionaries. Resolve internal links and data with MyLibraryPaths.siteUrl; never hardcode a leading slash. Add the route to the route-contract tests. Keep family interests and story drafts in their own local static dataset; do not introduce accounts, profiles, saved progress, external trackers, or back-end storage.
