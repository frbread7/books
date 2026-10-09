# Reference implementation audit

Audit target: geniuskey/books (https://github.com/geniuskey/books), source revision `8473a359574061e82f5a6c2b1c61a982fa46738a` on main, reviewed 2026-10-09. The audit covered actual source files, catalog structures, scripts, skill material, assets, and hosting configuration, not only README.

Revision boundary: the source findings above are pinned to that inspected commit. I separately checked current upstream HEAD `108b0bd81a8496d445c51e3ae0052dcea2a9bcd3` on 2026-10-09. The delta adds TaxBook and EconomicsBook catalog/discovery records, experiment catalog data, two simulator screenshots, and cover/map rendering changes. The license file and the reviewed hosting, analytics, shared-skill, and route-check paths are unchanged across these revisions; the delta does not change the independent-static-portal architecture or the deployment/licensing findings below. The additional content is not reused.

## Useful architectural concepts

- The reference is a static, data-driven portal: the homepage and data/books.json feed its bookshelf rather than storing every book card in a page.
- Its page family includes library, category/field views, a knowledge map, roadmap, reading paths, interactive-experiment discovery, and feedback.
- css/style.css and JavaScript render books, filters, and views from data. Recognizable covers/spines and a wafer-map motif make semiconductor subjects legible.
- tools/check-routes.py and data-check workflows show the value of validating routes and catalog records before publishing.
- .agents/skills/book-series-common/ contains series conventions and audit guidance. Those conventions were reviewed but not adopted wholesale.
- The upstream root has LICENSE.md. Its distinction between MIT code and CC BY 4.0 text/catalog material matters when reusing anything.

### Source evidence

- `index.html`, `js/core.js`, `js/home.js`, and `data/books.json` compose the home view and data-driven bookshelf. `js/library.js` supplies catalog search/filtering; `field/` pages plus `js/field.js`, `js/field-index.js`, and `js/field-maps.js` provide subject navigation and knowledge maps.
- `roadmap.html`/`js/roadmap.js`, `paths.html`/`data/paths.json`, and `simulators.html`/`js/discovery.js` implement roadmap, learning paths, and simulator discovery. Experiment detail data is split across `data/experiment-catalog.json` and generated `data/discovery.json`.
- `css/style.css`, `js/covers.js`, `js/wafer.js`, `js/field-art.js`, `favicon.svg`, `og.png`, and `img/sims/` contain the presentation and visual assets. Page shells use semantic landmarks and labeled controls; the shared stylesheet includes visible focus treatment and narrow-screen layout rules.
- `tools/check-routes.py`, `tools/check-discovery.py`, `tools/check-models.cjs`, `tools/build-fields.py`, and `.github/workflows/check-discovery.yml` provide static route, discovery, and model-reference checks. The workflow checks out `geniuskey/yieldbook` and `geniuskey/computerbook`, so it is coupled to upstream repositories.
- `.agents/skills/book-series-common/SKILL.md` and `.agents/skills/book-series-common/scripts/audit.py` prescribe and audit upstream canonical URLs, domain links, analytics, feedback context, and book-series conventions.
- `CNAME`, `index.html`, per-route `*/index.html`, `sitemap.xml`, and `robots.txt` establish the custom-domain SEO/deployment identity. `data/feedback-config.json`, `js/feedback-inbox.js`, `worker/wrangler.jsonc`, `worker/auth.js`, and `worker/migrations/` configure an authenticated feedback inbox using a Cloudflare Worker, D1, Google identity, and origin restrictions.
- `LICENSE.md`, `LICENSE-MIT`, and `LICENSE-CC-BY-4.0` separate executable code from prose/catalog assets. `img/sims/` screenshots follow the source textbooks' licenses as described in `LICENSE.md`; bundled fonts are not present, and font CSS references Google-hosted sources.

## Deployment, identity, and security findings

- The reference is configured for its own custom domain books.euiyun.com, including canonical and sitemap references, CNAME, and root-relative route/data fetches. Those do not work unchanged under the /books/ project-site prefix.
- Production configuration includes an upstream analytics beacon/token, Google administrator identity, and a Cloudflare Worker/D1 feedback path. The shared series skill and route checks assume original-domain/analytics conventions. These are unsuitable for this project.
- Reference workflows include checks tied to other named book repositories. They do not provide a clean, repository-independent GitHub Pages Actions deployment for this project.
- The catalog and generated discovery data describe books outside this collection; reusing that material would incorrectly imply ownership or publication.
- The reference is Korean-first and includes broad navigation states. My Library uses an English-default bilingual interface and represents only verified published books.

## Licensing and reuse decision

The reference LICENSE.md labels software code MIT, most prose/catalog/social-preview assets CC BY 4.0, and simulator screenshots as governed by originating textbook licenses; fonts carry their own notices. This project does not need to transplant upstream components, so it is an independent implementation with no copied catalog text, covers, screenshots, generated discovery data, analytics, or backend code. The design pattern is attributed in docs/UPSTREAM_ATTRIBUTION.md. No upstream MIT notice is required for code that was not copied; the upstream license remains linked there.

## Resulting choices

- Keep the useful data-driven bookshelf, search, roadmap, learning-path, and knowledge-map concepts.
- Keep books in independent repositories and deploy the portal as static Pages.
- Centralize project-prefix URL resolution in site/js/paths.js.
- Use project-owned branding and a new PMICBook cover drawn for this portal.
- Use GitHub Issues for feedback and omit analytics, Cloudflare, Google admin configuration, and credentials.
- Validate manifests and actual /books/ browser journeys before deployment.

## Evidence boundary

The PMICBook entry is based on stable v1.0.0 source and public release, chapter index, license/attribution documents, and production routes checked 2026-10-09. Local PMICBook working files were not used as an authority and were not modified. Four experiment anchors were confirmed in stable chapter source. Representative production pages returning HTTP 200 is a route check; it does not establish that every PMICBook JavaScript interaction was tested during this portal build.
