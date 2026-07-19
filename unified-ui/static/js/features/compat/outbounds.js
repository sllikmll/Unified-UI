import { getOutboundsApi } from '../outbounds.js';

window.UnifiedUI = window.UnifiedUI || {};
const UnifiedUI = window.UnifiedUI;
UnifiedUI.features = UnifiedUI.features || {};

const outboundsApi = typeof getOutboundsApi === 'function' ? getOutboundsApi() : null;
if (outboundsApi) {
  const legacyOutboundsApi = UnifiedUI.features.outbounds || {};
  UnifiedUI.features.outbounds = legacyOutboundsApi;
  Object.assign(legacyOutboundsApi, outboundsApi);
}
