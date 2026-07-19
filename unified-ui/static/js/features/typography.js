let typographyModuleApi = null;

(() => {
  'use strict';

  window.UnifiedUI = window.UnifiedUI || {};
  const XK = window.UnifiedUI;
  const Typo = typographyModuleApi || {};
  typographyModuleApi = Typo;

  function toast(msg, isError) {
    try {
      if (typeof window.showToast === 'function') return window.showToast(String(msg || ''), isError ? 'error' : 'info');
      if (XK.ui && typeof XK.ui.showToast === 'function') return XK.ui.showToast(String(msg || ''), !!isError);
      console.log(msg);
    } catch (e) {}
  }

  function byId(id) {
    try { return document.getElementById(id); } catch (e) { return null; }
  }

  function _num(v, def) {
    const n = Number(v);
    return Number.isFinite(n) ? n : def;
  }

  function readPrefsFallback() {
    try {
      const raw = localStorage.getItem('unified-typography-v1');
      return raw ? JSON.parse(raw) : {};
    } catch (e) {
      return {};
    }
  }

  function initDevtoolsControls() {
    const elScale = byId('dt-typo-scale');
    const elFamily = byId('dt-typo-family');
    const elMonoScale = byId('dt-typo-mono-scale');
    const elMonoFamily = byId('dt-typo-mono-family');
    const elReset = byId('dt-typo-reset');

    if (!elScale && !elFamily && !elMonoScale && !elMonoFamily) return;

    const core = (XK.ui && XK.ui.typography) ? XK.ui.typography : null;
    const load = () => (core && core.load) ? core.load() : readPrefsFallback();
    const apply = (p) => {
      try {
        if (core && core.apply) return core.apply(p);
        // best-effort fallback
        const root = document.documentElement;
        const scale = _num(p.scale, 1);
        const monoScale = (p.monoScale === null || typeof p.monoScale === 'undefined') ? scale : _num(p.monoScale, scale);
        root.style.setProperty('--xk-font-scale', String(scale));
        root.style.setProperty('--xk-mono-font-scale', String(monoScale));
        if (p.fontFamily) root.style.setProperty('--xk-font-family', String(p.fontFamily));
        if (p.monoFamily) root.style.setProperty('--xk-mono-font-family', String(p.monoFamily));
      } catch (e) {}
    };
    const save = (p) => {
      try {
        if (core && core.save) return core.save(p);
        localStorage.setItem('unified-typography-v1', JSON.stringify(p || {}));
      } catch (e) {}
    };

    function syncControls(p) {
      const scale = _num(p.scale, 1);
      const monoScale = (p.monoScale === null || typeof p.monoScale === 'undefined') ? null : _num(p.monoScale, null);

      try {
        if (elScale) elScale.value = String(scale);
        if (elFamily) elFamily.value = String(p.fontFamily || '');
        if (elMonoScale) elMonoScale.value = (monoScale === null) ? 'auto' : String(monoScale);
        if (elMonoFamily) elMonoFamily.value = String(p.monoFamily || '');
      } catch (e) {}
    }

    let prefs = load();
    syncControls(prefs);

    const onChange = () => {
      prefs = prefs || {};

      const next = {
        scale: elScale ? _num(elScale.value, 1) : _num(prefs.scale, 1),
        fontFamily: elFamily ? String(elFamily.value || '') : String(prefs.fontFamily || ''),
        monoScale: prefs.monoScale,
        monoFamily: elMonoFamily ? String(elMonoFamily.value || '') : String(prefs.monoFamily || ''),
      };

      if (elMonoScale) {
        const v = String(elMonoScale.value || 'auto');
        next.monoScale = (v === 'auto') ? null : _num(v, null);
      }

      save(next);
      apply(next);
      toast('Типографика: применено');
    };

    [elScale, elFamily, elMonoScale, elMonoFamily].forEach((el) => {
      if (!el) return;
      if (el.dataset && el.dataset.unifiedWired === '1') return;
      el.addEventListener('change', onChange);
      if (el.dataset) el.dataset.unifiedWired = '1';
    });

    if (elReset && (!elReset.dataset || elReset.dataset.unifiedWired !== '1')) {
      elReset.addEventListener('click', () => {
        try {
          if (core && core.reset) core.reset();
          else localStorage.removeItem('unified-typography-v1');
        } catch (e) {}
        prefs = load();
        syncControls(prefs);
        toast('Типографика: сброшено');
      });
      if (elReset.dataset) elReset.dataset.unifiedWired = '1';
    }

    // Sync UI if prefs were changed in another tab
    try {
      window.addEventListener('storage', (ev) => {
        if (!ev) return;
        if (ev.key !== 'unified-typography-v1') return;
        prefs = load();
        syncControls(prefs);
      });
    } catch (e) {}

    try {
      document.addEventListener('unified-ui-prefs-applied', () => {
        prefs = load();
        syncControls(prefs);
      });
    } catch (e) {}
  }

  Typo.init = function init() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initDevtoolsControls);
    } else {
      initDevtoolsControls();
    }
  };

  // Auto-init
  try { Typo.init(); } catch (e) {}
})();
export function getTypographyApi() {
  try {
    return typographyModuleApi;
  } catch (error) {
    return null;
  }
}

export function initTypography(...args) {
  const api = getTypographyApi();
  if (!api || typeof api.init !== 'function') return null;
  return api.init(...args);
}

export const typographyApi = Object.freeze({
  get: getTypographyApi,
  init: initTypography,
});
