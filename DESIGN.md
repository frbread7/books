# Design

## Source of truth

**Status:** Active candidate — Reading Room selected, 2026-10-19

**Product surfaces:** My Library home, published catalog, subject collections and maps, individual book details and chapter/lab links, Learning Journey, editorial roadmaps, and Little Explorers.

**Evidence reviewed:** Existing route shells and renderers in `site/*.html` and `site/js/app.js`; bilingual copy in `site/js/i18n.js`; current palette and responsive rules in `site/css/style.css`; five canonical records in `catalog/books/*.json` and generated `site/data/books.json`; existing SVG covers; `docs/PRODUCT_VISION.md`, `docs/ARCHITECTURE.md`, `docs/USER_MANUAL.md`, and `docs/KIDS_FAMILY_PORTAL_SPEC.md`; Playwright baseline screenshots at `/tmp/books-renaissance-baseline` (390 px and 1440 px); official visual references listed under Visual language.

This brief is the source of truth for the visual renaissance. Published-book availability, language URLs, chapter and experiment links, roadmap status, story status, curriculum/source boundaries, and print rights remain owned by their existing catalog records and editorial specifications.

## Brand

My Library should feel like an independent illustrated press for ideas: curious, vivid, deeply considered, and trustworthy. The interface should make books and the ideas inside them the visual subject. Original cover and section art may use technical motifs, field-guide illustration, process diagrams, and storybook landscapes, with each published title clearly differentiated.

The reader should feel invited to open a book without being nudged into a course, funnel, or contest. Trust comes from readable metadata, honest publication states, direct chapter and lab links, bilingual editions, careful source boundaries, and original artwork.

Avoid a generic dashboard, stock-photo collage, imitation of another publisher's covers or logo, faux user activity, gamified progress, decorative data that suggests authority, and dense cards whose metadata competes with the cover.

## Product goals

- Make a real, available chapter or experiment reachable from the home page in no more than three clear actions.
- Give each of the five published books a distinct, legible, original cover identity and a compelling route into its actual contents.
- Turn search, subjects, roadmaps, verified learning paths, mathematics, and the Learning Journey into understandable ways to browse without implying that plans are available books.
- Preserve the separate Little Explorers experience: adult-child reading, gentle illustrated interests, honest draft/proposal labels, optional prompts, and printable stories.
- Work equally well in English and Korean, on narrow touch screens, with keyboard and assistive technology, in light and dark themes.
- Keep the site static, fast, maintainable, private by default, and independent of external runtime services.

**Non-goals:** hosting textbook chapters or experiment runtimes; user accounts, favorites, personal reading lists, saved progress, analytics, rankings, quizzes, recommendations based on behavior, or changes to scientific content; changing the published inventory or promotion state of pending work.

**Success signals:** readers can identify what is published, find a relevant book or subject quickly, reach a real chapter or verified lab without guessing, read comfortably in either language and theme, and understand that family manuscripts and roadmap items are still unpublished.

## Personas and jobs

- **Engineering reader:** compare the scope of published books, then open a useful chapter or verified experiment directly.
- **Independent learner / educator:** follow a subject map or explicitly editorial path while distinguishing available material from suggestions.
- **Korean or English reader:** switch language without losing the current location or encountering mixed-language controls.
- **Parent or caregiver with a child:** choose a gentle story world, see safety and source notes, read together at their own pace, and optionally print a draft.
- **Keyboard or screen-reader user:** move through the whole portal with semantic landmarks, predictable focus, clear labels, and no hover-only actions.

## Information architecture

- **Home:** clear invitation and primary Explore action; an editorial display of the five published books; direct entry points to current chapters/labs and subjects; separate paths to the Learning Journey, Little Explorers, and roadmap.
- **Library:** title-led cover shelf; search across existing indexed metadata; subject and publication-state filters; clear count and empty state. Query parameters remain bookmarkable.
- **Subjects:** published maps and available book connections first; empty subjects link to the existing Learning Journey or roadmap with their status visible.
- **Book detail:** cover, title, purpose, language and version information, publication status, direct textbook and language links, chapter index, verified experiments, and truthful prerequisites/related-book context.
- **Learning Journey / Mathematics:** editorial concept maps and preparation links, explicitly distinct from published-book records and readiness judgments.
- **Roadmap:** proposals and active projects in clearly secondary, unpublished sections.
- **Little Explorers:** interest worlds, the three complete bilingual HeavyVehicleBook drafts, and proposal-only scopes; caregiver notes before reading; optional prompts and illustrations; one-spread-per-page print view.

Primary navigation remains shared across the existing flat routes. Common destinations are reachable without relying on a mega-menu or fragile pointer behavior.

## Design principles

