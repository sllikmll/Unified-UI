import { getBackupsApi } from '../backups.js?v=20260317b';

window.UnifiedUI = window.UnifiedUI || {};
const UnifiedUI = window.UnifiedUI;

const backupsApi = typeof getBackupsApi === 'function' ? getBackupsApi() : null;
if (backupsApi) {
  const legacyBackupsApi = UnifiedUI.backups || {};
  UnifiedUI.backups = legacyBackupsApi;
  Object.assign(legacyBackupsApi, backupsApi);
}
