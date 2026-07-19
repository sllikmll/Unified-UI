(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const state = { lists: [], interfaces: [], services: {}, selected: null };

  function setStatus(msg, type='') {
    const el = $('dns-routes-status');
    if (!el) return;
    el.textContent = msg || '';
    el.dataset.status = type || '';
  }
  function esc(s) {
    return String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }
  async function api(path, opts={}) {
    const res = await fetch(path, Object.assign({cache:'no-store'}, opts));
    const data = await res.json().catch(()=>({}));
    if (!res.ok || data.ok === false) throw new Error(data.message || data.error || `HTTP ${res.status}`);
    return data;
  }
  function routeMode() {
    const value = localStorage.getItem('unified.dnsRoutes.mode') || 'mihomo';
    document.querySelectorAll('input[name="dns-routing-mode"]').forEach(r => { r.checked = r.value === value; });
  }
  function wireMode() {
    document.querySelectorAll('input[name="dns-routing-mode"]').forEach(r => {
      r.addEventListener('change', () => {
        if (r.checked) localStorage.setItem('unified.dnsRoutes.mode', r.value);
      });
    });
    routeMode();
  }
  function fillInterfaces(selected='') {
    const sel = $('dns-routes-interface');
    if (!sel) return;
    sel.innerHTML = '';
    for (const it of state.interfaces || []) {
      const opt = document.createElement('option');
      opt.value = it.name;
      opt.textContent = it.description ? `${it.name} — ${it.description}` : it.name;
      if (it.name === selected) opt.selected = true;
      sel.appendChild(opt);
    }
  }
  function fillServices() {
    const sel = $('dns-routes-service');
    if (!sel) return;
    sel.innerHTML = '';
    Object.entries(state.services || {}).forEach(([key, svc]) => {
      const opt = document.createElement('option');
      opt.value = key;
      opt.textContent = svc.label || key;
      sel.appendChild(opt);
    });
  }
  function selectList(list) {
    state.selected = list || null;
    $('dns-routes-name').value = list ? list.name : '';
    $('dns-routes-description').value = list ? (list.description || '') : '';
    $('dns-routes-items').value = list ? (list.items || []).join('\n') : '';
    fillInterfaces(list ? list.interface : '');
    const note = $('dns-routes-editor-note');
    if (note) note.textContent = list ? `${list.name}: ${list.items.length} элементов · интерфейс ${list.interface || 'не задан'}` : 'Новый список. После применения будет создан domain-listN.';
    renderList();
  }
  function renderList() {
    const root = $('dns-routes-list');
    if (!root) return;
    if (!state.lists.length) {
      root.innerHTML = '<div class="xk-empty-state">DNS route списки не найдены.</div>';
      return;
    }
    root.innerHTML = state.lists.map(l => `
      <button type="button" class="xk-selector-row ${state.selected && state.selected.name === l.name ? 'active' : ''}" data-dns-list="${esc(l.name)}" style="width:100%; text-align:left; margin:6px 0; border-radius:4px;">
        <div style="display:flex; justify-content:space-between; gap:8px; align-items:center;">
          <strong>${esc(l.description || l.name)}</strong>
          <code>${esc(l.name)}</code>
        </div>
        <div class="commands-subtitle">${esc(l.interface || 'интерфейс не задан')} · ${Number(l.items?.length || 0)} элементов</div>
      </button>`).join('');
    root.querySelectorAll('[data-dns-list]').forEach(btn => {
      btn.addEventListener('click', () => selectList(state.lists.find(x => x.name === btn.dataset.dnsList)));
    });
  }
  async function load() {
    const view = $('view-dns-routes');
    if (!view) return;
    setStatus('Загрузка…');
    try {
      const data = await api('/api/keenetic/dns-routes');
      state.lists = data.lists || [];
      state.interfaces = data.interfaces || [];
      state.services = data.services || {};
      fillServices();
      fillInterfaces();
      renderList();
      if (!state.selected && state.lists.length) selectList(state.lists[0]);
      setStatus(`OK · списков: ${state.lists.length} · интерфейсов: ${state.interfaces.length}`, 'success');
    } catch (e) {
      setStatus(`Ошибка: ${e.message || e}`, 'error');
    }
  }
  async function generate() {
    const service = $('dns-routes-service')?.value || '';
    const dns_server = $('dns-routes-dns-server')?.value || '';
    const preview = $('dns-routes-service-preview');
    if (preview) preview.textContent = 'Генерирую…';
    try {
      const data = await api('/api/keenetic/dns-routes/preview-service', {
        method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({service, dns_server})
      });
      const existing = $('dns-routes-items').value.trim();
      const next = data.items || [];
      $('dns-routes-description').value = data.label || service;
      $('dns-routes-items').value = (existing ? existing + '\n' : '') + next.join('\n');
      if (preview) preview.textContent = `Добавлено в редактор: ${next.length}; DNS-resolved IP: ${(data.resolved_ips || []).length}`;
    } catch (e) {
      if (preview) preview.textContent = `Ошибка генерации: ${e.message || e}`;
    }
  }
  async function apply() {
    const payload = {
      name: $('dns-routes-name').value.trim(),
      description: $('dns-routes-description').value.trim(),
      interface: $('dns-routes-interface').value.trim(),
      items: $('dns-routes-items').value.split(/\n+/).map(x=>x.trim()).filter(Boolean),
    };
    if (!payload.interface || !payload.items.length) { setStatus('Выбери интерфейс и заполни список', 'error'); return; }
    if (!confirm(`Применить DNS route ${payload.name || '(новый список)'} через ${payload.interface}? Будет создан backup running-config.`)) return;
    setStatus('Применяю…');
    try {
      const data = await api('/api/keenetic/dns-routes/apply', {
        method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)
      });
      setStatus(`Применено: ${data.name} → ${data.interface}; backup: ${data.backup}`, 'success');
      state.selected = null;
      await load();
    } catch (e) {
      setStatus(`Ошибка применения: ${e.message || e}`, 'error');
    }
  }
  function init() {
    if (!$('view-dns-routes')) return;
    wireMode();
    $('dns-routes-refresh-btn')?.addEventListener('click', load);
    $('dns-routes-new-btn')?.addEventListener('click', () => selectList(null));
    $('dns-routes-generate-btn')?.addEventListener('click', generate);
    $('dns-routes-apply-btn')?.addEventListener('click', apply);
    const tab = document.querySelector('[data-view="dns-routes"]');
    tab?.addEventListener('click', () => setTimeout(load, 50));
    setTimeout(load, 300);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
