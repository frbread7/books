# HeavyVehicleBook editorial pilot

**Status: three complete bilingual story drafts and original SVG preview art; unpublished and outside the book catalog.** HeavyVehicleBook is an editorial pilot under Kids & Family / Little Explorers. It has no separate textbook repository, release, production site, publication evidence, or book manifest. The canonical manuscripts and structured story data live in [`catalog/kids-family.json`](../catalog/kids-family.json); the portal renders those records through `site/data/kids-family.json`. The English and Korean story prose is shown publicly for editorial preview with no reuse license granted; a separate content license is required before publication. The authored SVG previews follow the portal's separate MIT software license, which does not cover the prose.

## Collection intent

The pilot explores the requested preschool-scale ideas through a real story arc: color and counting, shape sorting, then size, direction, and simple machine movement. The stories are read-aloud experiences, not vehicle instruction. Each theme starts from three existing preschool Learning Journey concepts across three distinct subject strands: mathematics plus two relevant strands. Choosing another stage follows the Learning Journey's explicit revisit links; the story itself is not mapped to every stage or subject.

| Draft story | Main preschool ideas | Story arc | Existing preschool links |
| --- | --- | --- | --- |
| **The Three Trucks and the Garden Path** / **세 대의 트럭과 정원 길** | Red, yellow, and blue; count one, two, three; repeat a color sequence; notice forward, pause, return. | Rain leaves one muddy turn. A professional crew plans and prepares a garden path. Mina counts three trucks from a public viewing place; the crew checks the finished route and the neighbors visit the garden. | `math-preschool-quantity-and-pattern`; `arts-preschool-materials-and-sound`; `computing-preschool-tools-and-cause` |
| **The Excavator and the Shape Garden** / **굴착기와 모양 정원** | Circle, square, triangle; sort like shapes; notice a repeating pattern; name boom, arm, bucket without teaching controls. | Markers are mixed up at a garden design table. The adult crew checks its plan; an excavator prepares a closed work area while everyone stays clear. Workers sort and place the markers, then open the finished garden. | `math-preschool-quantity-and-pattern`; `computing-preschool-tools-and-cause`; `arts-preschool-materials-and-sound` |
| **Big, Small, Up, and Down** / **크고 작게, 위로 아래로** | Compare big/small; follow up/across/down; notice a roof's shadow and a crane's simple direction. | A garden reading nook needs shade. A crew plans a broad roof, and a crane lifts it while a family watches from outside the work zone. During a fictional cautious pause, the panel rests on prepared ground-level supports with no suspended load; the roof is later placed and the nook is ready for stories. | `math-preschool-quantity-and-pattern`; `science-preschool-noticing-and-wonder`; `computing-preschool-tools-and-cause` |

The full six-spread English and Korean text, image alt text, optional prompt, and optional detail for each story are in the canonical JSON. Every story has caregiver notes, factual notes, and reference IDs. The JSON—not a separate book package—is the source of truth for the drafts.

## Flagship storyboard: The Three Trucks and the Garden Path

| Spread | Narrative beat | Original illustration direction |
| --- | --- | --- |
| 1. A muddy turn | After rain, one path turn is muddy; Mina and Jun notice that Auntie Hana takes the smooth route around. | From a public path, show a small muddy bend, an open neighboring path, flowers, and visitors outside the work boundary. No person enters an active work area. |
| 2. A colorful plan | The adult crew reviews a plan inside a fenced work area; Mina notices three simple colors from the public overlook. | Show a plan board with three large color/shape marks, a closed fence between visitors and crew, and no legible real work markings. |
| 3. One, two, three trucks | Red, yellow, and blue dump trucks arrive in order; Mina counts them from far away. | Draw three distinct original truck forms, with numerals 1, 2, 3 and visibly different body colors. The marked work area is closed to visitors. |
| 4. The materials arrive | The trucks tip planned material only in the prepared work area; Mina counts the trucks and notices three colors. | Show adult supervision and separate equipment positions inside the fenced area; no person stands near a moving or tipping vehicle. Use story color cues, not realistic traffic signs. |
| 5. The roller rolls | The crew prepares the path; a roller moves forward, pauses, and returns while Mina watches. | Show the roller alone in its clear travel lane. Children remain on the public path. Use a repeated wheel motif as a non-instructional visual detail. |
| 6. A path for neighbors | The crew checks the path; neighbors walk together to the garden and the three trucks have left. | Show the completed public path and a welcoming garden. No construction equipment remains in the visitor area. |

