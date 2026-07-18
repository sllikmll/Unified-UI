let initialized = false;
let loading = false;
let lastConnections = [];
let selectedId = '';
let autoTimer = null;

function $(id) { return document.getElementById(id); }

function csrfToken() {
  try {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? String(meta.getAttribute('content') || '') : '';
  } catch (e) { return ''; }
}

async function fetchJson(url, options = {}) {
  const headers = Object.assign({ 'Accept': 'application/json' }, options.headers || {});
  const method = String(options.method || 'GET').toUpperCase();
  if (method !== 'GET' && method !== 'HEAD') {
    const csrf = csrfToken();
    if (csrf) headers['X-CSRF-Token'] = csrf;
  }
  const response = await fetch(url, Object.assign({ cache: 'no-store' }, options, { headers }));
  const data = await response.json().catch(() => ({}));
  if (!response.ok || data.ok === false) {
    const msg = data.error || data.message || ('HTTP ' + response.status);
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
  }
  return data;
}

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, (ch) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[ch]));
}

function setText(id, text) {
  const el = $(id);
  if (el) el.textContent = text || '';
}

function formatBytes(value) {
  const n = Number(value || 0);
  if (!Number.isFinite(n) || n <= 0) return '0 B';
  if (n >= 1024 * 1024 * 1024) return (n / 1024 / 1024 / 1024).toFixed(2) + ' GB';
  if (n >= 1024 * 1024) return (n / 1024 / 1024).toFixed(1) + ' MB';
  if (n >= 1024) return (n / 1024).toFixed(1) + ' KB';
  return Math.round(n) + ' B';
}

function splitSource(value) {
  const raw = String(value || '');
  if (!raw) return { host: '', port: '' };
  const m = raw.match(/^\[?([^\]]+)\]?:([0-9]+)$/);
  if (m) return { host: m[1], port: m[2] };
  const idx = raw.lastIndexOf(':');
  if (idx > 0 && /^\d+$/.test(raw.slice(idx + 1))) return { host: raw.slice(0, idx), port: raw.slice(idx + 1) };
  return { host: raw, port: '' };
}

function connId(conn) { return String(conn && (conn.id || conn.ID || conn.uuid || '') || ''); }
function connHost(conn) { return String(conn && (conn.host || conn.metadata?.host || conn.metadata?.destinationIP || conn.metadata?.sniffHost || conn.metadata?.destinationPort || '') || ''); }
function connDestination(conn) {
  const meta = conn && conn.metadata ? conn.metadata : {};
  const host = String(meta.host || meta.sniffHost || meta.destinationIP || conn.host || '');
  const port = String(meta.destinationPort || meta.dport || '');
  return host + (port ? ':' + port : '');
}
function connSource(conn) {
  const meta = conn && conn.metadata ? conn.metadata : {};
  const src = String(meta.sourceIP || meta.source || conn.source || '');
  const port = String(meta.sourcePort || meta.sport || '');
  return src + (port ? ':' + port : '');
}
function connChain(conn) {
  const chains = conn && Array.isArray(conn.chains) ? conn.chains : [];
  return chains.join(' → ');
}

function filteredConnections() {
  const q = String($('mihomo-connections-filter')?.value || '').trim().toLowerCase();
  const srcFilter = String($('mihomo-connections-source-filter')?.value || '').trim();
  return lastConnections.filter((conn) => {
    const srcHost = splitSource(connSource(conn)).host;
    if (srcFilter && srcHost !== srcFilter) return false;
    if (!q) return true;
    const hay = [
      connId(conn), connSource(conn), connDestination(conn), connHost(conn),
      connChain(conn), conn.rule, conn.rulePayload, conn.network, conn.type,
      conn.metadata && JSON.stringify(conn.metadata)
    ].join(' ').toLowerCase();
    return hay.includes(q);
  });
}

function renderSourceFilter() {
  const select = $('mihomo-connections-source-filter');
  if (!select) return;
  const current = String(select.value || '');
  const hosts = Array.from(new Set(lastConnections.map((conn) => splitSource(connSource(conn)).host).filter(Boolean))).sort();
  select.innerHTML = '<option value="">Все источники</option>' + hosts.map((host) => `<option value="${esc(host)}">${esc(host)}</option>`).join('');
  if (hosts.includes(current)) select.value = current;
}

function renderDetails(conn) {
  const box = $('mihomo-connection-details');
  if (!box) return;
  if (!conn) {
    box.innerHTML = '<div class="xk-empty-state">Выбери соединение слева — покажу детали, chain, rule, host, upload/download и кнопку закрытия.</div>';
    return;
  }
  const id = connId(conn);
  const src = connSource(conn) || '—';
  const dst = connDestination(conn) || '—';
  const chain = connChain(conn) || '—';
  const rule = String(conn.rule || conn.rulePayload || '—');
  const network = String(conn.network || conn.type || '—');
  const up = formatBytes(conn.upload);
  const down = formatBytes(conn.download);
  box.innerHTML = `
    <h3>${esc(connHost(conn) || dst || id || 'Соединение')}</h3>
    <div class="xk-connection-detail-grid">
      <div><span>ID</span><code>${esc(id || '—')}</code></div>
      <div><span>Источник</span><code>${esc(src)}</code></div>
      <div><span>Назначение</span><code>${esc(dst)}</code></div>
      <div><span>Network</span><span>${esc(network)}</span></div>
      <div><span>Rule</span><span>${esc(rule)}</span></div>
      <div><span>Chain</span><span>${esc(chain)}</span></div>
      <div><span>Upload</span><span>${esc(up)}</span></div>
      <div><span>Download</span><span>${esc(down)}</span></div>
    </div>
    <div style="display:flex; gap:8px; flex-wrap:wrap; margin:10px 0;">
      <button type="button" class="btn-secondary terminal-tool-btn-danger" id="mihomo-connection-close-one-btn" ${id ? '' : 'disabled'}>Разорвать соединение</button>
    </div>
    <pre class="xk-connection-json">${esc(JSON.stringify(conn, null, 2))}</pre>
  `;
  const closeBtn = $('mihomo-connection-close-one-btn');
  if (closeBtn && id) closeBtn.addEventListener('click', () => closeConnection(id));
}

