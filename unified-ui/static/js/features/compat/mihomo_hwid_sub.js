import { getMihomoHwidSubApi } from '../mihomo_hwid_sub.js';

window.UnifiedUI = window.UnifiedUI || {};
const UnifiedUI = window.UnifiedUI;
UnifiedUI.features = UnifiedUI.features || {};

const mihomoHwidSubApi = typeof getMihomoHwidSubApi === 'function' ? getMihomoHwidSubApi() : null;
if (mihomoHwidSubApi) {
  const legacyMihomoHwidSubApi = UnifiedUI.features.mihomoHwidSub || {};
  UnifiedUI.features.mihomoHwidSub = legacyMihomoHwidSubApi;
  Object.assign(legacyMihomoHwidSubApi, mihomoHwidSubApi);
}
