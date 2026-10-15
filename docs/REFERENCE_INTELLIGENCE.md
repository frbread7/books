# Reference intelligence and incremental monitoring

My Library checks the public `geniuskey/books` collection and each repository currently linked from its central catalog. The monitor is deterministic Python; it does not call an LLM, execute upstream files, import textbook content, change My Library roadmaps, or publish a book.

## Snapshot and coverage

The checked-in observation is [inventory.json](../catalog/reference-intelligence/inventory.json), validated by [reference-inventory.schema.json](../schemas/reference-inventory.schema.json). It records catalog facts, observed repository revisions, relevant source paths and Git blob SHAs, chapter headings, simulator source paths, concise license-file observations, and the two central source files `data/books.json` and `data/editorial-backlog.json`. The editorial backlog stores concise idea identifiers and dispositions, not the original prose. The inventory deliberately avoids storing full textbook chapters.

Snapshot facts as of the `lastSuccessfulInspectionAt` value in the JSON:

- `geniuskey/books` catalog revision: `f51e57c03c6bd42c6bccc976feb75126483ebdfd`.
- 43 catalog records: 37 currently linked to public repositories and 6 planned records without repositories.
- 689 chapter source files were indexed across the 37 repositories. Catalog-declared chapter counts and indexed files are kept as separate facts.
- Central editorial backlog revision: the Git blob SHA and `reviewedOn` date are recorded under `upstream.centralSourceFiles`.
- GitHub's repository metadata API reported `NOASSERTION` for the central and indexed repositories during this inspection. The actual files often declare distinct software and educational-material terms; neither fact establishes rights for every embedded asset.

The repository inventory includes each catalog-linked repository, not only the selected overlap examples. It does not claim to inspect non-indexed private repositories, external assets, every line of prose, or every license's legal scope. Upstream book descriptions, license text, and chapter contents are not copied into this database.

## Local commands

Validate the checked-in reference data and publication provenance records:

```sh
python3 tools/reference_intelligence.py validate
```

Review the source and differentiation record before starting a proposed book:

```sh
python3 tools/reference_intelligence.py review-project --project-id fabcontrolbook
```

Run that target-project gate against the latest observation immediately before substantial work. If any relevant source SHA/path or the central catalog changed, inspect the report and affected rights files first, update only that project's source pins after editorial review, then validate the gate against the refreshed reviewed inventory. Stale pins for another project do not block this project's gate.

Refresh the observed inventory locally and produce a report without writing any GitHub issue:

```sh
python3 tools/reference_intelligence.py monitor --output-dir /tmp/my-library-reference-report
```

The last command makes public GitHub API/raw-file reads. It reuses the checked-in inventory's source maps whenever a repository HEAD has not changed. It still requests each repository's latest commit SHA so it can detect new revisions; unchanged trees, license files, and chapter pages are not downloaded again. No upstream scripts are executed.

## Scheduled report and review lifecycle

`.github/workflows/reference-monitor.yml` runs weekly and supports `workflow_dispatch`. Its privileged job runs only on `main`, checks out `main` explicitly, and serializes all tracker writes through one concurrency group; manual dispatches selecting another ref are skipped. It requests read access to repository contents and issue write access only for the deduplicated review tracker. A maintainer can also run the script without issue persistence for a read-only check. Rate-limit waits honor `Retry-After` and primary reset headers; when GitHub asks for a delay beyond the bounded retry window, the run fails with a rerun-after-reset message instead of retrying early.

The workflow compares in two steps:

1. It fetches changed source data relative to the most recent successful observation checkpoint.
2. It renders the complete unresolved comparison against the checked-in inventory, which remains the last reviewed baseline.

The monitor reuses one issue titled `Upstream reference intelligence — review tracker`. It stores a compressed, hashed snapshot in bounded issue comments; the issue body changes only when newly observed material changes appear. An unchanged run leaves the issue untouched. A new material delta can reopen a manually closed tracker. Duplicate tracker discovery is bounded to 300 most recently updated issues; if the tracker cannot be located within that bound, the run fails closed instead of creating a possible duplicate. Checkpoint restoration accepts comments authored by the repository owner or GitHub Actions bot only, checks the digest and schema, and enforces decompression and comment-count limits.

The issue and attached artifact are a review queue, not an accepted editorial decision. The issue and Actions summary contain a concise escaped Markdown report; the complete observed inventory, machine-readable changes, and report are retained in the `reference-intelligence-report` artifact for 30 days. A human/editorial review updates `catalog/reference-intelligence/editorial-decisions.json` and pins the source repository and SHA reviewed. Only after review should the checked-in `inventory.json` be advanced as the new reviewed baseline. Upstream changes never silently remove, create, reprioritize, or publish My Library content.

## Failure and security behavior

- HTTPS requests are limited to `api.github.com` and `raw.githubusercontent.com`; responses, JSON documents, paths, concurrency, timeouts, retries, and pagination are bounded. Upstream-controlled titles and paths are escaped before Markdown rendering.
- API 404 means a source is unavailable and is reported. Authentication failures, malformed/oversized data, rate-limit exhaustion, and incomplete pagination fail the run rather than updating a successful observation.
- The optional `GITHUB_TOKEN` / `GH_TOKEN` is used only by the GitHub workflow/client for API access. Local read-only monitoring can run anonymously. The workflow token is not printed or written into the inventory.
- Workflow permissions are limited to `contents: read` and `issues: write`; it does not grant pull-request, deployment, package, or administration rights.
- The main-only job guard and explicit `main` checkout protect runs that use the reviewed workflow definition from executing branch-controlled monitor code. They do not make workflow YAML immutable: a collaborator with workflow write access can alter the YAML on another branch and dispatch that altered workflow/ref. Treat Actions/workflow writers and their dispatch authority as trusted; review and restrict those changes through the repository's branch and access controls. The checkout pin does not neutralize altered workflow steps or permissions.
- All fetched upstream content is untrusted input. The monitor parses bounded JSON/HTML and records paths/hashes. It never invokes fetched code.

## Snapshot update and maintenance

Review report deltas, inspect linked upstream compare pages, refresh affected editorial assessments, then regenerate the snapshot from the latest tracked inventory:

```sh
python3 tools/reference_intelligence.py inventory \
  --previous catalog/reference-intelligence/inventory.json \
  --output catalog/reference-intelligence/inventory.json
python3 tools/reference_intelligence.py validate
```

The snapshot update should be committed with the reviewed assessment changes and a concise note in [REFERENCE_OVERLAP_FRAMEWORK.md](REFERENCE_OVERLAP_FRAMEWORK.md). Do not update `reviewedAt` or a source SHA merely because the scheduled monitor observed it. A reviewer must inspect relevant chapter/source diffs and rights notices. The report can guide analysis but is not a legal opinion.

## Boundaries

The four My Library publications remain independent repositories. This system only reads their existing provenance documentation for the audit in [PROVENANCE_AUDIT.md](PROVENANCE_AUDIT.md); it does not modify those repositories. The central portal's published count is derived only from its own validated manifests, never from upstream reference counts.
