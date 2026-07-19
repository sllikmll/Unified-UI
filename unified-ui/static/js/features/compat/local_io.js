import { getLocalIoApi } from '../local_io.js';

window.UnifiedUI = window.UnifiedUI || {};
const UnifiedUI = window.UnifiedUI;

const localIoApi = typeof getLocalIoApi === 'function' ? getLocalIoApi() : null;
if (localIoApi) {
  const legacyLocalIoApi = UnifiedUI.localIO || {};
  UnifiedUI.localIO = legacyLocalIoApi;
  Object.assign(legacyLocalIoApi, localIoApi);
}
