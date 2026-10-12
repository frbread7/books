# Mathematics collection and first advanced-textbook specification

**All titles below are proposals.** They live in `catalog/roadmap.json` under `mathematicsBooks`; none appears in `catalog/books/` or the published catalog. Their localized audience, questions, proposed chapter groups, prerequisites, relationships, boundaries, and interactive ideas are the canonical roadmap fields.

## Subject graph and book boundaries

`catalog/roadmap.json` is the machine-readable book-level graph. Each proposed math title carries `prerequisiteIds`; the validator rejects unknown nodes, duplicate/self edges, and cycles. The current suggested-preparation edges are:

~~~text
AlgebraBook → CalculusBook → DifferentialEquationsBook → EngineeringMathBook
AlgebraBook → LinearAlgebraBook → NumericalMethodsBook → EngineeringMathBook
AlgebraBook → ProbabilityStatisticsBook ─────────────────→ EngineeringMathBook
CalculusBook ───────────────────────────→ NumericalMethodsBook
LinearAlgebraBook ──────────────────────→ EngineeringMathBook
~~~

These are editorial links among planned titles, shown as preparation pointers in the roadmap. They are not enrollment requirements, learner gates, age placements, or claims of universal sequencing. Some courses can be studied in parallel; the separate Learning Journey concept graph uses its own stable concept IDs.

The Learning Journey uses a six-stage representative Mathematics thread: play with quantity/pattern → number and operations → fractions/measurement/proportional reasoning → algebraic relationships → functions/trigonometry/change → university mathematical models. The age/stage map is flexible editorial guidance. Concept nodes have stable IDs and explicit links; they are not official achievement standards or a universal prerequisite law.

Three different meanings of “algebra” must remain separate:

- **Elementary/school algebra** (AlgebraBook): symbolic expressions, equations, inequalities, systems, and functions. Its job is to make school/early-college symbolic reasoning coherent.
- **Linear algebra** (LinearAlgebraBook): vector spaces, bases, dimension, linear maps, matrices, eigenstructure, least squares, and conditioning.
- **Abstract algebra**: groups, rings, fields, and other algebraic structures. It is not implied by AlgebraBook or LinearAlgebraBook; it remains a separate future university-level branch unless a distinct need and roadmap proposal are approved.

## Differentiation from upstream MathBook

The audited [`geniuskey/mathbook`](https://github.com/geniuskey/mathbook/tree/ca108356c078b119f43aee56430cca7be10d2972) is a useful Korean-first, application-oriented engineering mathematics book. Its 13 chapters touch calculus, complex numbers/matrices, ODE/PDE, Fourier methods, sampling, probability, information, optimization, numerical analysis, geometry, symmetry, and group-algebra ideas. It provides interactive application tools and describes itself as a shared foundation layer for its own series.

My Library’s candidates are differentiated course-scale or role-specific texts, not alternate catalog names for MathBook chapters. Link upstream examples where useful; do not copy its prose, figures, or tools. MathBook’s license separates MIT software from CC BY 4.0 content; any actual reuse would require a file-specific license and attribution review. This roadmap uses source facts and links only.

| Candidate | Distinct purpose and boundary | MathBook overlap | Suggested order |
| --- | --- | --- | ---: |
| AlgebraBook | Fill the school/early-college symbolic algebra and function prerequisite gap; exclude vector-space and abstract-algebra theory. | Algebra appears within applications, not as a systematic prerequisite course. | 1 |
| CalculusBook | Complete, scaffolded course in limits, continuity, derivatives, integrals, series, and possibly multivariable methods with assumptions and error. | MathBook has selected applied calculus material; link rather than repeat. | 2 |
| LinearAlgebraBook | Develop vector spaces/maps, proofs, conditioning, and numerical linear algebra beyond intuitive matrix applications. | MathBook includes a matrix/linear-algebra application chapter. | 3 |
| ProbabilityStatisticsBook | Teach distributions, sampling, inference, design, dependence, and uncertainty communication. | MathBook touches probability, Bayes, sampling, and information; WATBook/PMICBook use selected statistics. | 4 |
| DifferentialEquationsBook | Teach formulation, initial/boundary conditions, existence/behavior, stability, and numerical limits systematically. | MathBook has application-first ODE/PDE material. | 5 |
| NumericalMethodsBook | Teach error, conditioning, convergence, stability, reproducibility, and method selection. | MathBook has selected numerical analysis examples; use them only as comparisons. | 6 |
| EngineeringMathBook | Lowest-priority synthesis/method-selection handbook across the collection. | Very high: MathBook already connects many engineering mathematics applications. Proceed only if a genuine selection/synthesis gap emerges. | 7 |

## First advanced-mathematics textbook: CalculusBook

**Recommendation:** after the AlgebraBook foundation is authored and reviewed, make CalculusBook the first advanced mathematics textbook. It supports the widest set of later study: differential equations, numerical methods, engineering models, and advanced probability. This is an editorial sequence, not a universal institutional prerequisite rule; the [MIT 2026–2027 mathematics catalog](https://catalog.mit.edu/degree-charts/mathematics-course-18/) is one example, not a global standard.

- **Audience:** advanced high-school learners and first-year university students entering science, engineering, or further mathematics.
- **Prerequisites:** fluent school algebra and functions, trigonometry, and coordinate geometry. Linear algebra may run in parallel. State alternate pathways and do not present age as proof of readiness.
- **Chapter groups:** functions/limits/continuity; derivative definitions and applications; approximation and optimization; integral and accumulation; Fundamental Theorem; sequences/series and convergence; optional multivariable calculus/vector fields after editorial scoping.
- **Interactive concept:** an error-aware calculus laboratory where learners compare derivative limits to finite differences, vary partition size in an integral, inspect convergence, and see approximation error and assumptions. Reset/reference cases should have analytical checks; the interface must label simplified models and numerical precision.
- **Boundary with MathBook:** teach a complete, progressive course with consistent notation, derivations/proofs at an appropriate level, convergence and error reasoning, exercises, and references. MathBook’s short application-oriented calculus explanations stay upstream; link them as contextual examples rather than duplicating text or interactions.
- **Editorial gate:** source-supported equations and examples, bilingual terminology review, prerequisite review, independent mathematics review, and numerical cross-checks for every interactive calculation before Book Factory publication evidence is recorded.

## Future maintenance

When a proposal changes, update the canonical JSON and rerun `python3 tools/book_factory.py generate` plus `npm test`. If actual content authoring starts, maintain its planned roadmap status and record in-progress state separately until publication criteria pass. After a real book is released, remove the proposal record and register its independently deployed manifest through Book Factory; published counts derive only from that manifest. Do not create repositories for proposals to make the shelf appear full.
