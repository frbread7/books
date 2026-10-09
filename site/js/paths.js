/* Project-site safe URL helpers: derive the site base from the document base URL. */
(function () {
  const base = new URL("./", document.baseURI);
  const siteUrl = (path = "") => new URL(String(path).replace(/^\/+/, ""), base).href;
  window.MyLibraryPaths = Object.freeze({ base, siteUrl });
})();
