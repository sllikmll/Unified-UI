import { getGithubApi } from '../github.js';

window.UnifiedUI = window.UnifiedUI || {};
const UnifiedUI = window.UnifiedUI;

const githubApi = typeof getGithubApi === 'function' ? getGithubApi() : null;
if (githubApi) {
  const legacyGithubApi = UnifiedUI.github || {};
  UnifiedUI.github = legacyGithubApi;
  Object.assign(legacyGithubApi, githubApi);
}
