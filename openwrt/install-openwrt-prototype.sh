#!/bin/sh
set -eu

UI_ROOT="/www/unified-ui"
CGI_PATH="/www/cgi-bin/unified-ui-api"
CONF_DIR="/etc/unified-ui"
CONF_FILE="$CONF_DIR/openwrt.env"

mkdir -p "$UI_ROOT" "$CONF_DIR" /www/cgi-bin

_secret="$(uci -q get nikki.mixin.api_secret 2>/dev/null || true)"
_secret_q="$(printf '%s' "$_secret" | sed "s/'/'\\''/g")"
{
  printf "%s\n" "UNIFIED_UI_NAME='Unified UI OpenWrt'"
  printf "%s\n" "MIHOMO_CONTROLLER='http://127.0.0.1:6060'"
  printf "MIHOMO_SECRET='%s'\n" "$_secret_q"
  printf "%s\n" "MIHOMO_RUN_DIR='/etc/nikki/run'"
  printf "%s\n" "MIHOMO_CONFIG='/etc/nikki/run/config.yaml'"
  printf "%s\n" "MIHOMO_INIT='/etc/init.d/nikki'"
} > "$CONF_FILE"
chmod 600 "$CONF_FILE"

cat > "$CGI_PATH" <<'CGI'
#!/bin/sh
CONF_FILE="/etc/unified-ui/openwrt.env"
[ -f "$CONF_FILE" ] && . "$CONF_FILE"
MIHOMO_CONTROLLER="${MIHOMO_CONTROLLER:-http://127.0.0.1:6060}"
MIHOMO_SECRET="${MIHOMO_SECRET:-}"
MIHOMO_INIT="${MIHOMO_INIT:-/etc/init.d/nikki}"
MIHOMO_CONFIG="${MIHOMO_CONFIG:-/etc/nikki/run/config.yaml}"

json_escape() {
  sed 's/\\/\\\\/g; s/"/\\"/g; s/\t/\\t/g; s/\r/\\r/g; s/$/\\n/' | tr -d '\n' | sed 's/\\n$//'
}

hdr_json() {
  printf 'Status: %s\r\n' "${1:-200 OK}"
  printf 'Content-Type: application/json; charset=utf-8\r\n'
  printf 'Cache-Control: no-store\r\n\r\n'
}

mihomo_get() {
  path="$1"
  if [ -n "$MIHOMO_SECRET" ]; then
    header_name="Authorization"
    header_value="Bearer $MIHOMO_SECRET"
    curl -sS --max-time 8 -H "$header_name: $header_value" "$MIHOMO_CONTROLLER$path"
  else
    curl -sS --max-time 8 "$MIHOMO_CONTROLLER$path"
  fi
}

mihomo_req() {
  method="$1"
  path="$2"
  body="${3:-}"
  if [ -n "$MIHOMO_SECRET" ]; then
    header_name="Authorization"
    header_value="Bearer $MIHOMO_SECRET"
    if [ -n "$body" ]; then
      curl -sS --max-time 12 -X "$method" -H "$header_name: $header_value" -H 'Content-Type: application/json' --data "$body" "$MIHOMO_CONTROLLER$path"
    else
      curl -sS --max-time 12 -X "$method" -H "$header_name: $header_value" "$MIHOMO_CONTROLLER$path"
    fi
  else
    if [ -n "$body" ]; then
      curl -sS --max-time 12 -X "$method" -H 'Content-Type: application/json' --data "$body" "$MIHOMO_CONTROLLER$path"
    else
      curl -sS --max-time 12 -X "$method" "$MIHOMO_CONTROLLER$path"
    fi
  fi
}

read_body() {
  len="${CONTENT_LENGTH:-0}"
  case "$len" in ''|*[!0-9]*) len=0 ;; esac
  if [ "$len" -gt 0 ]; then
    dd bs=1 count="$len" 2>/dev/null
  fi
}

