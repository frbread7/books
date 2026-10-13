# Reference overlap and editorial differentiation

This framework asks whether a proposed book creates enough value to justify an independently maintained publication. A shared subject or title does not imply duplication or copying. Compare the intended audience, learning outcomes, depth, teaching method, technical support, and maintenance cost.

## Decision outcomes

| Outcome | Use when |
| --- | --- |
| `reference-only` | The existing source sufficiently serves the intended learning goal; link to it. |
| `companion-book` | The theme overlaps, but the audience or reading experience is materially different. |
| `adapt-and-extend` | A clearly licensed subset can be reused and a substantial original contribution is planned; record each source file and required notice. |
| `original-deeper-treatment` | The source is useful context but the proposed course adds clear depth, progression, validation, or an application focus. |
| `defer-or-cancel` | No bounded audience or differentiated result is presently supported. |

Each current assessment pins source repository revisions and relevant chapter paths in `catalog/reference-intelligence/editorial-decisions.json`. That file records editorial judgments separately from automatically observed facts in `inventory.json`. The records are recommendations for current scope, not permanent approval to reuse source expression.

## Current examples

| Proposal | Closest upstream evidence | Current outcome and reason |
| --- | --- | --- |
| FabControlBook | YieldBook statistical/signature/commonality chapters; TestBook limits/DC chapters | **Original deeper treatment.** Focus on control plans, FDC/APC loops, alarm quality, response, and signal lineage. Link to statistical foundations. |
| ThinFilmBook | ProcessBook deposition/epitaxy; DopingBook thermal integration | **Original deeper treatment.** Deepen growth kinetics, nucleation, conformality, interfaces, stress, defects, and film/device impact. |
| ReliabilityEngineeringBook | FailureBook, TCADBook, TestBook, DeviceBook | **Original deeper treatment.** Center degradation physics, acceleration assumptions, censored lifetime analysis, uncertainty, qualification, and field-to-test limits. |
| AlgebraBook | MathBook chapters and applications | **Original deeper treatment.** Build a progressive course through expressions, equations, inequalities, functions, graphs, systems, polynomials, and modeling. |
| CalculusBook | MathBook calculus-related chapters and applications | **Original deeper treatment.** Establish a complete limits-to-multivariable/vector-calculus progression with assumptions and modeling. |
| EngineeringMathBook | MathBook's existing applied mathematics | **Defer or cancel for now.** Its current audience and outcomes are not distinct enough from the planned AlgebraBook, CalculusBook, and subject-specific engineering texts. Reassess after those scopes mature. |
| HeavyVehicleBook | Upstream CarBook and other engineering books | **Companion book.** Preschool story-led experiences integrate a few concepts such as color, counting, shapes, comparisons, vocabulary, and cause/effect. It is not a simplified adaptation of adult engineering content. |
| CarBook | Upstream CarBook | **Companion book.** My Library's proposal is for child-centered bilingual picture stories. Upstream CarBook is a professional automotive engineering title, not a preschool storybook. |
| DinosaurBook | BodyBook and relevant biology/Earth science sources | **Companion book.** A story can introduce fossils, time, habitat, evidence, comparison, and scientific uncertainty. |
| RobotBook | DigitalBook and ComputerBook | **Companion book.** Explore movement, patterns, sequences, and helpful instructions without suggesting robots have human feelings or turning the story into a coding test. |

All comparisons use source revision pins in the JSON file; the linked chapter paths, exact SHAs, confidence, unresolved questions, and reuse strategies are the canonical detail. No proposal has been automatically approved or rejected by an upstream title match.

## Cross-branch interpretation

- Semiconductor books should link to common device, module, measurement, yield, and failure foundations rather than repeating them without a reason.
- Mathematics proposals should distinguish foundational algebra from linear algebra and abstract algebra, and distinguish a complete mathematics course from application chapters inside engineering books.
- Kids & Family stories may share a theme with an adult technical book while having a different audience and learning objective. Shared theme does not authorize reuse of text, art, diagrams, code, or simulator designs.
- The upstream central editorial backlog is inventoried as editorial ideas. It is not a My Library publication catalog and its plans are not treated as completed content.

## Review template

Use [REFERENCE_REVIEW_TEMPLATE.md](REFERENCE_REVIEW_TEMPLATE.md) for new or refreshed assessments. Inspect current source revisions first, then record observed evidence and judgments separately. If rights are uncertain, link to the source or author independently until the exact file-level permission is established.
