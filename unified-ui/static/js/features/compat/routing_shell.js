import { getRoutingShellApi } from '../routing_shell.js';

window.UnifiedUI = window.UnifiedUI || {};
const UnifiedUI = window.UnifiedUI;
UnifiedUI.features = UnifiedUI.features || {};

const routingShellApi = typeof getRoutingShellApi === 'function' ? getRoutingShellApi() : null;
if (routingShellApi) {
  const legacyRoutingShellApi = UnifiedUI.features.routingShell || {};
  UnifiedUI.features.routingShell = legacyRoutingShellApi;
  Object.assign(legacyRoutingShellApi, routingShellApi);
}
