# Visual renaissance: concept rationale

**Review date:** 2026-10-19

**Status:** Three concepts reviewed; Reading Room selected for the local candidate.

This note records what is visible in the three static concept pages and their checked-in desktop and 390 px screenshots. It is a comparative design review, not a usability study or accessibility certification. The concepts are [The Reading Room](../design/prototypes/reading-room.html), [The Engineering Atlas](../design/prototypes/engineering-atlas.html), and [The Monograph Gallery](../design/prototypes/monograph-gallery.html). Corresponding screenshots are in [`design/prototypes/screenshots/`](../design/prototypes/screenshots/).

## Comparison

Ratings describe the displayed concept: **Strong** means the direction clearly supports the criterion in both page structure and screenshot; **Mixed** means it supports it with a visible trade-off; **Limited** means the current preview provides little evidence or has an evident drawback. Ratings do not replace testing the implemented site.

| Criterion | Reading Room | Engineering Atlas | Monograph Gallery |
| --- | --- | --- | --- |
| 1. Published books have visual presence | **Strong** — large featured cover and a shelf for all five. | **Mixed** — covers sit within a map metaphor; individual titles are less dominant. | **Strong** — large cover display and an edition-like five-book grid. |
| 2. Entry to a real book or chapter is clear | **Strong** — “Start with a chapter” and “Open book” links are visible. | **Strong** — subject entry and a chapter CTA accompany book links. | **Strong** — direct PMICBook and contents actions are present. |
| 3. Subject relationships are understandable | **Mixed** — the page emphasizes reading and collection more than subject relations. | **Strong** — routes and labeled subject nodes make the organizing metaphor explicit. | **Mixed** — subject names appear in the edition descriptions, with no visible map. |
| 4. Five titles can be scanned and compared | **Strong** — horizontal desktop shelf; two-column mobile shelf. | **Mixed** — detailed, colorful rows are easy to parse but tall, including on mobile. | **Strong** — consistent edition cards form a five-title grid, including two columns on mobile. |
| 5. Published and proposed material stay distinct | **Strong** — the collection and family preview are separate sections with explicit draft wording. | **Strong** — “Published routes” and “unpublished” story-draft copy are explicit. | **Strong** — “current editions” and “future proposals” are explicitly labeled. |
| 6. Little Explorers has a distinct, calm identity | **Strong** — warm landscape art and a separate family section. | **Mixed** — separate family section, but it shares the dark atlas page and route metaphor. | **Strong** — separate pale-green family section and clear draft language. |
| 7. Mobile page hierarchy remains clear at 390 px | **Mixed** — sections stack and the book shelf becomes two columns; the header links wrap into a second row. | **Mixed** — single-column routes are clear but make the page long; header links fit in a tight row. | **Mixed** — two-column edition cards are compact; the header navigation is visibly clipped at the right edge. |
| 8. Bilingual layout readiness is demonstrated | **Limited** — previews show English copy and a nonfunctional EN preview marker. | **Limited** — previews show English copy and a nonfunctional EN preview marker. | **Limited** — previews show English copy and a nonfunctional EN preview marker. |
| 9. Accessibility behavior is demonstrated | **Limited** — semantic landmarks and a skip link are present in markup, but screenshots do not verify keyboard, contrast, or assistive-technology behavior. | **Limited** — same evidence boundary; visible map art is marked decorative. | **Limited** — same evidence boundary; preview does not establish control behavior or full-page accessibility. |
| 10. Visual identity matches an illustrated independent library | **Strong** — warm paper, restrained ink/rust palette, and cover-led reading-room scene. | **Mixed** — memorable deep-blue atlas treatment, but the map metaphor and dark canvas dominate the books. | **Strong** — restrained gallery presentation makes the local covers the main visual subject. |
| 11. Implementation and maintenance fit the static site | **Strong** — cover shelf, native links, and existing data-driven cards fit the current HTML/CSS/JS; artwork remains replaceable SVG. | **Mixed** — the labeled atlas relationships need more route-specific layout work and upkeep when maps change. | **Strong** — the repeated card system is simple, though long canonical titles need careful responsive tuning. |
| 12. Originality and professional credibility | **Strong** — distinct local covers carry the subject matter without decorative pseudo-data. | **Mixed** — the route metaphor is memorable, but its dark technical panels can suggest a dashboard more than a library. | **Strong** — quiet edition framing supports credible books, though it is less expressive about subject connections. |