function renderConnections() {
  renderSourceFilter();
  const list = $('mihomo-connections-list');
  if (!list) return;
  const rows = filteredConnections();
  setText('mihomo-connections-summary', `Показано: ${rows.length} из ${lastConnections.length} · upload ${formatBytes(lastConnections.reduce((a, c) => a + Number(c.upload || 0), 0))} · download ${formatBytes(lastConnections.reduce((a, c) => a + Number(c.download || 0), 0))}`);
  if (!rows.length) {
    list.innerHTML = '<div class="xk-empty-state">Активных соединений нет или фильтр слишком злой.</div>';
    renderDetails(null);
    return;
  }
  list.innerHTML = rows.map((conn) => {
    const id = connId(conn);
    const host = connHost(conn) || connDestination(conn) || id || '—';
    const src = connSource(conn) || '—';
    const dst = connDestination(conn) || '—';
    const chain = connChain(conn) || '—';
    const active = id && id === selectedId;
    return `<button type="button" class="xk-connection-row ${active ? 'active' : ''}" data-connection-id="${esc(id)}">
      <div class="xk-connection-main"><span class="xk-connection-host">${esc(host)}</span><span class="xk-connection-pill">${esc(conn.network || conn.type || 'tcp')}</span></div>
      <div class="xk-connection-meta"><span>src: ${esc(src)}</span><span>dst: ${esc(dst)}</span><span>↑ ${esc(formatBytes(conn.upload))}</span><span>↓ ${esc(formatBytes(conn.download))}</span></div>
      <div class="xk-connection-chain">${esc(chain)}</div>
    </button>`;
  }).join('');
  list.querySelectorAll('[data-connection-id]').forEach((btn) => {
    btn.addEventListener('click', () => {
      selectedId = String(btn.getAttribute('data-connection-id') || '');
      const conn = lastConnections.find((item) => connId(item) === selectedId);
      renderConnections();
      renderDetails(conn || null);
    });
  });
  const selected = selectedId ? rows.find((item) => connId(item) === selectedId) : null;
  if (selected) renderDetails(selected);
  else renderDetails(rows[0]);
}

async function loadConnections() {
  if (loading) return;
  loading = true;
  setText('mihomo-connections-status', 'Загрузка…');
  try {
    const result = await fetchJson('/api/mihomo/clash/connections');
    const data = result.data || {};
    lastConnections = Array.isArray(data.connections) ? data.connections : [];
    setText('mihomo-connections-status', `OK · ${lastConnections.length}`);
    renderConnections();
  } catch (error) {
    setText('mihomo-connections-status', 'Ошибка: ' + error.message);
  } finally {
    loading = false;
  }
}

async function closeConnection(id) {
  const cid = String(id || '').trim();
  if (!cid) return;
  if (!window.confirm('Разорвать это соединение?')) return;
  setText('mihomo-connections-status', 'Разрываю…');
  try {
    await fetchJson('/api/mihomo/clash/connections/' + encodeURIComponent(cid), { method: 'DELETE' });
    selectedId = '';
    await loadConnections();
  } catch (error) {
    setText('mihomo-connections-status', 'Ошибка разрыва: ' + error.message);
  }
}

async function closeAllConnections() {
  if (!window.confirm('Разорвать ВСЕ активные соединения Mihomo?')) return;
  setText('mihomo-connections-status', 'Разрываю все…');
  try {
    await fetchJson('/api/mihomo/clash/connections', { method: 'DELETE' });
    selectedId = '';
    await loadConnections();
  } catch (error) {
    setText('mihomo-connections-status', 'Ошибка разрыва всех: ' + error.message);
  }
}

function syncAutoRefresh() {
  const enabled = !!$('mihomo-connections-auto-refresh')?.checked;
  if (autoTimer) {
    clearInterval(autoTimer);
    autoTimer = null;
  }
  if (enabled) autoTimer = setInterval(() => loadConnections(), 5000);
}

export function initMihomoConnectionsPanel() {
  if (initialized) return;
  initialized = true;
  $('mihomo-connections-refresh-btn')?.addEventListener('click', () => loadConnections());
  $('mihomo-connections-close-all-btn')?.addEventListener('click', () => closeAllConnections());
  $('mihomo-connections-filter')?.addEventListener('input', () => renderConnections());
  $('mihomo-connections-source-filter')?.addEventListener('change', () => renderConnections());
  $('mihomo-connections-auto-refresh')?.addEventListener('change', () => syncAutoRefresh());
  loadConnections();
}

export function onShowMihomoConnectionsPanel() {
  initMihomoConnectionsPanel();
  loadConnections();
}
