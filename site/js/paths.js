/* Project-site safe URL helpers: derive /books/ from the current flat page URL. */
(function () {
  const base = new URL("./", window.location.href);
  const siteUrl = (path = "") => new URL(String(path).replace(/^\/+/, ""), base).href;
  window.MyLibraryPaths = Object.freeze({ base, siteUrl });
})();
