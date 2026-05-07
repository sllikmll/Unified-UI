import { initMihomoGenerator } from '../features/mihomo_generator.js';
import { getXkeenPageName } from '../features/xkeen_runtime.js';
import { wireTopLevelNavigation } from './top_level_nav.shared.js';

function isMihomoGeneratorPage() {
  return !!(
    getXkeenPageName() === 'mihomo_generator' ||
    document.body?.classList.contains('mihomo-generator-page')
  );
}

function safe(fn) {
  try {
    fn();
  } catch (error) {
    console.error(error);
  }
}

export function initMihomoGeneratorPage() {
  if (!isMihomoGeneratorPage()) return;

  safe(() => {
    wireTopLevelNavigation(document);
  });

  safe(() => {
    initMihomoGenerator();
  });
}

export function bootMihomoGeneratorPage() {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMihomoGeneratorPage, { once: true });
    return;
  }

  initMihomoGeneratorPage();
}

export default initMihomoGeneratorPage;
