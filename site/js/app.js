(function () {
  const { siteUrl } = window.MyLibraryPaths;
  const { language, t, localized } = window.MyLibraryI18n;
  const page = document.documentElement.dataset.page || "home";
  const main = document.querySelector("#main");
  const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const safeHref = value => { try { const url = new URL(value); return url.protocol === "https:" ? url.href : "#"; } catch { return "#"; } };
  const getPreference = key => { try { return localStorage.getItem(key); } catch { return null; } };
  const setPreference = (key, value) => { try { localStorage.setItem(key, value); } catch { /* Preferences remain usable for this page view. */ } };
  const local = path => esc(siteUrl(path));
  const statusText = status => ({ published: t("statusPublished"), planned: t("statusPlanned"), "in-progress": t("statusProgress"), archived: t("statusArchived") })[status] || status;
  const setMeta = (title, description, canonicalUrl = location.href.split("?")[0].split("#")[0]) => {
    document.title = title === "My Library" ? "My Library — Interactive Engineering & Knowledge Books" : `${title} — My Library`;
    const desc = document.querySelector('meta[name="description"]'); if (desc) desc.content = description;
    let canonical = document.querySelector('link[rel="canonical"]');
    if (!canonical) { canonical = document.createElement("link"); canonical.rel = "canonical"; document.head.append(canonical); }
    canonical.href = canonicalUrl;
    let og = document.querySelector('meta[property="og:url"]');
    if (!og) { og = document.createElement("meta"); og.setAttribute("property", "og:url"); document.head.append(og); }
    og.content = canonical.href;
    for (const [property, content] of [["og:title", document.title], ["og:description", description]]) {
      let meta = document.querySelector(`meta[property="${property}"]`);
      if (!meta) { meta = document.createElement("meta"); meta.setAttribute("property", property); document.head.append(meta); }
      meta.content = content;
    }
  };
  const nav = [
    ["home", "", "navHome"], ["library", "library.html", "navLibrary"], ["categories", "categories.html", "navSubjects"],
    ["roadmap", "roadmap.html", "navRoadmap"], ["journey", "learning-journey.html", "navJourney"], ["family", "kids-family.html", "navFamily"], ["experiments", "experiments.html", "navExperiments"]
  ];
  function header() {
    const active = page === "book" ? "library" : page;
    document.querySelector("#site-header").innerHTML = `<header class="site-header"><div class="header-inner"><a class="brand" href="${local("")}" aria-label="My Library home"><span class="brand-mark" aria-hidden="true">M</span><span><strong>My Library</strong><small>Interactive Engineering &amp; Knowledge Books</small></span></a><nav class="primary-nav" aria-label="${esc(t("primaryNavigation"))}">${nav.map(([id, href, label]) => `<a href="${local(href)}"${active === id ? ' aria-current="page"' : ""}>${esc(t(label))}</a>`).join("")}</nav><div class="header-tools"><button type="button" class="icon-button language-button" data-action="language" aria-label="Switch language">${esc(t("language"))}</button><button type="button" class="icon-button theme-button" data-action="theme" aria-label="${esc(t("themeDark"))}" title="${esc(t("themeDark"))}"><span aria-hidden="true">◐</span></button></div></div></header>`;
    document.querySelector("#site-footer").innerHTML = `<footer class="site-footer"><div><a class="footer-brand" href="${local("")}">My Library</a><p>${esc(t("footerLine"))}</p></div><div class="footer-links"><a href="${local("feedback.html")}">${esc(t("navFeedback"))}</a><a href="https://github.com/frbread7/books" target="_blank" rel="noopener noreferrer">GitHub ↗</a><a href="#main">${esc(t("footerTop"))} ↑</a></div><small>© ${new Date().getUTCFullYear()} My Library · Independent project</small></footer>`;
  }
  function cover(book, className = "book-cover") {
    return `<img class="${className}" src="${local(book.cover)}" alt="${esc(localized(book.title))} cover" loading="lazy" width="480" height="640">`;
  }
  function badge(status) { return `<span class="badge badge-${esc(status)}">${esc(statusText(status))}</span>`; }
  function bookCard(book, { featured = false } = {}) {
    const title = localized(book.title);
    const excerpt = localized(book.description);
    return `<article class="book-card${featured ? " book-card-featured" : ""}" style="--accent:${esc(book.theme?.accent || "#315d6d")};--accent-soft:${esc(book.theme?.accentSoft || "#e3ebe7")}"><a class="cover-link" href="${local(`book.html?slug=${encodeURIComponent(book.slug)}`)}" aria-label="${esc(t("details"))}: ${esc(title)}">${cover(book)}</a><div class="book-card-body"><div class="card-topline">${badge(book.status)}<span class="book-edition">${esc(book.version)}</span></div><h3><a href="${local(`book.html?slug=${encodeURIComponent(book.slug)}`)}">${esc(title)}</a></h3><p class="book-subtitle">${esc(localized(book.subtitle))}</p><p class="book-description">${esc(excerpt)}</p><div class="tag-row">${book.tags.slice(0, 4).map(tag => `<span class="tag">${esc(tag)}</span>`).join("")}</div><a class="text-link" href="${local(`book.html?slug=${encodeURIComponent(book.slug)}`)}">${esc(t("details"))} <span aria-hidden="true">↗</span></a></div></article>`;
  }
  const headerTitle = (eyebrow, title, intro) => `<div class="page-heading"><p class="eyebrow">${esc(eyebrow)}</p><h1>${esc(title)}</h1><p class="lead">${esc(intro)}</p></div>`;
  function categoryName(categories, id) { return localized(categories.find(c => c.id === id)?.name) || id; }
  function bookReferenceLinks(ids, books) {
    return ids.map(id => books.find(item => item.id === id && item.status === "published")).filter(Boolean)
      .map(item => `<a class="text-link" href="${local(`book.html?slug=${encodeURIComponent(item.slug)}`)}">${esc(localized(item.title))} ↗</a>`).join(" · ");
  }
  function home(books, categories, roadmap) {
    const published = books.filter(b => b.status === "published");
    const featured = published.find(book => book.id === "pmicbook") || published[0];
    const experimentCount = published.reduce((sum, b) => sum + b.experiments.length, 0);
    setMeta("My Library", t("heroBody"));
    const plannedCount = [...roadmap.books, ...roadmap.mathematicsBooks, ...roadmap.familyProjects].length;
    return `<section class="hero"><div class="hero-copy"><p class="eyebrow"><span class="eyebrow-dot"></span>${esc(t("eyebrow"))}</p><h1>${esc(t("heroTitle"))}</h1><p>${esc(t("heroBody"))}</p><div class="hero-actions"><a class="button button-primary" href="${local("library.html")}">${esc(t("browseBooks"))}<span aria-hidden="true">→</span></a><a class="button button-quiet" href="${local("roadmap.html")}">${esc(t("seeRoadmap"))}</a><a class="button button-quiet" href="${local("learning-journey.html")}">${esc(t("navJourney"))}</a><a class="button button-quiet" href="${local("kids-family.html")}">${esc(t("navFamily"))}</a></div><div class="hero-stats" aria-label="Library statistics"><div><strong>${published.length.toString().padStart(2, "0")}</strong><span>${esc(t("bookCount"))}</span></div><div><strong>${plannedCount.toString().padStart(2, "0")}</strong><span>${esc(t("plannedCount"))}</span></div><div><strong>${experimentCount.toString().padStart(2, "0")}</strong><span>${esc(t("experimentsCount"))}</span></div></div></div><div class="hero-art" aria-hidden="true"><div class="orb orb-one"></div><div class="orb orb-two"></div><div class="hero-book-stack"><div class="stack-book stack-book-back"></div><div class="stack-book stack-book-mid"></div>${featured ? `<div class="stack-book stack-book-front"><img src="${local(featured.cover)}" alt="" width="480" height="640"></div>` : ""}</div><span class="orbit-label">SEMICONDUCTOR ENGINEERING</span><span class="orbit-line"></span></div></section><section class="shelf-section"><div class="section-heading"><div><p class="eyebrow">${esc(t("shelfLabel"))}</p><h2>${esc(t("shelfHeading"))}</h2><p>${esc(t("shelfIntro"))}</p></div><a class="text-link" href="${local("library.html")}">${esc(t("navLibrary"))} <span aria-hidden="true">↗</span></a></div>${featured ? `<div class="featured-shelf"><div class="featured-shelf-card">${bookCard(featured, { featured: true })}<div class="featured-note"><span class="note-rule"></span><p class="eyebrow">${esc(t("featured"))}</p><p>${esc(t("pmicCoverage"))}</p><a class="button button-dark" href="${esc(safeHref(featured.productionUrl))}" target="_blank" rel="noopener noreferrer">${esc(t("readBook"))}<span aria-hidden="true">↗</span></a>${featured.languageUrls?.ko ? `<a class="korean-edition" href="${esc(safeHref(featured.languageUrls.ko))}" target="_blank" rel="noopener noreferrer">${esc(t("koreanEdition"))} ↗</a>` : ""}</div></div><div class="shelf-rail" aria-hidden="true"></div></div>` : `<div class="empty-state"><h3>${esc(t("emptyTitle"))}</h3><p>${esc(t("noMap"))}</p></div>`}</section><section class="subject-strip"><div class="section-heading"><div><p class="eyebrow">${esc(t("subject"))}</p><h2>${esc(t("categoriesHeading"))}</h2></div><a class="text-link" href="${local("categories.html")}">${esc(t("navSubjects"))} <span aria-hidden="true">↗</span></a></div><div class="subject-chips">${categories.map(c => `<a class="subject-chip" href="${local(`categories.html?id=${encodeURIComponent(c.id)}`)}"><span class="chip-mark" style="--chip:${esc(c.color)}"></span><span>${esc(localized(c.name))}</span><span class="chip-count">${books.filter(b => b.category === c.id && b.status === "published").length}</span></a>`).join("")}</div></section><section class="next-shelf"><div><p class="eyebrow">${esc(t("planned"))}</p><h2>${esc(localized(roadmap.books[0]?.title))}</h2><p>${esc(localized(roadmap.books[0]?.subtitle))} · ${esc(t("roadmapIntro"))}</p></div><a class="button button-outline" href="${local("roadmap.html")}">${esc(t("roadmapCta"))}<span aria-hidden="true">→</span></a></section>`;
  }
  function library(books, categories) {
    setMeta(t("navLibrary"), t("catalogIntro"));
    const query = new URLSearchParams(location.search);
    const initialSearch = query.get("q") || "";
    const initialCategory = query.get("category") || "";
    const initialStatus = query.get("status") || "";
    return `${headerTitle(t("navLibrary"), t("catalogHeading"), t("catalogIntro"))}<section class="catalog-tools" aria-label="${esc(t("navLibrary"))}"><div class="search-wrap"><label for="book-search">${esc(t("searchLabel"))}</label><span aria-hidden="true" class="search-icon">⌕</span><input id="book-search" type="search" placeholder="${esc(t("search"))}" value="${esc(initialSearch)}" autocomplete="off"></div><div class="filter-wrap"><label for="category-filter">${esc(t("category"))}</label><select id="category-filter"><option value="">${esc(t("allSubjects"))}</option>${categories.map(c => `<option value="${esc(c.id)}"${initialCategory === c.id ? " selected" : ""}>${esc(localized(c.name))}</option>`).join("")}</select></div><div class="filter-wrap"><label for="status-filter">${esc(t("status"))}</label><select id="status-filter"><option value="">${esc(t("allStatuses"))}</option>${["published", "planned", "in-progress", "archived"].map(s => `<option value="${s}"${initialStatus === s ? " selected" : ""}>${esc(statusText(s))}</option>`).join("")}</select></div><button class="button button-filter-reset" data-action="clear-filters" type="button">${esc(t("clearFilters"))}</button></section><p class="result-count" id="result-count" aria-live="polite"></p><section id="book-grid" class="book-grid" aria-label="${esc(t("catalogHeading"))}"></section>`;
  }
  function categoriesPage(books, categories) {
    const selectedId = new URLSearchParams(location.search).get("id");
    const selected = categories.find(c => c.id === selectedId);
    const canonical = new URL(siteUrl("categories.html"));
    if (selected) canonical.searchParams.set("id", selected.id);
    setMeta(selected ? localized(selected.name) : t("navSubjects"), t("categoriesIntro"), canonical.href);
    const cards = categories.map(cat => {
      const count = books.filter(b => b.category === cat.id && b.status === "published").length;
      const link = count ? `library.html?category=${encodeURIComponent(cat.id)}` : cat.id === "mathematics" ? "learning-journey.html?strand=mathematics" : "roadmap.html";
      return `<a class="category-card" href="${local(link)}" style="--category:${esc(cat.color)}"><span class="category-index">${String(categories.indexOf(cat) + 1).padStart(2, "0")}</span><span class="category-orbit" aria-hidden="true">${cat.id === "semiconductor" ? "◉" : "＋"}</span><h2>${esc(localized(cat.name))}</h2><p>${esc(localized(cat.description))}</p><span class="category-foot">${count ? `${count} ${esc(t("bookCount"))}` : esc(t("planned"))} <span aria-hidden="true">↗</span></span></a>`;
    }).join("");
    let map = "";
    if (selected) {
      const published = books.filter(b => b.status === "published" && b.category === selected.id);
      map = `<section class="knowledge-section"><div class="section-heading"><div><p class="eyebrow">${esc(t("knowledgeMap"))}</p><h2>${esc(localized(selected.name))}</h2><p>${esc(t("mapIntro"))}</p></div><a class="text-link" href="${local("categories.html")}">${esc(t("navSubjects"))}</a></div>${selected.map.length ? `<div class="knowledge-map">${selected.map.map((node, index) => { const connections = node.connections.map(connection => { const book = published.find(item => item.id === connection.bookId); return { book, chapter: book?.chapters.find(c => c.id === connection.chapterId) }; }).filter(item => item.book && item.chapter); return `<section class="map-node"><div class="map-node-head"><span class="map-node-number">${String(index + 1).padStart(2, "0")}</span><h3>${esc(localized(node.label))}</h3></div><p>${esc(node.topics.join(" · "))}</p>${connections.length ? `<ul>${connections.map(({ book, chapter }) => `<li><a href="${esc(safeHref(chapter.urls[language] || chapter.urls.en || chapter.urls.ko || Object.values(chapter.urls)[0]))}" target="_blank" rel="noopener noreferrer">${esc(localized(book.title))} · ${esc(localized(chapter.title))} ↗</a></li>`).join("")}</ul>` : `<span class="map-unconnected">${esc(t("planned"))}</span>`}</section>`; }).join("")}</div>` : `<div class="empty-state"><h3>${esc(t("noMap"))}</h3><p>${esc(t("roadmapIntro"))}</p><a class="text-link" href="${local(selected.id === "mathematics" ? "learning-journey.html?strand=mathematics" : "roadmap.html")}">${esc(selected.id === "mathematics" ? t("openJourney") : t("roadmapCta"))} ↗</a></div>`}</section>`;
    }
    return `${headerTitle(t("navSubjects"), t("categoriesHeading"), t("categoriesIntro"))}<section class="category-grid">${cards}</section>${map}`;
  }
  function roadmapPage(roadmap) {
    setMeta(t("navRoadmap"), t("roadmapIntro"));
    const mathematics = new Map(roadmap.mathematicsBooks.map(item => [item.id, item]));
    const renderIdea = (book, contentHeadingKey) => {
      const preparationLinks = (book.prerequisiteIds || []).map(id => mathematics.get(id)).filter(Boolean).map(item => `<li><a href="${local(`roadmap.html#idea-${encodeURIComponent(item.id)}`)}">${esc(localized(item.title))} ↗</a></li>`).join("");
      const preparationGraph = book.prerequisiteIds ? `<p class="roadmap-graph-label">${esc(t("mathDependencyLinks"))}</p>${preparationLinks ? `<ul class="roadmap-prerequisite-links">${preparationLinks}</ul>` : `<p>${esc(t("noMathDependencies"))}</p>`}` : "";
      return `<article class="roadmap-card" id="idea-${esc(book.id)}"><div class="roadmap-priority"><span>${String(book.priority).padStart(2, "0")}</span><small>${esc(t("priority"))}</small></div><div class="roadmap-main"><div class="roadmap-title-row"><div><p class="eyebrow">${esc(t("planned"))}${book.workState === "active-project" ? ` · ${esc(t("activeProject"))}` : ""}</p><h3>${esc(localized(book.title))}</h3><p class="book-subtitle">${esc(localized(book.subtitle))}</p></div>${badge(book.status)}</div><div class="roadmap-meta">${book.purpose ? `<section><h4>${esc(t("purpose"))}</h4><p>${esc(localized(book.purpose))}</p></section>` : ""}<section><h4>${esc(t("audience"))}</h4><p>${esc(localized(book.audience))}</p></section><section><h4>${esc(t("questions"))}</h4><ul>${localized(book.questions).map(q => `<li>${esc(q)}</li>`).join("")}</ul></section><section><h4>${esc(t(contentHeadingKey))}</h4><div class="tag-row">${localized(book.chapterGroups).map(g => `<span class="tag">${esc(g)}</span>`).join("")}</div></section><section><h4>${esc(t("prerequisites"))}</h4><p>${esc(localized(book.prerequisites))}</p>${preparationGraph}</section><section><h4>${esc(t("relationship"))}</h4><p>${esc(localized(book.relationships))}</p></section><section><h4>${esc(t("differentiation"))}</h4><p>${esc(localized(book.differentiation))}</p></section><details class="sim-ideas"><summary>${esc(t("simulationIdeas"))}</summary><ul>${localized(book.simulatorIdeas).map(s => `<li>${esc(s)}</li>`).join("")}</ul></details></div></div></article>`;
    };
    const section = (id, titleKey, introKey, items, contentHeadingKey = "chapterGroups") => `<section class="roadmap-section" id="roadmap-${id}"><div class="section-heading"><div><p class="eyebrow">${esc(t("planned"))}</p><h2>${esc(t(titleKey))}</h2><p>${esc(t(introKey))}</p></div></div><div class="roadmap-list">${items.slice().sort((a, b) => a.priority - b.priority).map(item => renderIdea(item, contentHeadingKey)).join("")}</div></section>`;
    return `${headerTitle(t("planned"), t("roadmapHeading"), t("roadmapIntro"))}${section("semiconductor", "semiconductorRoadmap", "semiconductorRoadmapIntro", roadmap.books)}${section("mathematics", "mathematicsRoadmap", "mathematicsRoadmapIntro", roadmap.mathematicsBooks)}${section("family", "familyRoadmap", "familyRoadmapIntro", roadmap.familyProjects, "familyPilotIdeas")}<section class="editorial-space"><span class="editorial-mark" aria-hidden="true">✳</span><div><p class="eyebrow">${esc(t("roadmapSpace"))}</p><h2>${esc(localized(roadmap.productSpecific.title))}</h2><p>${esc(localized(roadmap.productSpecific.description))}</p></div></section>`;
  }
  function pathsPage(paths, books) {
    setMeta(t("navPaths"), t("pathsIntro"));
    const cards = paths.paths.map((path, pathIndex) => {
      const steps = path.steps.map((step, index) => {
        const book = books.find(b => b.id === step.bookId && b.status === "published");
        const chapter = book?.chapters.find(c => c.id === step.chapterId);
        if (!book || !chapter) return `<li class="path-step path-step-unavailable"><span class="step-marker">${index + 1}</span><div><h3>${esc(t("emptyTitle"))}</h3><p>${esc(t("planned"))}</p></div></li>`;
        return `<li class="path-step"><span class="step-marker">${String(index + 1).padStart(2, "0")}</span><div><p class="eyebrow">${esc(localized(book.title))} · ${esc(t("step"))} ${index + 1}</p><h3><a href="${esc(safeHref(chapter.urls[language] || chapter.urls.en || chapter.urls.ko || Object.values(chapter.urls)[0]))}" target="_blank" rel="noopener noreferrer">${esc(localized(chapter.title))} <span aria-hidden="true">↗</span></a></h3><p>${esc(localized(step.why))}</p></div></li>`;
      }).join("");
      return `<article class="path-card"><div class="path-card-heading"><span class="path-id">PATH ${String(pathIndex + 1).padStart(2, "0")}</span><h2>${esc(localized(path.title))}</h2><p>${esc(localized(path.outcome))}</p><p class="path-audience"><strong>${esc(t("pathAudience"))}:</strong> ${esc(localized(path.audience))}</p></div><ol class="path-steps">${steps}</ol></article>`;
    }).join("");
    return `${headerTitle(t("navPaths"), t("pathsHeading"), t("pathsIntro"))}${cards || `<div class="empty-state"><h2>${esc(t("emptyTitle"))}</h2></div>`}`;
  }
  function familyIllustration(sceneId, description) {
    const fence = `<path class="family-art-fence" d="M286 125V238M286 143h416M286 171h416M286 199h416M286 227h416M306 125v113m38-113v113m38-113v113m38-113v113m38-113v113m38-113v113m38-113v113m38-113v113m38-113v113m38-113v113m38-113v113"/>`;
    const visitors = `<g class="family-art-visitors"><circle cx="70" cy="193" r="13"/><path d="M57 211h26l7 32H50z"/><circle cx="121" cy="199" r="10"/><path d="M111 212h20l6 28h-32z"/><circle cx="164" cy="190" r="14"/><path d="M151 208h26l7 35h-40z"/><path d="M205 237h20m-16 0v-16l-13 1"/></g>`;
    const truck = (x, color, number) => `<g transform="translate(${x} 0)"><path class="family-art-truck-body" fill="${color}" d="M0 188h62l15 14h25v27H0z"/><path class="family-art-truck-cab" d="M77 202h20l15 15v12H77z"/><path class="family-art-window" d="M83 205h12l10 10H83z"/><circle class="family-art-wheel" cx="22" cy="230" r="10"/><circle class="family-art-wheel" cx="83" cy="230" r="10"/><text class="family-art-number" x="28" y="218">${number}</text></g>`;
    const excavator = `<g class="family-art-machine"><path d="M362 212h102v20H362z"/><circle cx="380" cy="235" r="13"/><circle cx="444" cy="235" r="13"/><path d="M380 210q10-43 47-43l28 26-12 12z"/><path d="M420 170l43-42 16 9-31 47"/><path d="M475 137l33 34-12 10-27-27"/><path d="M496 181l14 7-8 15-17-9z"/><path d="M372 213l-3 21m88-21 3 21"/></g>`;
    const crane = (roofY = 169, suspended = true) => `<g class="family-art-crane"><path d="M362 160h34v77h-34zM352 237h68v9h-68z"/><circle cx="367" cy="244" r="9"/><circle cx="405" cy="244" r="9"/><path d="M378 160V94l196-28 4 10-195 34"/>${suspended ? `<path d="M566 73v${roofY - 73}h5v${roofY - 73}"/><path class="family-art-roof" d="M${515 - (roofY - 169) / 2} ${roofY}h190v17h-190z"/><path d="M562 158h15v16h-15z"/>` : ""}</g>`;
    const shapeMarkers = grouped => {
      const positions = grouped ? [[363,188,"circle","#d96c54"],[411,188,"square","#477a95"],[459,188,"triangle","#e2ad47"],[363,219,"circle","#d96c54"],[411,219,"square","#477a95"],[459,219,"triangle","#e2ad47"]] : [[376,198,"circle","#d96c54"],[431,198,"square","#477a95"],[486,198,"triangle","#e2ad47"],[538,198,"circle","#d96c54"]];
      return positions.map(([x,y,shape,color]) => shape === "circle" ? `<circle class="family-art-shape" cx="${x}" cy="${y}" r="15" fill="${color}"/>` : shape === "square" ? `<rect class="family-art-shape" x="${x}" y="${y}" width="30" height="30" rx="3" fill="${color}"/>` : `<path class="family-art-shape" d="M${x+15} ${y}l16 29h-32z" fill="${color}"/>`).join("");
    };
    let scene = "";
    if (sceneId.startsWith("truck-")) {
      if (sceneId === "truck-colors" || sceneId === "truck-count") scene = truck(330, "#d96c54", 1) + truck(455, "#e2ad47", 2) + truck(580, "#477a95", 3);
      if (sceneId === "truck-plan") scene = `<rect class="family-art-board" x="390" y="148" width="188" height="63" rx="5"/><circle cx="427" cy="178" r="13" fill="#d96c54"/><rect x="466" y="165" width="26" height="26" fill="#e2ad47"/><path d="M535 164l15 27h-30z" fill="#477a95"/>`;
      if (sceneId === "truck-rolling") scene = `<g class="family-art-machine"><rect x="398" y="190" width="117" height="31" rx="12"/><circle cx="425" cy="228" r="20"/><circle cx="491" cy="228" r="20"/><rect x="435" y="165" width="47" height="31" rx="5"/><path d="M450 165v-18h28l19 18"/></g>`;
      if (sceneId === "truck-problem") scene = `<path class="family-art-water" d="M340 221q22-16 45 0t46 0t46 0v22H340z"/><path d="M365 190l18-10 18 10m-18-10v31" class="family-art-sign"/>`;
      if (sceneId === "truck-garden") scene = `<g class="family-art-flowers"><path d="M377 224v-38m40 38v-49m41 49v-35"/><circle cx="377" cy="183" r="11"/><circle cx="417" cy="174" r="12"/><circle cx="458" cy="186" r="11"/></g>`;
    } else if (sceneId.startsWith("shape-")) {
      if (sceneId === "shape-excavate") scene = excavator;
      if (sceneId === "shape-plan") scene = `<rect class="family-art-board" x="350" y="150" width="250" height="79" rx="5"/>${shapeMarkers(false)}`;
      if (sceneId === "shape-mixup") scene = shapeMarkers(false);
      if (sceneId === "shape-sort") scene = shapeMarkers(true);
      if (sceneId === "shape-pattern" || sceneId === "shape-garden") scene = `<path class="family-art-garden-bed" d="M345 224q20-49 49 0m7 0q22-49 50 0m7 0q20-49 49 0m7 0q22-49 50 0"/>${shapeMarkers(true)}`;
    } else if (sceneId.startsWith("crane-")) {
      const roofY = sceneId === "crane-up" ? 121 : sceneId === "crane-wind-pause" ? 153 : sceneId === "crane-shadow" ? 184 : 169;
      scene = crane(roofY, sceneId !== "crane-wind-pause");
      if (sceneId === "crane-shadow" || sceneId === "crane-finish") scene += `<path class="family-art-bench" d="M398 225h103m10 0h82m-176 2v13m70-13v13m34-13v13m68-13v13"/>`;
      if (sceneId === "crane-plan") scene += `<rect class="family-art-board" x="501" y="188" width="150" height="34" rx="4"/><path d="M515 207h122" class="family-art-route"/>`;
      if (sceneId === "crane-wind-pause") scene += `<path class="family-art-roof" d="M515 207h190v17H515z"/><path class="family-art-support" d="M535 224h22v14h-22zm128 0h22v14h-22z"/><path class="family-art-wind" d="M493 105q26-21 49 0m-38 17q26-21 49 0m-35 17q26-21 49 0"/>`;
    }
    return `<svg class="family-illustration-art" viewBox="0 0 720 300" role="img" aria-label="${esc(description)}"><title>${esc(description)}</title><rect width="720" height="300" fill="#eaf3f4"/><circle cx="640" cy="58" r="25" fill="#efc66e"/><path d="M0 177q78-44 157 0t157 0t157 0t157 0t157 0v123H0z" fill="#d4e1d0"/><path d="M0 232q115-13 235 4v64H0z" fill="#d3c6a1"/><path d="M285 240h424" stroke="#9cae83" stroke-width="16"/><path d="M285 240h424" stroke="#f7f2dc" stroke-width="2" stroke-dasharray="12 10"/>${scene}${visitors}${fence}<path d="M0 258h720" stroke="#fffefa" stroke-width="8"/></svg>`;
  }
  function kidsFamilyPage(data, journey, promptsVisible = true, detailVisible = false) {
    const params = new URLSearchParams(location.search);
    const interestId = data.interests.some(item => item.id === params.get("interest")) ? params.get("interest") : "";
    const selectedInterest = data.interests.find(item => item.id === interestId);
    const visibleThemes = data.themes.filter(theme => !interestId || theme.interestIds.includes(interestId));
    const selectedTheme = visibleThemes.find(theme => theme.id === params.get("theme")) || visibleThemes[0] || null;
    const selectedStage = journey.stages.find(item => item.id === params.get("stage")) || journey.stages.find(item => item.id === "preschool") || journey.stages[0];
    const story = selectedTheme ? data.stories.find(item => item.id === selectedTheme.storyId) : null;
    const isReading = Boolean(story && params.get("story") === story.id);
    const requestedPage = Number.parseInt(params.get("page") || "0", 10);
    const pageIndex = isReading && Number.isFinite(requestedPage) ? Math.max(0, Math.min(story.pages.length - 1, requestedPage)) : 0;
    const spread = story?.pages[pageIndex];
    const conceptsById = new Map(journey.concepts.map(item => [item.id, item]));
    const stageOrder = journey.stages.findIndex(item => item.id === selectedStage.id);
    const continuations = (selectedTheme?.conceptIds || []).map(id => {
      let concept = conceptsById.get(id);
      while (concept && journey.stages.findIndex(item => item.id === concept.stageId) < stageOrder) {
        concept = journey.concepts.find(item => item.revisits === concept.id);
      }
      return concept?.stageId === selectedStage.id ? concept : null;
    }).filter(Boolean);
    setMeta(t("navFamily"), t("familyIntro"), siteUrl("kids-family.html"));

    const interests = [
      `<button type="button" class="family-interest${interestId ? "" : " is-selected"}" data-interest-select="" aria-pressed="${!interestId}">${esc(t("familyAllInterests"))}</button>`,
      ...data.interests.map(item => `<button type="button" class="family-interest${item.id === interestId ? " is-selected" : ""}" data-interest-select="${esc(item.id)}" aria-pressed="${item.id === interestId}">${esc(localized(item.label))}</button>`)
    ].join("");
    const themes = visibleThemes.map(theme => {
      const relatedStory = data.stories.find(item => item.id === theme.storyId);
      return `<button type="button" class="family-theme-card${theme.id === selectedTheme?.id ? " is-selected" : ""}" data-theme-select="${esc(theme.id)}" aria-pressed="${theme.id === selectedTheme?.id}" aria-controls="family-selected-theme"><span class="eyebrow">${esc(t("familyTheme"))}</span><h3>${esc(localized(theme.title))}</h3><p>${esc(localized(theme.description))}</p><small>${esc(localized(relatedStory.title))} · ${esc(t("familyDraft"))}</small></button>`;
    }).join("");
    const themeChoices = visibleThemes.length ? themes : `<article class="family-empty-interest"><p class="eyebrow">${esc(t("familyEditorialPreview"))}</p><h3>${esc(selectedInterest ? localized(selectedInterest.label) : t("familyChooseInterest"))}</h3><p>${esc(t("familyInterestEmpty"))}</p><p>${esc(t("familyMoreIdeas"))}</p></article>`;
    const stageButtons = journey.stages.slice().sort((a, b) => a.order - b.order).map(item => `<button type="button" class="family-stage${item.id === selectedStage.id ? " is-selected" : ""}" data-family-stage-select="${esc(item.id)}" aria-pressed="${item.id === selectedStage.id}"><span>${esc(localized(item.label))}</span></button>`).join("");
    const conceptCards = continuations.map(concept => {
      const strand = journey.strands.find(item => item.id === concept.strandId);
      const href = local(`learning-journey.html?stage=${encodeURIComponent(concept.stageId)}&strand=${encodeURIComponent(concept.strandId)}`);
      return `<a class="family-concept" href="${href}"><span>${esc(localized(strand?.label))}</span><h3>${esc(localized(concept.title))}</h3><p>${esc(localized(concept.description))}</p><small>${esc(concept.id)}</small></a>`;
    }).join("");
    const storyReferences = story ? data.references.filter(ref => story.referenceIds.includes(ref.id)) : [];
    const printableStory = story ? `<section class="family-print-story"><p class="family-print-status">${esc(t("familyPrintStatus"))}</p><div class="family-print-rights"><p lang="en">${esc(data.pilot.rightsNotice.en)}</p><p lang="ko">${esc(data.pilot.rightsNotice.ko)}</p></div><h1>${esc(localized(story.title))}</h1><p class="family-print-edition">${esc(t("familyEnglishLabel"))} · ${esc(t("familyKoreanLabel"))}</p>${story.pages.map((page, index) => `<article class="family-print-spread"><h2>${esc(t("familySpread"))} ${index + 1} · ${esc(t("familySpreadKorean"))} ${index + 1}</h2><figure><div>${familyIllustration(page.sceneId, localized(page.illustrationAlt))}</div><figcaption><span>${esc(page.illustrationAlt.en)}</span><span lang="ko">${esc(page.illustrationAlt.ko)}</span></figcaption></figure><div class="family-print-text"><p lang="en"><small>${esc(t("familyEnglishLabel"))}</small>${esc(page.text.en)}</p><p lang="ko"><small>${esc(t("familyKoreanLabel"))}</small>${esc(page.text.ko)}</p></div>${page.prompt ? `<p class="family-print-optional"><strong>${esc(t("familyCaregiverPrompt"))}</strong> ${esc(page.prompt.en)} · ${esc(page.prompt.ko)}</p>` : ""}<p class="family-print-optional"><strong>${esc(t("familyOptionalDetail"))}</strong> ${esc(page.optionalDetail.en)} · ${esc(page.optionalDetail.ko)}</p></article>`).join("")}<section class="family-print-notes"><h2>${esc(t("familyCaregiverPreview"))}</h2><div class="family-print-text"><div><h3>${esc(t("familyEnglishLabel"))}</h3><ul>${story.caregiverNotes.en.map(note => `<li>${esc(note)}</li>`).join("")}</ul></div><div lang="ko"><h3>${esc(t("familyKoreanLabel"))}</h3><ul>${story.caregiverNotes.ko.map(note => `<li>${esc(note)}</li>`).join("")}</ul></div></div><h3>${esc(t("familyFactNotes"))}</h3><div class="family-print-text"><div><h4>${esc(t("familyEnglishLabel"))}</h4><ul>${story.factualNotes.en.map(note => `<li>${esc(note)}</li>`).join("")}</ul></div><div lang="ko"><h4>${esc(t("familyKoreanLabel"))}</h4><ul>${story.factualNotes.ko.map(note => `<li>${esc(note)}</li>`).join("")}</ul></div></div><h3>${esc(t("familyStorySources"))}</h3><ul>${storyReferences.map(ref => `<li>${esc(localized(ref.title))} · ${esc(ref.organization)} · ${esc(ref.url)}</li>`).join("")}</ul></section></section>` : "";
    const reader = isReading ? `<section class="family-reader" id="family-reader" aria-labelledby="family-reader-title"><div class="family-reader-heading"><div><p class="eyebrow">${esc(t("familyDraft"))}</p><h2 id="family-reader-title" tabindex="-1">${esc(localized(story.title))}</h2><p>${esc(localized(data.pilot.readerNote))}</p></div><button type="button" class="button button-outline" data-story-close>${esc(t("familyBackToTheme"))}</button></div><details class="family-caregiver-notes" open><summary>${esc(t("familyCaregiverPreview"))}</summary><ul>${story.caregiverNotes[language].map(note => `<li>${esc(note)}</li>`).join("")}</ul><h3>${esc(t("familyFactNotes"))}</h3><ul>${story.factualNotes[language].map(note => `<li>${esc(note)}</li>`).join("")}</ul><h3>${esc(t("familyStorySources"))}</h3><ul>${storyReferences.map(ref => `<li><a href="${esc(safeHref(ref.url))}" target="_blank" rel="noopener noreferrer">${esc(localized(ref.title))}</a> · ${esc(ref.organization)}</li>`).join("")}</ul></details><div class="family-spread" aria-live="polite"><div class="family-illustration">${familyIllustration(spread.sceneId, localized(spread.illustrationAlt))}</div><div class="family-story-copy"><p class="family-page-count" id="family-page-count" role="status" tabindex="-1">${esc(t("familySpread"))} ${pageIndex + 1} / ${story.pages.length}</p><p>${esc(localized(spread.text))}</p></div></div><div class="family-reader-tools">${spread.prompt ? `<button type="button" class="button button-quiet" data-prompts-toggle aria-pressed="${promptsVisible ? "true" : "false"}">${esc(promptsVisible ? t("familyHidePrompts") : t("familyShowPrompts"))}</button>` : ""}<button type="button" class="button button-quiet" data-story-detail aria-expanded="${detailVisible ? "true" : "false"}">${esc(detailVisible ? t("familyHideDetail") : t("familyFindDetail"))}</button><button type="button" class="button button-quiet" data-story-print>${esc(t("familyPrintStory"))}</button></div>${spread.prompt ? `<p class="family-prompt" data-caregiver-prompt${promptsVisible ? "" : " hidden"}><strong>${esc(t("familyCaregiverPrompt"))}</strong> ${esc(localized(spread.prompt))}</p>` : ""}<p class="family-optional-detail" data-optional-detail${detailVisible ? "" : " hidden"}><strong>${esc(t("familyOptionalDetail"))}</strong> ${esc(localized(spread.optionalDetail))}</p><div class="family-reader-controls"><button type="button" class="button button-outline" data-story-prev${pageIndex === 0 ? " disabled" : ""}>${esc(t("familyPrevious"))}</button><span>${esc(t("familyNoProgress"))}</span><button type="button" class="button button-primary" data-story-next${pageIndex === story.pages.length - 1 ? " disabled" : ""}>${esc(pageIndex === story.pages.length - 1 ? t("familyStoryEnd") : t("familyNext"))}</button></div></section>` : "";
    const selectedContent = selectedTheme ? `<section class="family-selected-theme" id="family-selected-theme" aria-labelledby="family-selected-title"><div class="family-theme-summary"><div><p class="eyebrow">${esc(t("familyTheme"))}</p><h2 id="family-selected-title" tabindex="-1">${esc(localized(selectedTheme.title))}</h2><p>${esc(localized(selectedTheme.description))}</p></div><span class="family-status-pill">${esc(t("familyDraft"))}</span></div><div class="family-control-block"><h3 id="family-stage-title">${esc(t("familyChooseStage"))}</h3><p>${esc(t("familyStageLinkNote"))}</p><div class="family-stage-list" role="group" aria-labelledby="family-stage-title">${stageButtons}</div></div><div class="family-connections"><div class="family-section-heading"><h3>${esc(t("familyConnections"))}</h3><p>${esc(localized(selectedStage.description))}</p></div><div class="family-concept-grid">${conceptCards}</div></div><article class="family-story-card"><div><p class="eyebrow">${esc(t("familyDraft"))}</p><h3>${esc(localized(story.title))}</h3><p>${esc(localized(story.description))}</p><p class="family-status-note">${esc(t("familyManuscriptNote"))}</p></div><button type="button" class="button button-primary" data-story-open>${esc(t("familyOpenStory"))}<span aria-hidden="true">→</span></button></article></section>` : "";
    const proposals = data.proposals.map(proposal => `<article class="family-proposal-card"><div class="family-proposal-meta"><span class="family-status-pill">${esc(proposal.status === "editorial-pilot" ? t("familyPilotStatusShort") : t("familyProposalStatus"))}</span><span>${esc(t("familyUnpublished"))}</span></div><h3>${esc(localized(proposal.title))}</h3><p>${esc(localized(proposal.scope))}</p>${proposal.id === data.pilot.id ? `<a class="text-link" href="${siteUrl("kids-family.html")}#family-browse">${esc(t("familyExplorePilot"))} <span aria-hidden="true">↗</span></a>` : ""}</article>`).join("");

    return `${headerTitle(t("familyEyebrow"), t("familyHeading"), t("familyIntro"))}<section class="family-pilot-banner"><strong>${esc(t("familyPilotStatus"))}</strong><p>${esc(localized(data.pilot.description))}</p><p>${esc(localized(data.pilot.readerNote))}</p><p class="family-rights-notice">${esc(localized(data.pilot.rightsNotice))}</p></section><section class="family-browse" id="family-browse" aria-labelledby="family-interest-title"><div class="family-section-heading"><h2 id="family-interest-title">${esc(t("familyChooseInterest"))}</h2><p>${esc(t("familyInterestHelp"))}</p></div><div class="family-interest-list" role="group" aria-labelledby="family-interest-title">${interests}</div><div class="family-theme-grid" role="group" aria-label="${esc(t("familyThemes"))}">${themeChoices}</div></section>${selectedContent}${reader}${isReading ? printableStory : ""}<section class="family-proposals" aria-labelledby="family-proposals-title"><div class="family-section-heading"><div><p class="eyebrow">${esc(t("familyEditorialPreview"))}</p><h2 id="family-proposals-title">${esc(t("familyMoreIdeasHeading"))}</h2></div><p>${esc(t("familyMoreIdeas"))}</p></div><div class="family-proposal-grid">${proposals}</div></section><details class="family-sources"><summary>${esc(t("familySources"))}</summary><p>${esc(t("familySourcesNote"))}</p><ul>${data.references.map(ref => `<li><div><strong>${esc(localized(ref.title))}</strong><span>${esc(ref.organization)} · ${esc(t("reviewedOn"))} ${esc(ref.reviewedOn)}</span><p>${esc(localized(ref.use))}</p></div><a href="${esc(safeHref(ref.url))}" target="_blank" rel="noopener noreferrer">${esc(t("referenceLink"))} ↗</a></li>`).join("")}</ul></details><aside class="family-privacy"><h2>${esc(t("familyPrivacyHeading"))}</h2><p>${esc(t("familyPrivacyText"))}</p></aside>`;
  }
  function attachKidsFamilyControls(data, journey) {
    let promptsVisible = true;
    let detailVisible = false;
    const bind = () => {
      for (const button of main.querySelectorAll("[data-interest-select]")) button.addEventListener("click", () => {
        const interest = button.dataset.interestSelect || null;
        const nextTheme = data.themes.find(theme => !interest || theme.interestIds.includes(interest));
        navigate({ interest, theme: nextTheme?.id || null, story: null, page: null }, "", `[data-interest-select="${interest || ""}"]`);
      });
      for (const button of main.querySelectorAll("[data-theme-select]")) button.addEventListener("click", () => navigate({ theme: button.dataset.themeSelect, story: null, page: null }, "", `[data-theme-select="${button.dataset.themeSelect}"]`));
      for (const button of main.querySelectorAll("[data-family-stage-select]")) button.addEventListener("click", () => navigate({ stage: button.dataset.familyStageSelect }, "", `[data-family-stage-select="${button.dataset.familyStageSelect}"]`));
      main.querySelector("[data-story-open]")?.addEventListener("click", () => {
        const params = new URLSearchParams(location.search);
        const selected = data.themes.find(theme => theme.id === params.get("theme")) || data.themes[0];
        params.set("story", selected.storyId);
        params.set("page", "0");
        history.pushState(null, "", `${siteUrl("kids-family.html")}?${params}#family-reader`);
        promptsVisible = true;
        detailVisible = false;
        render("#family-reader-title");
        main.querySelector("#family-reader")?.scrollIntoView({ block: "start" });
      });
      main.querySelector("[data-story-close]")?.addEventListener("click", () => {
        promptsVisible = true;
        navigate({ story: null, page: null }, "#family-selected-title", "#family-selected-title");
      });
      main.querySelector("[data-prompts-toggle]")?.addEventListener("click", () => {
        promptsVisible = !promptsVisible;
        render("[data-prompts-toggle]");
      });
      main.querySelector("[data-story-detail]")?.addEventListener("click", () => {
        detailVisible = !detailVisible;
        render("[data-story-detail]");
      });
      main.querySelector("[data-story-print]")?.addEventListener("click", () => window.print());
      const changePage = delta => {
        const params = new URLSearchParams(location.search);
        const selectedTheme = data.themes.find(theme => theme.id === params.get("theme")) || data.themes[0];
        const currentStory = data.stories.find(item => item.id === selectedTheme.storyId);
        const currentPage = Number.parseInt(params.get("page") || "0", 10);
        const nextPage = Math.max(0, Math.min(currentStory.pages.length - 1, (Number.isFinite(currentPage) ? currentPage : 0) + delta));
        params.set("page", String(nextPage));
        history.replaceState(null, "", `${siteUrl("kids-family.html")}?${params}#family-reader`);
        detailVisible = false;
        render("#family-page-count");
      };
      main.querySelector("[data-story-prev]")?.addEventListener("click", () => changePage(-1));
      main.querySelector("[data-story-next]")?.addEventListener("click", () => changePage(1));
    };
    const render = (focusSelector = null) => {
      main.innerHTML = kidsFamilyPage(data, journey, promptsVisible, detailVisible);
      bind();
      if (focusSelector) main.querySelector(focusSelector)?.focus();
    };
    const navigate = (updates, hash = "", focusSelector = null) => {
      const params = new URLSearchParams(location.search);
      for (const [key, value] of Object.entries(updates)) value === null ? params.delete(key) : params.set(key, value);
      const suffix = params.size ? `?${params}` : "";
      history.pushState(null, "", `${siteUrl("kids-family.html")}${suffix}${hash}`);
      detailVisible = false;
      render(focusSelector);
    };
    bind();
    window.onpopstate = () => render();
  }
  function journeyPage(journey, books, roadmap) {
    const query = new URLSearchParams(location.search);
    const stage = journey.stages.find(item => item.id === query.get("stage")) || journey.stages[0];
    const strand = journey.strands.find(item => item.id === query.get("strand")) || journey.strands.find(item => item.id === "mathematics") || journey.strands[0];
    const concept = journey.concepts.find(item => item.stageId === stage.id && item.strandId === strand.id);
    setMeta(t("navJourney"), t("journeyIntro"), siteUrl("learning-journey.html"));
    const stageButtons = journey.stages.slice().sort((a, b) => a.order - b.order).map(item => `<button type="button" class="journey-stage${item.id === stage.id ? " is-selected" : ""}" data-stage-select="${esc(item.id)}" aria-pressed="${item.id === stage.id}"><span>${esc(localized(item.label))}</span><small>${esc(item.guidanceOnly ? t("guidanceOnly") : "")}</small></button>`).join("");
    const strandButtons = journey.strands.map(item => `<button type="button" class="journey-strand${item.id === strand.id ? " is-selected" : ""}" data-strand-select="${esc(item.id)}" aria-pressed="${item.id === strand.id}">${esc(localized(item.label))}</button>`).join("");
    const conceptHref = item => local(`learning-journey.html?stage=${encodeURIComponent(item.stageId)}&strand=${encodeURIComponent(item.strandId)}`);
    const prereqs = (concept?.prerequisites || []).map(id => journey.concepts.find(item => item.id === id)).filter(Boolean);
    const next = concept ? journey.concepts.filter(item => item.revisits === concept.id || item.prerequisites.includes(concept.id)).sort((a, b) => journey.stages.find(x => x.id === a.stageId).order - journey.stages.find(x => x.id === b.stageId).order || a.depth - b.depth) : [];
    const linkedMaterials = (concept?.publishedMaterials || []).map(material => {
      const book = books.find(item => item.id === material.bookId && item.status === "published");
      const chapter = book?.chapters.find(item => item.id === material.chapterId);
      const href = chapter && (chapter.urls[language] || chapter.urls.en || chapter.urls.ko || Object.values(chapter.urls)[0]);
      return book && chapter && href ? { book, chapter, href, why: material.why } : null;
    }).filter(Boolean);
    const planned = (concept?.plannedBookIds || []).map(id => [...roadmap.books, ...roadmap.mathematicsBooks, ...roadmap.familyProjects].find(item => item.id === id && item.status === "planned")).filter(Boolean);
    const authorityKey = ({ "official-domain-informed": "authorityDomain", "professional-recommendation": "authorityRecommendation", "editorial-proposal": "authorityEditorial" })[concept?.authority] || "authorityEditorial";
    const relationLinks = (items, label) => items.length ? `<section class="journey-relations"><h3>${esc(t(label))}</h3><ul>${items.map(item => `<li><a href="${conceptHref(item)}">${esc(localized(item.title))} <span aria-hidden="true">↗</span></a></li>`).join("")}</ul></section>` : "";
    const materials = linkedMaterials.length || planned.length ? `<div class="journey-materials">${linkedMaterials.map(({book,chapter,href,why}) => `<article class="journey-material journey-material-available"><p class="eyebrow">${esc(t("availableVerified"))}</p><h4><a href="${esc(safeHref(href))}" target="_blank" rel="noopener noreferrer">${esc(localized(book.title))} · ${esc(localized(chapter.title))} ↗</a></h4><p>${esc(localized(why))}</p></article>`).join("")}${planned.map(item => `<article class="journey-material journey-material-planned"><p class="eyebrow">${esc(t("plannedBook"))}</p><h4><a href="${local(`roadmap.html#idea-${encodeURIComponent(item.id)}`)}">${esc(localized(item.title))} · ${esc(localized(item.subtitle))} ↗</a></h4><p>${esc(localized(item.purpose))}</p></article>`).join("")}</div>` : `<div class="journey-material journey-material-concept"><p class="eyebrow">${esc(t("conceptOnly"))}</p><p>${esc(t("conceptOnlyBody"))}</p></div>`;
    const refs = journey.references.map(ref => `<li><article><div><p class="eyebrow">${esc(t(ref.kind === "official-curriculum" ? "sourceOfficial" : ref.kind === "professional-guidance" || ref.kind === "research-report" ? "sourceResearch" : ref.kind === "university-catalog" ? "sourceUniversity" : "sourceAudit"))}</p><h3>${esc(localized(ref.title))}</h3><p>${esc(ref.version)} · ${esc(t("reviewedOn"))} ${esc(ref.reviewedOn)}</p><p>${esc(localized(ref.use))}</p>${ref.reuseLimit ? `<p class="source-reuse-limit">${esc(localized(ref.reuseLimit))}</p>` : ""}</div><a href="${esc(safeHref(ref.url))}" target="_blank" rel="noopener noreferrer">${esc(t("referenceLink"))} ↗</a></article></li>`).join("");
    return `${headerTitle(t("journeyEyebrow"), t("journeyHeading"), t("journeyIntro"))}<aside class="journey-guidance"><strong>${esc(t("guidanceOnly"))}</strong><p>${esc(t("stageGuidance"))}</p></aside><section class="journey-explorer" aria-label="${esc(t("journeyExplorer"))}"><div class="journey-control-block"><h2 id="stage-selector-title">${esc(t("stagePicker"))}</h2><div class="journey-stage-list" role="group" aria-labelledby="stage-selector-title">${stageButtons}</div></div><div class="journey-control-block"><h2 id="strand-selector-title">${esc(t("strandPicker"))}</h2><div class="journey-strand-list" role="group" aria-labelledby="strand-selector-title">${strandButtons}</div></div><section id="journey-panel" class="journey-panel"><div class="journey-panel-heading"><div><p class="eyebrow">${esc(localized(stage.label))} · ${esc(localized(strand.label))}</p><h2 id="selected-strand-heading">${esc(localized(strand.label))}</h2><p>${esc(localized(stage.description))}</p><p>${esc(localized(strand.description))}</p></div><div class="journey-depth"><span>${esc(t("mapDepth"))} ${concept?.depth ?? "—"}</span><small>${esc(t("depthNote"))}</small></div></div>${concept ? `<article class="journey-concept"><div class="journey-concept-meta"><span class="journey-authority">${esc(t(authorityKey))}</span><span class="journey-concept-id">${esc(concept.id)}</span></div><h3>${esc(localized(concept.title))}</h3><p class="journey-concept-description">${esc(localized(concept.description))}</p><div class="journey-concept-grid">${concept.revisits ? `<section class="journey-relations"><h4>${esc(t("revisits"))}</h4><a href="${conceptHref(journey.concepts.find(item => item.id === concept.revisits))}">${esc(localized(journey.concepts.find(item => item.id === concept.revisits)?.title))} ↗</a></section>` : ""}${relationLinks(prereqs, "journeyPrerequisites")} ${relationLinks(next, "recommendedNext")}</div><section class="journey-material-section"><div><h4>${esc(t("materialsHeading"))}</h4><p>${esc(t("materialsExplanation"))}</p></div>${materials}</section></article>` : `<div class="journey-material journey-material-concept"><h3>${esc(t("conceptOnly"))}</h3><p>${esc(t("conceptOnlyBody"))}</p></div>`}</section></section><div class="journey-links"><a class="button button-outline" href="${local("roadmap.html#roadmap-mathematics")}">${esc(t("seeMathematicsRoadmap"))}</a><a class="text-link" href="${local("paths.html")}">${esc(t("classicPathsLink"))} ↗</a><a class="text-link" href="${local("categories.html?id=mathematics")}">${esc(t("mathCategoryLink"))} ↗</a></div><details class="journey-sources"><summary>${esc(t("sourcesHeading"))}</summary><p>${esc(t("sourcesDisclaimer"))}</p><ol>${refs}</ol></details>`;
  }
  function attachJourneyControls(journey, books, roadmap) {
    const announceSelection = () => {
      const params = new URLSearchParams(location.search);
      const stage = journey.stages.find(item => item.id === params.get("stage")) || journey.stages[0];
      const strand = journey.strands.find(item => item.id === params.get("strand")) || journey.strands.find(item => item.id === "mathematics") || journey.strands[0];
      const concept = journey.concepts.find(item => item.stageId === stage.id && item.strandId === strand.id);
      const region = document.querySelector("#journey-announcer");
      if (region) region.textContent = `${t("journeyNowShowing")}: ${localized(stage.label)} · ${localized(strand.label)} · ${concept ? localized(concept.title) : t("conceptOnly")}`;
    };
    const render = (focusedButton = document.activeElement) => {
      const focusTarget = focusedButton?.dataset?.stageSelect
        ? { type: "stage", id: focusedButton.dataset.stageSelect }
        : focusedButton?.dataset?.strandSelect
          ? { type: "strand", id: focusedButton.dataset.strandSelect }
          : null;
      main.innerHTML = journeyPage(journey, books, roadmap);
      attachJourneyControls(journey, books, roadmap);
      announceSelection();
      if (focusTarget) {
        const selector = focusTarget.type === "stage" ? "stageSelect" : "strandSelect";
        const replacement = [...main.querySelectorAll(`[data-${focusTarget.type}-select]`)].find(button => button.dataset[selector] === focusTarget.id);
        replacement?.focus();
      }
    };
    for (const button of main.querySelectorAll("[data-stage-select]")) button.addEventListener("click", () => {
      const params = new URLSearchParams(location.search);
      params.set("stage", button.dataset.stageSelect);
      history.pushState(null, "", `${siteUrl("learning-journey.html")}?${params}`);
      render(button);
    });
    for (const button of main.querySelectorAll("[data-strand-select]")) button.addEventListener("click", () => {
      const params = new URLSearchParams(location.search);
      params.set("strand", button.dataset.strandSelect);
      history.pushState(null, "", `${siteUrl("learning-journey.html")}?${params}`);
      render(button);
    });
    window.onpopstate = render;
  }
  function experimentsPage(books) {
    const experiments = books.filter(b => b.status === "published").flatMap(book => book.experiments.map(item => ({ ...item, book, chapter: book.chapters.find(c => c.id === item.chapterId) })));
    setMeta(t("navExperiments"), t("experimentsIntro"));
    const list = experiments.map((item, i) => `<article class="experiment-card"><span class="experiment-index">${String(i + 1).padStart(2, "0")}</span><div class="experiment-icon" aria-hidden="true">${["↗", "⌁", "◉", "∿"][i % 4]}</div><div class="experiment-copy"><p class="eyebrow">${esc(localized(item.book.title))} · ${esc(t("chapter"))} ${item.chapter?.number ?? ""}</p><h2>${esc(localized(item.title))}</h2><p>${esc(localized(item.kind))}</p><a href="${esc(safeHref(item.url))}" class="text-link" target="_blank" rel="noopener noreferrer">${esc(t("openExperiment"))} <span aria-hidden="true">↗</span></a></div><span class="experiment-kind">${esc(localized(item.kind))}</span></article>`).join("");
    return `${headerTitle(t("navExperiments"), t("experimentsHeading"), t("experimentsIntro"))}<section class="experiment-list">${list || `<div class="empty-state"><h2>${esc(t("experimentEmpty"))}</h2><p>${esc(t("experimentEmpty"))}</p></div>`}</section>`;
  }
  function bookPage(books, categories) {
    const slug = new URLSearchParams(location.search).get("slug");
    const book = books.find(b => b.slug === slug);
    if (!book) {
      setMeta(t("bookNotFound"), t("bookNotFound"));
      return `<section class="not-found"><p class="eyebrow">404 · ${esc(t("navLibrary"))}</p><h1>${esc(t("bookNotFound"))}</h1><p>${esc(t("emptyBody"))}</p><a class="button button-primary" href="${local("library.html")}">${esc(t("returnLibrary"))}</a></section>`;
    }
    const title = localized(book.title);
    setMeta(title, localized(book.description), new URL(siteUrl(`book.html?slug=${encodeURIComponent(book.slug)}`)).href);
    if (book.status !== "published") {
      const message = t("bookUnavailable").replace("{status}", statusText(book.status));
      const repository = book.status === "in-progress" && book.repositoryUrl
        ? `<a class="button button-quiet progress-repository" href="${esc(safeHref(book.repositoryUrl))}" target="_blank" rel="noopener noreferrer">${esc(t("repository"))} ↗</a>`
        : "";
      return `<section class="not-found book-progress-detail" data-book-status="${esc(book.status)}"><p class="eyebrow">${esc(t("navLibrary"))} · ${badge(book.status)}</p><h1>${esc(title)}</h1><p class="detail-subtitle">${esc(localized(book.subtitle))}</p><p class="detail-description">${esc(localized(book.description))}</p><p class="unavailable-note">${esc(message)}</p><div class="detail-actions">${repository}<a class="button button-primary" href="${local("library.html")}">${esc(t("returnLibrary"))}</a></div></section>`;
    }
    const chapterList = book.chapters.map(chapter => `<li><span class="chapter-number">${String(chapter.number).padStart(2, "0")}</span><div><a href="${esc(safeHref(chapter.urls[language] || chapter.urls.en || chapter.urls.ko || Object.values(chapter.urls)[0]))}" target="_blank" rel="noopener noreferrer">${esc(localized(chapter.title))} <span aria-hidden="true">↗</span></a><div class="chapter-topics">${chapter.topics.map(x => `<span>${esc(x)}</span>`).join("")}</div></div></li>`).join("");
    const experimentList = book.experiments.map(item => `<a class="mini-experiment" href="${esc(safeHref(item.url))}" target="_blank" rel="noopener noreferrer"><span aria-hidden="true">⌁</span><span><strong>${esc(localized(item.title))}</strong><small>${esc(localized(item.kind))}</small></span><span aria-hidden="true">↗</span></a>`).join("");
    return `<section class="book-detail-hero" style="--accent:${esc(book.theme.accent)};--accent-soft:${esc(book.theme.accentSoft)}"><div class="detail-cover-wrap">${cover(book, "detail-cover")}</div><div class="detail-copy"><p class="eyebrow">${esc(categoryName(categories, book.category))} · ${esc(t("featured"))}</p>${badge(book.status)}<h1>${esc(title)}</h1><p class="detail-subtitle">${esc(localized(book.subtitle))}</p><p class="detail-description">${esc(localized(book.description))}</p><div class="detail-actions"><a class="button button-primary" href="${esc(safeHref(book.productionUrl))}" target="_blank" rel="noopener noreferrer">${esc(t("readBook"))}<span aria-hidden="true">↗</span></a>${book.languageUrls?.ko ? `<a class="button button-quiet" href="${esc(safeHref(book.languageUrls.ko))}" target="_blank" rel="noopener noreferrer">${esc(t("koreanEdition"))} ↗</a>` : ""}<a class="button button-quiet" href="${esc(safeHref(book.repositoryUrl))}" target="_blank" rel="noopener noreferrer">${esc(t("repository"))} ↗</a></div><dl class="book-facts"><div><dt>${esc(t("version"))}</dt><dd>${esc(book.version)}</dd></div><div><dt>${esc(t("updated"))}</dt><dd><time datetime="${esc(book.lastUpdated)}">${esc(book.lastUpdated)}</time></dd></div><div><dt>${esc(t("languages"))}</dt><dd>${book.languages.map(l => esc(t(l === "en" ? "languageEnglish" : "languageKorean"))).join(" · ")}</dd></div><div><dt>${esc(t("chapter"))}</dt><dd>${book.chapterCount}</dd></div></dl></div></section><section class="detail-section"><div class="detail-section-heading"><p class="eyebrow">${esc(t("topics"))}</p><h2>${esc(t("contents"))}</h2></div><p class="coverage-copy">${esc(book.tags.join(" · "))}</p><div class="tag-row tag-row-large">${book.tags.map(tag => `<span class="tag">${esc(tag)}</span>`).join("")}</div><h3 class="subsection-title">${esc(t("chapterIndex"))} <span>${book.chapterCount}</span></h3><ol class="chapter-list">${chapterList}</ol></section><aside class="detail-side-grid"><section class="detail-panel"><p class="eyebrow">${esc(t("experimentsHeading"))}</p><h2>${esc(t("experimentsCount"))}</h2>${experimentList || `<p>${esc(t("experimentEmpty"))}</p>`}</section><section class="detail-panel"><p class="eyebrow">${esc(t("prerequisites"))}</p><h2>${esc(book.prerequisites.length ? t("prerequisites") : t("prerequisitesNone"))}</h2><p>${book.prerequisites.length ? bookReferenceLinks(book.prerequisites, books) : esc(t("noPrereqs"))}</p><p><strong>${esc(t("relatedBooksLabel"))}:</strong> ${bookReferenceLinks(book.relatedBooks, books) || "—"}</p><p><strong>${esc(t("subject"))}:</strong> ${esc(categoryName(categories, book.category))}</p></section></aside>`;
  }
  function feedbackPage() {
    setMeta(t("navFeedback"), t("feedbackBody"));
    return `${headerTitle(t("navFeedback"), t("feedbackHeading"), t("feedbackBody"))}<section class="feedback-card"><div class="feedback-icon" aria-hidden="true">✳</div><div><h2>${esc(t("openIssues"))}</h2><p>${esc(t("feedbackBody"))}</p><a class="button button-primary" href="https://github.com/frbread7/books/issues/new?template=feedback.yml" target="_blank" rel="noopener noreferrer">${esc(t("openIssues"))}<span aria-hidden="true">↗</span></a></div></section><p class="attribution-note">${esc(t("feedbackAttribution"))}</p>`;
  }
  function notFound() {
    setMeta(t("notFoundTitle"), t("notFoundBody"));
    return `<section class="not-found"><p class="eyebrow">404 · MY LIBRARY</p><h1>${esc(t("notFoundTitle"))}</h1><p>${esc(t("notFoundBody"))}</p><a class="button button-primary" href="${local("")}">${esc(t("home"))} <span aria-hidden="true">→</span></a></section>`;
  }
  function attachCatalogFilters(books) {
    const search = document.querySelector("#book-search"), category = document.querySelector("#category-filter"), status = document.querySelector("#status-filter");
    const grid = document.querySelector("#book-grid"), count = document.querySelector("#result-count");
    if (!search || !category || !status || !grid) return;
    const paint = () => {
      const q = search.value.trim().toLowerCase(), cat = category.value, state = status.value;
      const found = books.filter(book => {
        const text = [localized(book.title), localized(book.subtitle), localized(book.description), ...book.tags, ...book.chapters.flatMap(c => [localized(c.title), ...c.topics])].join(" ").toLowerCase();
        return (!q || text.includes(q)) && (!cat || book.category === cat) && (!state || book.status === state);
      });
      grid.innerHTML = found.length ? found.map(book => bookCard(book)).join("") : `<div class="empty-state empty-grid"><span class="empty-mark" aria-hidden="true">⌕</span><h2>${esc(t("emptyTitle"))}</h2><p>${esc(t("emptyBody"))}</p></div>`;
      count.textContent = `${found.length} ${t("resultCount")}`;
      const params = new URLSearchParams(); if (q) params.set("q", q); if (cat) params.set("category", cat); if (state) params.set("status", state);
      history.replaceState({}, "", `${location.pathname}${params.size ? `?${params}` : ""}`);
    };
    [search, category, status].forEach(el => el.addEventListener(el === search ? "input" : "change", paint));
    document.querySelector('[data-action="clear-filters"]').addEventListener("click", () => { search.value = ""; category.value = ""; status.value = ""; paint(); search.focus(); });
    paint();
  }
  function attachGlobalControls() {
    const storedTheme = getPreference("my-library-theme");
    const preferred = window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    document.documentElement.dataset.theme = storedTheme || preferred;
    const button = document.querySelector('[data-action="theme"]');
    document.querySelector('[data-action="language"]').setAttribute("aria-label", t("languageControl"));
    const syncThemeLabel = () => {
      const dark = document.documentElement.dataset.theme === "dark";
      button.setAttribute("aria-label", t(dark ? "themeLight" : "themeDark"));
      button.title = t(dark ? "themeLight" : "themeDark");
      button.querySelector("span").textContent = dark ? "☼" : "◐";
    };
    syncThemeLabel();
    button.addEventListener("click", () => { const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark"; document.documentElement.dataset.theme = next; setPreference("my-library-theme", next); syncThemeLabel(); });
    document.querySelector('[data-action="language"]').addEventListener("click", () => { setPreference("my-library-language", language === "en" ? "ko" : "en"); location.reload(); });
  }
  function attachNotFoundSkipLink() {
    if (page !== "not-found") return;
    const link = document.querySelector(".skip-link");
    if (!link || !main) return;
    const destination = new URL(location.href);
    destination.hash = "main";
    link.href = destination.href;
    link.addEventListener("click", event => {
      event.preventDefault();
      history.replaceState(null, "", destination.href);
      main.focus();
    });
  }
  async function start() {
    attachNotFoundSkipLink();
    try {
      const loadJson = name => fetch(siteUrl(`data/${name}.json`)).then(response => { if (!response.ok) throw new Error(`${name}: ${response.status}`); return response.json(); });
      const [books, categoriesData, roadmap, paths, journey, kidsFamily] = await Promise.all([loadJson("books"), loadJson("categories"), loadJson("roadmap"), loadJson("learning-paths"), loadJson("learning-journey"), page === "family" ? loadJson("kids-family") : Promise.resolve(null)]);
      const categories = categoriesData.categories;
      header();
      const renderers = { home: () => home(books, categories, roadmap), library: () => library(books, categories), categories: () => categoriesPage(books, categories), roadmap: () => roadmapPage(roadmap), journey: () => journeyPage(journey, books, roadmap), family: () => kidsFamilyPage(kidsFamily, journey), paths: () => pathsPage(paths, books), experiments: () => experimentsPage(books), book: () => bookPage(books, categories), feedback: feedbackPage, "not-found": notFound };
      main.innerHTML = renderers[page]?.() || notFound();
      document.querySelector(".brand").setAttribute("aria-label", t("homeLinkAria"));
      document.querySelector(".brand small").textContent = t("siteSubtitle");
      document.querySelector(".primary-nav").setAttribute("aria-label", t("primaryNavigation"));
      document.querySelector(".hero-stats")?.setAttribute("aria-label", t("statsLabel"));
      attachGlobalControls();
      if (page === "library") attachCatalogFilters(books);
      if (page === "journey") attachJourneyControls(journey, books, roadmap);
      if (page === "family") attachKidsFamilyControls(kidsFamily, journey);
    } catch (error) {
      console.error("My Library failed to initialize", error);
      header();
      main.innerHTML = `<section class="not-found"><p class="eyebrow">MY LIBRARY</p><h1>${esc(t("loadingError"))}</h1><button type="button" class="button button-primary" data-action="retry">${esc(t("retry"))}</button></section>`;
      document.querySelector('[data-action="retry"]').addEventListener("click", () => location.reload());
    }
  }
  start();
})();
