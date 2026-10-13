# Existing My Library provenance audit

Reviewed on 2026-10-13 from the public repositories and current My Library pilot/catalog files. This was a read-only document audit; no independent textbook repository or release was modified. The findings distinguish declared project claims from conclusions: topic overlap alone is not copying or infringement.

| Work | Observed provenance | Finding |
| --- | --- | --- |
| PMICBook | Its attribution document identifies ProcessBook as a derivative baseline at `0bc4314d1e13c485a658e0cb1d4fd237b5fc8dff`, maps chapters as CC BY adaptations/translations/merges, and preserves shared MIT notices. Its license separates software and educational material. | **P2.** The documented source/destination chapter map is useful; MIT code reuse is not exhaustively mapped file by file. Improve the code provenance map during maintenance. This is a documentation gap, not an infringement finding. No change made. |
| WATBook | License describes original educational content and software terms separately. `docs/REFERENCES.md` and its overlap/scope review describe upstream texts as cited/reference sources; synthetic examples are labeled. | **Informational.** Current docs distinguish citations from reuse. Recheck embedded assets and pinned revisions when the book changes. No change made. |
| ProcessIntegrationBook | Its license declares book prose/figures/examples and software separately. References, overlap audit, and citation audit state that external books are linked/referenced rather than copied. | **Informational.** Current records identify original content and cited sources. Keep exact source revisions pinned when the audit is refreshed. No change made. |
| HeavyVehicleBook pilot | The three bilingual stories and inline SVG scenes exist only as central-repository editorial pilot material. Its rights notice says no reuse license is granted; the site's MIT software license does not license the story text. It remains unpublished. | **P2 follow-up.** Choose and document the book-level rights for prose and original art before publishing or transferring the pilot. This is not an upstream-rights concern. No change made. |

## Scope limits

The audit reviewed declared licenses, attribution/reference documents, and pilot rights metadata. It did not conduct forensic text similarity analysis, inspect every rendered asset's chain of title, or provide a legal opinion. It does not certify that third-party material is absent. The machine-readable detail is in `catalog/reference-intelligence/provenance-audit.json`.