case "${PATH_INFO:-}" in
  /version)
    hdr_json
    mihomo_get /version || printf '{"ok":false,"error":"mihomo request failed"}'
    ;;
  /configs)
    hdr_json
    mihomo_get /configs || printf '{"ok":false,"error":"mihomo request failed"}'
    ;;
  /proxies)
    hdr_json
    mihomo_get /proxies || printf '{"ok":false,"error":"mihomo request failed"}'
    ;;
  /connections)
    hdr_json
    mihomo_get /connections || printf '{"ok":false,"error":"mihomo request failed"}'
    ;;
  /status)
    hdr_json
    pid="$(pidof mihomo 2>/dev/null || true)"
    ver="$(mihomo_get /version 2>/dev/null | jsonfilter -e '@.version' 2>/dev/null || true)"
    printf '{"ok":true,"pid":"%s","version":"%s","controller":"%s","config":"%s","config_exists":%s}' \
      "$pid" "$ver" "$MIHOMO_CONTROLLER" "$MIHOMO_CONFIG" "$([ -f "$MIHOMO_CONFIG" ] && echo true || echo false)"
    ;;
  /select)
    body="$(read_body)"
    group_enc="$(printf '%s' "$body" | jsonfilter -e '@.groupEncoded' 2>/dev/null || true)"
    name="$(printf '%s' "$body" | jsonfilter -e '@.name' 2>/dev/null || true)"
    if [ -z "$group_enc" ] || [ -z "$name" ]; then
      hdr_json '400 Bad Request'
      printf '{"ok":false,"error":"groupEncoded and name are required"}'
      exit 0
    fi
    name_json="$(printf '%s' "$name" | json_escape)"
    hdr_json
    mihomo_req PUT "/proxies/$group_enc" "{\"name\":\"$name_json\"}" || printf '{"ok":false,"error":"mihomo select failed"}'
    ;;
  /delay)
    body="$(read_body)"
    name_enc="$(printf '%s' "$body" | jsonfilter -e '@.nameEncoded' 2>/dev/null || true)"
    test_url="$(printf '%s' "$body" | jsonfilter -e '@.url' 2>/dev/null || true)"
    timeout="$(printf '%s' "$body" | jsonfilter -e '@.timeout' 2>/dev/null || true)"
    [ -n "$timeout" ] || timeout=5000
    [ -n "$test_url" ] || test_url='https://www.gstatic.com/generate_204'
    if [ -z "$name_enc" ]; then
      hdr_json '400 Bad Request'
      printf '{"ok":false,"error":"nameEncoded is required"}'
      exit 0
    fi
    hdr_json
    mihomo_req GET "/proxies/$name_enc/delay?timeout=$timeout&url=$test_url" || printf '{"ok":false,"error":"mihomo delay failed"}'
    ;;
  /connection-close)
    body="$(read_body)"
    id="$(printf '%s' "$body" | jsonfilter -e '@.id' 2>/dev/null || true)"
    if [ -z "$id" ]; then
      hdr_json '400 Bad Request'
      printf '{"ok":false,"error":"id is required"}'
      exit 0
    fi
    hdr_json
    mihomo_req DELETE "/connections/$id" || printf '{"ok":false,"error":"mihomo close connection failed"}'
    ;;
  /connections-close-all)
    hdr_json
    mihomo_req DELETE "/connections" || printf '{"ok":false,"error":"mihomo close all failed"}'
    ;;
  /restart)
    before="$(pidof mihomo 2>/dev/null || true)"
    out="$($MIHOMO_INIT restart 2>&1)"
    sleep 3
    after="$(pidof mihomo 2>/dev/null || true)"
    hdr_json
    esc="$(printf '%s' "$out" | json_escape)"
    changed=false; [ "$before" != "$after" ] && changed=true
    printf '{"ok":true,"before":"%s","after":"%s","pid_changed":%s,"log":"%s"}' "$before" "$after" "$changed" "$esc"
    ;;
  *)
    hdr_json '404 Not Found'
    printf '{"ok":false,"error":"unknown endpoint","path":"%s"}' "${PATH_INFO:-}"
    ;;
