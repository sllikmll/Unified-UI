import { getTopLevelScreenRegistryApi } from './top_level_screen_registry.js';
import {
  applyScreenDocumentState,
  attachScreenRoot,
  captureCurrentDocumentScreenSnapshot,
  detachScreenRoot,
  ensureScreenStyles,
  fetchTopLevelScreenSnapshot,
} from './top_level_screen_host.shared.js';

function isXkeenLocation() {
  try {
    return !!(
      window.UnifiedUI?.pageConfig?.page === 'unified' ||
      document.body?.classList.contains('unified-page') ||
      document.getElementById('unified-body') ||
      document.getElementById('unified-config-editor')
    );
  } catch (error) {
    return false;
  }
}

async function resolveXkeenBootstrapModule() {
  return import('./unified.screen.bootstrap.js');
}

function createXkeenScreen() {
  let snapshot = null;
  let runtimeApi = null;
  let initialized = false;
  let serializedState = null;

  async function ensureSnapshot() {
    if (snapshot) return snapshot;
    snapshot = isXkeenLocation()
      ? captureCurrentDocumentScreenSnapshot('unified')
      : await fetchTopLevelScreenSnapshot('unified', '/unified');
    return snapshot;
  }

  async function ensureRuntimeApi(boot = false) {
    if (runtimeApi && !boot) return runtimeApi;

    const mod = await resolveXkeenBootstrapModule();
    if (boot) {
      runtimeApi = await mod.bootXkeenScreen();
      initialized = true;
      return runtimeApi;
    }

    runtimeApi = mod.getXkeenTopLevelApi();
    return runtimeApi;
  }

  return {
    async mount() {
      await ensureSnapshot();
    },
    async activate(context) {
      const nextSnapshot = await ensureSnapshot();
      ensureScreenStyles(nextSnapshot);
      applyScreenDocumentState(nextSnapshot);
      attachScreenRoot(nextSnapshot);

      if (!initialized) {
        await ensureRuntimeApi(true);
      } else if (!runtimeApi) {
        await ensureRuntimeApi(false);
      }

      if (runtimeApi && typeof runtimeApi.restoreState === 'function' && serializedState) {
        try { await runtimeApi.restoreState(serializedState, context); } catch (error) {}
      }

      if (runtimeApi && typeof runtimeApi.activate === 'function') {
        await runtimeApi.activate(context);
      }
    },
    async deactivate(context) {
      if (!runtimeApi && isXkeenLocation()) {
        await ensureRuntimeApi(false);
      }
      if (runtimeApi && typeof runtimeApi.serializeState === 'function') {
        try { serializedState = await runtimeApi.serializeState(context); } catch (error) {}
      }
      if (runtimeApi && typeof runtimeApi.deactivate === 'function') {
        await runtimeApi.deactivate(context);
      }
      detachScreenRoot(snapshot);
    },
    dispose() {
      detachScreenRoot(snapshot);
    },
  };
}

export function registerXkeenTopLevelScreen() {
  const registry = getTopLevelScreenRegistryApi();
  const screen = createXkeenScreen();
  registry.registerScreen('unified', screen);
  if (isXkeenLocation()) {
    Promise.resolve(screen.mount()).catch(() => {});
  }
  return screen;
}
