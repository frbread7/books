# Adding a new book

Each textbook lives in its own repository and deploys independently. My Library stores and validates a manifest, generates discovery indexes, and links to the textbook; it does not copy chapters or deploy the book for you.

## 0. Refresh references and define unique value

The weekly monitor detects upstream source changes; it does not decide to reuse, defer, or publish content. **Immediately before substantial authoring**, run a read-only monitor refresh and inspect both the concise report and machine-readable deltas:

```sh
python3 tools/reference_intelligence.py monitor \
  --baseline catalog/reference-intelligence/inventory.json \
  --decisions catalog/reference-intelligence/editorial-decisions.json \
  --output-dir /tmp/my-library-reference-preflight
cat /tmp/my-library-reference-preflight/report.md
python3 -m json.tool /tmp/my-library-reference-preflight/changes.json | less
python3 -m json.tool /tmp/my-library-reference-preflight/observed-inventory.json | less
```

If a relevant source revision, chapter path, license, notice, or central catalog entry changed, inspect its linked diff and rights files before recording a decision. Refresh only the affected project's `sourceRevisions` from `observed-inventory.json` (full current SHA, pinned source URL, and paths present in that snapshot) and update `reviewedAgainstCatalogSha` when the central catalog changed. Do not blindly copy new SHAs: the monitor observes revisions but does not review or accept them. Once editorial review is complete, advance the checked-in reviewed inventory and decisions together; validate the target project against that refreshed inventory:

```sh
python3 tools/reference_intelligence.py review-project \
  --project-id NEWBOOKID \
  --inventory catalog/reference-intelligence/inventory.json \
  --decisions catalog/reference-intelligence/editorial-decisions.json
python3 tools/reference_intelligence.py validate
```

For a new ID, record its audience, unique value, overlap, development strategy, exact source commit SHAs/paths, reuse plan, and unresolved questions in `catalog/reference-intelligence/editorial-decisions.json`. Select an explicit editorial outcome. `docs/REFERENCE_REVIEW_TEMPLATE.md` provides the review record. `scaffold_book.py` checks that decision before creating files, and the Book Factory checks again when registering a new active book or promoting it to published. If any content, code, image, data, or other material may be reused, complete its file-level attribution mapping using `docs/COPYRIGHT_AND_PROVENANCE.md`.

## 1. Create the independent textbook

From the parent directory that contains the `books/` checkout, scaffold a new repository. Substitute a unique ID, accurate metadata, repository URL, and production URL; choose every language that will actually be deployed.

```sh
python3 ./books/tools/scaffold_book.py \
  --id fabcontrolbook \
  --title-en FabControlBook \
  --title-ko FabControlBook \
  --subtitle-en "Statistical and manufacturing process control" \
  --subtitle-ko "통계적·제조 공정 제어" \
  --description-en "A reviewed technical textbook on semiconductor manufacturing process control." \
  --description-ko "반도체 제조 공정 제어를 다루는 검토된 기술 교재입니다." \
  --repository-url https://github.com/frbread7/fabcontrolbook \
  --production-url https://frbread7.github.io/fabcontrolbook/ \
  --category semiconductor --languages en,ko \
  --out ./fabcontrolbook
```

The scaffold is only a starting point. Replace its landing page and artwork, author both language editions, cite public technical sources, choose/record licenses, and implement tests. The generated `site/` includes a linked license-and-attribution notice; update it with the selected licenses and complete third-party notices before publication. Keep its manifest `in-progress`. Create the public repository, configure its Pages workflow, and verify the actual published site before claiming a release.

## 2. Build and review the textbook

Each book owns its chapter data, assets, simulators, validation, and deployment workflow. Keep the manifest chapter index, chapter count, available language editions, experiment anchors, and production links synchronized with the built site. Simulators need a documented model, assumptions, units, valid range, reference calculations, edge-case checks, and an honest validation label. Synthetic datasets must be labeled synthetic.

Run that book's validation in its repository. For WATBook, the exact commands are:

```sh
cd ../watbook
npm ci
npm test
npm run build
```

Do not set `published` while content, model review, CI, release, deployment, chapter URLs, or experiment checks are incomplete.

## 3. Register an active book as in-progress

