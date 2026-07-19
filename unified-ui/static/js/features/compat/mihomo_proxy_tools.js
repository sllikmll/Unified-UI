import { getMihomoProxyToolsApi } from '../mihomo_proxy_tools.js';

window.UnifiedUI = window.UnifiedUI || {};
const UnifiedUI = window.UnifiedUI;
UnifiedUI.features = UnifiedUI.features || {};

const mihomoProxyToolsApi = typeof getMihomoProxyToolsApi === 'function' ? getMihomoProxyToolsApi() : null;
if (mihomoProxyToolsApi) {
  const legacyMihomoProxyToolsApi = UnifiedUI.features.mihomoProxyTools || {};
  UnifiedUI.features.mihomoProxyTools = legacyMihomoProxyToolsApi;
  Object.assign(legacyMihomoProxyToolsApi, mihomoProxyToolsApi);
}
