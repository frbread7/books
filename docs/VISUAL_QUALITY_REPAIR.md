# Visual quality repair audit

**Status:** Candidate implementation, local rendered-image review, focused checks, and the full local `npm test` suite are complete. The independent GPT-6 Sol High review (`gpt-6-sol`, High) approved the candidate; GPT-6.1 Sol was unavailable due to model capacity. No publication is planned or reported.
**Baseline:** repository commit `87e8161`.
**Scope:** visual quality evidence and follow-up for the reported book-cover and tag legibility concerns. The exact context of the user's screenshot is unknown: route, viewport, language, theme, content/catalog, and deployed build have not been identified.

This audit is distinct from the prior representative review in [visual renaissance QA](VISUAL_RENAISSANCE_QA.md). Baseline capture automation produced 168 states under `/tmp/books-visual-audit-baseline`; this records matrix size only. It is not a full pixel review or a claim that every state passed. Captures and automated overflow checks establish that artifacts were produced and some conditions were checked; they do not establish that every screenshot was visually inspected or that the rendered design passed.

## Baseline evidence

- The checked-in shelf comparison includes before/after home and library captures at 390 px and 1440 px, with close views. The inspected 390 px home close-up shows full covers and portions of the next book at the horizontal shelf edge. That partial next-book visibility is consistent with the shelf's documented horizontal browsing behavior; it is not evidence of document-level horizontal overflow. See [mobile home close-up](shelf-comparison/assets/after-home-390-close.png) and [desktop home close-up](shelf-comparison/assets/after-home-1440-close.png).
- Current FabControlBook and ProcessIntegrationBook source SVG title bounding boxes are inside their viewboxes in Chromium. This checks source geometry, not perceived title size or legibility in every rendered context.
- Shelf titles and the current visible shelf strings are complete in the checked captures. This does not establish that a different, unidentified user screenshot uses the same route, dimensions, language, theme, catalog, or build.
- Current book-detail cover sizing is 72 px at widths up to 360 px and 90 px up to 600 px. The five detail and roadmap tag variants use 10–11 px text. Baseline measured text contrast is 6.53:1 in light and 8.29:1 in dark; measured tag-fill separation is 1.02:1 and 1.39:1 respectively. The reported baseline tag text has no WCAG AA text-contrast failure. Fill-separation values are not text-contrast ratios and do not establish non-text contrast conformance.
- Independent baseline inspection found roadmap prerequisite links at 1.77:1 contrast and touch targets that are too small: P1 findings. The priority number measures 2.56:1 contrast: P2 finding. These are separate from the measured tag-text ratios above.
- At 200% browser zoom, the ProcessIntegrationBook detail title fragments and a Learning Journey stage label clips: P2 findings. The initial cover scale is small, tags are 10–11 px, and tag surfaces are insufficiently distinct; the repair contract records enlarged covers and at least 12 px tags with distinct surfaces. Candidate behavior remains unverified.
- Baseline evidence is available from an image matrix of 168 states in `/tmp/books-visual-audit-baseline`. Matrix capture does not imply exhaustive image-by-image inspection; findings above are the states and defects specifically confirmed by review.
- The root workflow run `39862080048` for remote commit `87e8161` reported a failed post-deploy browser smoke. A later manual, read-only run of the same smoke passed. The cause of the discrepancy is unknown; neither result identifies or validates the local visual repair candidate. No workflow was rerun for this audit.
- The prior QA document records a stale pre-shelf screenshot trap: older screenshots may depict a layout that is no longer current. Match artifacts to commit and route before using them as current-state evidence.

## Defect register

Severity: P0 release blocker; P1 important defect; P2 in-scope improvement; P3 optional or future. Baseline findings and candidate evidence are kept separate. Candidate statements refer to the local uncommitted source hashes listed below.

