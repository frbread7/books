# Reader specimen handoff

## Purpose and status

This folder contains a locally runnable, static design specimen for a future bilingual textbook reader. It is not a hosted-book change, a deployed route, or an edit to any textbook repository. All chapter prose and examples are newly written illustrative UI content; they do not quote, describe, or revise PMIC, WAT, process integration, or other textbook material.

Open `index.html` directly, or serve this folder with any static HTTP server. The specimen has no network calls, remote fonts, images, packages, or third-party resources. The repository is a static HTML site with Node/Playwright validation tooling (`package.json`); this artifact uses plain semantic HTML, CSS, and browser JavaScript to stay portable and isolated.

## Design choices

- **Purpose and tone:** support sustained technical reading with a composed, book-like page that keeps context and navigation close without competing with the text.
- **Differentiator:** a narrow, persistent chapter rail on desktop becomes a native collapsible outline on smaller screens. It remains supplemental to the chapter heading and text.
- **Typography:** system serif stacks for long-form copy and headings, system sans serif for controls and labels. The measure is capped near 66 characters. Korean uses a Korean serif stack, taller line spacing, `word-break: keep-all`, and normal wrapping rather than fixed-width glyph assumptions.
- **Color:** warm paper, dark ink, muted rust, and sage. CSS custom properties provide paired light and dark palettes. Accent blocks label questions and reminders.
- **Motion:** brief color transitions and native smooth anchor scrolling. Both are reduced when `prefers-reduced-motion: reduce` is set.
- **Responsive layout:** a two-column page at wide widths; a single column with a collapsible contents list below 800px; compressed header controls and one-column contents list below 460px. The comparison table has a labeled, keyboard-focusable horizontal scroll region.

## Integration contract for a future textbook owner

This specimen is a visual and interaction reference, not an application integration. A future reader implementation can preserve these behaviors while mapping them to the textbook's canonical chapter, language, and theme data:

1. Keep the book and current chapter visible near the top, followed by a clear chapter title and short orientation text.
2. Give every contents entry a real in-page anchor. Keep the outline supplemental and ensure it does not cover text while scrolling.
3. Preserve semantic heading order, table captions and scoped headers, and labeled note/callout regions. Use a semantic math representation and an equivalent localized accessible name for equations.
4. Treat translations as authored content, not machine substitutions. Preserve natural Korean wrapping and give translated controls, labels, and accessible names the active language.
5. Keep language and theme controls keyboard operable with visible focus and explicit pressed state. Respect reduced-motion preferences.
6. Keep any future persistence key app-specific and coordinate with the owning reader; this specimen currently uses `reader-specimen-theme` only for its local theme preference.
7. Replace the illustrative copy only with owner-approved, licensed textbook content. Do not use this specimen as a source of technical claims.

The static file boundary is `index.html` + `reader.css` + `reader.js`. The translation object in `reader.js` uses each element's `data-copy` key. The chapter outline targets stable section IDs: `begin`, `notice`, `compare`, `model`, `practice`, and `reflect`.

## Accessibility states and behavior

- A visible-on-focus skip link moves keyboard users to the chapter title.
- Header settings use native buttons. The language buttons expose `aria-pressed`; the theme button exposes `aria-pressed` and changes the page palette. `Tab`, `Shift+Tab`, `Enter`, and `Space` use native keyboard behavior.
- The contents outline uses native `<details>` and `<summary>`. It opens by default on wide layouts and collapses by default on mobile; activating a mobile contents link closes it.
- The active section is indicated on its corresponding contents link with `aria-current="location"` when `IntersectionObserver` is available. All contents links remain valid anchors without it.
- Callouts have note semantics and labels. The comparison table has a caption, column and row headers, and a named scroll region. The equation is exposed as math with a localized accessible name.
- Focus rings use a high-visibility outline. Dark and light palettes keep text and surfaces distinct; the `prefers-reduced-motion` media query suppresses animated transitions and smooth scrolling.
- EN and KO update visible copy, document language, control names, table-region name, equation name, and pressed states together.

## Content and provenance note

The chapter title, examples, table entries, formula-like relationship, and bilingual copy are fabricated solely to show reader layout and interaction. “What we observed + the context = a useful account” is an illustrative reading aid, explicitly not a scientific equation or textbook claim. This folder contains no borrowed covers, screenshots, published textbook prose, or textbook data. The specimen is a local design artifact only and has not changed a hosted book or a textbook source repository.
