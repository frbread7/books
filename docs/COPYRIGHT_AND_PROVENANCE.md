# Copyright, licenses, and provenance workflow

This workflow records what a project actually reuses and what notices it preserves. It does not automatically certify legal compliance and is not professional legal advice.

## Material classifications

Use one classification for each source/destination mapping:

- `original`: independently authored expression informed by research; keep citations for factual claims.
- `reference-only`: cite or link to a source without reproducing its protected expression.
- `cc-by-4.0-adaptation`: text, illustration, question, diagram, or other material adapted under verified CC BY 4.0 terms.
- `mit-code-reuse`: software reused under its applicable MIT license, with required copyright and license notices retained.
- `third-party-material`: an asset, data set, standard, font, image, component, or other material with a distinct rights record.
- `license-uncertain`: ownership, scope, or permissions are unresolved. Do not incorporate the material into a release until reviewed.

Repository metadata such as SPDX `NOASSERTION`, a repository-level license badge, a README statement, subject overlap, or a license on neighboring files does not by itself establish the rights for an individual asset or embedded work. Several upstream repos explicitly separate executable/source code from educational prose and figures. Inspect the exact file and current commit, the repository's detailed license terms, and applicable third-party notices.

## Required assessment record

Every published book must have at least one explicit rights/provenance assessment. An assessment is not an assertion that every possible source has been found: its `summary`, `auditScope`, source evidence, rights observation, and destination identify what was actually reviewed. Do not leave `reuseRecords` empty.

For `original` material, identify the reviewed source location, the destination, and a `rightsStatus` that distinguishes copyright in prose/art from the software license. For `third-party-material`, identify the specific title/asset, creator or credited publisher, source path or asset ID, source URL or repository, exact license name and URL, `rightsStatus`, restrictions (including an explicit statement when none are identified), required notices, destination, and `noticeLocation` in the product or its notices page. External web pages, standards, and datasets do not need to be Git repositories; use `sourceUrl` and identify the relevant page/table/asset in `sourcePath`. If rights cannot be established, classify the material as `license-uncertain`, record the follow-up, and do not incorporate it into a release.

For `reference-only`, identify the source/revision and relevant paths, the citation destination, and state that no protected expression/code/assets were copied. For a GitHub source, pin a full commit SHA; for another source, record a stable URL and access/version date where available.

## Required record for adaptation or code reuse

Record the original work title, author/publisher attribution, exact source location, source URL, applicable license and license URL, required notice, changes made (including translation), and destination path. For GitHub sources, also record the repository and full source commit SHA; a non-Git source may use a stable external `sourceUrl` without fabricated repository metadata. For MIT code, retain the applicable copyright/license text in redistributed copies. For CC BY 4.0 adaptation, credit the creator, link the license, identify changes and translation, and do not imply creator endorsement. Add third-party notices separately when required.

Do not use a percentage-of-change rule to decide whether attribution is required. If the exact material's permission is uncertain, use reference-only treatment or independently author the content until rights are clarified.

## Publication gate

The Book Factory checks that every published My Library manifest has a provenance audit record, the audit is reviewed or has explicitly recorded follow-up, no P0/P1 finding remains, and no reused source is marked `license-uncertain`. The validation is a project control, not legal certification. P2 follow-up may remain with the limitation disclosed and a concrete action recorded.

Before any new project begins, run the editorial source/differentiation gate. Before release, inspect every `reuseRecords` mapping and the deployed license/notice pages. Automated schema validation checks record completeness and status; human/editorial review still decides whether the cited licenses apply to the actual material.

## Reusable attribution record

```json
{
  "classification": "cc-by-4.0-adaptation",
  "sourceTitle": "Exact source work title",
  "sourceAuthor": "Author or publisher credited by the source",
  "sourceRepository": "https://github.com/OWNER/REPOSITORY",
  "sourcePath": "chapters/example.html",
  "sourceCommitSha": "0123456789abcdef0123456789abcdef01234567",
  "sourceUrl": "https://github.com/OWNER/REPOSITORY/blob/REVISION/chapters/example.html",
  "licenseName": "CC BY 4.0",
  "licenseUrl": "https://creativecommons.org/licenses/by/4.0/",
  "requiredNotices": ["Retain the applicable source notice"],
  "changesMade": "Translated and reorganized with newly authored examples; modifications are identified in the chapter.",
  "translationStatus": "English source adapted into Korean",
  "destinationPath": "chapters/example.ko.html"
}
```

For `cc-by-4.0-adaptation` and `mit-code-reuse`, record `requiredNotices` and `translationStatus` as well as source, revision, license, modifications, and destination. If inspection confirms that a source supplied no additional notice, say so explicitly rather than leaving the field blank. For `reference-only`, record the source revision, relevant paths, citation destination, and the decision that no expression/code/assets were copied. For `third-party-material`, record rights status, restrictions, required notices, the asset identifier, creator, exact license and URL, source URL, destination, and deployed `noticeLocation`. The Book Factory requires at least one assessment per published work and blocks incomplete `original`, `third-party-material`, and adaptation/code records. Follow-up audits need a concrete action for a P0/P1/P2 finding. These structural checks do not establish ownership or license applicability.

## Templates and audits

- Use [REFERENCE_REVIEW_TEMPLATE.md](REFERENCE_REVIEW_TEMPLATE.md) for overlap and provenance planning.
- The read-only findings for current My Library work are in [PROVENANCE_AUDIT.md](PROVENANCE_AUDIT.md).
- The canonical records are in `catalog/reference-intelligence/provenance-audit.json` and are schema-checked locally.