1. **Show the book before its metadata.** Covers, chapter titles, and real subject illustrations should lead; operational facts support the decision.
2. **Make reading the shortest path.** Each book on the shelf has one obvious details action; details expose direct chapter and lab entry points.
3. **Distinguish fact from proposal in every visual treatment.** Published status is conveyed with explicit text, not color alone; planned work never borrows a published-cover treatment.
4. **Use original art to explain, not decorate.** Technical motifs can make the collection memorable but must not imply measured results or calibrated process guidance.
5. **Keep child-facing interaction calm and caregiver-visible.** No motion-dependent instructions, autoplay, personal data collection, gamification, or hidden safety context.
6. **Respect bilingual content as layout content.** Do not truncate Korean or assume Latin word lengths; allow titles and controls to wrap at every breakpoint.
7. **Use color with restraint and meaning.** Distinct subject and book accents coexist with accessible text contrast and clear focus states.

## Visual language

Three rendered concepts have been compared in [the visual renaissance rationale](docs/VISUAL_RENAISSANCE.md), with desktop and 390 px screenshots. The Reading Room is the selected candidate: its cover-led composition gives the five published books a clearer identity and a shorter path to a real chapter, while the implemented subject tiles borrow the Atlas direction's stronger discovery cue. The concepts use local catalog cover files and vector motifs:

- **Collected studio:** an inviting reading-room composition with generous illustrated cover art and a horizontal, tactile shelf.
- **Knowledge atlas:** a vivid subject-map composition that shows how real books connect to engineering ideas and paths.
- **Field-guide press:** a contemporary illustrated publication system with restrained technical color and distinct edition-like book panels.

Track implementation and release evidence in [the visual renaissance QA report](docs/VISUAL_RENAISSANCE_QA.md). Candidate art inventory and provenance limits are recorded in the rationale. The separate [reader specimen handoff](design/reader/handoff.md) defines bilingual and light/dark interaction guidance for a future textbook reader; it remains a local static specimen, not an implemented or deployed reader route.

