# Book Factory

The Book Factory is a small contract and registration command, not a CMS. Every textbook is authored, reviewed, released, and hosted in its own repository. My Library registers metadata and external links.

## Contract

The canonical v1 shape is schemas/book.schema.json; semantic checks live in tools/book_factory.py. A record includes stable ID and slug, bilingual display metadata, subject and tags, status, public destination URLs when available, languages, version/date, chapter count/index, experiments, prerequisite/related book IDs, cover and color theme, license attribution, and publication evidence. Only `in-progress` records may omit top-level `repositoryUrl` and `productionUrl`; `languageUrls` requires `productionUrl`. In-progress scaffolds may retain the `CHOOSE-AND-RECORD` license placeholder; published records reject placeholders and explicit no-license statements.

Install the small validator with python3 -m pip install -r requirements.txt. JSON Schema catches structural and format errors; Python checks enforce cross-record IDs, category/chapter links, production-host boundaries, and generated-index integrity.

Chapter URLs must use HTTPS and, when a production URL exists, remain under its host and path. In-progress chapter and experiment routes without a production URL are prospective metadata, not live links; the portal does not render them on the book detail page. Experiments require an existing chapter ID and an HTTPS URL with a fragment. Every experiment in a published book must also carry successful live-check evidence: exact checked URL, ISO date, HTTP 200, fragment present, response SHA-256, full 40-character deployment commit SHA, a caller-attestation note, and a short evidence note. The checker validates SHA format but does not confirm repository membership; obtain and record the SHA from the successful Pages deployment metadata. The cover must be stored under site/assets/ in this portal. Related/prerequisite IDs must refer to registered books; empty lists are valid, and a book cannot list itself. Roadmap proposals belong in catalog/roadmap.json, not catalog/books/.

`version` and `publicationEvidence.releaseUrl` identify the formal book release. `publicationEvidence.productionRevision` separately identifies the source commit behind the currently deployed Pages site, so it can advance without creating or implying a new stable textbook release.

## Commands

Validate all manifests and confirm generated browser indexes exactly match canonical inputs. This command performs no writes:

~~~sh
python3 tools/book_factory.py validate
~~~

When catalog manifests, categories, roadmap, or learning paths change, explicitly regenerate the browser indexes before committing:

~~~sh
python3 tools/book_factory.py generate
~~~

For actual live experiment checks, use the bounded HTTPS verifier. It restricts requests and redirects to the manifest's declared public production host/path, pins each validated public destination IP (including proxy CONNECT destinations), preserves configured proxy and HTTPS CA behavior, enforces an 8-second overall response deadline and a 1 MB body limit, requires HTTP 200 and the fragment in returned HTML, and records a response hash:

~~~sh
python3 tools/verify_experiments.py catalog/books/<id>.json \
  --source-revision <full-pages-deployment-commit-sha> --write-back
~~~

This command makes network requests and writes only after all links pass. Pass the 40-character SHA from the book repository's successful Pages deployment record, not merely the stable release tag. Ordinary `npm test` remains deterministic and offline; it validates the recorded evidence structurally but does not repeat the live check.

Register a new manifest without replacing an existing record:

~~~sh
python3 tools/book_factory.py register /path/to/new-book/library-manifest.json
~~~

Update the existing record with the same stable ID:

~~~sh
python3 tools/book_factory.py update /path/to/new-book/library-manifest.json
~~~

The command validates first, rejects duplicate IDs/slugs, requires explicit update to replace a file, forbids ID changes, and restores the prior manifest if index generation fails. It never changes status for you. A published record needs a release URL and recorded site/chapter checks. A record with experiments also needs experiment-verification evidence.

