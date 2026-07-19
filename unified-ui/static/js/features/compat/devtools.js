import { getDevtoolsApi } from '../devtools.js?v=20260219a';
import { getDevtoolsNamespace } from '../devtools_namespace.js';

window.UnifiedUI = window.UnifiedUI || {};
const UnifiedUI = window.UnifiedUI;
UnifiedUI.features = UnifiedUI.features || {};

const namespace = getDevtoolsNamespace();
const mainDevtoolsApi = typeof getDevtoolsApi === 'function' ? getDevtoolsApi() : null;
if (mainDevtoolsApi) {
  namespace.devtools = mainDevtoolsApi;
}

for (const key of Object.keys(namespace)) {
  const api = namespace[key];
  if (!api) continue;
  const legacyApi = UnifiedUI.features[key] || {};
  Object.assign(legacyApi, api);
  UnifiedUI.features[key] = legacyApi;
}