These observations come from the named HTML pages and supplied screenshots only. They do not prove that navigation destinations work, that layouts hold at other widths, or that the pages meet WCAG. The small screenshots also show a navigation fit issue in Reading Room and visible clipping in Monograph Gallery; Atlas keeps its links in one narrow row. Resolve header behavior in whichever direction is selected.

## Original art and provenance

The three concept pages reference the five local SVG cover files in `site/assets/covers/`: `pmicbook.svg`, `watbook.svg`, `processintegrationbook.svg`, `fabcontrolbook.svg`, and `thinfilmbook.svg`. The family illustrations in the concept pages are inline SVG authored in each prototype HTML file. The separate `site/assets/little-explorers/heavy-vehicle-worksite.svg` is a local illustrated asset used by the wider project. No remote image URLs or external image dependencies appear in these concept pages.

The markup and assets inspected here show project-local vector artwork and no visible third-party image attribution. The candidate art was drawn as SVG markup in this worktree by Codex agents for this redesign; the five covers revise existing project-local SVG paths and the four Little Explorers illustrations are new files. That production history does not independently establish copyright ownership or prove that every possible influence was excluded. The asset inventory below records the observed files and source boundary for owner review before publication. Do not treat visual references listed in [DESIGN.md](../DESIGN.md) as asset sources or reuse permissions. The existing project rights workflow is in [COPYRIGHT_AND_PROVENANCE.md](COPYRIGHT_AND_PROVENANCE.md).

| Candidate asset | Visual subject | Source and reuse record |
| --- | --- | --- |
| `site/assets/covers/pmicbook.svg` | Power distribution from a central device | Revised project-local SVG; no imported image or external asset reference. |
| `site/assets/covers/watbook.svg` | Wafer measurement field and probe | Revised project-local SVG; no imported image or external asset reference. |
| `site/assets/covers/processintegrationbook.svg` | Layered process cross-section | Revised project-local SVG; no imported image or external asset reference. |
| `site/assets/covers/fabcontrolbook.svg` | Tool, decision, and feedback loop | Revised project-local SVG; no imported image or external asset reference. |
| `site/assets/covers/thinfilmbook.svg` | Film growth over a substrate | Revised project-local SVG; no imported image or external asset reference. |
| `site/assets/little-explorers/heavy-vehicle-worksite.svg` | Fenced worksite viewed from a public path | New project-local SVG; no imported image or external asset reference. |
| `site/assets/little-explorers/dinosaur-fossil-field-guide.svg` | Fossil field notebook | New project-local SVG; no imported image or external asset reference. |
| `site/assets/little-explorers/wildlife-habitat.svg` | Quiet pond habitat | New project-local SVG; no imported image or external asset reference. |
| `site/assets/little-explorers/helpful-robot-machine.svg` | Tabletop robot sorting shapes | New project-local SVG; no imported image or external asset reference. |

## Reader specimen boundary

The separate [`design/reader/` specimen handoff](../design/reader/handoff.md) describes a local static visual specimen, not a hosted book or a textbook integration. Its constraints remain: use only owner-approved licensed content; map chapters, languages, and themes to the owning textbook's canonical data; preserve semantic structure, keyboard operation, focus, reduced motion, localized accessible names, and natural Korean wrapping; coordinate any persistence key with the reader owner. The illustrative prose and equation in that specimen are not technical source material. This concept comparison does not authorize integrating it into a published book.

## Decision and next evidence

**Primary concept:** The Reading Room, with clearer subject discovery borrowed from the Engineering Atlas.

**Decision owner:** renaissance lead. The cover-led composition makes the five published titles the strongest visual signal, keeps one verified chapter close to the opening view, and allows Little Explorers to have its own warm illustration space. The Atlas is better at subject relationships, so the candidate adds editorial subject tiles after the book shelf. The Gallery supports comparison but its long-title treatment and clipped mobile header make it a weaker base.

**Evidence to collect before candidate completion:** resolved mobile header behavior; bilingual and light/dark implementation review; keyboard, responsive, and accessibility checks documented in the [QA report](VISUAL_RENAISSANCE_QA.md).
