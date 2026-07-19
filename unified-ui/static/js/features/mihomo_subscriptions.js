let initialized = false;

function $(id) { return document.getElementById(id); }
function csrfToken() {
  try { const meta = document.querySelector('meta[name="csrf-token"]'); return meta ? String(meta.getAttribute('content') || '') : ''; } catch (e) { return ''; }
}
async function fetchJson(url, options = {}) {
  const headers = Object.assign({ 'Accept': 'application/json' }, options.headers || {});
  const method = String(options.method || 'GET').toUpperCase();
  if (method !== 'GET' && method !== 'HEAD') {
    headers['Content-Type'] = headers['Content-Type'] || 'application/json';
    const csrf = csrfToken();
    if (csrf) headers['X-CSRF-Token'] = csrf;
  }
  const response = await fetch(url, Object.assign({ cache: 'no-store' }, options, { headers }));
  const data = await response.json().catch(() => ({}));
  if (!response.ok || data.ok === false) throw new Error(String(data.error || data.message || ('HTTP ' + response.status)));
  return data;
}
function setStatus(message, isError = false) {
  const el = $('mihomo-status');
  if (el) el.textContent = String(message || '');
  try { if (typeof window.toast === 'function') window.toast(String(message || ''), isError ? 'error' : 'info'); } catch (e) {}
}
async function updateSubscriptions() {
  const btn = $('mihomo-update-subscriptions-btn');
  if (!window.confirm('Обновить все подписки/proxy-providers Mihomo?')) return;
  if (btn) btn.disabled = true;
  setStatus('Обновляю подписки Mihomo…');
  try {
    const data = await fetchJson('/api/mihomo/clash/providers/proxies/update-all', { method: 'POST', body: JSON.stringify({}) });
    const results = Array.isArray(data.results) ? data.results : [];
    const ok = results.filter((x) => x && x.ok).length;
    const failed = results.length - ok;
    setStatus(`Подписки обновлены: ${ok}/${results.length}${failed ? ' · ошибок: ' + failed : ''}`, failed > 0);
    try { document.dispatchEvent(new CustomEvent('unified:mihomo-subscriptions-updated', { detail: data })); } catch (e) {}
  } catch (error) {
    setStatus('Ошибка обновления подписок: ' + error.message, true);
  } finally {
    if (btn) btn.disabled = false;
  }
}
export function initMihomoSubscriptionsButton() {
  if (initialized) return;
  initialized = true;
  const btn = $('mihomo-update-subscriptions-btn');
  if (btn) btn.addEventListener('click', () => updateSubscriptions());
}
