(() => {
  "use strict";

  // Bootstrap: utilities and tiny polyfills that other modules may rely on.
  // IMPORTANT: keep this file DOM-free (belongs to UnifiedUI.util).
  // Stage 5 final rule: do not publish feature bridges, migration proxies,
  // or window.* aliases from this bootstrap layer.

  window.UnifiedUI = window.UnifiedUI || {};
  const XK = window.UnifiedUI;
  XK.util = XK.util || {};
})();