| ID | Severity | Area | Baseline finding | Candidate evidence and status |
| --- | --- | --- | --- | --- |
| VQ-1 | P2 | Book-detail cover scale | Baseline cover was 72 px at widths ≤360 px and 90 px up to 600 px. | Enlarged while preserving complete artwork with `object-fit: contain`. All five detail pages were inspected at narrow and wide widths; no cover crop or title collision was seen. Candidate review complete. |
| VQ-2 | P2 | Detail and roadmap tags | Baseline text was 10–11 px; tag fill separation measured 1.02:1 light / 1.39:1 dark. Baseline text contrast was 6.53:1 light / 8.29:1 dark. | Tags are at least 12 px with a visible fill and border. Across 1,036 detail-tag and 1,215 roadmap-tag samples, minimum text contrast was 8.23:1; minimum fill/page separation was 1.26:1 detail and 1.39:1 roadmap; minimum border/page separation was 2.91:1 and 2.95:1. Candidate review complete. Fill separation is not text contrast or a WCAG non-text conformance claim. |
| VQ-3 | P1 | Roadmap prerequisite links | Baseline link contrast was 1.77:1 and target size was inadequate. | Across 351 samples, minimum text contrast was 9.75:1 and minimum target size was 85.06 × 30 px. The browser check also verifies ≥24 px spacing between adjacent target centers. Candidate image review complete; focused rerun passed (12 tests across mobile/tablet/desktop) on unchanged app source hashes. |
| VQ-4 | P2 | Priority number | Baseline contrast was 2.56:1. | Across 270 samples, minimum text contrast was 6.93:1. Candidate review complete. |
| VQ-5 | P2 | Narrow-width reflow proxy | At the earlier 200% zoom setup, the ProcessIntegrationBook title fragmented and a Learning Journey stage label clipped. | The title and six Journey stages fit at 195 CSS px with DPR 2, and page-level overflow was not detected. This is a narrow-layout proxy only; native browser/OS 200% zoom is not certified. Focused rerun passed (12 tests across mobile/tablet/desktop) on unchanged app source hashes. |
| VQ-6 | P3 | Fab/Process SVG title geometry | Source title bounding boxes fit their SVG viewboxes, but geometry alone did not establish rendered legibility. | FabControlBook and ProcessIntegrationBook cover art was inspected in detail and shelf contexts; full cover art remains visible. No catalog artwork or title data changed. |
| VQ-7 | Unknown | User-reported screenshot | Route, width, language, theme, catalog, and build are unavailable. | The user's specific screenshot cause remains unknown; no specific crop cause is claimed. |
| VQ-8 | P2 | Shelf edge behavior | At mobile widths, partial visibility of the next book is intentional internal shelf scrolling. | The current diagnostics exclude only the `.bookcase-viewport` internal scroller from page-overflow checks. Across 226 candidate captures, there were no page-overflow, broken-image, console, or page errors. Candidate review complete. |

## Candidate repair and rendered evidence

The local candidate changes detail-cover sizing, tag size/surface, roadmap link/priority tokens and touch spacing, and narrow-layout flex/wrapping. A display-title helper adds break opportunities at CamelCase boundaries without altering the underlying title string. Catalog facts, scientific prose, publication status, route behavior, and artwork were not changed.

The final local capture used a server process started from this worktree on `127.0.0.1:18473`; served asset hashes matched the checked-out files. The capture harness uses `document.documentElement.clientWidth` as the layout viewport, records `innerWidth` and `visualViewport.width` separately, and checks print states as well. The manifest records 226 unique captures, 0 failures, 0 per-record errors, and 0 per-record problems. All 226 PNGs exist. This automated result is diagnostics only, not a visual pass.

Evidence artifacts:

- Candidate gallery: `/tmp/books-visual-quality-candidate-20261023-final-owned18473/index.html`
- Manifest: `/tmp/books-visual-quality-candidate-20261023-final-owned18473/manifest.json`
- Contact-sheet index: `/tmp/books-visual-quality-candidate-20261023-final-owned18473/contact-sheets/index.html` (48 grouped sheets, top and full views)
- Computed style metrics: `/tmp/books-visual-quality-candidate-20261023-complete/review-crops/computed-review-metrics.json`
- Candidate CSS SHA-256: `bf84fb439ec28c1ebc576e54df7d2759668909fbb400e630f369c1d382e3fb5c`
- Candidate JS SHA-256: `d620b873934d87fd158c10ccbc3c39a1f14d79337e78cec469fa6c3f7f6a9056`

Full-resolution candidate crops were visually inspected for cover/title fit, tag surfaces, target appearance, narrow Journey controls, and story spreads:

