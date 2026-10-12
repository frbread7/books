# Learning Journey architecture and editorial contract

The Learning Journey is a bilingual, static concept explorer for Mathematics and lifelong learning. It sits beside the published textbook catalog; it does not turn curriculum concepts or proposed titles into books.

## Information model

- [`schemas/learning-journey.schema.json`](../schemas/learning-journey.schema.json) defines version 1 of the source register, stages, strands, and concepts.
- [`catalog/learning-journey.json`](../catalog/learning-journey.json) is canonical editorial map data, with six guidance-only stages, eleven bilingual subject strands, stable concept IDs, explicit preparation links, and separate continuity/revisit links.
- `catalog/books/<id>.json` remains the only source for registered book records. A concept may point to verified materials only by a published `bookId` plus a real `chapterId`.
- `catalog/roadmap.json` stores proposals under distinct `books`, `mathematicsBooks`, and `familyProjects` arrays. Every concept’s `plannedBookIds` must resolve there and remain marked `planned`.
- `site/data/learning-journey.json`, like the other `site/data/*.json` files, is generated. Do not edit generated indexes by hand.

Concept IDs are stable lower-case slugs. IDs are never recycled for another idea. A concept’s `threadId` identifies a continuing idea across stages; `depth` increases within that thread. `revisits` names an earlier concept in that thread to show continuity; it is deliberately separate from `prerequisites`. Only add prerequisite links when prior preparation is educationally meaningful. A revisit does not imply a gate, and an age stage never proves readiness. The v1 map provides one representative concept for every stage/strand pair; it is an orientation map, not an exhaustive curriculum.

The English and Korean labels/descriptions are both required. References distinguish official curriculum notices, professional/research recommendations, one university example, and upstream source audits. Official sources inform but do not dictate the editorial strand map. See [Curriculum Sources](CURRICULUM_SOURCES.md).

Preschool entries linked to CuriosityBook describe planned story-led concepts, including shared picture-book reading, animal counting/patterns, optional English side notes, weather exploration, and a proposed King Sejong story. They are editorial illustrations only; neither a story manuscript nor its interactions are implemented or published. See the [CuriosityBook pilot specification](CURIOSITYBOOK_SPEC.md).

## Material states

The UI derives three honest states from those separate data sources:

1. **Available · catalog and chapter verified** — a current published Book Factory record and chapter URL resolve.
2. **Planned book · not published** — a roadmap proposal exists, but there is no book link.
3. **Curriculum concept · no authored book yet** — the concept is editorial map content only.

The Learning Journey never exposes an `in-progress` or roadmap record as a published resource. It links to the existing [verified reading paths](../site/paths.html) for curated sequences through real textbook chapters. Query parameters allow stage and strand selection to be bookmarked; there is no account, learner profile, stored child progress, or analytics event.

## Add or revise an entry

1. Check the source register and review date. Distinguish an official requirement, research/professional recommendation, and editor-created proposal in the wording.
2. Choose a stable ID. Add both English and Korean title/description. Preserve the ID if wording changes; use a new ID when the concept meaning changes materially.
3. Set the strand, stage, thread, and increasing depth. Add only defensible preparation links. Use `revisits` to show continuity without implying a prerequisite. Do not infer that chronological age alone proves readiness.
4. Add source IDs. For a textbook, point to its planned roadmap ID or to an actual published book/chapter. Never add a placeholder chapter URL.
5. Update this JSON and, where needed, the matching roadmap/spec documentation. Do not add a curriculum concept to `catalog/books/`.
6. Regenerate and validate:

~~~sh
python3 tools/book_factory.py generate
npm test
~~~

The validator checks IDs, bilingual fields, category membership, full representative stage/strand coverage, source references, graph acyclicity, same-thread revisit progression, roadmap references, and published book/chapter targets. Playwright verifies the interface, controls, query navigation, legacy reading-path route, and responsive layouts.

## Privacy and age-stage design

Age bands are approximate navigation guidance. They do not rank learners or require personal data. The portal does not request a child’s name, date of birth, image, school, profile, or progress history. There are no accounts, public child profiles, saved answers, quizzes, competition, streaks, or tracking. If a future standalone child-oriented book proposes any progress feature, its privacy model needs a separate, explicit review before it is built. Do not add child tracking to the portal as an incidental feature.

## Versioning and governance

`schemaVersion` changes only for a backward-incompatible data shape. Curriculum sources are versioned independently. A maintainer should review official Korean curriculum notices at least once a year and before asserting any new mapping, update exact source metadata, preserve past source version context, and ask a Korean curriculum specialist to review substantive changes. Keep planned projects distinct from actual repositories and publication evidence.
