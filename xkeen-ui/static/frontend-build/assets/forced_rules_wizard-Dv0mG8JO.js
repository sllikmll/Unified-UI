import{o as e}from"./routing-Bxv7EMdb.js";import{t}from"./routing_cards_namespace-Bdk12Xcz.js";(function(){window.XKeen=window.XKeen||{};let n=window.XKeen;window.XKeen;let r=t();r.rules=r.rules||{},r.rules.forcedRulesWizard=r.rules.forcedRulesWizard||{};let i=r.rules.forcedRulesWizard,a=r.common||{},o=typeof a.toast==`function`?a.toast:function(e,t){try{console[t?`error`:`log`](String(e||``))}catch{}},s=r.rules&&r.rules.model?r.rules.model:{},c=r.rules&&r.rules.apply?r.rules.apply:{},l=r.rules&&r.rules.render?r.rules.render:{},u=`routing-forced-rules-modal`,d={close:`routing-forced-rules-close-btn`,cancel:`routing-forced-rules-cancel-btn`,run:`routing-forced-rules-run-btn`,dry:`routing-forced-rules-dry-btn`,refresh:`routing-forced-rules-refresh-tags-btn`,status:`routing-forced-rules-status`,list:`routing-forced-rules-list`,outbound:`routing-forced-rules-outbound`,type:`routing-forced-rules-type`,values:`routing-forced-rules-values`,add:`routing-forced-rules-add-btn`,clearProxy:`routing-forced-rules-clear-proxy-btn`,clearAll:`routing-forced-rules-clear-all-btn`,inboundOnly:`routing-forced-rules-inbound-only`,priority:`routing-forced-rules-priority`,importLegacy:`routing-forced-rules-import-legacy`,summary:`routing-forced-rules-summary`};function f(e){try{return document.getElementById(e)}catch{return null}}function p(){let e=f(u);return e||(document.body?(document.body.insertAdjacentHTML(`beforeend`,`
      <div id="routing-forced-rules-modal" class="modal hidden" data-modal-key="routing-forced-rules-premium-v4" role="dialog" aria-modal="true" aria-label="Принудительные правила (обход балансировщика)">
        <div class="modal-content" data-modal-key="routing-forced-rules-premium-v4-content">
          <div class="modal-header">
            <span class="modal-title">Принудительные правила (обход балансировщика)</span>
            <button type="button" class="modal-close" id="routing-forced-rules-close-btn" title="Закрыть">×</button>
          </div>
          <div class="modal-body">
            <div class="xk-forced-wizard-lead">
              <div class="xk-forced-wizard-lead-icon">⇄</div>
              <div class="xk-forced-wizard-lead-text">
                <div class="xk-forced-wizard-lead-title">Домены и IP → конкретный outbound</div>
                <p class="modal-description" style="margin:0;">
                  Мастер создаёт правила <code>type: field</code>, которые отправляют выбранные значения <b>мимо балансировщика</b> прямо на нужный <code>outboundTag</code>.
                </p>
              </div>
            </div>

            <div class="xk-forced-wizard-grid">
              <section class="xk-forced-wizard-panel xk-forced-wizard-input-panel">
                <div class="xk-forced-wizard-panelhead">
                  <div>
                    <div class="xk-forced-wizard-kicker">Шаг 1</div>
                    <div class="terminal-menu-title" style="margin:0;">Добавить значения</div>
                  </div>
                </div>

                <div class="xk-forced-controls-grid">
                  <label class="xk-forced-fieldgroup">
                    <span class="xk-forced-fieldlabel">outbound</span>
                    <div class="xk-forced-outbound-wrap">
                      <select id="routing-forced-rules-outbound" class="routing-rule-input"></select>
                      <button type="button" class="btn-secondary btn-icon xk-icon-btn" id="routing-forced-rules-refresh-tags-btn" data-tooltip="Обновить список outbound-тегов" aria-label="Обновить список outbound-тегов"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M16.2 10a6.2 6.2 0 1 1-1.83-4.39"/><path d="M16.2 4.6v3.62h-3.62"/></svg></button>
                    </div>
                  </label>

                  <label class="xk-forced-fieldgroup xk-forced-fieldgroup-compact">
                    <span class="xk-forced-fieldlabel">Тип</span>
                    <select id="routing-forced-rules-type" class="routing-rule-input">
                      <option value="domain">domain</option>
                      <option value="ip">ip</option>
                    </select>
                  </label>
                </div>

                <div class="xk-forced-editor-block">
                  <div class="xk-forced-editor-head">
                    <span class="xk-forced-fieldlabel">Значения</span>
                    <div class="xk-forced-wizard-toolbar">
                      <button type="button" class="btn-secondary btn-icon xk-icon-btn" id="routing-forced-rules-add-btn" data-tooltip="Добавить значения в выбранный outbound" aria-label="Добавить значения"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 4.2v11.6"/><path d="M4.2 10h11.6"/></svg></button>
                      <button type="button" class="btn-secondary btn-icon xk-icon-btn" id="routing-forced-rules-clear-proxy-btn" data-tooltip="Очистить значения только у выбранного outbound" aria-label="Очистить выбранный outbound"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M8.1 5h6.95a1.4 1.4 0 0 1 1.4 1.4v7.2a1.4 1.4 0 0 1-1.4 1.4H8.1L3.55 10 8.1 5Z"/><path d="m9.3 8 4.1 4.1"/><path d="m13.4 8-4.1 4.1"/></svg></button>
                      <button type="button" class="btn-danger btn-icon xk-icon-btn" id="routing-forced-rules-clear-all-btn" data-tooltip="Удалить все записи мастера" aria-label="Удалить все записи"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5.8 6.2h8.4"/><path d="M7.1 6.2V5a1 1 0 0 1 1-1h3.8a1 1 0 0 1 1 1v1.2"/><path d="M7.2 8.2v6.1"/><path d="M10 8.2v6.1"/><path d="M12.8 8.2v6.1"/><path d="M6.5 6.2l.6 9a1 1 0 0 0 1 .9h3.8a1 1 0 0 0 1-.9l.6-9"/></svg></button>
                    </div>
                  </div>

                  <textarea id="routing-forced-rules-values" class="xkeen-textarea" spellcheck="false" rows="7" placeholder="По одному на строке
example.com
domain:google.com
geosite:youtube

Для ip:
1.2.3.4/32
geoip:private"></textarea>
                </div>

                <div class="xk-forced-wizard-note">
                  Поддерживаются обычные значения Xray для <code>domain</code>/<code>ip</code>: <code>domain:example.com</code>, <code>geosite:TAG</code>, <code>geoip:TAG</code> и другие.
                </div>
              </section>

              <section class="xk-forced-wizard-panel xk-forced-wizard-preview-panel">
                <div class="xk-forced-wizard-panelhead">
                  <div>
                    <div class="xk-forced-wizard-kicker">Шаг 2</div>
                    <div class="terminal-menu-title" style="margin:0;">Параметры и результат</div>
                  </div>
                  <div id="routing-forced-rules-summary" class="xk-forced-wizard-summary" data-tooltip="Количество outbound, domain и ip в мастере">0 outbound · 0 domain · 0 ip</div>
                </div>

                <div class="xk-forced-options-grid">
                  <label class="xk-forced-option-card global-autorestart-toggle">
                    <input type="checkbox" id="routing-forced-rules-inbound-only" checked>
                    <div class="xk-forced-option-copy">
                      <strong>Только redirect / tproxy</strong>
                      <small>Не трогать другие inbound</small>
                    </div>
                  </label>

                  <label class="xk-forced-option-card xk-forced-option-select">
                    <span class="xk-forced-fieldlabel">Приоритет</span>
                    <select id="routing-forced-rules-priority" class="routing-rule-input">
                      <option value="after_block">После block-правил</option>
                      <option value="before_balancer">Перед балансировщиком</option>
                    </select>
                  </label>

                  <label class="xk-forced-option-card global-autorestart-toggle xk-forced-option-wide">
                    <input type="checkbox" id="routing-forced-rules-import-legacy">
                    <div class="xk-forced-option-copy">
                      <strong>Импорт legacy-правил</strong>
                      <small>Мигрировать правила без <code>ruleTag</code> без дублей</small>
                    </div>
                  </label>
                </div>

                <div class="xk-forced-wizard-listbox">
                  <div class="xk-forced-wizard-listhead">
                    <div class="xk-forced-wizard-listtitle">
                      <div class="terminal-menu-title" style="margin:0;">Текущие правила</div>
                      <div class="xk-forced-list-subtitle">Карточки по outboundTag: компактный обзор, клик по chip удаляет значение</div>
                    </div>
                    <div id="routing-forced-rules-status" class="modal-hint" style="margin:0;"></div>
                  </div>
                  <div id="routing-forced-rules-list" class="xk-card-desc xk-forced-wizard-list">—</div>
                </div>
              </section>
            </div>
          </div>

          <div class="modal-actions xk-forced-wizard-footer">
            <button type="button" class="btn-compact" id="routing-forced-rules-cancel-btn">Отмена</button>
            <div class="xk-forced-wizard-footer-actions">
              <button type="button" class="btn-secondary btn-compact xk-forced-primary-action" id="routing-forced-rules-dry-btn" data-tooltip="Только применить изменения в редакторе без сохранения и рестарта"><span class="xk-btn-inline-glyph" aria-hidden="true">✓</span><span>Только применить</span></button>
              <button type="button" class="btn-danger btn-compact xk-forced-primary-action" id="routing-forced-rules-run-btn"><span class="xk-btn-inline-glyph" aria-hidden="true">⟳</span><span>Применить + Рестарт</span></button>
            </div>
          </div>
        </div>
      </div>
    `),e=f(u),e):null)}function m(){try{window.XKeen&&n.ui&&n.ui.modal&&typeof n.ui.modal.syncBodyScrollLock==`function`&&n.ui.modal.syncBodyScrollLock()}catch{}}function h(){let e=p();if(e){try{e.classList.remove(`hidden`)}catch{}m()}}function g(){let e=f(u);if(e){try{e.classList.add(`hidden`)}catch{}m()}}function _(e,t){let n=f(d.status);if(n)try{n.textContent=String(e||``),n.style.color=t?`var(--danger, #ef4444)`:`var(--modal-muted, var(--muted, #9ca3af))`}catch{}}function v(){let e=f(d.summary);if(!e)return;let t=i._state.forced||{},n=Object.keys(t),r=0,a=0;n.forEach(e=>{let n=t[e]||{};r+=Array.isArray(n.domains)?n.domains.length:0,a+=Array.isArray(n.ips)?n.ips.length:0});try{e.textContent=`${n.length} outbound · ${r} domain · ${a} ip`}catch{}}function y(e){[d.run,d.dry,d.refresh,d.cancel,d.close,d.add,d.clearProxy,d.clearAll,d.outbound,d.type,d.values,d.inboundOnly,d.priority,d.importLegacy].forEach(t=>{let n=f(t);if(n){try{n.disabled=!!e}catch{}try{n.classList.toggle(`is-busy`,!!e)}catch{}}})}let b=`xk_forced_`;i._state=i._state||{forced:{},tags:[]};function x(e){let t=String(e||``).replace(/,/g,`
`).split(/\r?\n/).map(e=>String(e||``).trim()).filter(Boolean),n=[],r=new Set;for(let e of t)r.has(e)||(r.add(e),n.push(e));return n}function S(e,t){let n=String(e||``).trim().replace(/[^a-zA-Z0-9_-]/g,`_`),r=t===`ip`?`_ip`:t===`domain`?`_domain`:``;return b+(n||`proxy`)+r}function C(e){let t=String(e||``).toLowerCase();return t===`block`||t===`blackhole`||t===`reject`}function w(e){if(!e||typeof e!=`object`||Array.isArray(e)||e.balancerTag||!e.outboundTag)return!1;let t=String(e.outboundTag||``).trim();if(!t||C(t)||t.toLowerCase()===`direct`||!e.domain&&!e.ip)return!1;let n=Object.keys(e),r=new Set([`type`,`outboundTag`,`inboundTag`,`domain`,`ip`,`ruleTag`]);for(let e of n)if(!r.has(e))return!1;if(e.inboundTag&&Array.isArray(e.inboundTag)){let t=new Set(e.inboundTag.map(e=>String(e||``).trim()).filter(Boolean));if(!(t.has(`redirect`)||t.has(`tproxy`)))return!1}return!0}function T(e,t){let n={};if(!e||!Array.isArray(e.rules))return n;for(let r of e.rules){if(!r||typeof r!=`object`||Array.isArray(r))continue;let e=String(r.ruleTag||``).startsWith(b),i=!e&&!!t&&w(r);if(!e&&!i)continue;let a=String(r.outboundTag||``).trim();a&&(n[a]||(n[a]={domains:[],ips:[]}),Array.isArray(r.domain)&&(n[a].domains=n[a].domains.concat(r.domain.map(e=>String(e||``).trim()).filter(Boolean))),Array.isArray(r.ip)&&(n[a].ips=n[a].ips.concat(r.ip.map(e=>String(e||``).trim()).filter(Boolean))))}for(let e of Object.keys(n))n[e].domains=x(n[e].domains.join(`
`)),n[e].ips=x(n[e].ips.join(`
`)),!n[e].domains.length&&!n[e].ips.length&&delete n[e];return n}function E(){let e=f(d.list);if(!e)return;let t=i._state.forced||{},n=Object.keys(t);if(v(),!n.length){e.innerHTML=`<div class="xk-forced-wizard-empty">Пока пусто. Добавьте домены или IP слева.</div>`;return}function r(e,t,n){return`<span class="xk-chip" data-kind="${D(t)}" data-tag="${D(e)}" data-value="${D(n)}" title="Удалить значение">${D(n)} ×</span>`}function a(e,t,n){if(!n.length)return``;let i=n.map(n=>r(e,t,n)).join(` `);return`<div class="xk-forced-inline-row" data-kind="${D(t)}"><span class="xk-forced-inline-label">${D(t)}</span><div class="xk-forced-rule-chips is-inline">${i}</div></div>`}n.sort((e,t)=>e.localeCompare(t,`ru`));let o=[];for(let e of n){let n=t[e]||{domains:[],ips:[]},i=Array.isArray(n.domains)?n.domains:[],s=Array.isArray(n.ips)?n.ips:[],c=i.length+s.length,l=c<=5&&i.length<=3&&s.length<=3,u=i.map(t=>r(e,`domain`,t)).join(` `),d=s.map(t=>r(e,`ip`,t)).join(` `),f=[];l?(i.length&&f.push(a(e,`domain`,i)),s.length&&f.push(a(e,`ip`,s))):(i.length&&f.push(`<div class="xk-forced-rule-group" data-kind="domain"><div class="xk-forced-rule-group-head"><span class="xk-forced-rule-group-title">domain</span><span class="xk-forced-rule-group-meta">${i.length}</span></div><div class="xk-forced-rule-chips">${u}</div></div>`),s.length&&f.push(`<div class="xk-forced-rule-group" data-kind="ip"><div class="xk-forced-rule-group-head"><span class="xk-forced-rule-group-title">ip</span><span class="xk-forced-rule-group-meta">${s.length}</span></div><div class="xk-forced-rule-chips">${d}</div></div>`)),o.push(`<div class="xk-forced-rule-card${l?` is-inline`:``}"><div class="xk-forced-rule-head"><div class="xk-forced-rule-tagwrap"><span class="xk-forced-rule-accent" aria-hidden="true"></span><div class="xk-forced-rule-tag"><code>${D(e)}</code></div></div><div class="xk-forced-rule-badges"><span class="xk-forced-count is-total">${c} знач.</span><span class="xk-forced-count is-domain">domain ${i.length}</span><span class="xk-forced-count is-ip">ip ${s.length}</span></div></div><div class="xk-forced-rule-groups${l?` is-inline`:``}">${f.join(``)||`<span class="xk-forced-rule-empty">—</span>`}</div></div>`)}e.innerHTML=o.join(``)}function D(e){return String(e||``).replace(/&/g,`&amp;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`).replace(/"/g,`&quot;`).replace(/'/g,`&#039;`)}function O(e,t,n){let r=String(e||``).trim();if(!r)return;let a=t===`ip`?`ips`:`domains`,o=String(n||``).trim(),s=i._state.forced&&i._state.forced[r];if(!(!s||!Array.isArray(s[a]))){if(s[a]=s[a].filter(e=>String(e||``).trim()!==o),!s.domains.length&&!s.ips.length)try{delete i._state.forced[r]}catch{}E()}}async function k(){let e=a&&typeof a.buildOutboundTagsUrl==`function`?a.buildOutboundTagsUrl():`/api/xray/outbound-tags`;try{let t=await fetch(e,{method:`GET`}),n=await t.json().catch(()=>({}));return!t.ok||!n||n.ok===!1||!Array.isArray(n.tags)?[]:n.tags.map(e=>String(e||``).trim()).filter(Boolean)}catch{return[]}}let A=new Set([`dns`,`freedom`,`blackhole`,`reject`,`bypass`]);function j(e){let t=String(e||``).trim();if(!t)return!0;let n=t.toLowerCase();return!!(A.has(n)||n===`api`||n===`xray-api`||n===`metrics`)}function M(e){let t=f(d.outbound);if(!t)return;let n=String(t.value||``).trim(),r=(e||[]).filter(e=>!j(e));if(t.innerHTML=``,!r.length){let e=document.createElement(`option`);e.value=``,e.textContent=`Нет outbound-тегов`,t.appendChild(e),t.value=``;return}for(let e of r){let n=document.createElement(`option`);n.value=e,n.textContent=e,t.appendChild(n)}n&&r.includes(n)?t.value=n:t.value=r[0]||``}function N(e,t,n){let r=String(e||``).trim();if(!r)return{added:0};i._state.forced[r]||(i._state.forced[r]={domains:[],ips:[]});let a=i._state.forced[r],o=t===`ip`?`ips`:`domains`,s=new Set((a[o]||[]).map(e=>String(e||``).trim()).filter(Boolean)),c=0;for(let e of n){let t=String(e||``).trim();!t||s.has(t)||(s.add(t),a[o].push(t),c++)}if(a[o]=x(a[o].join(`
`)),!a.domains.length&&!a.ips.length)try{delete i._state.forced[r]}catch{}return{added:c}}function P(){let e=f(d.outbound),t=e?String(e.value||``).trim():``;if(t){if(i._state.forced&&i._state.forced[t])try{delete i._state.forced[t]}catch{}E()}}function F(){i._state.forced={},E()}function I(e,t){return Array.isArray(e)?e.filter(e=>!e||typeof e!=`object`||Array.isArray(e)?!0:!(String(e.ruleTag||``).startsWith(b)||t&&w(e))):[]}function L(e){if(!Array.isArray(e))return-1;for(let t=0;t<e.length;t++){let n=e[t];if(!(!n||typeof n!=`object`||Array.isArray(n))&&n.balancerTag)return t}return-1}function R(e){if(!e||typeof e!=`object`||Array.isArray(e))return!1;let t=Object.keys(e),n=new Set([`type`,`outboundTag`,`balancerTag`,`ruleTag`]);for(let e of t)if(!n.has(e))return!1;return!0}function z(e){if(!Array.isArray(e)||!e.length)return 0;for(let t=e.length-1;t>=0;t--){let n=e[t];if(!R(n))return e.length;let r=String(n&&(n.outboundTag||n.balancerTag)||``).toLowerCase();if(r===`direct`||r===`block`||r===`blackhole`||r===`reject`)return t}return e.length}function B(e,t){let n=L(e);if(t===`before_balancer`)return n>=0?n:z(e);let r=n>=0?n:e.length,i=0;for(;i<r;i++){let t=e[i];if(!t||typeof t!=`object`||Array.isArray(t)||!C(String(t.outboundTag||``).trim()))break}return i}function V(e,t,n,r){let i=t===`ip`?`ip`:`domain`,a=x(Array.isArray(n)?n.join(`
`):n),o={type:`field`,outboundTag:e,ruleTag:S(e,i)};return r&&r.inboundOnly&&(o.inboundTag=[`redirect`,`tproxy`]),a.length&&(o[i]=a),o}async function H(){return!c||typeof c.applyToEditor!=`function`?(o(`Не найден модуль применения (applyToEditor).`,!0),!1):await c.applyToEditor({silent:!1})}async function U(){let t=e();if(t&&typeof t.save==`function`){let e=document.getElementById(`global-autorestart-xkeen`),n=e?!!e.checked:null;try{return e&&(e.checked=!0),await t.save(),!0}finally{try{e&&n!==null&&(e.checked=n)}catch{}}}try{let e=a&&typeof a.getEditorText==`function`?a.getEditorText():``,t=await fetch(`/api/routing?restart=1&async=1`,{method:`POST`,headers:{"Content-Type":`text/plain;charset=utf-8`},body:String(e||``)}),n=await t.json().catch(()=>({}));if(!t.ok||!n||n.ok===!1)throw Error(String(n&&n.error||t.statusText||`HTTP `+t.status));return!0}catch(e){return o(`Не удалось сохранить routing: `+String(e&&e.message?e.message:e),!0),!1}}async function W(e){y(!0),_(`Подготовка…`,!1);try{let t=!!(f(d.importLegacy)&&f(d.importLegacy).checked),n=s&&typeof s.loadFromEditor==`function`?s.loadFromEditor({setError:!0}):{ok:!1};if(!n||n.ok===!1)return _(`Сначала исправьте JSON в редакторе (или дождитесь загрузки файла).`,!0),!1;let r=s&&typeof s.ensureModel==`function`?s.ensureModel():n.model||{};(!r||!Array.isArray(r.rules))&&(r.rules=[]);let a=i._state.forced||{},c=Object.keys(a).filter(e=>{let t=a[e];return t?(Array.isArray(t.domains)?t.domains.length:0)+(Array.isArray(t.ips)?t.ips.length:0)>0:!1}),u=T(r,t),p=Object.keys(u).length>0;if(!c.length&&!p)return _(`Список принудительных правил пуст. Добавьте домены/IP и повторите.`,!0),!1;let m=new Set((i._state.tags||[]).map(e=>String(e||``).trim()).filter(Boolean));if(c.length&&m.size){let e=c.filter(e=>!m.has(e));if(e.length)return _(`outboundTag не найден в outbounds: ${e.join(`, `)}. Обновите список тегов или выберите конкретный outbound.`,!0),!1}r.rules=I(r.rules,t),c.sort((e,t)=>e.localeCompare(t,`ru`));let h=!!(f(d.inboundOnly)&&f(d.inboundOnly).checked),v=[];for(let e of c){let t=a[e]||{domains:[],ips:[]},n=x((t.domains||[]).join(`
`)),r=x((t.ips||[]).join(`
`));!n.length&&!r.length||(n.length&&v.push(V(e,`domain`,n,{inboundOnly:h})),r.length&&v.push(V(e,`ip`,r,{inboundOnly:h})))}if(v.length){let e=String(f(d.priority)&&f(d.priority).value||`after_block`),t=B(r.rules,e);r.rules.splice(t,0,...v)}try{s&&typeof s.markDirty==`function`&&s.markDirty(!0)}catch{}try{l&&typeof l.renderAll==`function`&&l.renderAll()}catch{}return _(`Применяю изменения в JSON‑редактор…`,!1),await H()?e&&e.dry?(_(`Готово: изменения применены в редактор (без сохранения/рестарта).`,!1),o(`Изменения применены в редактор`,!1),!0):(_(`Сохраняю и перезапускаю…`,!1),await U()?(_(`Готово. Лог операции — в “Журнал операций Xkeen”.`,!1),o(`Готово`,!1),g(),!0):(_(`Сохранение/перезапуск завершились с ошибкой. См. журнал.`,!0),!1)):(_(`Не удалось применить изменения в редактор.`,!0),!1)}catch(e){let t=String(e&&e.message?e.message:e);return _(`Ошибка: `+t,!0),o(`Ошибка: `+t,!0),!1}finally{y(!1)}}async function G(){_(`Получаю теги из outbounds…`,!1);let e=await k();i._state.tags=e,M(e),_(e.length?`Теги загружены: ${e.length}`:`Не удалось получить outbound‑теги.`,!e.length)}function K(){let e=!!(f(d.importLegacy)&&f(d.importLegacy).checked),t=s&&typeof s.loadFromEditor==`function`?s.loadFromEditor({setError:!1}):{ok:!1};if(!t||t.ok===!1)return;let n=s&&typeof s.ensureModel==`function`?s.ensureModel():t.model||{};i._state.forced=T(n,e)}function q(){if(i.__wired)return;let e=p(),t=f(`routing-forced-rules-btn`);if(!t||!e)return;i.__wired=!0,t.addEventListener(`click`,async e=>{e.preventDefault(),_(``,!1),h(),y(!0);try{await G()}catch{_(`Не удалось обновить список outbound‑тегов. Можно ввести значения и всё равно применить.`,!0)}finally{y(!1)}try{K(),E()}catch{E()}});let n=f(d.close);n&&n.addEventListener(`click`,e=>{e.preventDefault(),g()});let r=f(d.cancel);r&&r.addEventListener(`click`,e=>{e.preventDefault(),g()}),e.addEventListener(`click`,t=>{try{t&&t.target===e&&g()}catch{}}),document.addEventListener(`keydown`,e=>{try{if(e.key!==`Escape`)return;let t=f(u);if(!t||t.classList.contains(`hidden`))return;g()}catch{}});let a=f(d.refresh);a&&a.addEventListener(`click`,async e=>{e.preventDefault(),y(!0);try{await G()}finally{y(!1)}});let o=f(d.add);o&&o.addEventListener(`click`,e=>{e.preventDefault();let t=f(d.outbound),n=f(d.type),r=f(d.values),i=t?String(t.value||``).trim():``,a=n?String(n.value||`domain`):`domain`,o=x(r?r.value:``);if(!i){_(`Выберите outboundTag.`,!0);return}if(!o.length){_(`Добавьте хотя бы одно значение.`,!0);return}let s=N(i,a,o);try{r&&(r.value=``)}catch{}E(),_(`Добавлено: ${s.added}.`,!1)});let s=f(d.clearProxy);s&&s.addEventListener(`click`,e=>{e.preventDefault(),P(),_(`Очищено.`,!1)});let c=f(d.clearAll);c&&c.addEventListener(`click`,e=>{e.preventDefault(),F(),_(`Удалены все записи мастера.`,!1)});let l=f(d.importLegacy);l&&l.addEventListener(`change`,()=>{try{K(),E()}catch{}});let m=f(d.list);m&&m.addEventListener(`click`,e=>{try{let t=e&&e.target;if(!t||!t.getAttribute||!t.classList||!t.classList.contains(`xk-chip`))return;O(t.getAttribute(`data-tag`),t.getAttribute(`data-kind`),t.getAttribute(`data-value`))}catch{}});let v=f(d.dry);v&&v.addEventListener(`click`,async e=>{e.preventDefault(),await W({dry:!0})});let b=f(d.run);b&&b.addEventListener(`click`,async e=>{e.preventDefault(),await W({dry:!1})})}i.init=function(){setTimeout(()=>{try{q()}catch{}},0)},document.readyState===`loading`?document.addEventListener(`DOMContentLoaded`,()=>i.init()):i.init()})();