# Visual renaissance QA report

**Status:** Candidate visual review recorded; full post-merge verification remains pending.

**Candidate review date:** 2026-10-19.

The candidate catalog snapshot contains five published books, 74 chapters, and 20 verified experiment anchors. Reconfirm these totals against the integrated catalog before finalizing release documentation. This report records candidate evidence only and is not an accessibility certification.

## Candidate decision

- **Selected direction:** Reading Room, with subject discovery cues from the Engineering Atlas; decision recorded 2026-10-19.
- **Decision owner:** Renaissance lead.
- **Implemented routes/surfaces reviewed:** home, library, book detail, subjects, and Little Explorers. Other routes remain in the candidate but are not represented in the capture matrix.
- **Visual reviewers:** Root and renaissance lead.

## Visual review

The candidate screenshot matrix contains 140 states: five routes (home, library, book detail, categories, Little Explorers) × seven widths (320, 360, 390, 768, 1024, 1440, 1920 px) × English/Korean × light/dark. The first capture reported `captures=140`, `anomalies=[]`, and `errors=[]` after forcing lazy-image decoding. Root and lead visually inspected home at 1440 px EN/light and 390 px KO/dark, including family illustration crops; library at 390 px EN/light; Little Explorers at 390 px EN/light; categories at KO/dark; and a mobile book detail. No blocking visual issue was reported in those inspected states.

The captured run used an equivalent temporary script. The repository command below is pending a fresh post-merge run; the earlier artifact set is candidate evidence, not final release evidence.

| View | Width / state | Artifact | Result |
| --- | --- | --- | --- |
| Home, library, book detail, categories, Little Explorers | 320, 360, 390, 768, 1024, 1440, 1920 px; EN/KO; light/dark | `/tmp/books-renaissance-qa-final` (140 PNGs) | Capture completed with no reported anomalies or errors; selected states visually inspected as described above. |
| Reader specimen | 390 and 1440 px; EN/KO; light/dark (8 states) | Separate local specimen capture; KO/dark screenshot settled | No findings reported. This is the isolated specimen, not a deployed route or textbook integration. |

## Behavior and accessibility checks

| Check | Method / command | Result | Evidence or issue |
| --- | --- | --- | --- |
| Screenshot capture and responsive state generation | Equivalent temporary capture script; 5 routes × 7 widths × 2 languages × 2 themes | 140 captures; zero reported anomalies and errors | `/tmp/books-renaissance-qa-final`; official repository capture script rerun pending after merge. |
| Language/theme state coverage in portal screenshots | Included in the 140-state matrix | Captured; only listed representative states received manual visual inspection | Full keyboard, storage, and accessibility review remains pending. |
| Storage-denied URL fallback regression | Targeted Playwright regression across 3 projects | 3/3 passed | Confirms this targeted regression only; full suite remains pending. |
| Navigation targets and direct chapter/lab links | Pending | Pending | Pending |
| Search, filters, URL state, empty/error states | Pending | Pending | A library language-query fix was made in review round 2; broader behavior review pending. |
| Keyboard order, skip link, focus visibility, native controls | Pending | Pending | Pending |
| Screen-reader names, landmarks, headings, status announcements | Pending | Pending | Pending |
| Text and non-text contrast; status not conveyed by color alone | Pending | Pending | A dark-family contrast issue found in round 1 was fixed; full contrast audit pending. |
| Zoom, text wrapping, touch targets, reduced motion | Pending | Pending | Pending |
| Story draft/proposal labels and print view | Pending | Pending | Pending |
| Existing project validation commands and full test suite | Pending | Pending | Run after candidate/main integration. |
| Reader specimen bilingual and light/dark behavior | Separate 8-state local capture | No findings reported | Local design specimen only; not deployed integration. |

## Findings

| Round | Severity | Route / area | Finding | Disposition / verification |
| --- | --- | --- | --- | --- |
| 1 | P1 | Subject navigation and dark family view | Subject navigation issue and dark family contrast issue | Fixed in candidate. Full regression and contrast review remain pending. |
| 2 | P2 | Library language query | Language query handling issue | Fixed; targeted storage-denied URL fallback regression passed 3/3 Playwright projects. |
| — | — | Other reviewed areas | No additional confirmed P0/P1 findings reported | Full review remains pending. |

Severity: P0 release blocker; P1 important defect; P2 in-scope improvement; P3 optional or future.

## Release evidence

- **Candidate screenshot run:** 140 PNGs in `/tmp/books-renaissance-qa-final`; capture reported zero anomalies and errors.
- **Repository capture command:** `node design/capture-matrix.cjs /tmp/books-renaissance-qa-final` — pending fresh post-merge run; do not treat this as the command used for the earlier temporary-script capture.
- **Targeted regression:** storage-denied URL fallback, 3/3 Playwright projects passed.
- **Full local build, validation, and test commands:** pending post-merge run.
- **Manual keyboard, print, error-state, and full contrast checks:** pending; no results recorded.
- **Remote CI status:** not checked; GitHub-hosted Actions are not authorized by default.
- **Physical-device status:** not checked.
- **Final reviewer and date:** pending final post-merge review.
