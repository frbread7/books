# Project agent rules

## Visual quality work

- Inspect the current implementation and the affected rendered pages before proposing or making UI changes. Preserve existing behavior and architecture unless the task calls for a change.
- Treat screenshots as evidence for the exact route, viewport, language, theme, content, and build they capture. Do not describe capture success or an automated overflow check as a visual pass. Record the image paths and inspect the actual images.
- For every materially changed page family or state, inspect rendered images before and after the change. Cover the relevant routes, English and Korean, light and dark themes, responsive widths, and realistic long titles/content. Inspect every materially changed family/state; a large capture matrix alone does not satisfy this requirement.
- Check DOM-visible content, computed contrast, clipping, focus, and horizontal overflow alongside images. Distinguish page-level overflow from intentionally scrollable regions such as the book shelf. Include synthetic catalog sizes and varied title lengths when a change affects data-driven layouts.
- For overflow checks under mobile emulation, use `document.documentElement.clientWidth` as the layout viewport. Record `scrollWidth`, `innerWidth`, and `visualViewport.width` separately; comparing only `scrollWidth` with `innerWidth` can hide an overflowing layout. Exempt only documented internal scrollers such as `.bookcase-viewport`.
- Measure touch targets and spacing in rendered CSS pixels, including the nearest distance between adjacent targets. A browser assertion must check the actual affected breakpoint and each configured viewport project.
- Report text contrast separately from surface/border separation. Do not label a fill-to-background ratio as text contrast or as WCAG non-text conformance.
- Label narrow-width/high-DPR tests as zoom proxies. Do not claim native browser or operating-system zoom certification unless that mode was actually exercised.
- Before capture, verify the local server belongs to this worktree and that served asset hashes match the candidate files. Record both viewport metrics and image/console diagnostics in a local manifest. Capture count and zero automated diagnostics are evidence, not a visual pass.
- For substantial UI changes, obtain an independent adverse review of the rendered evidence and reported defects. Record reviewer scope, findings, disposition, and unreviewed states; do not claim independent review without evidence.
- Keep a visual defect register with evidence, severity (P0–P3), status, and links to reproducible artifacts. Separate observed facts from inference and unknown context. Keep before/after captures and coverage results in the report.
- Do not infer what a user's screenshot depicts when its route, viewport, language, theme, content, and build are unknown. Ask for or record the missing context, and proceed only with conclusions supported by available artifacts.

## Repository and release boundaries

- Keep changes small and reviewable. Do not alter catalog facts, scientific content, publication state, route contracts, or product scope as part of a visual repair without explicit task scope.
- Use local verification. Do not create, trigger, rerun, or rely on GitHub-hosted Actions, and do not push by default. Inspect and report local evidence separately from remote deployment, CI, and physical-device results.
- Do not publish or deploy a candidate as part of visual QA unless the task explicitly authorizes that external action.
