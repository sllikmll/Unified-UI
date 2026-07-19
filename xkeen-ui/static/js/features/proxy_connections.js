let initialized = false;
let cache = { connections: [], protocols: [], selectors: [] };

const PROTOCOLS = ['wireguard', 'amnezia', 'hysteria2', 'vless', 'trojan', 'mieru', 'naiveproxy'];

function $(sel, root = document) { return root.querySelector(sel); }
function $all(sel, root = document) { return Array.from(root.querySelectorAll(sel)); }
function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, (ch) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[ch]));
}
function csrfToken() {
  try { return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''; } catch (e) { return ''; }
}
async function fetchJson(url, options = {}) {
  const headers = Object.assign({ Accept: 'application/json' }, options.headers || {});
  const method = String(options.method || 'GET').toUpperCase();
  if (method !== 'GET' && method !== 'HEAD') {
    headers['Content-Type'] = headers['Content-Type'] || 'application/json';
    const csrf = csrfToken();
    if (csrf) headers['X-CSRF-Token'] = csrf;
  }
  const res = await fetch(url, Object.assign({ cache: 'no-store' }, options, { headers }));
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.ok === false) throw new Error(data.error || data.message || ('HTTP ' + res.status));
  return data;
}
function setStatus(proto, text, bad = false) {
  $all(`[data-protocol-status="${CSS.escape(proto)}"], [data-protocol-import-status="${CSS.escape(proto)}"]`).forEach((el) => {
    if (!el) return;
    el.textContent = String(text || '');
    el.classList.toggle('error', !!bad);
  });
}
function protocolLabel(proto) {
  const found = (cache.protocols || []).find((x) => x.id === proto);
  return found ? found.label : proto;
}
function selectorOptions(selected = []) {
  const autoAll = !selected || !selected.length;
  const selectedSet = new Set((selected || []).map(String));
  return (cache.selectors || []).map((name) => `<option value="${esc(name)}"${(autoAll || selectedSet.has(String(name))) ? ' selected' : ''}>${esc(name)}</option>`).join('');
}
function selectedValues(select) {
  return Array.from(select?.selectedOptions || []).map((x) => x.value).filter(Boolean);
}
function yamlSnippet(text) {
  const raw = String(text || '').trim();
  if (!raw) return '<span class="muted">—</span>';
  return `<pre class="xk-protocol-yaml">${esc(raw.split('\n').slice(0, 12).join('\n'))}${raw.split('\n').length > 12 ? '\n…' : ''}</pre>`;
}
function renderProtocol(proto) {
  const list = $(`[data-protocol-list="${CSS.escape(proto)}"]`);
  if (!list) return;
  const conns = (cache.connections || []).filter((c) => c.protocol === proto);
  const select = $(`[data-protocol-selectors="${CSS.escape(proto)}"]`);
  if (select) select.innerHTML = selectorOptions([]);
  if (!conns.length) {
    list.innerHTML = `<div class="xk-empty-state">Пока нет ${esc(protocolLabel(proto))} подключений. Вставь ссылку или загрузи файл слева.</div>`;
    setStatus(proto, '0 подключений');
    return;
  }
  list.innerHTML = conns.map((c) => {
    const used = Array.isArray(c.usedBySelectors) ? c.usedBySelectors : [];
    const configured = Array.isArray(c.selectors) ? c.selectors : [];
    const badges = used.length ? used.map((x) => `<span class="routing-editor-badge is-good">${esc(x)}</span>`).join('') : '<span class="routing-editor-badge is-muted">не добавлен в selector</span>';
    return `<article class="xk-protocol-item" data-conn-id="${esc(c.id)}">
      <div class="xk-protocol-item-head">
        <div>
          <h4>${esc(c.name || '—')}</h4>
          <div class="commands-subtitle">${esc(c.protocolLabel || protocolLabel(proto))} · ${c.mihomoSupported ? 'Mihomo: yes' : 'Mihomo: staging'} · ${c.enabled === false ? 'выключено' : 'включено'}</div>
        </div>
        <div class="xk-protocol-item-actions">
          <label class="xk-checkbox-inline"><input type="checkbox" data-conn-enabled="${esc(c.id)}" ${c.enabled === false ? '' : 'checked'}> enabled</label>
          <button type="button" class="btn-secondary" data-conn-save="${esc(c.id)}">💾</button>
          <button type="button" class="btn-secondary terminal-tool-btn-danger" data-conn-delete="${esc(c.id)}">Удалить</button>
        </div>
      </div>
      <div class="xk-protocol-used"><b>В selector’ах сейчас:</b> ${badges}</div>
      <label class="xk-protocol-field"><span>Должен быть в selector’ах</span><select class="terminal-input" multiple size="6" data-conn-selectors="${esc(c.id)}">${selectorOptions(configured)}</select></label>
      <details class="xk-protocol-details"><summary>YAML / metadata</summary>${yamlSnippet(c.proxyYaml)}</details>
    </article>`;
  }).join('');
  setStatus(proto, `${conns.length} подключений`);
}
function renderAll() { PROTOCOLS.forEach(renderProtocol); }
async function loadConnections() {
  const data = await fetchJson('/api/proxy-connections');
  cache.connections = Array.isArray(data.connections) ? data.connections : [];
  cache.protocols = Array.isArray(data.protocols) ? data.protocols : [];
  cache.selectors = Array.isArray(data.selectors) ? data.selectors : [];
  renderAll();
}
async function readFileInput(proto) {
  const input = $(`[data-protocol-file="${CSS.escape(proto)}"]`);
  const file = input && input.files && input.files[0];
  if (!file) return '';
  return await file.text();
}
async function importProtocol(proto) {
  const name = $(`[data-protocol-name="${CSS.escape(proto)}"]`)?.value || '';
  const textarea = $(`[data-protocol-content="${CSS.escape(proto)}"]`);
  const fromFile = await readFileInput(proto);
  const content = (fromFile || textarea?.value || '').trim();
  const selectors = selectedValues($(`[data-protocol-selectors="${CSS.escape(proto)}"]`));
  if (!content) { setStatus(proto, 'Нечего импортировать: вставь ссылку или выбери файл', true); return; }
  setStatus(proto, 'Импортирую…');
  try {
    await fetchJson('/api/proxy-connections/import', { method: 'POST', body: JSON.stringify({ protocol: proto, name, content, selectors }) });
    if (textarea) textarea.value = '';
    const file = $(`[data-protocol-file="${CSS.escape(proto)}"]`); if (file) file.value = '';
    setStatus(proto, 'Импортировано, применяю в Mihomo…');
    await applyManaged(proto, true);
    await loadConnections();
  } catch (error) { setStatus(proto, 'Ошибка импорта: ' + error.message, true); }
}
async function updateConnection(id) {
  const enabled = $(`[data-conn-enabled="${CSS.escape(id)}"]`)?.checked !== false;
  const selectors = selectedValues($(`[data-conn-selectors="${CSS.escape(id)}"]`));
  await fetchJson('/api/proxy-connections/' + encodeURIComponent(id), { method: 'PATCH', body: JSON.stringify({ enabled, selectors }) });
}
async function deleteConnection(id) {
  if (!window.confirm('Удалить подключение из registry? После применения оно исчезнет из managed-блока Mihomo.')) return;
  await fetchJson('/api/proxy-connections/' + encodeURIComponent(id) + '?apply=1&restart=1', { method: 'DELETE' });
}
async function applyManaged(proto, restart = true) {
  setStatus(proto, restart ? 'Применяю и перезапускаю Mihomo…' : 'Применяю…');
  try {
    const data = await fetchJson('/api/proxy-connections/apply', { method: 'POST', body: JSON.stringify({ restart }) });
    setStatus(proto, data.changed ? `Применено: ${data.count} proxy · backup ${data.backup || '—'}` : `Конфиг уже актуален: ${data.count} proxy`);
    try { document.dispatchEvent(new CustomEvent('xkeen:proxy-connections-applied', { detail: data })); } catch (e) {}
    await loadConnections();
  } catch (error) { setStatus(proto, 'Ошибка применения: ' + error.message, true); }
}
async function previewManaged(proto) {
  setStatus(proto, 'Готовлю preview…');
  try {
    const data = await fetchJson('/api/proxy-connections/preview', { method: 'POST', body: JSON.stringify({}) });
    const win = window.open('', '_blank');
    if (win) {
      win.document.write(`<pre style="white-space:pre-wrap;background:#07111f;color:#d7e8ff;padding:16px;">${esc(data.block || data.configPreview || 'empty')}</pre>`);
      win.document.close();
    }
    setStatus(proto, data.ok ? 'Preview OK' : ('Preview YAML error: ' + data.error), !data.ok);
  } catch (error) { setStatus(proto, 'Preview error: ' + error.message, true); }
}
function bind() {
  PROTOCOLS.forEach((proto) => {
    $all(`[data-protocol-import="${CSS.escape(proto)}"]`).forEach((btn) => btn.addEventListener('click', () => importProtocol(proto)));
    $all(`[data-protocol-refresh="${CSS.escape(proto)}"]`).forEach((btn) => btn.addEventListener('click', () => loadConnections().catch((e) => setStatus(proto, e.message, true))));
    $all(`[data-protocol-apply="${CSS.escape(proto)}"]`).forEach((btn) => btn.addEventListener('click', () => applyManaged(proto, true)));
    $all(`[data-protocol-preview="${CSS.escape(proto)}"]`).forEach((btn) => btn.addEventListener('click', () => previewManaged(proto)));
    $all(`[data-protocol-file="${CSS.escape(proto)}"]`).forEach((input) => input.addEventListener('change', async () => {
      const text = await readFileInput(proto).catch(() => '');
      const textarea = $(`[data-protocol-content="${CSS.escape(proto)}"]`);
      if (textarea && text) textarea.value = text;
    }));
  });
  document.addEventListener('click', (event) => {
    const save = event.target && event.target.closest ? event.target.closest('[data-conn-save]') : null;
    const del = event.target && event.target.closest ? event.target.closest('[data-conn-delete]') : null;
    if (save) {
      const id = save.getAttribute('data-conn-save') || '';
      updateConnection(id).then(() => { const conn = (cache.connections || []).find((x) => x.id === id); return applyManaged(conn?.protocol || 'wireguard', true); }).then(loadConnections).catch((e) => alert(e.message));
    }
    if (del) {
      const id = del.getAttribute('data-conn-delete') || '';
      deleteConnection(id).then(loadConnections).catch((e) => alert(e.message));
    }
  });
}
export function initProxyConnectionsPanel() {
  if (initialized) return;
  initialized = true;
  bind();
  loadConnections().catch((error) => PROTOCOLS.forEach((p) => setStatus(p, 'Ошибка: ' + error.message, true)));
}
export function onShowProxyConnectionsPanel(proto) {
  initProxyConnectionsPanel();
  if (!cache.connections.length) loadConnections().catch((e) => setStatus(proto || 'wireguard', e.message, true));
}
