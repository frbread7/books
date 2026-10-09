# Book series contract

## Repository and release boundary

- One textbook per repository, with independent version history, source license, release process, and production deployment.
- My Library consumes metadata and outbound URLs. It does not vendor chapters, run a book backend, or redeploy books.
- A catalog entry is not an endorsement beyond its stated verification. Each book owns its content and assets.

## Manifest rules

- Stable, unique lowercase ID and slug; the portal filename is catalog/books/<id>.json.
- Bilingual catalog labels and descriptions support the portal UI. languages reports actual textbook editions.
- chapterCount equals chapters.length; chapter IDs and sequence numbers are unique.
- Chapter URLs use the production host and refer to real chapters.
- Every experiment has a unique ID, points to a chapter, and has a verified URL anchor.
- Prerequisites and relatedBooks refer to already registered IDs. Empty lists mean no relationship is claimed.
- Cover paths resolve to original art served by this portal; theme colors use six-digit hexadecimal values.
- Status is planned, in-progress, published, or archived. Roadmap ideas remain separate from registered books.
- Published requires a verifiable release, site check, and chapter check. If experiments are listed, record their anchor checks.
- Per-book license and source acknowledgements are explicit. Cataloging a link does not transfer a book's license.

## Content boundaries

DevicePhysicsBook should own general semiconductor materials, carrier behavior, transport, and device foundations. PMICBook owns power-management requirements, PMIC circuits, and their BCD implementation context. A future fabrication book should teach transferable process modules and integration fundamentals; product-specific process details should be linked to the corresponding product title.

InlineMetrologyBook owns measurements and method limits; YieldDefectBook owns defect/yield populations and statistical inference; FailureAnalysisBook owns localization, physical methods, and evidence interpretation. PowerDeviceBook extends beyond PMICBook's integrated BCD context into discrete and module-level power technologies. These boundaries reduce repeated explanations while allowing cross-links.

## Review status

Creating a starter or registering an in-progress book does not create a publication claim. Status changes only by an explicit manifest update supported by release and verification evidence.
