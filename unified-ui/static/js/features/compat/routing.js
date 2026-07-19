import { getRoutingApi } from '../routing.js';

window.UnifiedUI = window.UnifiedUI || {};
const UnifiedUI = window.UnifiedUI;
UnifiedUI.features = UnifiedUI.features || {};

const routingApi = typeof getRoutingApi === 'function' ? getRoutingApi() : null;
if (routingApi) {
  const legacyRoutingApi = UnifiedUI.routing || {};
  UnifiedUI.routing = legacyRoutingApi;
  Object.assign(legacyRoutingApi, routingApi);
  UnifiedUI.features.routing = legacyRoutingApi;
}
