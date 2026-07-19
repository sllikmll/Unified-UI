import { getMihomoImportApi } from '../mihomo_import.js';

window.UnifiedUI = window.UnifiedUI || {};
const UnifiedUI = window.UnifiedUI;
UnifiedUI.features = UnifiedUI.features || {};

const mihomoImportApi = typeof getMihomoImportApi === 'function' ? getMihomoImportApi() : null;
if (mihomoImportApi) {
  const legacyMihomoImportApi = UnifiedUI.features.mihomoImport || {};
  UnifiedUI.features.mihomoImport = legacyMihomoImportApi;
  Object.assign(legacyMihomoImportApi, mihomoImportApi);
}