An unstarted editorial idea belongs in `catalog/roadmap.json`. Once the book repository is active, register its manifest in `catalog/books/` with `status: "in-progress"` and remove its matching idea from the roadmap in the same My Library change. Copy the original cover to `site/assets/covers/`, update the category map and learning paths only when real registered content supports those links, then use the Book Factory:

```sh
cd ../books
mkdir -p site/assets/covers
cp ../fabcontrolbook/site/assets/covers/fabcontrolbook.svg site/assets/covers/fabcontrolbook.svg
python3 tools/book_factory.py register ../fabcontrolbook/library-manifest.json
python3 tools/book_factory.py validate
npm test
```

`register` validates the new record and regenerates derived indexes. It refuses to overwrite a record. For a later change to the same stable ID, use `update` instead. Before committing, confirm the roadmap no longer contains that ID and inspect the generated bookshelf, category links, learning paths, and experiment discovery.

## 4. Promote to published only with evidence

After content and technical reviews and exact-source tests pass, publish the reviewed source and wait for its successful GitHub Pages deployment. Obtain the full source SHA from that same successful `github-pages` deployment record, then verify the live pages and experiment anchors below. Create the immutable version tag and formal release for that verified source revision before promoting the My Library record. Keep the release version/tag and deployment SHA as separate facts. Fail closed when deployment is missing, still running, failed, or has no valid SHA.

For a new book, inspect its latest Pages deployment before using its SHA:

```sh
set -eu
deployment_id=$(gh api repos/OWNER/REPOSITORY/deployments --jq '[.[] | select(.environment == "github-pages")][0].id // empty')
test -n "$deployment_id"
deployment_state=$(gh api "repos/OWNER/REPOSITORY/deployments/$deployment_id/statuses" --jq '.[0].state // empty')
test "$deployment_state" = success
production_sha=$(gh api "repos/OWNER/REPOSITORY/deployments/$deployment_id" --jq '.sha // empty')
printf '%s\n' "$production_sha" | rg '^[0-9a-f]{40}$'
```

Verify the English and Korean entry pages, every chapter URL, and every declared experiment anchor against production. The existing verifier checks exact experiment URL/fragment responses and records their date, status, content hash, and caller-attested deployment SHA:

```sh
python3 tools/verify_experiments.py catalog/books/BOOK_ID.json \
  --source-revision "$production_sha" --write-back
```

Review the resulting evidence. The verifier confirms SHA shape and the live checked routes; the caller is responsible for copying the SHA from the successful Pages deployment for the same source revision.

Update the My Library manifest to `published` only when the required release URL/date, successful production revision, content-review note, site verification, chapter verification, and all experiment evidence have been recorded. Pass the completed manifest to `update`, then validate:

```sh
python3 tools/book_factory.py update /path/to/validated-published-manifest.json
python3 tools/book_factory.py validate
npm test
```

## 5. Executable My Library examples

PMICBook is the existing published reference record. Inspect and validate it without touching its independent repository:

```sh
cd /home/ubuntu/projects/books
python3 tools/book_factory.py validate
python3 - <<'PY'
import json
from pathlib import Path
book = json.loads(Path("catalog/books/pmicbook.json").read_text())
assert book["status"] == "published"
assert book["repositoryUrl"] == "https://github.com/frbread7/pmicbook"
assert book["chapterCount"] == len(book["chapters"]) == 25
assert book["version"] == "1.2.0"
assert book["publicationEvidence"]["releaseUrl"].endswith("/v1.2.0")
assert book["publicationEvidence"]["productionRevision"] == "45edf20e3b1a0924699bf3ea76a6adb0eb767e67"
assert len(book["experiments"]) == 4
assert all(
    experiment["verification"]["httpStatus"] == 200
    and experiment["verification"]["fragmentFound"]
    and experiment["verification"]["sourceRevision"] == book["publicationEvidence"]["productionRevision"]
    for experiment in book["experiments"]
)
print(book["publicationEvidence"]["releaseUrl"], book["publicationEvidence"]["productionRevision"])
PY
```

