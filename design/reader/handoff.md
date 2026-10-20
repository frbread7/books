# Reader specimen handoff

## Purpose and status

This folder contains a locally runnable, static design specimen for a future bilingual textbook reader. It is not a hosted-book change, a deployed route, or an edit to any textbook repository. All chapter prose, the ideal DC calculation, and its SVG circuit are newly written or drawn illustrative UI content; they do not quote, describe, or revise PMIC, WAT, process integration, or other textbook material.

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

### Scientific reading rules

- **Equations:** preserve the owner's formula, variable names, sign convention, significant figures, and units exactly. Place symbol definitions and assumptions beside the equation. Show worked arithmetic with dimensional consistency and an accessible linear reading in each language. If a formula needs MathML or another renderer, the textbook owner chooses and validates that implementation; this specimen's `role="math"` is only a layout example.
- **Diagrams and figures:** give each figure an owner-approved caption, a descriptive text alternative that states relationships rather than colors alone, and legible labels at mobile and zoom sizes. Keep axes, scales, units, legends, uncertainty, and provenance intact for scientific plots. Do not put decorative artwork over plotted data or redraw a technical figure from memory. The original ideal circuit here is a presentation specimen, not a diagram to copy into a real chapter.
- **Tables and callouts:** retain table captions, scoped header cells, units in column headings, source notes, and horizontal access on narrow screens. Label callouts by purpose (question, definition, safety, or limitation), place them next to the passage they qualify, and do not move a caveat away from the claim it limits.
- **Experiments and links:** place each experiment next to the relevant explanation and keep its owner-verified anchor and expected state. Avoid promoting an experiment or chapter to published unless the canonical source confirms that status. Keep links, citation targets, and cross-references stable during layout work.

### Safe integration sequence

1. The textbook owner creates or authorizes a **separate branch in that textbook repository**. Record the canonical chapter files, translation source, figure provenance/license, experiment anchors, and the current publication state before changes.
2. Copy only the reader's layout and interaction patterns into the book's existing architecture. Map chapter text, equations, tables, figures, language, theme, links, and contents entries to canonical owner data. Do not import the fictional prose or ideal circuit as textbook content.
3. Have the textbook owner reconcile every moved passage, formula, unit, figure, caption, table, callout, citation, and experiment link against the unchanged source. Any scientific correction or translation change is a separate owner-reviewed content decision, never an incidental reader styling edit.
4. Capture visual diffs of representative long and short chapters, equations, diagrams, tables, callouts, and experiments at mobile and desktop widths in English and Korean, light and dark. Check full keyboard navigation, visible focus, text zoom, reduced motion, print layout, and screen-reader reading order with the owner; verify figure alternatives and spoken math.
5. Run that textbook's local content/build/link and browser tests, then obtain subject-owner review of scientific meaning and accessibility review before integration. Merge through the owner's normal process only after the source/content reconciliation and test evidence are accepted. Keep the My Library portal and textbook release decisions separate.

The static file boundary is `index.html` + `reader.css` + `reader.js`. The translation object in `reader.js` uses each element's `data-copy` key. The chapter outline targets stable section IDs: `begin`, `notice`, `compare`, `model`, `practice`, and `reflect`.

## Accessibility states and behavior

- A visible-on-focus skip link moves keyboard users to the chapter title.
- Header settings use native buttons. The language buttons expose `aria-pressed`; the theme button exposes `aria-pressed` and changes the page palette. `Tab`, `Shift+Tab`, `Enter`, and `Space` use native keyboard behavior.
- The contents outline uses native `<details>` and `<summary>`. It opens by default on wide layouts and collapses by default on mobile; activating a mobile contents link closes it.
- The active section is indicated on its corresponding contents link with `aria-current="location"` when `IntersectionObserver` is available. All contents links remain valid anchors without it.
- Callouts have note semantics and labels. The comparison table has a caption, column and row headers, and a named scroll region. The equation is exposed as math with a localized accessible name.
- Focus rings use a high-visibility outline. Dark and light palettes keep text and surfaces distinct; the `prefers-reduced-motion` media query suppresses animated transitions and smooth scrolling.
- EN and KO update visible copy, document language, control names, table-region name, equation name, and pressed states together.

## Local review script

Run `node design/reader/check.cjs /tmp/books-renaissance-reader-capture` from the My Library repository root for the eight width/language/theme screenshots and automated state, anchor, accessible-name, formula, and overflow checks. Then open `design/reader/index.html` directly and perform these manual checks before passing the design to a textbook owner:

1. At desktop and a 390 px viewport, tab from the skip link through settings and chapter contents. Verify visible focus, correct anchor targets, and that mobile contents close after selection.
2. Switch EN/KO and light/dark. Read the circuit title, description, labels, caption, and equation aloud; verify all stated quantities and the direction from positive terminal through the resistor remain understandable without color.
3. At mobile width, keyboard-scroll the comparison table to its last column. Increase text zoom and inspect the equation and diagram for clipping; check reduced-motion and print layouts.
4. For any actual textbook integration, repeat with a screen reader and the textbook's real figures, math, experiments, and long chapters. Record the device, browser, assistive technology, and any content-owner sign-off; the local automated script does not perform these checks.

## Content and provenance note

The chapter title, general observation examples, table entries, and bilingual copy are fabricated solely to show reader layout and interaction. The Ohm's-law arithmetic is an original elementary ideal-circuit specimen: 6 V / 1.0 kΩ = 6 mA, under the assumptions stated beside it. The SVG is original. Neither is a measurement, a copied textbook figure, or a claim about a hosted book. This folder contains no borrowed covers, screenshots, published textbook prose, or textbook data. The specimen is a local design artifact only and has not changed a hosted book or a textbook source repository.
