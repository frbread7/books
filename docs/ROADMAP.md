# Roadmap

The canonical proposals are in `catalog/roadmap.json`. They are editorial ideas, not repository, release, or publication commitments. Only an explicitly registered book appears in the library catalog; only records with verified release evidence count as published.

WATBook v1.0.2 is the current published release in `catalog/books/watbook.json`, with release, deployment, chapter, and experiment evidence. It corrects release-review and registration metadata only; the original content release v1.0.0 remains recorded in its release history. WATBook has been removed from the unstarted proposal list; future updates must use the existing catalog record rather than treating it as a new roadmap idea.

PMICBook and WATBook are the only published titles in the current catalog. ProcessIntegrationBook remains the highest semiconductor priority; its active effort is marked `workState: active-project` while its publication status stays `planned` until release evidence passes.

## Differentiated semiconductor priorities

| Priority | Candidate | Intended boundary | Existing reference coverage to reuse and link |
| --- | --- | --- | --- |
| 1 | ProcessIntegrationBook | Advanced cross-module interactions, thermal/material budgets, technology co-optimization, and integration learning. | Upstream ProcessBook surveys process modules; this title must teach the constraints between them, not repeat the survey. PMICBook remains a BCD product example. |
| 2 | FabControlBook | Operational SPC/FDC/APC, signal quality, control loops, alarm policy, and response workflows. | Upstream YieldBook and TestBook already cover statistical foundations and selected SPC; link those concepts and focus on control-system decisions. |
| 3 | ThinFilmBook | Quantitative thin-film growth, epitaxy, interfaces, materials, and film-specific measurement. | Upstream ProcessBook introduces deposition and epitaxy; a future title must provide a meaningful advanced materials and interface treatment. |
| 4 | ReliabilityEngineeringBook | Failure physics, mechanism-relevant acceleration, lifetime inference, qualification design, and uncertainty. | Upstream FailureBook focuses on failure-analysis methods. PMICBook provides product-level reliability context; link both without repeating their introductions. |
| 5 | RFICBook or MEMSBook | One future specialization selected only after a distinct audience and content gap are established. | Compare with upstream DesignBook, AnalogBook, SensorBook, and relevant MEMS material before choosing either path. |

The reference collection already provides broad device physics, circuit/design, process-module, yield, test, failure-analysis, and product coverage. My Library must keep these external works clearly attributed as independent references, not as books authored or published by this collection. See [the reference audit](REFERENCE_AUDIT.md) and each upstream repository's current license before any reuse.

The roadmap is intentionally short. Future product-specific textbooks can be proposed when they have a clear audience, substantial technical gap, and explicit links to shared foundations. Do not create empty repositories to increase the catalog count.

## Mathematics and lifelong learning

Suggested Mathematics sequence: AlgebraBook, CalculusBook, LinearAlgebraBook, ProbabilityStatisticsBook, DifferentialEquationsBook, NumericalMethodsBook, then EngineeringMathBook. EngineeringMathBook has the highest overlap risk with upstream MathBook and stays lowest priority unless it becomes a method-selection synthesis instead of another subject survey. School/elementary algebra, linear algebra, and abstract algebra remain distinct. See [Mathematics Roadmap](MATHEMATICS_ROADMAP.md).

The family-project proposal is CuriosityBook, a Korean-first illustrated parent-child read-aloud series—not a published book. Its pilot story ideas include a raindrop-and-rain story, an animal-counting story, and a historically researched King Sejong story. Sparse optional taps may enrich illustrations, while uninterrupted read-aloud and complementary printable/offline editions remain available. See [CuriosityBook Specification](CURIOSITYBOOK_SPEC.md).

The Learning Journey contains separate editorial curriculum-map entries for six flexible stages and eleven strands. Official source versions and review dates are documented in [Curriculum Sources](CURRICULUM_SOURCES.md); its data and privacy contract is in [Learning Journey](LEARNING_JOURNEY.md). Concepts do not count as books, and stage bands do not make a placement or curriculum-compliance claim.
