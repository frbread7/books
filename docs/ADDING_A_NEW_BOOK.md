# Adding a new book

This keeps the textbook independently deployable and ensures the bookshelf links only to content that exists.

## 1. Scaffold an independent repository

Run this from the directory that contains the `books/` checkout:

~~~sh
python3 ./books/tools/scaffold_book.py \
  --id devicephysicsbook \
  --title-en DevicePhysicsBook \
  --title-ko DevicePhysicsBook \
  --subtitle-en "Semiconductor physics and devices" \
  --subtitle-ko "반도체 물리와 소자" \
  --description-en "An interactive textbook on semiconductor materials, transport, junctions, and devices." \
  --description-ko "반도체 재료, 수송, 접합 및 소자의 기초를 다루는 인터랙티브 교재입니다." \
  --repository-url https://github.com/frbread7/devicephysicsbook \
  --production-url https://frbread7.github.io/devicephysicsbook/ \
  --out ./devicephysicsbook
cd ./devicephysicsbook
~~~

The starter creates a bilingual metadata skeleton, a static landing page, an original cover placeholder, a license/attribution reminder, and an initial in-progress manifest. It is not a complete textbook and is not published.

## 2. Write and independently validate

Author substantive chapters, references, original diagrams, tests, and interactive models in the new repository. Keep its license and source acknowledgements. Set up its own Pages workflow and verify both language entry points and all chapter URLs. List an experiment only when its interface and anchor exist. Publish a release after content review; repository creation alone is not publication.

## 3. Prepare the My Library record

Edit the starter library-manifest.json. Supply actual available languages, version/date, chapter titles and URLs, chapter count, topics, prerequisite and related book IDs, and verified experiment anchors. Before registration:

- Use stable lowercase hyphenated ID and slug values.
- Set status to published only after the live site and content pass review.
- Add the formal release URL/version and factual site/chapter verification evidence for a published book. Also record `publicationEvidence.productionRevision`, the full source commit SHA from the current successful Pages deployment; this is distinct from the stable release tag and does not imply a new book release.
- Verify each experiment against the live deployed HTML with the verifier below. This records the checked URL, date, HTTP status, fragment result, response hash, and caller-attested production commit SHA. The verifier checks the SHA format but not repository membership.
- Choose a cover path under site/assets/ in My Library and place original artwork there.
- Keep prerequisites and relatedBooks empty when no existing published title applies.
- Advertise only real deployed language editions; catalog display text can be bilingual.
- Use HTTPS URLs on the actual production host.
- Do not assign the book a prerequisite ID that points back to itself.

## 4. Register in the portal

Register the starter as `in-progress` first. A title cannot be both a roadmap proposal and a registered book, so remove its matching ID from `books/catalog/roadmap.json` as soon as work starts; `devicephysicsbook` is already listed there. Keep its technical scope in the portal roadmap only while it remains unstarted. From the parent directory containing both sibling checkouts, copy the generated cover into the portal. Its actual scaffold path is `assets/covers/devicephysicsbook.svg`:

~~~sh
cd ..
mkdir -p ./books/site/assets/covers
cp ./devicephysicsbook/assets/covers/devicephysicsbook.svg ./books/site/assets/covers/devicephysicsbook.svg
python3 ./books/tools/book_factory.py register ./devicephysicsbook/library-manifest.json
cd ./books
npm ci
npx playwright install chromium
npm test
~~~

The starter manifest already uses `assets/covers/devicephysicsbook.svg`. The register command validates it and regenerates the portal indexes. `validate` is read-only and checks that those generated files still match the canonical catalog.

~~~sh
python3 tools/book_factory.py validate
npm test
~~~

After the book site is live and the release is reviewed, read the SHA of its current successful Pages deployment. This example uses GitHub CLI to read deployment metadata for the new repository:

~~~sh
production_sha=$(gh api repos/frbread7/devicephysicsbook/deployments --jq 'map(select(.environment == "github-pages")) | first.sha')
python3 tools/verify_experiments.py ../devicephysicsbook/library-manifest.json \
  --source-revision "$production_sha" --write-back
~~~

The verifier is the normal Book Factory step that makes network requests. It checks each experiment page against the declared host/path and writes evidence only if all checks pass. Edit `library-manifest.json` to set `status` to `published` and add the actual formal release URL/version, publication date, `productionRevision` using `$production_sha`, content review, site verification, and chapter verification. The release URL records the formal tagged release; `productionRevision` records the currently deployed site source. Then update the existing portal record:

~~~sh
python3 tools/book_factory.py update ../devicephysicsbook/library-manifest.json
npm test
~~~

Review `site/data/books.json`, the card, category map, and learning paths. Add a map connection to `catalog/categories.json` only after the book is registered. Learning-path steps must use chapter IDs present in registered books.

## 5. Deploy and update

Commit the canonical manifest, cover, catalog edits, and generated indexes together. Pull requests run read-only index-integrity validation and browser checks; a main-branch merge deploys the static site. Verify the live portal and book links after deployment.

To update later while retaining the same stable ID:

~~~sh
python3 tools/book_factory.py update ../devicephysicsbook/library-manifest.json
npm test
~~~

Register refuses to replace a current record; update is explicit and cannot change the ID.