esac
CGI
chmod +x "$CGI_PATH"

cat > "$UI_ROOT/index.html" <<'HTML'
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Unified UI — OpenWrt</title>
  <style>
    :root{color-scheme:dark;--bg:#07111f;--panel:#0d1b2e;--line:#20344f;--text:#e8f0fb;--muted:#94a9c6;--accent:#39a8ff;--ok:#3ddc97;--bad:#ff5d6c;--warn:#ffb84d}
    *{box-sizing:border-box} body{margin:0;background:radial-gradient(circle at top left,#123a63 0,#07111f 38%,#050a12 100%);color:var(--text);font-family:Inter,system-ui,-apple-system,Segoe UI,sans-serif}
    header{position:sticky;top:0;z-index:5;background:rgba(7,17,31,.92);backdrop-filter:blur(14px);border-bottom:1px solid var(--line);padding:14px 18px;display:flex;gap:14px;align-items:center;justify-content:space-between}
    h1{font-size:18px;margin:0}.dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--ok);box-shadow:0 0 16px var(--ok);margin-right:8px}.tabs{display:flex;gap:8px;flex-wrap:wrap}.tab{border:1px solid var(--line);background:#0b1728;color:var(--text);border-radius:10px;padding:8px 11px;cursor:pointer}.tab.active{background:linear-gradient(135deg,#168bff,#42d392);border-color:transparent;color:#001524;font-weight:800}
    main{padding:18px;display:grid;gap:16px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}.card{background:rgba(13,27,46,.88);border:1px solid var(--line);border-radius:18px;padding:16px;box-shadow:0 20px 60px rgba(0,0,0,.22)}
    .card h2{margin:0 0 10px;font-size:16px}.muted{color:var(--muted);font-size:13px}.kv{display:grid;grid-template-columns:120px 1fr;gap:8px;font-size:13px}.btn{border:0;border-radius:10px;padding:9px 12px;cursor:pointer;font-weight:800;background:#18314f;color:var(--text)}.btn.primary{background:linear-gradient(135deg,#168bff,#42d392);color:#001524}.btn.warn{background:#5a3510;color:#ffd9a3}.toolbar{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
    table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid var(--line);padding:8px;text-align:left;vertical-align:top}th{color:#bcd0ea}.pill{display:inline-flex;border-radius:999px;padding:3px 8px;background:#162944;color:#bdd2ef;font-size:12px}.online{background:rgba(61,220,151,.18);color:#8dffc8}.offline{background:rgba(255,93,108,.18);color:#ff9ba5}pre{white-space:pre-wrap;word-break:break-word;background:#08111e;border:1px solid var(--line);border-radius:12px;padding:10px;max-height:420px;overflow:auto}.hidden{display:none}select,input{background:#091728;color:var(--text);border:1px solid var(--line);border-radius:9px;padding:7px;max-width:100%}.btn.small{padding:5px 8px;font-size:12px}.row-actions{display:flex;gap:6px;flex-wrap:wrap}.toast{position:fixed;right:16px;bottom:16px;background:#10233d;border:1px solid var(--line);border-radius:12px;padding:10px 12px;box-shadow:0 20px 50px rgba(0,0,0,.35);z-index:20}
  </style>
</head>
<body>
<header><h1><span class="dot"></span>Unified UI <span class="muted">OpenWrt / Nikki / Mihomo</span></h1><div class="tabs"><button class="tab active" data-view="status">Статус</button><button class="tab" data-view="selectors">Маршрутизация</button><button class="tab" data-view="connections">Соединения</button><button class="tab" data-view="raw">Raw API</button></div></header>
<main>
  <section id="view-status" class="view grid"><div class="card"><h2>Состояние Mihomo</h2><div id="status" class="kv muted">Загрузка…</div><div class="toolbar"><button class="btn primary" onclick="loadAll()">Обновить</button><button class="btn warn" onclick="restartMihomo()">Restart Nikki/Mihomo</button></div></div><div class="card"><h2>OpenWrt адаптер</h2><p class="muted">Лёгкий backend без Python: uhttpd CGI → Mihomo API :6060 с secret из UCI Nikki.</p><pre id="restartLog">Пока без рестартов.</pre></div></section>
  <section id="view-selectors" class="view hidden"><div class="card"><h2>Селекторы / группы</h2><div class="toolbar"><button class="btn primary" onclick="loadProxies()">Обновить</button><button class="btn" onclick="pingVisible()">Обновить все пинги</button></div><div class="muted" id="proxySummary"></div><div id="groups"></div></div></section>
  <section id="view-connections" class="view hidden"><div class="card"><h2>Активные соединения</h2><div class="toolbar"><button class="btn primary" onclick="loadConnections()">Обновить соединения</button><button class="btn warn" onclick="closeAllConnections()">Разорвать все</button><input id="connFilter" placeholder="Фильтр host/IP/process" oninput="renderConnections()"></div><div id="connections"></div></div></section>
  <section id="view-raw" class="view hidden grid"><div class="card"><h2>/configs</h2><pre id="rawConfigs"></pre></div><div class="card"><h2>/version</h2><pre id="rawVersion"></pre></div></section>
</main>
<script>
const API='/cgi-bin/unified-ui-api';
const $=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let proxyCache={}; let connectionCache=[]; let visibleNodeNames=[];
function toast(msg){let t=document.createElement('div');t.className='toast';t.textContent=msg;document.body.appendChild(t);setTimeout(()=>t.remove(),2800)}
async function get(path){const r=await fetch(API+path,{cache:'no-store'}); if(!r.ok) throw new Error(path+' HTTP '+r.status); return r.json();}
async function post(path, body={}){const r=await fetch(API+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),cache:'no-store'}); if(!r.ok) throw new Error(path+' HTTP '+r.status); const txt=await r.text(); return txt?JSON.parse(txt):{};}
document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>{document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.querySelectorAll('.view').forEach(v=>v.classList.add('hidden'));$('#view-'+b.dataset.view).classList.remove('hidden');});
async function loadStatus(){try{const s=await get('/status');$('#status').innerHTML=`<b>PID</b><span>${esc(s.pid||'нет')}</span><b>Version</b><span>${esc(s.version||'unknown')}</span><b>Controller</b><span>${esc(s.controller)}</span><b>Config</b><span>${esc(s.config)} · ${s.config_exists?'есть':'нет'}</span>`;}catch(e){$('#status').textContent=e.message;}}
function latency(p){const h=p.history||[]; const last=h[h.length-1]; return typeof last?.delay==='number'?last.delay+' ms':'—';}
function optionList(g){return (g.all||[]).map(n=>`<option value="${esc(n)}" ${n===g.now?'selected':''}>${esc(n)}</option>`).join('')}
async function selectProxy(group,name){try{await post('/select',{group,groupEncoded:encodeURIComponent(group),name});toast(`Выбрано: ${group} → ${name}`);await loadProxies();}catch(e){toast('Ошибка выбора: '+e.message)}}
async function pingProxy(name){try{const d=await post('/delay',{name,nameEncoded:encodeURIComponent(name),timeout:5000,url:'https://www.gstatic.com/generate_204'});toast(`${name}: ${d.delay??'нет ответа'} ms`);await loadProxies();}catch(e){toast('Ping error: '+name+' · '+e.message)}}
async function pingVisible(){for(const n of visibleNodeNames.slice(0,80)){await pingProxy(n)}}
async function loadProxies(){const data=await get('/proxies'); proxyCache=data.proxies||{}; const proxies=proxyCache; const groups=Object.values(proxies).filter(p=>Array.isArray(p.all)); const nodes=Object.values(proxies).filter(p=>!Array.isArray(p.all)); visibleNodeNames=[...new Set(groups.flatMap(g=>g.all||[]).filter(n=>proxies[n] && !Array.isArray(proxies[n].all)))]; $('#proxySummary').textContent=`Групп: ${groups.length} · узлов/служебных proxy: ${nodes.length}`; $('#groups').innerHTML=groups.map((g,idx)=>`<h3>${esc(g.name)} <span class="pill">${esc(g.type)}</span> <span class="muted">сейчас: ${esc(g.now||'')}</span></h3><div class="toolbar"><select id="sel-${idx}">${optionList(g)}</select><button class="btn primary small" onclick="selectProxy(${JSON.stringify(g.name)}, document.getElementById('sel-${idx}').value)">Применить выбор</button></div><table><thead><tr><th>Proxy</th><th>Тип</th><th>Статус</th><th>Ping</th><th>Действия</th></tr></thead><tbody>${(g.all||[]).map(n=>{const p=proxies[n]||{}; const alive=p.alive===false?'offline':'online'; return `<tr><td>${esc(n)}</td><td>${esc(p.type||'')}</td><td><span class="pill ${alive}">${alive}</span></td><td><button class="btn small" onclick="pingProxy(${JSON.stringify(n)})">${esc(latency(p))}</button></td><td><button class="btn primary small" onclick="selectProxy(${JSON.stringify(g.name)}, ${JSON.stringify(n)})">Выбрать</button></td></tr>`}).join('')}</tbody></table>`).join('');}
async function loadConnections(){try{const d=await get('/connections'); connectionCache=d.connections||[]; renderConnections();}catch(e){$('#connections').textContent=e.message;}}
function renderConnections(){const q=($('#connFilter')?.value||'').toLowerCase(); const arr=connectionCache.filter(c=>JSON.stringify(c).toLowerCase().includes(q)); $('#connections').innerHTML=`<p class="muted">Соединений: ${arr.length} / ${connectionCache.length}</p><table><thead><tr><th>Host</th><th>Source</th><th>Process</th><th>Rule</th><th>Chains</th><th>Upload/Download</th><th></th></tr></thead><tbody>${arr.slice(0,300).map(c=>`<tr><td>${esc(c.metadata?.host||c.metadata?.destinationIP||'')}</td><td>${esc(c.metadata?.sourceIP||'')}:${esc(c.metadata?.sourcePort||'')}</td><td>${esc(c.metadata?.process||'')}</td><td>${esc(c.rule||'')}</td><td>${esc((c.chains||[]).join(' → '))}</td><td>${esc(c.upload||0)} / ${esc(c.download||0)}</td><td><button class="btn warn small" onclick="closeConnection(${JSON.stringify(c.id)})">Разорвать</button></td></tr>`).join('')}</tbody></table>`;}
async function closeConnection(id){try{await post('/connection-close',{id});toast('Соединение разорвано');await loadConnections();}catch(e){toast('Ошибка разрыва: '+e.message)}}
async function closeAllConnections(){try{await post('/connections-close-all',{});toast('Все соединения разорваны');await loadConnections();}catch(e){toast('Ошибка: '+e.message)}}
async function loadRaw(){for(const [id,path] of [['#rawConfigs','/configs'],['#rawVersion','/version']]){try{$(id).textContent=JSON.stringify(await get(path),null,2)}catch(e){$(id).textContent=e.message}}}
async function restartMihomo(){ $('#restartLog').textContent='Перезапускаю…'; try{const d=await get('/restart'); $('#restartLog').textContent=JSON.stringify(d,null,2); await new Promise(r=>setTimeout(r,1200)); loadAll(); }catch(e){$('#restartLog').textContent=e.message;} }
async function loadAll(){await loadStatus(); await Promise.allSettled([loadProxies(),loadConnections(),loadRaw()]);}
loadAll(); setInterval(loadStatus,10000);
</script>
</body>
</html>
HTML

printf 'Installed Unified UI OpenWrt prototype:\n  /www/unified-ui/index.html\n  %s\n' "$CGI_PATH"
