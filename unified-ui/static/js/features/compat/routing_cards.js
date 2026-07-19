import { getRoutingCardsApi } from '../routing_cards.js';
import { getRoutingCardsNamespace } from '../routing_cards_namespace.js';

window.UnifiedUI = window.UnifiedUI || {};
const UnifiedUI = window.UnifiedUI;
UnifiedUI.features = UnifiedUI.features || {};

const routingCardsNamespace = typeof getRoutingCardsNamespace === 'function' ? getRoutingCardsNamespace() : null;
const routingCardsApi = typeof getRoutingCardsApi === 'function' ? getRoutingCardsApi() : null;
if (routingCardsNamespace) {
  const previousLegacyRoutingCardsApi = UnifiedUI.features.routingCards || null;
  const legacyRoutingCardsApi = routingCardsNamespace;
  if (previousLegacyRoutingCardsApi && previousLegacyRoutingCardsApi !== legacyRoutingCardsApi) {
    Object.assign(legacyRoutingCardsApi, previousLegacyRoutingCardsApi);
  }
  UnifiedUI.features.routingCards = legacyRoutingCardsApi;
  if (routingCardsApi) Object.assign(legacyRoutingCardsApi, routingCardsApi);
}
