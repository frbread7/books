# Book Factory

The Book Factory is a small contract and registration command, not a CMS. Every textbook is authored, reviewed, released, and hosted in its own repository. My Library registers metadata and external links.

## Contract

The canonical v1 shape is schemas/book.schema.json; semantic checks live in tools/book_factory.py. A record includes stable ID and slug, bilingual display metadata, subject and tags, status, repository and production URLs, available languages, version/date, chapter count/index, verified experiments, prerequisite/related book IDs, cover and color theme, license attribution, and publication evidence.

Install the small validator with python3 -m pip install -r requirements.txt. JSON Schema catches structural and format errors; Python checks enforce cross-record IDs, category/chapter links, production-host boundaries, and generated-index integrity.

Chapter URLs must use the book's production host. Experiments require an existing chapter ID and an HTTPS URL with a fragment. Every experiment in a published book must also carry successful live-check evidence: exact checked URL, ISO date, HTTP 200, fragment present, response SHA-256, full 40-character deployment commit SHA, a caller-attestation note, and a short evidence note. The checker validates SHA format but does not confirm repository membership; obtain and record the SHA from the successful Pages deployment metadata. The cover must be stored under site/assets/ in this portal. Related/prerequisite IDs must refer to registered books; empty lists are valid, and a book cannot list itself. Roadmap proposals belong in catalog/roadmap.json, not catalog/books/.

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

For actual live experiment checks, use the bounded HTTPS verifier. It restricts requests and redirects to the manifest's declared public production host/path, uses an 8-second timeout and a 1 MB body limit, requires HTTP 200 and the fragment in returned HTML, and records a response hash:

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

## PMICBook example

PMICBook is registered in catalog/books/pmicbook.json. Its formal version and release URL remain v1.0.0; the current successful Pages deployment is source commit `a5290ff0ed0c785c6fc5bc0d7fa966b252710883`. These fields describe different facts. The record includes its stable title/chapter index, English/Korean entry points, and four live-checked experiment anchors. To verify the committed indexes without changing them:

~~~sh
python3 tools/book_factory.py validate
~~~

The textbook repository stays separate and is not changed by this workflow.

## Future-book workflow

1. Scaffold an independent textbook with python3 tools/scaffold_book.py. When work starts, remove its matching ID from catalog/roadmap.json; an editorial idea and registered book cannot share an ID.
2. Author, test, review, version, and deploy it in its own GitHub repository.
3. Confirm production routes and anchors and record release/review evidence.
4. Copy its completed manifest to catalog/books/<id>.json and cover artwork to the referenced site/assets/ path.
5. Add category and learning-path links only after their targets exist.
6. Run npm test and review generated index changes.
7. Commit and deploy My Library through its Actions workflow.

The exact worked sequence is documented in docs/ADDING_A_NEW_BOOK.md.
