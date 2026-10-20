# Visual renaissance QA report

**Status:** Local candidate implementation, automated regression checks, and screenshot review completed; publication review remains pending.
**Integration base:** `9786903`, which merges the PMICBook v1.2.0 catalog update into the redesign branch.
**Review date:** 2026-10-20.

The integrated catalog contains five published books, 74 chapters, and 20 verified experiment anchors. PMICBook v1.2.0 is included in this catalog snapshot. This report records local candidate evidence; it is not an accessibility certification.

## Candidate decision

- **Selected direction:** Reading Room, with subject discovery cues from the Engineering Atlas; selected 2026-10-19.
- **Decision owner:** Renaissance lead.
- **Routes and surfaces:** home, library, book detail, subjects, experiments, learning paths, Learning Journey, roadmap, Little Explorers, feedback, and 404.
- **Visual reviewers:** Root and renaissance lead.

## Visual review

The official post-merge capture contains 140 screenshots for home, library, book detail, categories, and Little Explorers across seven widths (320, 360, 390, 768, 1024, 1440, and 1920 px), English/Korean, and light/dark themes. It reported `captures=140`, `anomalies=[]`, and `errors=[]`. After this capture, the renaissance lead inspected home at 1440 px EN/light and 390 px KO/dark, library at 390 px EN/light, Little Explorers at 390 px EN/light, and mobile book detail. The detail image visibly shows PMICBook v1.2.0 and its 2026-10-19 date. Root and lead had also inspected representative pre-merge renders, including the mobile family and categories views. The full matrix is captured; visual inspection remains representative rather than exhaustive.

A supplemental capture covers Learning Journey, roadmap, paths, and experiments at 390 and 1440 px in EN/light and KO/dark: 16 more screenshots, `anomalies=[]`, `errors=[]`. The script checks active language/theme, decodes images, and checks for missing images and horizontal document overflow. The lead inspected the mobile journey and roadmap, desktop paths, and mobile KO/dark experiments renders. The isolated reader specimen was then recaptured in eight width/language/theme states after adding its original ideal-circuit section; focused EN/light and KO/dark screenshots show the equation, units, labels, and diagram at 390 px.

| View | Width / state | Artifact | Result |
| --- | --- | --- | --- |
| Portal screenshot matrix | Five routes × seven widths × EN/KO × light/dark | `/tmp/books-renaissance-qa-postmerge` (140 PNGs) | Official post-merge capture completed with no reported anomalies or errors; selected states visually inspected as described above. |
| Supplemental routes | Four routes × two widths × EN/light and KO/dark | `/tmp/books-renaissance-qa-supplemental` (16 PNGs) | No reported anomalies or errors; four representative states inspected. |
| Reader specimen | 390 and 1440 px × EN/KO × light/dark (8 states) | `/tmp/books-renaissance-qa-final/reader-*.png` | No findings in state, anchor, formula, diagram-name, localization, or overflow checks after waiting for transitions. It is an isolated specimen, not a deployed route or textbook integration. |

Selected before/after screenshots are checked in for review. The before images show the original portal before the redesign; the after images show selected post-merge candidate states.

| Surface / state | Before | After |
| --- | --- | --- |
| Home, 1440 px | [before](../design/qa-screenshots/before-home-1440.png) | [EN/light](../design/qa-screenshots/after-home-1440-en-light.png) |
| Home, 390 px | [before](../design/qa-screenshots/before-home-390.png) | [EN/light](../design/qa-screenshots/after-home-390-en-light.png), [KO/dark](../design/qa-screenshots/after-home-390-ko-dark.png) |
| Little Explorers, 390 px | [before](../design/qa-screenshots/before-kids-390.png) | [EN/light](../design/qa-screenshots/after-kids-390-en-light.png) |
| Library, 390 px | — | [EN/light](../design/qa-screenshots/after-library-390-en-light.png) |
| Learning Journey, 390 px | — | [EN/light](../design/qa-screenshots/after-journey-390-en-light.png) |
| Roadmap, 390 px | — | [EN/light](../design/qa-screenshots/after-roadmap-390-en-light.png) |
| Learning paths, 1440 px | — | [EN/light](../design/qa-screenshots/after-paths-1440-en-light.png) |
| Experiments, 390 px | — | [KO/dark](../design/qa-screenshots/after-experiments-390-ko-dark.png) |
| Reader technical specimen, 390 px | — | [EN/light](../design/qa-screenshots/reader-model-390-en-light.png), [KO/dark](../design/qa-screenshots/reader-model-390-ko-dark.png) |

## Automated checks

