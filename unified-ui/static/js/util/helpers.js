(() => {
  window.UnifiedUI = window.UnifiedUI || {};
  const UnifiedUI = window.UnifiedUI;
  UnifiedUI.util = UnifiedUI.util || {};

  // Common helpers moved out of main.js (step 3).
  // Keep backward compatibility via global aliases where useful.

  if (!UnifiedUI.util.escapeHtml) {
    UnifiedUI.util.escapeHtml = function escapeHtml(str) {
      if (str == null) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    };
  }

  // Backward-compatible global alias (main.js historically calls escapeHtml(...)).
  if (typeof window.escapeHtml !== 'function') {
    window.escapeHtml = UnifiedUI.util.escapeHtml;
  }
})();