- `/tmp/books-visual-quality-candidate-20261023-final-owned18473/review-crops/detail-process-en-light-320-hero.png`
- `/tmp/books-visual-quality-candidate-20261023-final-owned18473/review-crops/detail-pmic-ko-dark-320-tags.png`
- `/tmp/books-visual-quality-candidate-20261023-final-owned18473/review-crops/roadmap-ko-dark-390-card.png`
- `/tmp/books-visual-quality-candidate-20261023-final-owned18473/review-crops/roadmap-ko-dark-390-prerequisite-links.png`
- `/tmp/books-visual-quality-candidate-20261023-final-owned18473/review-crops/journey-en-light-195-stage-controls.png`
- `/tmp/books-visual-quality-candidate-20261023-final-owned18473/review-crops/explorers-en-light-390-first-spread.png`
- `/tmp/books-visual-quality-candidate-20261023-final-owned18473/review-crops/explorers-en-light-390-next-spread.png`

Direct baseline/candidate pairs:

- PMIC detail: `/tmp/books-visual-audit-baseline/pmic-390-en-light.png` and candidate `detail-pmicbook-en-light-390.png`.
- Fab detail: `/tmp/books-visual-audit-baseline/fab-390-ko-dark.png` and candidate `detail-fabcontrolbook-ko-dark-390.png`.
- Process detail: `/tmp/books-visual-audit-baseline/process-768-en-light.png` and candidate `detail-processintegrationbook-en-light-768.png`.
- Journey and roadmap: compare matching route/language/theme/width filenames in `/tmp/books-visual-audit-baseline` and the candidate gallery. The selected calculus/prerequisite and no-authored-material Journey states are separately captured in the final gallery.

Screenshots were checked by route-family contact sheets and full-resolution views of materially changed states. The final two deep-linked Journey states were also inspected at full resolution. Contact-sheet size is evidence of coverage, not proof of a visual pass. A temporary element-crop utility displayed a skip-link overlay while scrolling to a Journey panel; that crop was excluded, and the authentic full-page screenshot was used for review.

## Local validation

- `node --check tests/e2e/visual-quality.spec.js` and `node --check design/capture-visual-quality.cjs` passed.
- Focused command: `npm run test:e2e -- --grep 'detail covers decode uncropped|topic chips remain readable|roadmap links and priority labels|195px viewport reflows learning journey stages without clipping'` — **12 passed** across mobile, tablet, and desktop Playwright projects in 2.8 minutes. This covers detail titles/covers, detail and roadmap tags, roadmap contrast/target spacing, and the 195 CSS px Journey proxy.
- Full command: `npm test` — Python validation **106 passed** in 8.048 s; generated catalog indexes current; Playwright **111 passed, 3 skipped** across three projects in 4.7 minutes. The three skips are `tests/e2e/production-smoke.spec.js` (one per project), which targets the deployed site and was not run. Local Playwright status is recorded in `test-results/.last-run.json` as `passed` with no failed tests.
- Automated browser and style checks are supporting evidence; candidate images were reviewed separately. Native browser/OS zoom, physical devices, and screen readers were not exercised.

| State | Baseline | Candidate | Visual inspection |
| --- | --- | --- | --- |
| Detail, narrow, EN/light and KO/dark | 320/390 px PNGs in `/tmp/books-visual-audit-baseline` | Five books at 320/360/390 px, EN/KO and both themes | Full-resolution PMIC and Process crops; all five detail groups inspected in contact sheets |
| Detail, tablet/desktop | 768 px baseline PNGs | 768/1024/1440/1920 px, EN/light for all five books | Wide detail contact sheets and Process crop inspected |
| Roadmap and detail tags | EN/KO, light/dark in baseline matrix | Detail at 320/360/390/768/1440; Roadmap at 320/360/390/768/1024/1440/1920 | Candidate light/dark contact sheets and full-resolution tag/roadmap crops inspected |
| Journey and learning paths | Baseline journey/concept and path screenshots | Narrow/tablet/desktop; default, advanced calculus/prerequisite, and no-authored-material states; separate paths page | 195 px full page and stage controls; both added deep-link states; path page contact sheets |
| Home/library/search/filter/empty | Baseline route captures | 320/360/390/768/1024/1440/1920; search, filter, and empty states; EN/KO themes at 390 | Home/library contact sheets and synthetic catalogs inspected |
| Subjects/experiments/family/feedback/404 | Baseline route captures | Bilingual themes at 390 and responsive tablet/desktop; story, next spread, print, and synthetic variants | Contact sheets plus full-resolution actual story spreads inspected |