The home collection and Library catalog use one physical shelf component. Original covers stand upright on a shared support plane with a visible contact line, front lip, subtle page edges, and grounding shadows; concise status and book metadata sit below the plane without enclosing each cover in a card. The shelf browses horizontally at narrow widths with native swipe/scroll and labelled previous/next buttons. Both surfaces derive inventory and links from the current catalog; home shows published records only, and Library retains its filters and truthful status. The geometry remains legible in light/dark and English/Korean. This contract reflects the live [Books interactive library](https://books.euiyun.com/) homepage inspected on 2026-10-22 for spatial cues, without reusing its artwork, assets, branding, or code. The reference's Library page is a cover grid; My Library's Library follows the user's explicit physical-shelf request.

The selected implementation will define color tokens for page/canvas, text, muted text, rule, focus, accent, publication state, and separate child-safe illustrations; type roles for large display headings, Korean-capable body text, compact metadata, and monospaced technical labels; spacing, radius, shadow, and focus tokens; and a small motion vocabulary. No remote fonts or image services. Motion is decorative only, brief, and disabled under `prefers-reduced-motion`.

Visual reference research reviewed on 2026-10-19:

- [Apple Books: Organize books in the Books app](https://support.apple.com/en-hk/guide/iphone/iphab219b91/ios) — covers, collections, grid/list, and explicit sorting are useful library patterns. Treat as an interaction reference; do not copy its tab bar, icons, branding, or layout.
- [Brilliant: Science](https://brilliant.org/science/) — clear topical groupings and visible step-by-step learning explain how a learner can start. Use direct entry points without introducing scoring or course tracking.
- [3Blue1Brown: lessons](https://www.3blue1brown.com/?topic=analysis) — central lesson imagery and concise topic navigation support catalog discovery. Do not copy its illustrations, taxonomy, or distinctive visual identity.
- [National Geographic Kids: Books](https://kids.nationalgeographic.com/books/) — age/context grouping and related activities support children's discovery. Do not reuse its photography, covers, logo, or art; all story-world art here is original.
- [Stripe Press](https://press.stripe.com/) — individual cover art and editorial presentation give books presence. Do not reproduce its cover art, type treatments, logos, or specific compositions.

These sources establish visual and interaction patterns, not permission to reuse their assets. New covers and illustrations must be original and authored for this project. Existing family story prose remains subject to its separate rights notice.

## Components

Existing shared header, navigation, language/theme controls, footer, status badge, buttons, and data-driven book renderer remain the base. The redesign may reshape home/library/detail/subject composition and add small semantic components: an illustrated book display, compact subject/path links, a direct chapter preview, quick chapter/lab links, a mobile navigation disclosure if required, and proposal/pilot callouts.

The shared `bookcase` presentation owns cover objects, the support plane/lip, compact below-shelf labels, a focusable scroll region, and its paired labelled controls. On a Library search/filter update, it returns to the first matching book and recalculates control boundaries. Zero matches show the existing empty state without a fake shelf or book. Additional catalog records extend the same horizontal track instead of requiring hard-coded visual slots.

Base styles remain in `site/css/style.css`; candidate visual tokens and route-specific styles live in `site/css/renaissance.css`. Interactions use the existing vanilla-JavaScript renderer and native links, buttons, inputs, selects, and `details`. No component framework or runtime dependency is introduced.

## Accessibility

Target WCAG 2.2 AA heuristically; this is a design target, not a certification. Use semantic headings, landmarks, lists, and controls; preserve a skip link and visible focus indicator; give icon-only buttons accessible labels; maintain logical keyboard order and avoid custom keyboard traps; communicate status with text and shape as well as color; provide alt text for meaningful original illustrations and empty alt text for decorative art; honor zoom, contrast, Korean text metrics, and reduced motion. Controls should have generous touch targets and visible pressed/selected states.

## Responsive behavior

Verify 320, 360, 390, 768, 1024, 1440, and 1920 CSS-pixel widths. Small screens become a single reading column with large, uncropped cover art; filters stack in a clear order; the header compacts without hiding its destinations; chapter lists remain scannable; and bilingual titles wrap instead of truncating. Medium screens use compact two-column layouts where text remains comfortable. Large layouts use generous margins and readable maximum text widths. Hover styles are enhancements only; every action works on touch and keyboard.

The bookcase keeps full cover art and a physical contact line at every width. Its internal track may overflow horizontally; the page itself must not. A small screen shows roughly two books, a browsing instruction and controls; touch swipe, keyboard focus, and buttons reach later books. Reduced-motion preference removes smooth scrolling and decorative transitions.

### Legibility and cover contract

Preserve each cover's intrinsic aspect ratio and show its complete artwork; never crop a cover to force a uniform card shape. Keep title and supporting text readable at narrow widths and in both languages. The baseline book-detail covers are 72 px at viewport widths up to 360 px and 90 px up to 600 px; the repair contract is to enlarge them while preserving their aspect ratio and full artwork. The five roadmap/detail tag styles use 10–11 px text at baseline; use at least 12 px for these tags, with distinct surfaces and sufficient foreground contrast in both themes. Verify tag wrapping, tap targets, and layout at 200% browser zoom, including long English and Korean text. These values are design requirements for this repair, not an accessibility certification. Recheck cover proportions, tag legibility, wrapping, clipping, contrast, focus, and page overflow for affected routes and states.

## Interaction states

- **Loading:** retain a clear, announced catalog loading state.
- **Empty:** explain which search/filter can be changed; no invented recommendations.
- **Error:** identify the catalog load issue and offer a retry.
- **Success:** filtered result count updates politely and URL reflects current filters.
- **Disabled:** avoid disabled-looking anchors; planned material uses an explicit proposal state and points to the roadmap.
- **Offline/slow network:** the app and all data remain local; if JSON load fails, show the existing recoverable error. No external images or third-party scripts are needed.
- **Theme/language:** persist existing preferences locally when storage is available, continue to work during the current page if storage is unavailable, and expose each control's current action clearly.

## Content voice

Use direct, warm, specific language. Explain the idea or audience in one sentence before metadata. Never imply a book is underway or available unless the record says so. Distinguish a verified experiment from a suggested simulation. Avoid unsupported reading times, reviews, rankings, performance claims, curriculum compliance, fab calibration, or learner outcomes. Keep English and Korean copy parallel in intent, not forced into identical line lengths.

## Implementation constraints

- Preserve the static GitHub Pages `/books/` prefix, flat route shells, `MyLibraryPaths` URL helpers, existing JSON data contracts, and independent textbook deployments.
- Preserve all existing published metadata, all five title/production/Korean/repository links, 74 chapter links, 20 verified experiment anchors, categories, subject maps, learning paths, Mathematics and Learning Journey content, family drafts/proposals, source/provenance/copyright notices, and theme/language controls.
- Preserve publication and release metadata from the current canonical catalog; do not infer publication status from proposals or concept notes. Do not change scientific source prose or edit independent textbook repositories.
- Keep operational version/release facts secondary to reading information. Keep existing accessible keyboard/search/filter behavior.
- Use original optimized inline/static SVG art; no new framework, hosted font, analytics, external runtime API, backend, paid asset, or third-party script.
- Keep the existing Playwright/Python validation commands, add targeted visual/responsive and interaction checks, capture local before/after screenshots, and inspect rendered results before release review.

## Open questions

- [x] Select the Reading Room direction after reviewing all three full-page prototypes and their desktop/mobile screenshots. Owner: renaissance lead. Impact: cover-led composition and warm editorial palette.
- [ ] Independent visual reviewer to assess final screenshots across desktop/tablet/mobile, EN/KO, and light/dark. Owner: renaissance lead. Impact: candidate approval gate.