| Check | Method / command | Result | Scope and limits |
| --- | --- | --- | --- |
| Python validation and catalog indexes | `PLAYWRIGHT_BASE_URL=http://127.0.0.1:18473/books/ npm test` | Python tests 106/106 passed; `check-indexes` current | Local candidate checks. |
| Playwright regression suite | Same `npm test` invocation | 75/75 passed across mobile, tablet, and desktop projects | Served from isolated local server on port 18473; SHA-256 of served `app.js` and `books.json` matched the candidate. |
| Targeted production-smoke checks | Playwright production-smoke set | 3/3 passed | Ran against the isolated candidate server; no remote deploy or production site was tested. |
| Storage-denied language fallback | Targeted regression in 3 Playwright projects | 3/3 passed | Confirms URL-based language fallback and query preservation with local storage unavailable. |
| Screenshot matrix | `PLAYWRIGHT_BASE_URL=http://127.0.0.1:18473/books/ node design/capture-matrix.cjs /tmp/books-renaissance-qa-postmerge` | Exit 0; `captures=140`, `anomalies=[]`, `errors=[]` | Five routes × seven widths × EN/KO × light/dark; isolated local candidate server. |
| Supplemental route capture | `PLAYWRIGHT_BASE_URL=http://127.0.0.1:18473/books/ node design/capture-supplemental.cjs /tmp/books-renaissance-qa-supplemental` | Exit 0; `captures=16`, `anomalies=[]`, `errors=[]` | Four further routes × two widths × EN/light and KO/dark. |
| Reader specimen check | `node design/reader/check.cjs /tmp/books-renaissance-qa-final` | Exit 0; `captures=8`, `findings=[]` | Local `file://` reader; checks formula, diagram alternatives, state, navigation anchors, names, and overflow. The test script ships with the isolated prototype, not the hosted site. |

The Playwright suite verifies keyboard operation and focus behavior for Learning Journey stage/strand controls and family story navigation; story print media and bilingual spreads; the 404 skip link; placeholder and published-badge contrast in both themes; and fit, primary navigation, named controls, and page errors across primary routes. The contrast assertions cover the search placeholder and published badge, not every text or non-text color combination.

## Manual and assistive technology review

- Visual inspection covered the representative states listed above. The 140-state and 16-state screenshot captures do not mean every image was individually inspected.
- The CSS reduced-motion rules were inspected; dynamic reduced-motion behavior was not verified in a browser run.
- Full keyboard, zoom, print-dialog, error-state, and whole-site contrast audits remain pending beyond the automated assertions described above.
- No screen reader or other assistive technology testing was performed.
- No physical-device testing was performed.

## Findings

| Review round | Severity | Area | Finding | Disposition |
| --- | --- | --- | --- | --- |
| 1 | P1 | Subject navigation and dark family view | Subject reachability and dark-family contrast defects | Fixed; subject navigation is covered by browser checks, and dark-family tiles were visually inspected. Full contrast audit remains pending. |
| 2 | P2 | Library language query | Language fallback did not preserve the expected URL state | Fixed; targeted storage-denied regression passed 3/3 projects. |
| Final review | P2 | PMIC documentation and test assumptions | Stale PMIC release wording and test assumptions | Updated/reviewed against integrated PMICBook v1.2.0 metadata. |
| Targeted reader review | P2 | Scientific reading specimen and handoff | Needed a real equation/diagram and explicit technical content integration rules | Added original ideal Ohm’s-law example, circuit, bilingual alternatives, and owner reconciliation gates; independent correctness review found the new math, circuit, and handoff sound. |
| Targeted reader review | P3 | Korean accessible group/note names | Some pre-existing labels remained English after switching to Korean | Fixed across the reader's group, navigation, and note labels; eight-state rerun checked Korean names. |
| — | — | Remaining reviewed scope | No other confirmed P0/P1 findings reported | Requirements, correctness, test/QA, docs/release, and security/privacy reviewers completed their scoped read-only passes; targeted re-review found the repairs sound. |

Severity: P0 release blocker; P1 important defect; P2 in-scope improvement; P3 optional or future.

## Release evidence

- **Local suite:** `PLAYWRIGHT_BASE_URL=http://127.0.0.1:18473/books/ npm test` — Python 106/106, current catalog indexes, Playwright 75/75 across mobile/tablet/desktop.
- **Served candidate identity:** SHA-256 checks for served `app.js` and `books.json` matched the integrated candidate.
- **Targeted smoke:** 3/3 passed against the isolated candidate server.
- **Official screenshot matrix:** `PLAYWRIGHT_BASE_URL=http://127.0.0.1:18473/books/ node design/capture-matrix.cjs /tmp/books-renaissance-qa-postmerge` — exit 0, 140 captures, no anomalies, no errors.
- **Supplemental screenshots:** `PLAYWRIGHT_BASE_URL=http://127.0.0.1:18473/books/ node design/capture-supplemental.cjs /tmp/books-renaissance-qa-supplemental` — exit 0, 16 captures, no anomalies, no errors.
- **Isolated reader:** eight-state browser rerun with no findings; targeted independent correctness review of the scientific specimen and handoff passed.
- **Remote CI:** not checked; no GitHub-hosted Actions were run.
- **Deployment / production site:** not tested.
- **Reviewers and date:** renaissance lead with scoped independent requirements, correctness, test/QA, docs/release, and security/privacy reviews; 2026-10-19–20. Publication review remains pending.