Only the selected manifest and generated site/data/*.json indexes are changed. The command does not create a repository, deploy a book, mark a roadmap item complete, or publish a site.

## Read a successful Pages deployment revision

Use the latest `github-pages` deployment record and verify its newest status before attesting its source SHA. This command exits without printing a revision if no deployment exists or the latest status is not `success`:

~~~sh
set -eu
deployment_id=$(gh api repos/OWNER/REPOSITORY/deployments --jq '[.[] | select(.environment == "github-pages")][0].id // empty')
test -n "$deployment_id"
deployment_state=$(gh api "repos/OWNER/REPOSITORY/deployments/$deployment_id/statuses" --jq '.[0].state // empty')
test "$deployment_state" = success
production_sha=$(gh api "repos/OWNER/REPOSITORY/deployments/$deployment_id" --jq '.sha // empty')
test -n "$production_sha"
printf '%s\n' "$production_sha"
~~~

Replace `OWNER/REPOSITORY` with the book repository. The verifier checks the full SHA format; obtaining it from the checked successful deployment is the caller's provenance attestation.

## PMICBook example

PMICBook is registered in catalog/books/pmicbook.json. Its latest formal release is v1.2.0; the latest successful Pages deployment is source commit `45edf20e3b1a0924699bf3ea76a6adb0eb767e67` (Pages deployment `7166907725`, run `39207992437`). These fields describe different facts. The record includes 25 bilingual chapters, English/Korean entry points, four live-checked experiment anchors, and a production pass covering 53 HTML routes plus three runtime assets. To verify the committed indexes without changing them:

~~~sh
python3 tools/book_factory.py validate
~~~

The textbook repository stays separate and is not changed by this workflow.

## Future-book workflow

1. Scaffold an independent textbook with python3 tools/scaffold_book.py. Register its validated starter as `in-progress`, and remove its matching ID from catalog/roadmap.json in the same My Library change; an editorial idea and registered book cannot share an ID. WATBook, ProcessIntegrationBook, and FabControlBook are end-to-end worked examples; each remains an independent repository and its detailed scope and review evidence live there. ProcessIntegrationBook v1.1.0 has 13 bilingual chapters and three verified experiment links. Its immutable release tag targets `452043e782aaccc4a7c75c702dc4240716010f47`; Actions run `39864151127` and successful Pages deployment `7265122303` validate and deploy that same source. All 41 live resources matched tested source bytes, the production Chromium browser suite passed 16/16, and the three lab anchors were rechecked against that deployment on 2026-10-23. The earlier v1.0.0 tag remains available. Its source manifest remains an in-progress registration input; the published record in this catalog controls My Library publication status. FabControlBook v1.1.0 has 14 bilingual chapters and four verified experiment anchors. Its tag, successful Actions run `40044817582`, and successful Pages deployment `7291581369` all target `06869870d3e82de8f559fba30f7a5821fc4fbde7`, descended from frozen candidate `902ad7a43cfbb7be3537905342d810bf9c04e3c7`. Hosted checks passed Node 11/11, Python 9/9, Playwright 18/18; all 44 production resources matched tested source bytes, and production Playwright passed 18/18 across desktop/tablet/mobile. The four EN/KO lab links were verified. Its source manifest remains `in-progress`; this catalog is authoritative for publication status. An initial exact-source local full run hit one intermittent mobile keyboard-scroll failure (17/18); an identical-source rerun and isolated mobile check passed, leaving a documented P2 test flake. The scientific models remain synthetic educational examples, not fab or silicon validation.
2. Author, test, review, version, and deploy it in its own GitHub repository.
3. Confirm production routes and anchors and record release/review evidence.
4. Copy its completed manifest to catalog/books/<id>.json and cover artwork to the referenced site/assets/ path.
5. Add category and learning-path links only after their targets exist.
6. Run npm test and review generated index changes.
7. Commit and deploy My Library through its Actions workflow.

The exact worked sequence is documented in docs/ADDING_A_NEW_BOOK.md.

## Reference and provenance review gate

Before beginning substantial new content, validate and inspect the recorded editorial decision:

~~~sh
python3 tools/reference_intelligence.py validate
python3 tools/reference_intelligence.py monitor \
  --baseline catalog/reference-intelligence/inventory.json \
  --decisions catalog/reference-intelligence/editorial-decisions.json \
  --output-dir /tmp/my-library-reference-preflight
cat /tmp/my-library-reference-preflight/report.md
python3 tools/reference_intelligence.py review-project --project-id fabcontrolbook
~~~

For a new project, inspect `observed-inventory.json` and the report before scaffolding. If a relevant source changed, inspect its exact diff and rights files, refresh that project's source SHA/URL/paths and catalog pin after editorial review, and validate against the refreshed reviewed inventory; do not blindly accept a monitor observation. Add an assessment to `catalog/reference-intelligence/editorial-decisions.json` before scaffolding. Record the target audience, unique value, outcome, reuse plan, and unresolved questions. `scaffold_book.py` enforces this local decision before creating files; the Book Factory checks it again when a planned/archived record becomes active and when an in-progress record becomes published. The outcome must authorize a separate book. A published registration must also have a non-empty provenance audit containing at least one explicit assessment; `original` records need source location, destination, and rights status; `third-party-material` records need source, creator, license, rights status, restrictions, required notices, destination, and notice location; CC BY/MIT adaptations require verified notice and translation-status records. GitHub sources require a pinned full SHA for adaptations/reference-only, while external non-Git sources may use stable HTTPS URLs. Unresolved P0/P1 findings and any `license-uncertain` reuse block publication. A recorded P2 follow-up may remain with a concrete action and transparent limitation.

These checks validate the process and record shape. They do not certify that a license applies to a specific asset or provide legal advice. Apply the file-level process in `docs/COPYRIGHT_AND_PROVENANCE.md`; existing books remain in their own repositories.
