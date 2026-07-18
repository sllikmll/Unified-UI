import{o as e}from"./routing-Bxv7EMdb.js";import{t}from"./routing_cards_namespace-Bdk12Xcz.js";(function(){window.XKeen=window.XKeen||{};let n=window.XKeen;window.XKeen;let r=t();r.rules=r.rules||{},r.rules.quickBalancer=r.rules.quickBalancer||{};let i=r.rules.quickBalancer,a=r.common||{},o=typeof a.toast==`function`?a.toast:function(e,t){try{console[t?`error`:`log`](String(e||``))}catch{}},s=typeof a.safeJsonParse==`function`?a.safeJsonParse:function(e){try{return JSON.parse(String(e||``))}catch(e){return{__error:e}}},c=r.rules&&r.rules.model?r.rules.model:{},l=r.rules&&r.rules.apply?r.rules.apply:{},u=r.rules&&r.rules.render?r.rules.render:{},d=`routing-balancer-quick-modal`,f={close:`routing-balancer-quick-close-btn`,cancel:`routing-balancer-quick-cancel-btn`,run:`routing-balancer-quick-run-btn`,dry:`routing-balancer-quick-dry-btn`,refreshTags:`routing-balancer-quick-refresh-tags-btn`,status:`routing-balancer-quick-status`,tag:`routing-balancer-quick-tag`,fallback:`routing-balancer-quick-fallback`,tags:`routing-balancer-quick-tags`,probeUrl:`routing-balancer-quick-probe-url`,probeInterval:`routing-balancer-quick-probe-interval`,conc:`routing-balancer-quick-concurrency`,defaultRule:`routing-balancer-quick-default-rule`,overwriteObs:`routing-balancer-quick-overwrite-observatory`,summary:`routing-balancer-quick-summary`},p=`xk_auto_leastPing`,m=[`redirect`,`tproxy`];function h(e){try{return document.getElementById(e)}catch{return null}}function g(){let e=h(d);return e||(document.body?(document.body.insertAdjacentHTML(`beforeend`,`
      <div id="routing-balancer-quick-modal" class="modal hidden" role="dialog" aria-modal="true" aria-label="Быстрый старт балансировщика (leastPing)">
        <div class="modal-content xk-qb-modal" data-modal-key="routing-balancer-quick-premium-v1">
          <div class="modal-header">
            <span class="modal-title">Быстрый старт: балансировщик leastPing</span>
            <button type="button" class="modal-close" id="routing-balancer-quick-close-btn" title="Закрыть">×</button>
          </div>
          <div class="modal-body">
            <div class="xk-qb-lead">
              <div class="xk-qb-lead-icon">⚡</div>
              <div class="xk-qb-lead-text">
                <div class="xk-qb-lead-title">leastPing + observatory + готовое правило маршрутизации</div>
                <p class="modal-description" style="margin:0;">
                  Мастер создаст или обновит балансировщик <code>leastPing</code>, сформирует <code>07_observatory.json</code>, при необходимости добавит дефолтное правило и затем выполнит <b>Сохранить + Перезапуск</b> с логом.
                </p>
              </div>
            </div>

            <div class="xk-qb-grid">
              <section class="xk-qb-panel xk-qb-main-panel">
                <div class="xk-qb-panelhead">
                  <div>
                    <div class="xk-qb-kicker">Шаг 1</div>
                    <div class="terminal-menu-title" style="margin:0;">Параметры балансировщика</div>
                  </div>
                  <div id="routing-balancer-quick-summary" class="xk-qb-summary" data-tooltip="Текущий balancer.tag и количество выбранных прокси-тегов">proxy · 0 tag</div>
                </div>

                <div class="xk-qb-fields-grid">
                  <label>
                    <span class="xk-qb-fieldlabel">balancer.tag</span>
                    <input id="routing-balancer-quick-tag" class="routing-rule-input" type="text" value="proxy" placeholder="proxy">
                  </label>
                  <label>
                    <span class="xk-qb-fieldlabel">fallbackTag</span>
                    <input id="routing-balancer-quick-fallback" class="routing-rule-input" type="text" value="direct" placeholder="direct">
                  </label>
                  <label class="xk-qb-fieldwide">
                    <span class="xk-qb-fieldlabel">probeUrl</span>
                    <input id="routing-balancer-quick-probe-url" class="routing-rule-input" type="text" value="https://www.gstatic.com/generate_204" placeholder="https://www.gstatic.com/generate_204">
                  </label>
                  <label>
                    <span class="xk-qb-fieldlabel">probeInterval</span>
                    <input id="routing-balancer-quick-probe-interval" class="routing-rule-input" type="text" value="60s" placeholder="60s">
                  </label>
                </div>

                <div class="xk-qb-options-grid">
                  <label class="xk-qb-option-card">
                    <input type="checkbox" id="routing-balancer-quick-default-rule" checked>
                    <div class="xk-qb-option-copy">
                      <strong>Сделать балансировщик дефолтным</strong>
                      <small>Добавить правило match-all с <code>balancerTag</code> для inbound <code>redirect / tproxy</code>.</small>
                    </div>
                  </label>
                  <label class="xk-qb-option-card">
                    <input type="checkbox" id="routing-balancer-quick-overwrite-observatory" checked>
                    <div class="xk-qb-option-copy">
                      <strong>Перезаписать observatory</strong>
                      <small>Разрешить панели обновить существующий <code>07_observatory.json</code>.</small>
                    </div>
                  </label>
                  <label class="xk-qb-option-card xk-qb-option-card-compact">
                    <input type="checkbox" id="routing-balancer-quick-concurrency" checked>
                    <div class="xk-qb-option-copy">
                      <strong>enableConcurrency</strong>
                      <small>Параллельная проверка доступности узлов.</small>
                    </div>
                  </label>
                </div>
              </section>

              <section class="xk-qb-panel xk-qb-tags-panel">
                <div class="xk-qb-panelhead">
                  <div>
                    <div class="xk-qb-kicker">Шаг 2</div>
                    <div class="terminal-menu-title" style="margin:0;">Пул тегов для selector / subjectSelector</div>
                  </div>
                  <button type="button" class="btn-secondary btn-compact xk-qb-refresh-btn" id="routing-balancer-quick-refresh-tags-btn" data-tooltip="Взять теги из 04_outbounds.json и исключить служебные outbound">
                    <span class="xk-btn-inline-glyph" aria-hidden="true">⟳</span>
                    <span>Обновить</span>
                  </button>
                </div>

                <label class="xk-qb-editor-block">
                  <span class="xk-qb-fieldlabel">Список тегов</span>
                  <textarea id="routing-balancer-quick-tags" class="xkeen-textarea" spellcheck="false" rows="9" placeholder="tag1
tag2
..."></textarea>
                </label>

                <div class="xk-qb-note">
                  <div><b>Подсказка:</b> по умолчанию мастер подтягивает все обычные outbound-теги, исключая <code>direct</code>, <code>block</code>, <code>dns</code> и другие служебные значения.</div>
                  <div>Можно оставить только нужные теги вручную — по одному на строку.</div>
                </div>

                <div id="routing-balancer-quick-status" class="xk-qb-statusbar"></div>
              </section>
            </div>
          </div>

          <div class="modal-actions xk-qb-footer">
            <div class="xk-qb-footer-left">
              <button type="button" id="routing-balancer-quick-cancel-btn" class="btn-compact">Отмена</button>
            </div>
            <div class="xk-qb-footer-actions">
              <button type="button" class="btn-secondary btn-compact xk-qb-footer-btn" id="routing-balancer-quick-dry-btn" data-tooltip="Только обновить карточки и JSON-редактор, без сохранения и рестарта.">
                <span class="xk-btn-inline-glyph" aria-hidden="true">✓</span>
                <span>Только применить</span>
              </button>
              <button type="button" class="btn-danger btn-compact xk-qb-footer-btn xk-qb-primary-action" id="routing-balancer-quick-run-btn">
                <span class="xk-btn-inline-glyph" aria-hidden="true">⟳</span>
                <span>Применить + Рестарт</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    `),e=h(d),e):null)}function _(){try{window.XKeen&&n.ui&&n.ui.modal&&typeof n.ui.modal.syncBodyScrollLock==`function`&&n.ui.modal.syncBodyScrollLock()}catch{}}function v(){let e=g();if(e){try{e.classList.remove(`hidden`)}catch{}_()}}function y(){let e=h(d);if(e){try{e.classList.add(`hidden`)}catch{}_()}}function b(e,t,n){let r=h(f.status);if(r)try{r.textContent=String(e||``),r.classList&&(r.classList.toggle(`is-error`,!!t),r.classList.toggle(`is-success`,!t&&!!n)),!r.classList||!r.classList.contains(`is-error`)&&!r.classList.contains(`is-success`)?r.style.color=t?`var(--danger, #ef4444)`:`var(--modal-muted, var(--muted, #9ca3af))`:r.style.color=``}catch{}}function x(e){[f.run,f.dry,f.refreshTags,f.cancel,f.close].forEach(t=>{let n=h(t);if(n){try{n.disabled=!!e}catch{}try{n.classList.toggle(`is-busy`,!!e)}catch{}}})}function S(e){let t=String(e||``).replace(/,/g,`
`).split(/\r?\n/).map(e=>String(e||``).trim()).filter(Boolean),n=[],r=new Set;return t.forEach(e=>{r.has(e)||(r.add(e),n.push(e))}),n}function C(){let e=h(f.summary);if(!e)return;let t=[String(h(f.tag)&&h(f.tag).value||`proxy`).trim()||`proxy`,S(h(f.tags)&&h(f.tags).value||``).length+` tag`];try{h(f.defaultRule)&&h(f.defaultRule).checked&&t.push(`default`),e.textContent=t.join(` · `)}catch{}}function w(e){if(!e||typeof e!=`object`||Array.isArray(e))return[];let t=e.inboundTag;if(Array.isArray(t))return t.map(e=>String(e||``).trim()).filter(Boolean);let n=String(t||``).trim();return n?[n]:[]}function T(e){let t=w(e);return t.length?t.every(e=>e===`redirect`||e===`tproxy`):!0}function E(e,t){let n=String(t||``).trim();if(!n||!e||typeof e!=`object`||Array.isArray(e)||String(e.balancerTag||``).trim()!==n)return!1;let r=Object.keys(e),i=new Set([`type`,`balancerTag`,`ruleTag`,`inboundTag`]);for(let e of r)if(!i.has(e))return!1;let a=w(e);if(!a.length)return!0;let o=new Set(a);return o.has(`redirect`)||o.has(`tproxy`)}function D(e,t){return(Array.isArray(e&&e.rules)?e.rules:[]).some(e=>E(e,t))}function O(e){let t=Array.isArray(e&&e.balancers)?e.balancers:[];for(let e=0;e<t.length;e++){let n=t[e];if((n&&typeof n==`object`&&n.strategy&&typeof n.strategy==`object`?String(n.strategy.type||``).trim():``)===`leastPing`)return n}return null}function k(){let e=c&&typeof c.loadFromEditor==`function`?c.loadFromEditor({setError:!1}):{ok:!1};if(!e||e.ok===!1)return!1;let t=c&&typeof c.ensureModel==`function`?c.ensureModel():e.model||{},n=O(t);if(!n)return!1;let r=String(n.tag||``).trim()||`proxy`,i=String(n.fallbackTag||``).trim()||`direct`,a=Array.isArray(n.selector)?n.selector:[],o=h(f.tag),s=h(f.fallback),l=h(f.tags),u=h(f.defaultRule);return o&&(o.value=r),s&&(s.value=i),l&&a.length&&(l.value=a.map(e=>String(e||``).trim()).filter(Boolean).join(`
`)),u&&(u.checked=D(t,r)),C(),b(`Найден существующий leastPing-балансировщик. Поля предзаполнены из текущего routing.`,!1),!0}let A=new Set([`direct`,`block`,`dns`,`freedom`,`blackhole`,`reject`,`bypass`]);function j(e,t){let n=String(e||``).trim();if(!n||t&&n===String(t))return!0;let r=n.toLowerCase();return!!(A.has(r)||r===`api`||r===`xray-api`||r===`metrics`)}async function M(){let e=a&&typeof a.buildOutboundTagsUrl==`function`?a.buildOutboundTagsUrl():`/api/xray/outbound-tags`;try{let t=await fetch(e,{method:`GET`}),n=await t.json().catch(()=>({}));return!t.ok||!n||n.ok===!1||!Array.isArray(n.tags)?[]:n.tags.map(e=>String(e||``).trim()).filter(Boolean)}catch{return[]}}async function N(){try{let e=await fetch(`/api/xray/observatory/config`,{method:`GET`,cache:`no-store`}),t=await e.json().catch(()=>({}));return!e.ok||!t||t.ok===!1?null:t}catch{return null}}async function P(){let e=String(h(f.tag)&&h(f.tag).value||`proxy`).trim()||`proxy`;b(`Получаю теги из outbounds…`,!1);let t=(await M()).filter(t=>!j(t,e)),n=h(f.tags);if(n)try{n.value=t.join(`
`)}catch{}C(),t.length?b(`Найдено тегов: ${t.length}`,!1,!0):b(`Не удалось найти подходящие outbound-теги. Введите список вручную.`,!0)}function F(e,t,n,r){let i=e||{balancers:[],rules:[]};Array.isArray(i.balancers)||(i.balancers=[]);let a=null;for(let e=0;e<i.balancers.length;e++){let n=i.balancers[e];if(n&&typeof n==`object`&&!Array.isArray(n)&&String(n.tag||``)===t){a=n;break}}if(a||(a={tag:t},i.balancers.push(a)),a.tag=t,a.selector=n.slice(),a.strategy={type:`leastPing`},r)a.fallbackTag=r;else try{delete a.fallbackTag}catch{}try{a.__xkSelectorMode=`ui`}catch{}try{delete a.__xkSelectorDraft}catch{}try{delete a.__xkStrategyDraft}catch{}return a}function I(e){if(!e||typeof e!=`object`||Array.isArray(e))return!1;let t=Object.keys(e),n=new Set([`type`,`outboundTag`,`balancerTag`,`ruleTag`,`inboundTag`]);for(let e of t)if(!n.has(e))return!1;return!(!String(e.outboundTag||e.balancerTag||``).trim()||!T(e))}function L(e,t){if(!Array.isArray(e))return-1;for(let n=0;n<e.length;n++){let r=e[n];if(r&&typeof r==`object`&&!Array.isArray(r)&&String(r.ruleTag||``)===t)return n}return-1}function R(e){if(!Array.isArray(e)||!e.length)return 0;let t=e.length;for(let n=e.length-1;n>=0&&I(e[n]);n--)t=n;return t}function z(e,t){for(let t of Object.keys(e))if(!(t===`type`||t===`balancerTag`||t===`ruleTag`||t===`inboundTag`))try{delete e[t]}catch{}e.type=`field`,e.balancerTag=t,e.inboundTag=m.slice();try{delete e.outboundTag}catch{}return e.ruleTag=p,e}function B(e,t){let n=e||{rules:[]};Array.isArray(n.rules)||(n.rules=[]);let r=L(n.rules,p);if(r<0)for(let e=0;e<n.rules.length;e++){let i=n.rules[e];if(!(!i||typeof i!=`object`||Array.isArray(i))&&E(i,t)){r=e;break}}let i=r>=0,a=i?n.rules.splice(r,1)[0]:{};(!a||typeof a!=`object`||Array.isArray(a))&&(a={}),z(a,t);let o=R(n.rules);return n.rules.splice(o,0,a),{rule:a,idx:o,inserted:!i,existed:i}}function V(e){let t=e||{};if(!Array.isArray(t.rules))return{removed:!1,idx:-1};let n=L(t.rules,p);return n<0?{removed:!1,idx:-1}:(t.rules.splice(n,1),{removed:!0,idx:n})}async function H(e,t){let n={subjectSelector:e,probeUrl:String(t.probeUrl||``).trim(),probeInterval:String(t.probeInterval||``).trim(),enableConcurrency:!!t.enableConcurrency,overwrite:!!t.overwrite},r=await fetch(`/api/xray/observatory/generate`,{method:`POST`,headers:{"Content-Type":`application/json`},body:JSON.stringify(n)}),i=await r.json().catch(()=>({}));if(!r.ok||!i||i.ok===!1){let e=i&&(i.error||i.message)?String(i.error||i.message):`HTTP `+r.status;throw Error(e)}return i}async function U(){return!l||typeof l.applyToEditor!=`function`?(o(`Не найден модуль применения (applyToEditor).`,!0),!1):await l.applyToEditor({silent:!1})}async function W(){let t=e();if(t&&typeof t.save==`function`){let e=document.getElementById(`global-autorestart-xkeen`),n=e?!!e.checked:null;try{return e&&(e.checked=!0),await t.save(),!0}finally{try{e&&n!==null&&(e.checked=n)}catch{}}}try{let e=a&&typeof a.getEditorText==`function`?a.getEditorText():``,t=s(e);if(t&&t.__error)throw t.__error;let n=await fetch(`/api/routing?restart=1&async=1`,{method:`POST`,headers:{"Content-Type":`text/plain;charset=utf-8`},body:String(e||``)}),r=await n.json().catch(()=>({}));if(!n.ok||!r||r.ok===!1)throw Error(String(r&&r.error||n.statusText||`HTTP `+n.status));return!0}catch(e){return o(`Не удалось сохранить routing: `+String(e&&e.message?e.message:e),!0),!1}}async function G(e){x(!0),b(`Подготовка…`,!1);try{let t=c&&typeof c.loadFromEditor==`function`?c.loadFromEditor({setError:!0}):{ok:!1};if(!t||t.ok===!1)return b(`Сначала исправьте JSON в редакторе (или дождитесь загрузки файла).`,!0),!1;let n=c&&typeof c.ensureModel==`function`?c.ensureModel():t.model||{},r=String(h(f.tag)&&h(f.tag).value||`proxy`).trim()||`proxy`,i=String(h(f.fallback)&&h(f.fallback).value||`direct`).trim()||`direct`,a=S(h(f.tags)&&h(f.tags).value||``).filter(e=>!j(e,r));if(!a.length)return b(`Список тегов пуст. Нажмите “Обновить список” или укажите теги вручную.`,!0),!1;b(`Балансировщик: ${r} (selector: ${a.length})…`,!1),F(n,r,a,i),h(f.defaultRule)&&h(f.defaultRule).checked?B(n,r):V(n);try{c&&typeof c.markDirty==`function`&&c.markDirty(!0)}catch{}try{u&&typeof u.renderAll==`function`&&u.renderAll()}catch{}if(b(`Применяю изменения в JSON‑редактор…`,!1),!await U())return b(`Не удалось применить изменения в редактор.`,!0),!1;if(e&&e.dry)return b(`Готово: изменения применены в редактор (без сохранения/рестарта).`,!1,!0),o(`Изменения применены в редактор`,!1),!0;let s=!!(h(f.overwriteObs)&&h(f.overwriteObs).checked);b(`Генерирую 07_observatory.json…`,!1);let l=await H(a,{probeUrl:h(f.probeUrl)&&h(f.probeUrl).value||``,probeInterval:h(f.probeInterval)&&h(f.probeInterval).value||``,enableConcurrency:!!(h(f.conc)&&h(f.conc).checked),overwrite:s}),d=l&&l.existed&&l.overwritten===!1?`07_observatory.json уже существует: перезапись выключена, файл оставлен без изменений.`:``;return d&&b(d,!1,!0),b(d?`Сохраняю routing и перезапускаю. `+d:`Сохраняю и перезапускаю…`,!1),await W()?(b(d?`Готово. `+d+` Лог операции — в “Журнал операций Xkeen”.`:`Готово. Лог операции — в “Журнал операций Xkeen”.`,!1,!0),o(d?`Готово: observatory не менялся`:`Готово`,!1),y(),!0):(b(`Сохранение/перезапуск завершились с ошибкой. См. журнал.`,!0),!1)}catch(e){let t=String(e&&e.message?e.message:e);return b(`Ошибка: `+t,!0),o(`Ошибка: `+t,!0),!1}finally{x(!1)}}function K(){if(i.__wired)return;let e=g(),t=h(`routing-balancer-quick-btn`);if(!t||!e)return;i.__wired=!0,t.addEventListener(`click`,async e=>{e.preventDefault(),b(``,!1),v();let t=!1;try{t=k()}catch{}try{let e=await N();if(e&&e.exists&&e.config){let t=e.config,n=h(f.probeUrl),r=h(f.probeInterval),i=h(f.conc),a=h(f.tags);n&&t.probeUrl&&(n.value=String(t.probeUrl||``)),r&&t.probeInterval&&(r.value=String(t.probeInterval||``)),i&&typeof t.enableConcurrency==`boolean`&&(i.checked=!!t.enableConcurrency),a&&!String(a.value||``).trim()&&Array.isArray(t.subjectSelector)&&t.subjectSelector.length&&(a.value=t.subjectSelector.map(e=>String(e||``).trim()).filter(Boolean).join(`
`))}}catch{}try{let e=h(f.tags);e&&!String(e.value||``).trim()&&await P()}catch{}C(),t||b(`Заполните параметры и список тегов. Можно начать с кнопки “Обновить”.`,!1);try{h(f.tag)&&typeof h(f.tag).focus==`function`&&h(f.tag).focus()}catch{}});let n=h(f.close);n&&n.addEventListener(`click`,e=>{e.preventDefault(),y()});let r=h(f.cancel);r&&r.addEventListener(`click`,e=>{e.preventDefault(),y()}),e.addEventListener(`click`,t=>{try{t&&t.target===e&&y()}catch{}}),document.addEventListener(`keydown`,e=>{try{if(e.key!==`Escape`)return;let t=h(d);if(!t||t.classList.contains(`hidden`))return;y()}catch{}}),[f.tag,f.tags,f.fallback].forEach(e=>{let t=h(e);t&&(t.addEventListener(`input`,()=>C()),t.addEventListener(`change`,()=>C()))}),[f.defaultRule,f.overwriteObs,f.conc].forEach(e=>{let t=h(e);t&&t.addEventListener(`change`,()=>C())});let a=h(f.refreshTags);a&&a.addEventListener(`click`,async e=>{e.preventDefault(),x(!0);try{await P()}finally{x(!1)}});let o=h(f.dry);o&&o.addEventListener(`click`,async e=>{e.preventDefault(),await G({dry:!0})});let s=h(f.run);s&&s.addEventListener(`click`,async e=>{e.preventDefault(),await G({dry:!1})})}i.init=function(){setTimeout(()=>{try{K()}catch{}},0)},document.readyState===`loading`?document.addEventListener(`DOMContentLoaded`,()=>i.init()):i.init()})();