WATBook is the completed Book Factory example: current release `v1.0.2` (a documentation and registration-metadata patch), ten bilingual chapters, successful Pages deployment, and six verified experiment anchors. The original content release remains `v1.0.0` at `e27f1f7a7decdba191a2f610c47812870e23ffa3`; v1.0.1 and v1.0.2 only correct release-review/manifest metadata and change no chapter, simulator, or runtime behavior. The current successful release and deployment both target `63b0b0d14c2ea779b3314e8fef4a64a3e0c861da`. Its repository's `library-manifest.json` remains the in-progress registration input; the published catalog copy in `catalog/books/watbook.json` is the authoritative lifecycle and evidence record. Confirm the result without modifying either textbook repository:

```sh
cd /home/ubuntu/projects/books
python3 tools/book_factory.py validate
python3 - <<'PY'
import json
from pathlib import Path
book = json.loads(Path("catalog/books/watbook.json").read_text())
assert book["status"] == "published"
assert book["version"] == "1.0.2"
assert book["chapterCount"] == len(book["chapters"]) == 10
assert all(item["verification"]["httpStatus"] == 200 and item["verification"]["fragmentFound"] for item in book["experiments"])
assert book["publicationEvidence"]["releaseUrl"].endswith("/v1.0.2")
assert book["publicationEvidence"]["productionRevision"] == "63b0b0d14c2ea779b3314e8fef4a64a3e0c861da"
print(book["publicationEvidence"]["releaseUrl"])
PY
```

ProcessIntegrationBook is another end-to-end Book Factory example: release `v1.1.0`, 13 bilingual chapters, and three experiments (one analytically checked, model-limited thermal activity and two qualitative activities). The immutable tag points to `452043e782aaccc4a7c75c702dc4240716010f47`; Actions run `39864151127` and successful Pages deployment `7265122303` both target that SHA. The exact release source passed local generation (36 routes), Python 10/10, model 12/12 and Playwright 16/16; all 41 production resources matched source bytes by SHA-256 and production Playwright passed 16/16. The bounded live verifier rechecked each experiment URL and fragment on 2026-10-23, recording the deployment SHA and response hash. The original `v1.0.0` tag remains intact. The independent repository's `library-manifest.json` deliberately stays `in-progress` as a registration input; this central published record is authoritative for portal publication status. Historical Sze/Scotten source-page provenance, silicon calibration and fab applicability of the illustrative diffusion model remain unverified. These checks establish the educational artifact's release and route integrity, not foundry or laboratory validation.

FabControlBook is a further end-to-end example: `v1.1.0` is the first release of the reconstructed content and controller model, superseding the earlier `v1.0.0` release and `v1.0.1` documentation correction. The immutable tag and successful Actions run `40044817582` and Pages deployment `7291581369` target exact source `06869870d3e82de8f559fba30f7a5821fc4fbde7`, descended from frozen candidate `902ad7a43cfbb7be3537905342d810bf9c04e3c7`. Hosted validation passed Node 11/11, Python 9/9, and Playwright 18/18; all 44 live resources matched source bytes (36 HTML pages, including 28 chapters), and production Playwright passed 18/18 across desktop, tablet, and mobile. Four EN/KO lab links were verified. One initial full local exact-SHA run had 17/18 because of intermittent mobile keyboard scrolling; an identical-HEAD rerun passed 18/18 and the isolated mobile check passed 4/4, so retain this as a residual P2 QA flake. The source manifest remains `in-progress` as a registration input; its central catalog record is updated with release and live-check evidence, but the portal deployment is a separate step and is not claimed here. Synthetic models are not fab/silicon evidence, and no human translation or legal certification is claimed.

For a new book, follow sections 1–4 and register its in-progress record before publication; remove its matching proposal from the roadmap in that same catalog change. After the book's own release, deployment, review, and live checks pass, promote the My Library record with the `update` command above. Do not publish a planned book just to fill the shelf. PMICBook stays independently deployed and is not modified by portal registration.

## 6. Deploy the portal

Commit the canonical manifest, cover, matching roadmap/category/path changes, and generated indexes together. CI runs validation and browser journeys; merge/push to `main` deploys the My Library Pages artifact. Smoke-test the live portal and textbook links after deployment.

```sh
python3 tools/book_factory.py validate
npm test
```

`register` is for a new ID. `update` is explicit, validates before writing, and cannot change an existing ID.
