import { getInboundsApi } from '../inbounds.js';

window.UnifiedUI = window.UnifiedUI || {};
const UnifiedUI = window.UnifiedUI;
UnifiedUI.features = UnifiedUI.features || {};

const inboundsApi = typeof getInboundsApi === 'function' ? getInboundsApi() : null;
if (inboundsApi) {
  const legacyInboundsApi = UnifiedUI.features.inbounds || {};
  UnifiedUI.features.inbounds = legacyInboundsApi;
  Object.assign(legacyInboundsApi, inboundsApi);
}
