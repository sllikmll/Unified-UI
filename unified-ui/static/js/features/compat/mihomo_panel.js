import { getMihomoPanelApi } from '../mihomo_panel.js';

window.UnifiedUI = window.UnifiedUI || {};
const UnifiedUI = window.UnifiedUI;
UnifiedUI.features = UnifiedUI.features || {};

const mihomoPanelApi = typeof getMihomoPanelApi === 'function' ? getMihomoPanelApi() : null;
if (mihomoPanelApi) {
  const legacyMihomoPanelApi = UnifiedUI.features.mihomoPanel || {};
  UnifiedUI.features.mihomoPanel = legacyMihomoPanelApi;
  Object.assign(legacyMihomoPanelApi, mihomoPanelApi);
}