The story copy itself is authoritative in `catalog/kids-family.json`; the table summarizes the bilingual spreads without maintaining a second manuscript. Two companion stories are complete in the same data source and use the `shape-*` and `crane-*` scene families.

## Illustration and interaction direction

The current preview uses authored inline SVG shapes with original geometry and colors; it has no external image, icon, font, analytics, or media dependency. Localized SVG labels describe each scene. The illustrations are simplified editorial drawings and are not to-scale site plans, equipment diagrams, signs, or operating instructions.

Reading opens caregiver and factual notes before the first spread. Previous/next controls change the current spread; one optional prompt can be hidden, and an optional picture detail can be shown. All text carries the narrative without either interaction. The current page number is a generic URL query value only and is not written to account storage or learner history.

## Printable/offline companion

The reader's **Print or save this bilingual story** control opens the browser's print dialog. Its print view contains all six illustrated spreads in English and Korean, each optional prompt and detail, adult safety/factual notes, and the cited sources. Page breaks keep each spread together; the layout uses high-contrast black text on white and does not print portal navigation or controls. A caregiver can print it or save a local PDF through the browser. The print interaction does not upload a file or store reading progress. Physical printer output may vary; the review suite verifies browser print-media visibility and content rather than printer-specific pagination.

For an additional no-screen read-aloud, caregivers can point to the three truck colors and count them; draw or point to the circle/square/triangle pattern; or compare big/small and up/down arrows on paper. These remain optional, ordinary drawing/observation ideas, not construction activities. Do not visit an active worksite, use tools or construction materials, or imitate machine actions.

## Factual and safety references

These official sources inform narrow caregiver-facing facts about workplace hazards and scene boundaries. Their worker-hazard guidance does not prescribe visitor-access rules. Keeping children and other visitors outside the work boundary is a conservative editorial inference informed by those hazards, not a rule attributed to NIOSH or OSHA. These sources do not validate a construction plan or provide child-directed operating instructions.

| Source | Use in the pilot |
| --- | --- |
| [NIOSH, Construction Equipment Visibility](https://www.cdc.gov/niosh/motor-vehicle/constructionequipmentvisibilitydiagram/index.html) | A worker-focused source on equipment visibility hazards. The visitor exclusion is a conservative editorial inference informed by those hazards, not a visitor-access rule stated by NIOSH. |
| [NIOSH, Preventing Worker Injuries and Deaths from Backing Construction Vehicles and Equipment](https://www.cdc.gov/niosh/publications/numbered/2014-125.html) | A worker-focused source on backing hazards. The visitor exclusion and empty travel-lane art are editorial choices informed by those hazards, not visitor-access rules stated by NIOSH. |
| [OSHA, Motor Vehicle Safety — Construction](https://www.osha.gov/motor-vehicle-safety/construction) | Workplace-safety context for moving vehicles. It does not prescribe a visitor-access rule; the story's child/visitor boundary is a conservative editorial inference. |
| [OSHA, Cranes & Derricks in Construction FAQ](https://www.osha.gov/cranes-derricks-construction/faq) | Its FAQ is marked revised July 18, 2016. It informs review of professional roles and crane setup, but does not prescribe visitor access, state a wind rule, or support the story's gust-related pause. That pause is a fictional cautious plot choice; recheck current guidance before publication. The story omits numerical limits and hand signals. |
| [FHWA, Earthwork Compaction](https://www.fhwa.dot.gov/construction/cpmi04b8.cfm) | Supports the simple factual note that a roller compacts prepared material, without adding procedure or activity instructions. |

Source IDs, dates reviewed, localized source descriptions, factual notes, and per-story links are maintained in the canonical JSON. Recheck the official sources during a future publication review.

## Publication boundary and review gates

The pilot remains `editorial-pilot` / `unpublished`; individual stories remain `editorial-draft`. It is not in `catalog/books/`, `catalog/roadmap.json`, `catalog/categories.json`, or any published chapter map. Before a separate book can be proposed for publication, require Korean-language copy review, original-art rights review, fact checking, caregiver and child-safety review, accessibility review, and privacy/security review. Only later may a separately authored and deployed textbook enter the normal Book Factory process.

Samsung TV remains a future specification topic only. No TV build or device support is included in this pilot.
