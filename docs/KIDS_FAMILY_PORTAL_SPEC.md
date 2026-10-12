# Kids & Family / Little Explorers portal specification

**Status: portal preview implemented; HeavyVehicleBook remains an unpublished editorial pilot.** The route makes interests and story themes the entry point, then lets a caregiver follow a small set of story ideas into existing Learning Journey concepts. It is not a textbook catalog, child account, placement tool, or curriculum-compliance claim.

## Audience and experience

The experience is designed for a caregiver and a child to browse and read together. Start with a familiar interest, choose a story world, and read a complete short story. A caregiver can open safety and factual notes before reading. Optional prompts and picture details can be hidden; the story remains complete without them. Page navigation is ordinary reading control, not a quiz, score, streak, timer, or milestone.

The interface is available in English and Korean. The story texts, illustration descriptions, prompts, and caregiver notes are bilingual. SVG scenes are original artwork built in the portal source and use no borrowed or third-party reference images. Children and other visitors appear on a public path outside a closed work zone; adults operate the machines. No scene shows a child approaching, riding, loading, or directing equipment.

## Interest taxonomy and authored coverage

The current browse choices are cars and transport; heavy vehicles; trains, planes, and ships; robots and machines; animals and wildlife; dinosaurs and prehistory; ocean; insects and nature; space; weather and Earth; human body and health; stories, cultures, and history; colors and counting; shapes and sorting; and size and direction. The first twelve are the requested broad interest taxonomy; the last three are preschool learning lenses used by this pilot.

Only three story worlds have complete draft manuscripts: three colored dump trucks, an excavator and a shape garden, and a crane with a big/small, up/down story. Selecting another interest shows a clear “no complete story yet” message. The five cards below the browse controls define bounded editorial scopes; they are not roadmap or published-book records:

| Project | Scope | State |
| --- | --- | --- |
| HeavyVehicleBook | Three bilingual draft stories about adult-operated dump trucks, an excavator, and a crane; preschool colors/counting, shapes/sorting, size/direction, and simple movement. | Editorial pilot, unpublished |
| CarBook | Passenger vehicles, wheel movement, routes, direction, and sharing everyday transport spaces. | Proposal only |
| DinosaurBook | Fossils, evidence, dinosaurs, size, time, and prehistoric Earth. | Proposal only |
| AnimalBook | Animal features, habitats, life cycles, and respectful care for wildlife and nature. | Proposal only |
| RobotBook | Robots and machines, simple inputs and responses, cause/effect, and helpful tool design. | Proposal only |

CuriosityBook remains the separate, broader family-project proposal already documented in the roadmap and [`CURIOSITYBOOK_SPEC.md`](CURIOSITYBOOK_SPEC.md). The Kids & Family collection neither changes its identity nor claims that its planned concepts have manuscripts.

The [proposal briefs](KIDS_FAMILY_PROPOSALS.md) provide an audience/stage, example story seeds, Korean/English vocabulary, optional interaction, offline activity, fact-checking, accessibility/safety, and progression note for each of the five scopes. Only HeavyVehicleBook's three current manuscripts are authored drafts.

## Learning links and data boundary

`catalog/kids-family.json` is the canonical source for this collection. It is separate from `catalog/books/`, `catalog/categories.json`, and `catalog/roadmap.json`; `site/data/kids-family.json` is its generated runtime index. This separation keeps family themes and story links from appearing as published chapter connections or inflating publication and roadmap counts.

Each authored theme links to three relevant preschool concept IDs across distinct existing subject strands. Stage choices start at the existing preschool stage and follow only a unique explicit `revisits` edge in `catalog/learning-journey.json`. The route displays the resulting concept at the chosen stage and links back to its existing Learning Journey page. The existing 66 concept IDs, meanings, prerequisite edges, and revisit edges are unchanged. These connections are editorial continuity, not a required sequence or learner assessment.

## Reading and interaction rules

- One complete bilingual story is shown one spread at a time, with a simple page count and previous/next controls.
- Each spread has original vector art and localized alternative text.
- Optional caregiver prompts can be hidden; optional picture details are revealed only on request.
- The full adult preview opens before the first spread and includes caregiver guidance, factual notes, and that story's cited references.
- The address bar may reflect the chosen interest, theme, stage, story, and current spread. No child identity or free-form child input is requested, and the portal does not save a learner profile or progress record.
- No account, upload, camera/microphone, geolocation, analytics, advertising, autoplay, third-party script, or external API is introduced.
- Native buttons, keyboard focus, visible focus rings, responsive layouts, and reduced-motion styling support accessible browsing. Story art is decorative only when its localized alternative text is read as a scene description.

## Child safety, privacy, and inclusion

The page distinguishes a public viewing place from a closed work area and keeps every child outside the equipment path. Adult notes make clear that stories are not machine-operation or construction activities. No dangerous action is modeled for a child to imitate. The stories use accessible shared places as part of ordinary neighborhood life, while their main learning ideas remain concrete preschool concepts.

The portal does not request a child's name, age, school, image, location, account, or response. It stores no child profile, answer, or reading history. Only existing site preferences for display language and theme use browser local storage. Choosing a story spread updates a generic query parameter in the current page URL; it is not associated with an identity or used by app analytics.

## Deferred platform note: Samsung TV

Samsung TV support is a future product specification only; no television application, remote-control behavior, TV-specific packaging, Samsung SDK, or device test is implemented or claimed here. Any future proposal should use a 16:9 landscape layout; large readable text; D-pad navigation with a visible, high-contrast focus indicator; simple previous/back and next controls; and no hover-only action or touch dependency. It should allow an adult to choose an optional session duration, never autoplay or auto-advance, and preserve a complete read-aloud without interaction. Recheck actual TV accessibility and device constraints before making a support claim.

## Review gates before publication or a standalone book

Keep HeavyVehicleBook outside the published catalog until the team has completed Korean-language editorial review, original-art rights review, construction-fact review, caregiver and child-safety review, accessibility review, and privacy/security review. A later book would also need its own repository, release and deployment evidence, licensing decision, and Book Factory registration gate. These portal drafts do not satisfy those gates.

## Suggested next phase

Review the three current manuscripts and inline artwork with bilingual caregivers and relevant safety/factual reviewers. Revise this bounded pilot from their feedback before deciding whether to commission the four other scopes. Do not expand all interest categories into curricula or create speculative book repositories as part of this phase.
