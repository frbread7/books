# Decisions

| Decision | Rationale |
| --- | --- |
| Build an independent static derivative rather than fork the portal wholesale | Upstream catalog and custom-domain, Worker, and analytics configuration are bound to another owner's books and identity. |
| Keep textbooks in independent repositories | Each book owns its content, license, release, and deployment; this portal is a discovery layer. |
| Use flat HTML, vanilla JavaScript, and JSON | Works on project Pages with no application framework and keeps base paths auditable. |
| Centralize internal URLs in site/js/paths.js | The production site includes /books/; one derived base avoids root-hosting assumptions. |
| Keep future candidates out of catalog/books/ | Editorial ideas must not inflate book or publication counts. |
| Use evidence-backed chapter and experiment URLs | The PMICBook record tracks its cataloged v1.2.0 release and successful Pages deployment, not speculative simulators. |
| Use GitHub Issues for feedback | Free, transparent, and needs no Worker, database, credential, or third-party administrator identity. |
| Omit production analytics | A personal static library has no justified need for tracking tokens or external beacons. |
| Use Playwright only in development | Browser journeys are part of acceptance; production does not need a package runtime. |
| Offer portal code under MIT and authored planning/docs under CC BY 4.0 | Clear reuse terms for the independent implementation; individual books remain governed by their own licenses. |
| Keep curriculum-map concepts separate from registered books | A useful subject graph can exist before a textbook is authored. Only Book Factory manifests and publication evidence affect book counts or open textbook links. |
| Use a versioned, bilingual Learning Journey graph with explicit sources | Curriculum, recommendations, university examples, and editorial proposals have different authority; labeled sources and stable concept IDs keep that distinction reviewable. |
| Treat age bands as optional wayfinding and avoid child profiles | Family learning is a static guide, not a placement or progress system; no account, child data, analytics, or saved activity is justified. |
| Keep Nuri and National Academies material citation-only | Nuri’s source page indicates attribution/noncommercial/no-derivatives terms; citations and links explain the audit without copying or adapting protected material. |

## Open boundaries

Candidate books require substantive authorship and review in their separate repositories. GitHub Pages project-site configuration and public deployment are release steps performed only after the local review gate.
