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
    ["roadmap", "roadmap.html", "navRoadmap"], ["paths", "paths.html", "navPaths"], ["experiments", "experiments.html", "navExperiments"]
  ];
  function header() {
    const active = page === "book" ? "library" : page;
    document.querySelector("#site-header").innerHTML = `<header class="site-header"><div class="header-inner"><a class="brand" href="${local("")}" aria-label="My Library home"><span class="brand-mark" aria-hidden="true">M</span><span><strong>My Library</strong><small>Interactive Engineering &amp; Knowledge Books</small></span></a><nav class="primary-nav" aria-label="${esc(t("navLibrary"))}">${nav.map(([id, href, label]) => `<a href="${local(href)}"${active === id ? ' aria-current="page"' : ""}>${esc(t(label))}</a>`).join("")}</nav><div class="header-tools"><button type="button" class="icon-button language-button" data-action="language" aria-label="Switch language">${esc(t("language"))}</button><button type="button" class="icon-button theme-button" data-action="theme" aria-label="${esc(t("themeDark"))}" title="${esc(t("themeDark"))}"><span aria-hidden="true">◐</span></button></div></div></header>`;
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
    return `<section class="hero"><div class="hero-copy"><p class="eyebrow"><span class="eyebrow-dot"></span>${esc(t("eyebrow"))}</p><h1>${esc(t("heroTitle"))}</h1><p>${esc(t("heroBody"))}</p><div class="hero-actions"><a class="button button-primary" href="${local("library.html")}">${esc(t("browseBooks"))}<span aria-hidden="true">→</span></a><a class="button button-quiet" href="${local("roadmap.html")}">${esc(t("seeRoadmap"))}</a></div><div class="hero-stats" aria-label="Library statistics"><div><strong>${published.length.toString().padStart(2, "0")}</strong><span>${esc(t("bookCount"))}</span></div><div><strong>${roadmap.books.length.toString().padStart(2, "0")}</strong><span>${esc(t("plannedCount"))}</span></div><div><strong>${experimentCount.toString().padStart(2, "0")}</strong><span>${esc(t("experimentsCount"))}</span></div></div></div><div class="hero-art" aria-hidden="true"><div class="orb orb-one"></div><div class="orb orb-two"></div><div class="hero-book-stack"><div class="stack-book stack-book-back"></div><div class="stack-book stack-book-mid"></div>${featured ? `<div class="stack-book stack-book-front"><img src="${local(featured.cover)}" alt="" width="480" height="640"></div>` : ""}</div><span class="orbit-label">SEMICONDUCTOR ENGINEERING</span><span class="orbit-line"></span></div></section><section class="shelf-section"><div class="section-heading"><div><p class="eyebrow">${esc(t("shelfLabel"))}</p><h2>${esc(t("shelfHeading"))}</h2><p>${esc(t("shelfIntro"))}</p></div><a class="text-link" href="${local("library.html")}">${esc(t("navLibrary"))} <span aria-hidden="true">↗</span></a></div>${featured ? `<div class="featured-shelf"><div class="featured-shelf-card">${bookCard(featured, { featured: true })}<div class="featured-note"><span class="note-rule"></span><p class="eyebrow">${esc(t("featured"))}</p><p>${esc(t("pmicCoverage"))}</p><a class="button button-dark" href="${esc(safeHref(featured.productionUrl))}" target="_blank" rel="noopener noreferrer">${esc(t("readBook"))}<span aria-hidden="true">↗</span></a>${featured.languageUrls?.ko ? `<a class="korean-edition" href="${esc(safeHref(featured.languageUrls.ko))}" target="_blank" rel="noopener noreferrer">${esc(t("koreanEdition"))} ↗</a>` : ""}</div></div><div class="shelf-rail" aria-hidden="true"></div></div>` : `<div class="empty-state"><h3>${esc(t("emptyTitle"))}</h3><p>${esc(t("noMap"))}</p></div>`}</section><section class="subject-strip"><div class="section-heading"><div><p class="eyebrow">${esc(t("subject"))}</p><h2>${esc(t("categoriesHeading"))}</h2></div><a class="text-link" href="${local("categories.html")}">${esc(t("navSubjects"))} <span aria-hidden="true">↗</span></a></div><div class="subject-chips">${categories.map(c => `<a class="subject-chip" href="${local(`categories.html?id=${encodeURIComponent(c.id)}`)}"><span class="chip-mark" style="--chip:${esc(c.color)}"></span><span>${esc(localized(c.name))}</span><span class="chip-count">${books.filter(b => b.category === c.id && b.status === "published").length}</span></a>`).join("")}</div></section><section class="next-shelf"><div><p class="eyebrow">${esc(t("planned"))}</p><h2>${esc(localized(roadmap.books[0]?.title))}</h2><p>${esc(localized(roadmap.books[0]?.subtitle))} · ${esc(t("roadmapIntro"))}</p></div><a class="button button-outline" href="${local("roadmap.html")}">${esc(t("roadmapCta"))}<span aria-hidden="true">→</span></a></section>`;
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
      const link = count ? `library.html?category=${encodeURIComponent(cat.id)}` : `roadmap.html`;
      return `<a class="category-card" href="${local(link)}" style="--category:${esc(cat.color)}"><span class="category-index">${String(categories.indexOf(cat) + 1).padStart(2, "0")}</span><span class="category-orbit" aria-hidden="true">${cat.id === "semiconductor" ? "◉" : "＋"}</span><h2>${esc(localized(cat.name))}</h2><p>${esc(localized(cat.description))}</p><span class="category-foot">${count ? `${count} ${esc(t("bookCount"))}` : esc(t("planned"))} <span aria-hidden="true">↗</span></span></a>`;
    }).join("");
    let map = "";
    if (selected) {
      const published = books.filter(b => b.status === "published" && b.category === selected.id);
      map = `<section class="knowledge-section"><div class="section-heading"><div><p class="eyebrow">${esc(t("knowledgeMap"))}</p><h2>${esc(localized(selected.name))}</h2><p>${esc(t("mapIntro"))}</p></div><a class="text-link" href="${local("categories.html")}">${esc(t("navSubjects"))}</a></div>${selected.map.length ? `<div class="knowledge-map">${selected.map.map((node, index) => { const connections = node.connections.map(connection => { const book = published.find(item => item.id === connection.bookId); return { book, chapter: book?.chapters.find(c => c.id === connection.chapterId) }; }).filter(item => item.book && item.chapter); return `<section class="map-node"><div class="map-node-head"><span class="map-node-number">${String(index + 1).padStart(2, "0")}</span><h3>${esc(localized(node.label))}</h3></div><p>${esc(node.topics.join(" · "))}</p>${connections.length ? `<ul>${connections.map(({ book, chapter }) => `<li><a href="${esc(safeHref(chapter.urls[language] || chapter.urls.en || chapter.urls.ko || Object.values(chapter.urls)[0]))}" target="_blank" rel="noopener noreferrer">${esc(localized(book.title))} · ${esc(localized(chapter.title))} ↗</a></li>`).join("")}</ul>` : `<span class="map-unconnected">${esc(t("planned"))}</span>`}</section>`; }).join("")}</div>` : `<div class="empty-state"><h3>${esc(t("noMap"))}</h3><p>${esc(t("roadmapIntro"))}</p><a class="text-link" href="${local("roadmap.html")}">${esc(t("roadmapCta"))} ↗</a></div>`}</section>`;
    }
    return `${headerTitle(t("navSubjects"), t("categoriesHeading"), t("categoriesIntro"))}<section class="category-grid">${cards}</section>${map}`;
  }
  function roadmapPage(roadmap) {
    setMeta(t("navRoadmap"), t("roadmapIntro"));
    const list = roadmap.books.slice().sort((a, b) => a.priority - b.priority);
    return `${headerTitle(t("planned"), t("roadmapHeading"), t("roadmapIntro"))}<section class="roadmap-list">${list.map((book, i) => `<article class="roadmap-card"><div class="roadmap-priority"><span>${String(book.priority).padStart(2, "0")}</span><small>${esc(t("priority"))}</small></div><div class="roadmap-main"><div class="roadmap-title-row"><div><p class="eyebrow">${esc(t("planned"))}</p><h2>${esc(localized(book.title))}</h2><p class="book-subtitle">${esc(localized(book.subtitle))}</p></div>${badge(book.status)}</div><div class="roadmap-meta"><section><h3>${esc(t("audience"))}</h3><p>${esc(localized(book.audience))}</p></section><section><h3>${esc(t("questions"))}</h3><ul>${localized(book.questions).map(q => `<li>${esc(q)}</li>`).join("")}</ul></section><section><h3>${esc(t("chapterGroups"))}</h3><div class="tag-row">${localized(book.chapterGroups).map(g => `<span class="tag">${esc(g)}</span>`).join("")}</div></section><section><h3>${esc(t("prerequisites"))}</h3><p>${esc(localized(book.prerequisites))}</p></section><section><h3>${esc(t("relationship"))}</h3><p>${esc(localized(book.relationships))}</p></section><section><h3>${esc(t("differentiation"))}</h3><p>${esc(localized(book.differentiation))}</p></section><details class="sim-ideas"><summary>${esc(t("simulationIdeas"))}</summary><ul>${localized(book.simulatorIdeas).map(s => `<li>${esc(s)}</li>`).join("")}</ul></details></div></div></article>`).join("")}</section><section class="editorial-space"><span class="editorial-mark" aria-hidden="true">✳</span><div><p class="eyebrow">${esc(t("roadmapSpace"))}</p><h2>${esc(localized(roadmap.productSpecific.title))}</h2><p>${esc(localized(roadmap.productSpecific.description))}</p></div></section>`;
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
      return `<section class="not-found"><p class="eyebrow">${esc(t("navLibrary"))} · ${badge(book.status)}</p><h1>${esc(title)}</h1><p class="detail-subtitle">${esc(localized(book.subtitle))}</p><p>${esc(localized(book.description))}</p><p class="unavailable-note">${esc(message)}</p><a class="button button-primary" href="${local("library.html")}">${esc(t("returnLibrary"))}</a></section>`;
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
  async function start() {
    try {
      const [books, categoriesData, roadmap, paths] = await Promise.all(["books", "categories", "roadmap", "learning-paths"].map(name => fetch(siteUrl(`data/${name}.json`)).then(response => { if (!response.ok) throw new Error(`${name}: ${response.status}`); return response.json(); })));
      const categories = categoriesData.categories;
      header();
      const renderers = { home: () => home(books, categories, roadmap), library: () => library(books, categories), categories: () => categoriesPage(books, categories), roadmap: () => roadmapPage(roadmap), paths: () => pathsPage(paths, books), experiments: () => experimentsPage(books), book: () => bookPage(books, categories), feedback: feedbackPage, "not-found": notFound };
      main.innerHTML = renderers[page]?.() || notFound();
      document.querySelector(".brand").setAttribute("aria-label", t("homeLinkAria"));
      document.querySelector(".brand small").textContent = t("siteSubtitle");
      document.querySelector(".primary-nav").setAttribute("aria-label", t("primaryNavigation"));
      document.querySelector(".hero-stats")?.setAttribute("aria-label", t("statsLabel"));
      attachGlobalControls();
      if (page === "library") attachCatalogFilters(books);
    } catch (error) {
      console.error("My Library failed to initialize", error);
      header();
      main.innerHTML = `<section class="not-found"><p class="eyebrow">MY LIBRARY</p><h1>${esc(t("loadingError"))}</h1><button type="button" class="button button-primary" data-action="retry">${esc(t("retry"))}</button></section>`;
      document.querySelector('[data-action="retry"]').addEventListener("click", () => location.reload());
    }
  }
  start();
})();