## Coverage matrix

Record route, viewport, language, theme, content length/catalog variant, artifact path, and checks for each reviewed state. Select responsive widths appropriate to the changed layout, including narrow widths around 320/360/390 CSS px and relevant tablet/desktop widths. Include long English and Korean titles and synthetic varied catalog sizes when the changed UI is data-driven.

| Page family/state | Candidate responsive coverage | Language/theme coverage | Long/varied content | Diagnostics and image review |
| --- | --- | --- | --- | --- |
| Home and Library, including search/filter/empty | 320/360/390/768/1024/1440/1920; four synthetic catalog sizes | EN/KO and light/dark at 390; EN/light at all other widths | 5/10/25/50-book synthetic catalog | Page overflow, image decode/fit, shelf-scroller separation; home/library and synthetic contact sheets reviewed |
| Five book details | 320/360/390/600/768/1024/1440/1920 in targeted browser check; capture matrix includes 320/360/390/768/1024/1440/1920 | EN/KO and both themes at 320/360/390; wider capture EN/light | Long bilingual catalog titles and 50-book synthetic detail | Title/cover geometry, tag size/contrast/surface, page overflow, decoded uncropped images; detail contact sheets and full-resolution crops reviewed |
| Roadmap | 320/360/390/768/1024/1440/1920 | EN/KO, light/dark for 320/360/390/768; KO/dark at 1024/1440/1920 | Long planned-book titles and tags | Link/priority contrast and target geometry; contact sheets and crops reviewed |
| Learning Journey | 195/320/360/390/768/1024/1440/1920 | EN/light and KO/dark responsive states; all EN/KO/light/dark at 390 | Default, planned materials, advanced math/revisit, no-authored-material state | Stage/panel fit, URL-selected states, paths links; full-resolution review of 195 and deep links |
| Subjects, experiments, learning paths, Little Explorers, feedback, 404 | 320/390/768/1024/1440/1920 as applicable | EN/KO and light/dark at 390; EN/light on wider states | Selected subject, story and next spread, print, no fake catalog records | Full-page overflow, image decode, rendered screenshot inspection; story spread crops reviewed |

## Independent adverse review

**Baseline review:** independent baseline findings are recorded above.

**Candidate review — initial verdict:** A fresh independent `gpt-6-sol` reviewer using High reasoning completed review on 2026-10-23 against base commit `87e816125761172d6f2f463b54a6c0f0c16395c9`, the frozen candidate diff, and final capture manifest SHA-256 `8ce84232caa0ffb95a35071a446a2b035c5d2d871a129f6074b8a35c72f5cddf`. This was GPT-6 Sol High; GPT-6.1 Sol was unavailable due to model capacity.

The review covered the candidate diff, the 226-state gallery and grouped contact sheets, plus full-resolution changed-family images and selected crops for book details, roadmap, Learning Journey, shelves, and Little Explorers story spreads. **Verdict: approve; no P0 or unresolved P1 findings.** The first pass found P2 audit inconsistencies in the VQ-3 and VQ-5 status text; those now report the completed 12-test focused rerun. A subsequent targeted pass found the stale “Candidate review: pending” placeholder; this section records the reviewer and first-pass verdict. Targeted re-review of these final documentation updates passed.

The reviewer did not inspect every one of the 226 PNGs individually. Native browser/OS zoom, physical devices, screen readers, and production behavior were not exercised; those limitations remain explicit. This review is separate from the implementation-owner inspection and the earlier baseline review.

## Publication gate

Local-only until candidate images have been inspected, applicable coverage and DOM checks are recorded, defects are dispositioned, and the independent adverse review is complete. Remote deployment and production behavior are outside this audit. No GitHub Actions run, push, or publication is authorized or reported here. Any later publication decision requires its own explicit authorization and evidence.
