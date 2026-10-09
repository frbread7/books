# Book Factory

The Book Factory is a small contract and registration command, not a CMS. Every textbook is authored, reviewed, released, and hosted in its own repository. My Library registers metadata and external links.

## Contract

The canonical v1 shape is schemas/book.schema.json; semantic checks live in tools/book_factory.py. A record includes stable ID and slug, bilingual display metadata, subject and tags, status, repository and production URLs, available languages, version/date, chapter count/index, verified experiments, prerequisite/related book IDs, cover and color theme, license attribution, and publication evidence.

Install the small validator with python3 -m pip install -r requirements.txt. JSON Schema catches structural and format errors; Python checks enforce cross-record IDs, category/chapter links, production-host boundaries, and generated-index integrity.

Chapter URLs must use the book's production host. Experiments require an existing chapter ID and an HTTPS URL with an anchor. The cover must be stored under site/assets/ in this portal. Related/prerequisite IDs must refer to registered books; empty lists are valid. Roadmap proposals belong in catalog/roadmap.json, not catalog/books/.

## Commands

Validate all manifests and regenerate derived browser indexes:

~~~sh
python3 tools/book_factory.py validate
~~~

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

PMICBook is registered in catalog/books/pmicbook.json. It identifies release v1.0.0, its stable title/chapter index, English/Korean entry points, and four checked experiment anchors. To regenerate indexes:

~~~sh
python3 tools/book_factory.py validate
~~~

The textbook repository stays separate and is not changed by this workflow.

## Future-book workflow

1. Scaffold an independent textbook with python3 tools/scaffold_book.py.
2. Author, test, review, version, and deploy it in its own GitHub repository.
3. Confirm production routes and anchors and record release/review evidence.
4. Copy its completed manifest to catalog/books/<id>.json and cover artwork to the referenced site/assets/ path.
5. Add category and learning-path links only after their targets exist.
6. Run npm test and review generated index changes.
7. Commit and deploy My Library through its Actions workflow.

The exact worked sequence is documented in docs/ADDING_A_NEW_BOOK.md.
