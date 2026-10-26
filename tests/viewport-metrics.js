// Shared browser-side viewport measurement for tests and screenshot diagnostics.
// clientWidth is the effective layout area; innerWidth can expand in mobile
// emulation when overflowing content changes the reported viewport.
function collectViewportMetrics() {
  const root = document.documentElement;
  const body = document.body;
  return {
    layoutWidth: root.clientWidth,
    documentWidth: Math.max(root.scrollWidth, body ? body.scrollWidth : 0),
    innerWidth: window.innerWidth,
    visualViewportWidth: window.visualViewport ? window.visualViewport.width : null
  };
}

module.exports = collectViewportMetrics;
