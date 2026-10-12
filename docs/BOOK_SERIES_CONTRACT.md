# Book series contract

## Repository and release boundary

- One independently authored, reviewed, versioned, licensed, and deployed textbook per repository.
- My Library stores metadata and links; it does not copy chapters or redeploy books.
- A record describes the ownership and evidence it actually has. Independent reference books remain credited as their own projects and authors; they are not My Library publications.
- Upstream educational material or code is reused only after checking its current license and preserving the required notices and attribution. Prefer original prose, examples, and assets.

## Manifest rules

- Use a stable unique lowercase ID/slug and a matching `catalog/books/<id>.json` filename.
- Provide bilingual catalog metadata; `languages` must reflect editions that actually exist on the book's production site.
- `chapterCount` must equal the chapter index; chapter IDs/numbers are unique and URLs point to real pages on the declared production host.
- Experiments point to existing chapters and real anchors. A published experiment includes successful live URL, fragment, response-hash, and deployed-revision evidence.
- Prerequisites and related IDs reference registered books. Use empty lists if no published relationship is supported.
- Covers are original portal assets; colors and metadata pass the schema and semantic checks.
- A proposal is `planned` in `catalog/roadmap.json`. As soon as work is registered, it is `in-progress` in `catalog/books/` and removed from the roadmap. Do not list one ID in both places.
- `published` requires a real versioned release, successful production deployment revision, content review, site verification, and chapter checks. Books with experiments also need live experiment checks. The status is never inferred from a repository existing or a scaffold running.

## Content boundaries

PMICBook is the first My Library publication and owns its PMIC systems, circuit architecture, BCD applications, and product-level examples. Its current portal version and evidence must agree with the actual latest release and Pages deployment.

WATBook's distinct scope is professional wafer-level parametric measurement-to-decision: monitor intent and coverage, measurement conditions, extraction conventions, measurement uncertainty and validity, wafer/lot hierarchy and coordinate context, signatures as bounded process hypotheses, and the limits of WAT-to-EDS inference. It links to upstream DeviceBook for device physics/extraction foundations, ProcessBook for module coverage, TestBook for general prober and test-method material, YieldBook for statistical/spatial foundations, and FailureBook for failure-analysis methods. These reference books remain independent upstream works. WATBook must not repeat their generic device, TLM, SPC, yield, probing, or FA material.

ProcessIntegrationBook focuses on cross-module constraints and technology co-optimization beyond upstream ProcessBook's broad module survey. FabControlBook focuses on control-loop design, FDC/APC, alarms, signal quality, and response beyond the generic statistical tools already introduced by upstream YieldBook/TestBook. ThinFilmBook may deepen quantitative growth, interfaces, and materials beyond upstream ProcessBook's deposition/epitaxy introduction. ReliabilityEngineeringBook covers mechanism-based lifetime and qualification, distinct from FailureBook's localization/physical-analysis methods and PMICBook's product context.

Future RFIC or MEMS scope remains an editorial choice, not two commitments. Compare proposed content with upstream DesignBook, AnalogBook, SensorBook, and other relevant references before approving a new title. Product-specific process details belong in their product book and should link to shared foundations.

## Review status

A scaffold or in-progress registration is not publication. Internal reviewer-agent assessment is an engineering quality gate, not external certification, foundry approval, or laboratory validation. Numerical model labels must distinguish illustrative, analytically checked, numerically cross-checked, and externally reference-checked work. Synthetic examples must be labeled as synthetic.
