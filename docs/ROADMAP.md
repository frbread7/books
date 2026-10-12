# Roadmap

The canonical proposals are in `catalog/roadmap.json`. They are editorial ideas, not repository, release, or publication commitments. Only an explicitly registered book appears in the library catalog; only records with verified release evidence count as published.

Published books have authoritative records and release, deployment, chapter, and experiment evidence in `catalog/books/`. WATBook v1.0.2 corrects release-review and registration metadata only; the original content release v1.0.0 remains recorded in its release history. A published or active book is removed from the unstarted proposal list; future updates use its existing catalog record.

ProcessIntegrationBook v1.0.0 is now the third publication. Its cross-module integration scope complements PMICBook's product-centered BCD treatment and WATBook's parametric measurement-to-decision focus. See its [repository](https://github.com/frbread7/processintegrationbook), [release](https://github.com/frbread7/processintegrationbook/releases/tag/v1.0.0), and [production textbook](https://frbread7.github.io/processintegrationbook/).

## Differentiated semiconductor priorities

| Priority | Candidate | Intended boundary | Existing reference coverage to reuse and link |
| --- | --- | --- | --- |
| 1 | FabControlBook | Operational SPC/FDC/APC, signal quality, control loops, alarm policy, and response workflows. | Upstream YieldBook and TestBook already cover statistical foundations and selected SPC; link those concepts and focus on control-system decisions. |
| 2 | ThinFilmBook | Quantitative thin-film growth, epitaxy, interfaces, materials, and film-specific measurement. | Upstream ProcessBook introduces deposition and epitaxy; a future title must provide a meaningful advanced materials and interface treatment. |
| 3 | ReliabilityEngineeringBook | Failure physics, mechanism-relevant acceleration, lifetime inference, qualification design, and uncertainty. | Upstream FailureBook focuses on failure-analysis methods. PMICBook provides product-level reliability context; link both without repeating their introductions. |
| 4 | RFICBook or MEMSBook | One future specialization selected only after a distinct audience and content gap are established. | Compare with upstream DesignBook, AnalogBook, SensorBook, and relevant MEMS material before choosing either path. |

The reference collection already provides broad device physics, circuit/design, process-module, yield, test, failure-analysis, and product coverage. My Library must keep these external works clearly attributed as independent references, not as books authored or published by this collection. See [the reference audit](REFERENCE_AUDIT.md) and each upstream repository's current license before any reuse.

The roadmap is intentionally short. Future product-specific textbooks can be proposed when they have a clear audience, substantial technical gap, and explicit links to shared foundations. Do not create empty repositories to increase the catalog count.

## Mathematics and lifelong learning

Suggested Mathematics sequence: AlgebraBook, CalculusBook, LinearAlgebraBook, ProbabilityStatisticsBook, DifferentialEquationsBook, NumericalMethodsBook, then EngineeringMathBook. EngineeringMathBook has the highest overlap risk with upstream MathBook and stays lowest priority unless it becomes a method-selection synthesis instead of another subject survey. School/elementary algebra, linear algebra, and abstract algebra remain distinct. See [Mathematics Roadmap](MATHEMATICS_ROADMAP.md).

The family-project proposal is CuriosityBook, a Korean-first illustrated parent-child read-aloud series—not a published book. Its pilot story ideas include a raindrop-and-rain story, an animal-counting story, and a historically researched King Sejong story. Sparse optional taps may enrich illustrations, while uninterrupted read-aloud and complementary printable/offline editions remain available. See [CuriosityBook Specification](CURIOSITYBOOK_SPEC.md).

Kids & Family / Little Explorers is a separate portal collection, not an addition to the canonical roadmap. It contains a proposed HeavyVehicleBook editorial pilot with three complete bilingual draft stories and scope cards for HeavyVehicleBook, CarBook, DinosaurBook, AnimalBook, and RobotBook. None is a book record or publication. See the [Kids & Family portal specification](KIDS_FAMILY_PORTAL_SPEC.md) and [HeavyVehicleBook pilot](HEAVYVEHICLEBOOK_PILOT.md).

The Learning Journey contains separate editorial curriculum-map entries for six flexible stages and eleven strands. Official source versions and review dates are documented in [Curriculum Sources](CURRICULUM_SOURCES.md); its data and privacy contract is in [Learning Journey](LEARNING_JOURNEY.md). Concepts do not count as books, and stage bands do not make a placement or curriculum-compliance claim.
