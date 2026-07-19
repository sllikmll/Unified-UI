import { getDevtoolsNamespace, getDevtoolsSharedApi, setDevtoolsNamespaceApi } from '../devtools_namespace.js';

(() => {
  'use strict';

  window.UnifiedUI = window.UnifiedUI || {};
  const UnifiedUI = window.UnifiedUI;
  const XK = window.UnifiedUI;
  const DT = getDevtoolsNamespace();

  const SH = getDevtoolsSharedApi() || {};
  let _inited = false;
  const toast = SH.toast || function (m) { try { console.log(m); } catch (e) {} };
  const getJSON = SH.getJSON || (async (u) => {
    const r = await fetch(u, { cache: 'no-store' });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error((d && d.error) ? String(d.error) : ('HTTP ' + r.status));
    return d;
  });
  const postJSON = SH.postJSON || (async (u, b) => {
    const r = await fetch(u, { cache: 'no-store', method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(b || {}) });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error((d && d.error) ? String(d.error) : ('HTTP ' + r.status));
    return d;
  });
  const byId = SH.byId || ((id) => { try { return document.getElementById(id); } catch (e) { return null; } });

  const openModal = SH.openModal || ((modal, source) => {
    try { modal.classList.remove('hidden'); } catch (e) {}
    if (window.UnifiedUI && UnifiedUI.ui && UnifiedUI.ui.modal && typeof UnifiedUI.ui.modal.syncBodyScrollLock === 'function') {
      try { UnifiedUI.ui.modal.syncBodyScrollLock(); } catch (e2) {}
    } else {
      try { document.body.classList.add('modal-open'); } catch (e3) {}
    }
    return true;
  });
  const closeModal = SH.closeModal || ((modal, source) => {
    try { modal.classList.add('hidden'); } catch (e) {}
    if (window.UnifiedUI && UnifiedUI.ui && UnifiedUI.ui.modal && typeof UnifiedUI.ui.modal.syncBodyScrollLock === 'function') {
      try { UnifiedUI.ui.modal.syncBodyScrollLock(); } catch (e2) {}
    } else {
      try { document.body.classList.remove('modal-open'); } catch (e3) {}
    }
    return true;
  });

  // ------------------------- Logging settings (quick toggles) -------------------------

  function _itemMap(items) {
    const m = {};
    try {
      for (const it of (items || [])) {
        const k = String(it.key || '');
        if (k) m[k] = it;
      }
    } catch (e) {}
    return m;
  }

  function renderEnvTableMessage(message) {
    const tbody = byId('dt-env-tbody');
    if (!tbody) return;
    try { tbody.innerHTML = ''; } catch (e) {}

    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = 4;
    td.textContent = String(message || '');
    tr.appendChild(td);
    tbody.appendChild(tr);
  }

  function syncLoggingControls(items) {
    const mp = _itemMap(items);
    const coreEn = byId('dt-log-core-enable');
    const lvl = byId('dt-log-core-level');
    const acc = byId('dt-log-access-enable');
    const ws = byId('dt-log-ws-enable');
    const rot = byId('dt-log-rotate-mb');
    const bak = byId('dt-log-rotate-backups');

    function eff(key, defVal) {
      const it = mp[key];
      if (!it) return defVal;
      const v = (it.effective === null || typeof it.effective === 'undefined') ? '' : String(it.effective);
      return v !== '' ? v : defVal;
    }

    try {
      if (coreEn) {
        const v = eff('UNIFIED_LOG_CORE_ENABLE', '1').toLowerCase();
        coreEn.checked = (v === '1' || v === 'true' || v === 'yes' || v === 'on');
      }
      if (lvl) {
        const v = eff('UNIFIED_LOG_CORE_LEVEL', 'INFO').toUpperCase();
        lvl.value = ['ERROR','WARNING','INFO','DEBUG'].includes(v) ? v : 'INFO';
      }
      if (acc) {
        const v = eff('UNIFIED_LOG_ACCESS_ENABLE', '0').toLowerCase();
        acc.checked = (v === '1' || v === 'true' || v === 'yes' || v === 'on');
      }
      if (ws) {
        const v = eff('UNIFIED_LOG_WS_ENABLE', '0').toLowerCase();
        ws.checked = (v === '1' || v === 'true' || v === 'yes' || v === 'on');
      }
      if (rot) {
        const v = parseInt(eff('UNIFIED_LOG_ROTATE_MAX_MB', '2'), 10);
        rot.value = String((v && v > 0) ? v : 2);
      }
      if (bak) {
        const v = parseInt(eff('UNIFIED_LOG_ROTATE_BACKUPS', '3'), 10);
        bak.value = String((v && v > 0) ? v : 3);
      }
    } catch (e) {}
  }

  // ------------------------- ENV -------------------------

  const ENV_HELP = {
    'UNIFIED_UI_PORT': 'Порт веб-панели Unified UI. По умолчанию: 8088. Installer сохраняет его в devtools.env, чтобы обновления не сбрасывали порт назад на дефолт. После изменения нужен Restart UI.',
    'UNIFIED_UI_STATE_DIR': 'Каталог состояния UI (auth, devtools.env, restart.log и т.п.). По умолчанию: /opt/etc/unified-ui.',
    'UNIFIED_UI_ENV_FILE': 'Путь к env‑файлу DevTools (по умолчанию <UI_STATE_DIR>/devtools.env). Обычно менять не нужно. Эта переменная отображается только для информации (read‑only).',
    'UNIFIED_UI_SECRET_KEY': 'Секретный ключ Flask/сессий. При смене ключа текущие сессии станут недействительными. Значение не отображается.',
    'UNIFIED_RESTART_LOG_FILE': 'Файл, куда пишутся сообщения/ошибки при запуске/перезапуске UI (для диагностики). По умолчанию: <UI_STATE_DIR>/restart.log.',

    // Self-update (GitHub)
    'UNIFIED_UI_UPDATE_REPO': 'Репозиторий UI для обновления (owner/repo). По умолчанию: sllikmll/Unified-UI.',
    'UNIFIED_UI_UPDATE_CHANNEL': 'Канал обновлений UI: stable (релизы) или main (tarball из ветки).',
    'UNIFIED_UI_UPDATE_BRANCH': 'Ветка для канала main (по умолчанию: main).',
    'UNIFIED_UI_UPDATE_ASSET_NAME': 'Имя tar.gz ассета в релизе (канал stable). По умолчанию: unified-ui-routing.tar.gz.',
    'UNIFIED_UI_UPDATE_ALLOW_HOSTS': 'Allow‑list хостов, откуда разрешено скачивать обновления. Формат: через запятую. По умолчанию: github.com,objects.githubusercontent.com,codeload.github.com.',
    'UNIFIED_UI_UPDATE_ALLOW_HTTP': 'Разрешить HTTP (не рекомендуется). Значения: 1/0. По умолчанию: 0 (только HTTPS).',
    'UNIFIED_UI_UPDATE_MAX_BYTES': 'Максимальный размер tar.gz (в байтах), который разрешено скачать.',
    'UNIFIED_UI_UPDATE_MAX_CHECKSUM_BYTES': 'Максимальный размер checksum‑файла (sha/sha256) в байтах.',
    'UNIFIED_UI_UPDATE_CONNECT_TIMEOUT': 'Таймаут подключения (сек) при скачивании.',
    'UNIFIED_UI_UPDATE_DOWNLOAD_TIMEOUT': 'Таймаут скачивания (сек).',
    'UNIFIED_UI_UPDATE_API_TIMEOUT': 'Таймаут GitHub API (сек).',
    'UNIFIED_UI_UPDATE_REQUIRE_SHA': 'Требовать checksum (sha) перед установкой. Значения: 1/0.',
    'UNIFIED_UI_UPDATE_SHA_STRICT': 'Строгая проверка имени checksum‑файла. Значения: 1/0.',
    'UNIFIED_UI_PANEL_SECTIONS_WHITELIST': 'Whitelist видимых секций/вкладок на основной панели (/). Формат: ключи через запятую. Пусто/не задано = показывать всё. Ключи: routing,mihomo,mihomo-selectors,mihomo-connections,geodat,unified,xray-logs,commands,files,mihomo-generator,ui-settings,devtools,settings,donate. Пример: routing,mihomo,xray-logs,commands. (Секция “Files” может быть скрыта и по архитектуре/feature flags.)',
    'UNIFIED_UI_DEVTOOLS_SECTIONS_WHITELIST': 'Whitelist видимых секций DevTools (/devtools). Формат: ключи через запятую. Пусто/не задано = показывать всё. Ключи: tools,logs,service,update,logging,ui,branding,layout,theme,css,env. Пример: service,update,logging,ui,branding,layout,theme,css,env (или просто tools,env).',
    'UNIFIED_LOG_DIR': 'Каталог UI‑логов: core.log / access.log / ws.log. По умолчанию: /opt/var/log/unified-ui.',
    'UNIFIED_LOG_CORE_ENABLE': 'Включить/выключить core.log. Значения: 1/0. При 0 core.log не пишется (полезно для экономии flash).',
    'UNIFIED_LOG_CORE_LEVEL': 'Уровень логирования core.log: ERROR / WARNING / INFO / DEBUG.',
    'UNIFIED_LOG_ACCESS_ENABLE': 'Включить лог HTTP‑доступа (access.log). Значения: 1/0.',
    'UNIFIED_LOG_WS_ENABLE': 'Включить подробный лог WebSocket (ws.log). Значения: 1/0. Может заметно увеличить объём логов.',
    'UNIFIED_LOG_ROTATE_MAX_MB': 'Максимальный размер каждого log‑файла перед ротацией, в МБ. Минимум 1.',
    'UNIFIED_LOG_ROTATE_BACKUPS': 'Сколько архивных файлов логов хранить после ротации. Минимум 1.',
    'UNIFIED_GITHUB_OWNER': 'Владелец GitHub‑репозитория с конфигами (owner).',
    'UNIFIED_GITHUB_REPO': 'Имя GitHub‑репозитория с конфигами (repo).',
    'UNIFIED_GITHUB_BRANCH': 'Ветка GitHub для импорта/обновлений (например: main).',
    'UNIFIED_GITHUB_REPO_URL': 'Полный URL GitHub‑репозитория. Если задан — используется вместо owner/repo.',
    'UNIFIED_CONFIG_SERVER_BASE': 'Базовый URL конфиг‑сервера (FastAPI), если используете внешний сервер конфигураций.',
    'UNIFIED_PTY_MAX_BUF_CHARS': 'Лимит буфера вывода встроенного терминала (PTY), в символах.',
    'UNIFIED_PTY_IDLE_TTL_SECONDS': 'Через сколько секунд простоя закрывать терминальную (PTY) сессию.',
    'UNIFIED_REMOTEFM_ENABLE': 'Включить удалённый файловый менеджер (RemoteFM через lftp). Значения: 1/0. На MIPS и без lftp фича может быть недоступна.',
    'UNIFIED_REMOTEFM_MAX_SESSIONS': 'Максимум одновременных RemoteFM‑сессий.',
    'UNIFIED_REMOTEFM_SESSION_TTL': 'TTL RemoteFM‑сессии в секундах (авто‑закрытие по таймауту).',
    'UNIFIED_REMOTEFM_MAX_UPLOAD_MB': 'Максимальный размер загрузки через файловый менеджер, в МБ.',
    'UNIFIED_REMOTEFM_TMP_DIR': 'Временная директория для загрузок/стейджинга (по умолчанию /tmp).',
    'UNIFIED_REMOTEFM_STATE_DIR': 'Постоянный каталог состояния RemoteFM (known_hosts, служебные файлы). Если не задан, используется /opt/var/lib/unified-ui/remotefs или /tmp.',
    'UNIFIED_REMOTEFM_CA_FILE': 'Путь к CA bundle для проверки TLS‑сертификатов при FTPS (если включена проверка).',
    'UNIFIED_REMOTEFM_KNOWN_HOSTS': 'Файл known_hosts для SFTP (проверка ключей хостов).',
    'UNIFIED_LOCALFM_ROOTS': 'Разрешённые корни локального файлового менеджера. Формат: пути через двоеточие, например /opt/etc:/opt/var:/tmp.',
    'UNIFIED_PROTECT_MNT_LABELS': 'Защита от удаления/переименования верхнего уровня в каталоге монтирования (обычно /tmp/mnt). Значения: 1/0.',
    'UNIFIED_PROTECTED_MNT_ROOT': 'Каталог, для которого действует защита UNIFIED_PROTECT_MNT_LABELS (по умолчанию /tmp/mnt).',
    'UNIFIED_TRASH_DIR': 'Директория «Корзины» для локального файлового менеджера. По умолчанию: /opt/var/trash.',
    'UNIFIED_TRASH_MAX_BYTES': 'Максимальный размер корзины в байтах. Если задан, имеет приоритет над UNIFIED_TRASH_MAX_GB.',
    'UNIFIED_TRASH_MAX_GB': 'Максимальный размер корзины в гигабайтах (используется, если UNIFIED_TRASH_MAX_BYTES не задан).',
    'UNIFIED_TRASH_TTL_DAYS': 'Срок хранения файлов в корзине (в днях). 0 = хранение отключено (удаление будет «жёстким»).',
    'UNIFIED_TRASH_WARN_RATIO': 'Порог предупреждения заполнения корзины (0..1), например 0.9.',
    'UNIFIED_TRASH_STATS_CACHE_SECONDS': 'Кэширование расчёта размера корзины, в секундах (меньше — чаще пересчёт).',
    'UNIFIED_TRASH_PURGE_INTERVAL_SECONDS': 'Интервал авто‑очистки корзины, в секундах (минимум 60).',
    'UNIFIED_FILEOPS_WORKERS': 'Количество воркеров (параллельность) для операций копирования/перемещения.',
    'UNIFIED_FILEOPS_MAX_JOBS': 'Максимальное количество активных/хранимых задач FileOps.',
    'UNIFIED_FILEOPS_JOB_TTL': 'TTL задач FileOps в секундах (сколько хранить завершённые задачи).',
    'UNIFIED_FILEOPS_REMOTE2REMOTE_DIRECT': 'Разрешить прямые remote→remote операции через lftp (без локального спула). Значения: 1/0.',
    'UNIFIED_FILEOPS_FXP': 'Разрешить FXP (сервер‑сервер) копирование для FTP/FTPS через lftp. Значения: 1/0.',
    'UNIFIED_FILEOPS_SPOOL_DIR': 'Каталог спула (временных файлов) для FileOps, особенно при remote→remote переносах.',
    'UNIFIED_FILEOPS_SPOOL_MAX_MB': 'Лимит спула FileOps в МБ (минимум 16).',
    'UNIFIED_FILEOPS_SPOOL_CLEANUP_AGE': 'Возраст спул‑файлов (в секундах) для автоматической очистки (минимум 600).',
    'UNIFIED_MAX_ZIP_MB': 'Лимит использования /tmp при создании zip‑архивов, в МБ. 0/пусто — без лимита.',
    'UNIFIED_MAX_ZIP_ESTIMATE_ITEMS': 'Ограничение количества элементов при оценке размера zip (защита от огромных деревьев).',
    'UNIFIED_ALLOW_SHELL': 'Разрешить выполнение shell‑команд/терминал в UI. 1=включено, 0=выключено. Включайте только в доверенной сети.',
    'UNIFIED_XRAY_LOG_TZ_OFFSET': 'Сдвиг временных меток в логах Xray/Mihomo (в часах). Значение — целое число, по умолчанию 3.',
    'UNIFIED_XRAY_CONFIGS_DIR': 'Каталог с фрагментами Xray-конфига (routing/inbounds/outbounds). По умолчанию: /opt/etc/xray/configs.',
    'UNIFIED_XRAY_JSONC_DIR': 'Каталог, где UI хранит raw JSONC sidecar файлы (с комментариями). По умолчанию: /opt/etc/unified-ui/xray-jsonc. Важно: должен быть вне UNIFIED_XRAY_CONFIGS_DIR, чтобы Xray случайно не пытался парсить *.jsonc.',
    'UNIFIED_XRAY_ROUTING_FILE': 'Путь или имя файла роутинга Xray. Если указано имя без / — считается относительно UNIFIED_XRAY_CONFIGS_DIR. Пример: 05_routing(in_keenetic)_new.json',
    'UNIFIED_XRAY_INBOUNDS_FILE': 'Путь или имя файла 03_inbounds*.json. Если имя без / — относительно UNIFIED_XRAY_CONFIGS_DIR.',
    'UNIFIED_XRAY_OUTBOUNDS_FILE': 'Путь или имя файла 04_outbounds*.json. Если имя без / — относительно UNIFIED_XRAY_CONFIGS_DIR.',
    'UNIFIED_XRAY_ROUTING_FILE_RAW': 'Путь или имя raw JSONC-файла роутинга (с комментариями). Если указано имя без / — считается относительно UNIFIED_XRAY_JSONC_DIR. Если не задано — используется <routing>.jsonc в UNIFIED_XRAY_JSONC_DIR.',
    'UNIFIED_PORT_PROXYING_FILE': 'Файл со списком портов для проксирования. По умолчанию: /opt/etc/unified/port_proxying.lst.',
    'UNIFIED_PORT_EXCLUDE_FILE': 'Файл со списком портов-исключений. По умолчанию: /opt/etc/unified/port_exclude.lst.',
    'UNIFIED_IP_EXCLUDE_FILE': 'Файл со списком IP/подсетей-исключений. По умолчанию: /opt/etc/unified/ip_exclude.lst. В старых версиях мог быть /opt/etc/unified_exclude.lst — UI подхватит его автоматически, если новый путь отсутствует.',
  };

  ENV_HELP.UNIFIED_INIT_SCRIPT = 'Rezervnyi put k init.d-skriptu UnifiedUI dlya fallback-scenariev sovmestimosti. Osnovnoi put upravleniya - CLI `unified`; pri ego nedostupnosti UI ishet S05unified, potom S99unified.';
  ENV_HELP.UNIFIED_ALLOW_SHELL = 'Arbitrary shell в UI. По умолчанию 0 (выключено). Значение 1 включает shell для новых запусков терминала без Restart UI. Включайте только в доверенной сети.';
  ENV_HELP.UNIFIED_AUTH_LOGIN_WINDOW_SECONDS = 'Окно учёта неудачных логинов в секундах. По умолчанию 300.';
  ENV_HELP.UNIFIED_AUTH_LOGIN_MAX_ATTEMPTS = 'Максимум неудачных попыток входа с одного адреса в пределах окна. По умолчанию 5. Значение 0 отключает lockout.';
  ENV_HELP.UNIFIED_AUTH_LOGIN_LOCKOUT_SECONDS = 'На сколько секунд блокировать новые попытки входа после исчерпания лимита. По умолчанию 900. Значение 0 отключает lockout.';
  ENV_HELP.UNIFIED_UI_MAX_CONTENT_LENGTH = 'Явный app-wide ceiling для обычных HTTP request body в UI, в байтах. По умолчанию 16777216 (16 MiB). Загрузки файлового менеджера используют отдельный лимит UNIFIED_REMOTEFM_MAX_UPLOAD_MB.';
  ENV_HELP.UNIFIED_JSON_BODY_MAX_BYTES = 'Лимит обычных JSON API-запросов, в байтах. По умолчанию 65536 (64 KiB).';
  ENV_HELP.UNIFIED_JSON_HEAVY_MAX_BYTES = 'Лимит для “тяжёлых” JSON API (Xray config editor, JSON formatter, unified lists), в байтах. По умолчанию 1048576 (1 MiB).';
  ENV_HELP.UNIFIED_MIHOMO_JSON_MAX_BYTES = 'Лимит JSON-тела для Mihomo API, в байтах. По умолчанию 4194304 (4 MiB).';
  ENV_HELP.UNIFIED_GEODAT_UPLOAD_MAX_BYTES = 'Максимальный размер загружаемого бинарника xk-geodat через UI, в байтах. По умолчанию 16777216 (16 MiB).';
  ENV_HELP.UNIFIED_ROUTING_SAVE_MAX_BYTES = 'Максимальный размер тела для сохранения JSON/JSONC роутинга Xray, в байтах. По умолчанию 1048576.';
  ENV_HELP.UNIFIED_CONFIG_EXCHANGE_MAX_BYTES = 'Максимальный размер входящего тела для config exchange import/export API, в байтах. По умолчанию 4194304.';
  ENV_HELP.UNIFIED_MIHOMO_HWID = 'Ручной override x-hwid для premium/HWID-подписок Mihomo. Обычно оставьте пустым: панель сама определит HWID роутера. Заполняйте только если провайдер уже привязал подписку к конкретному HWID или ожидает значение из кабинета/поддержки. Применяется при следующей проверке/генерации HWID-подписки без Restart UI.';
  ENV_HELP.UNIFIED_HAPP_HELPER_CMD = 'Команда helper-дешифратора для Happ/INCY подписок. Если переменная пуста, панель попробует bundled helper `scripts/happ_transport_helper.py` автоматически. В команде можно использовать `%LINK%` как placeholder входной ссылки.';
  ENV_HELP.UNIFIED_HAPP_DECRYPTOR_CMD = 'Команда внешнего decryptor для raw `happ://crypt...` deep-link. Если переменная пуста, панель попробует auto-detect drop-in decryptor в `unified-ui/bin` или `unified-ui/scripts`. В команде можно использовать `%LINK%` как placeholder входной ссылки.';
  ENV_HELP.UNIFIED_HAPP_DECRYPTOR_REMOTE_URL = 'Необязательный HTTPS endpoint для remote fallback расшифровки raw `happ://crypt...`. Можно указать либо JSON API endpoint: панель отправит POST `{ \"url\": \"happ://crypt...\" }` и будет ждать JSON с `decryptedUrl`/`url`/`result`, либо URL-шаблон с `%LINK_ENCODED%`/`%LINK%`, который будет вызван через GET. По умолчанию выключено: включайте только если осознанно доверяете внешнему сервису.';
  ENV_HELP.UNIFIED_HAPP_HELPER_TIMEOUT = 'Таймаут запуска Happ helper в секундах. По умолчанию 15. Применяется к следующей попытке импорта или обновления без Restart UI.';
  ENV_HELP.UNIFIED_HAPP_DECRYPTOR_TIMEOUT = 'Таймаут запуска raw Happ decryptor в секундах. По умолчанию 45, потому что `crypt5` на роутере может считаться заметно дольше обычного helper. Применяется к следующей попытке импорта или обновления без Restart UI.';
  ENV_HELP.UNIFIED_HAPP_HELPER_HWID = 'Необязательный ручной HWID для bundled Happ helper. Обычно оставьте пустым: helper возьмёт HWID роутера автоматически.';
  ENV_HELP.UNIFIED_SUBSCRIPTION_HAPP_USER_AGENT = 'User-Agent для bundled Happ helper и Happ fallback-запросов. По умолчанию: Happ/3.18.3/Android/17771400994551771562.';
  ENV_HELP.UNIFIED_XRAY_TEST_TIMEOUT = 'Таймаут preflight-проверки Xray (`xray -test`) в секундах. По умолчанию 30 секунд для всех роутеров, минимум 5. Пользователь может подобрать значение под своё устройство; применяется при следующем сохранении без Restart UI.';
  ENV_HELP.UNIFIED_DAT_ALLOW_HOSTS = 'Доверенные хосты для обновления DAT по URL. Формат: через запятую. По умолчанию: GitHub/release/raw хосты.';
  ENV_HELP.UNIFIED_DAT_ALLOW_HTTP = 'Разрешить plain HTTP для DAT update. По умолчанию 0 (только HTTPS).';
  ENV_HELP.UNIFIED_DAT_ALLOW_CUSTOM_URLS = 'Разрешить DAT update с произвольных public URL вне allow-list. По умолчанию 0. Включайте только осознанно.';
  ENV_HELP.UNIFIED_DAT_ALLOW_PRIVATE_HOSTS = 'Разрешить DAT update с локальных/private host/IP. По умолчанию 0.';
  ENV_HELP.UNIFIED_GEODAT_ALLOW_HOSTS = 'Доверенные хосты для установки xk-geodat по URL. Формат: через запятую. По умолчанию: GitHub/release/raw хосты.';
  ENV_HELP.UNIFIED_GEODAT_ALLOW_HTTP = 'Разрешить plain HTTP для установки xk-geodat по URL. По умолчанию 0 (только HTTPS).';
  ENV_HELP.UNIFIED_GEODAT_ALLOW_CUSTOM_URLS = 'Разрешить установку xk-geodat с произвольных public URL вне allow-list. По умолчанию 0.';
  ENV_HELP.UNIFIED_GEODAT_ALLOW_PRIVATE_HOSTS = 'Разрешить установку xk-geodat по URL с локальных/private host/IP. По умолчанию 0.';

  const HAPP_REMOTE_URL_EXAMPLES = Object.freeze([
    {
      href: 'https://happy-decoder.cc/',
      fillValue: 'https://happy-decoder.cc/p/%LINK_ENCODED%',
      label: 'https://happy-decoder.cc/',
      note: 'подставит рабочий proxy-шаблон для этого поля',
      fillLabel: 'Подставить',
    },
    {
      href: 'https://leeeet.dev/happ-decryptor/',
      fillValue: '',
      label: 'https://leeeet.dev/happ-decryptor/',
      note: 'браузерный decryptor, не JSON API',
      fillLabel: '',
    },
  ]);


  

  // ENV help modal content
  // Keys that apply without restarting UI (either immediately or on next request).
  const ENV_NO_RESTART_KEYS = new Set([
    'UNIFIED_LOG_CORE_ENABLE',
    'UNIFIED_LOG_CORE_LEVEL',
    'UNIFIED_LOG_ACCESS_ENABLE',
    'UNIFIED_LOG_WS_ENABLE',
    'UNIFIED_LOG_ROTATE_MAX_MB',
    'UNIFIED_LOG_ROTATE_BACKUPS',

    // Self-update: read at runtime (check latest / runner uses env per run).
    'UNIFIED_UI_UPDATE_CHANNEL',
    'UNIFIED_UI_UPDATE_REPO',
    'UNIFIED_UI_UPDATE_BRANCH',
    'UNIFIED_UI_UPDATE_ASSET_NAME',
    'UNIFIED_UI_UPDATE_ALLOW_HTTP',
    'UNIFIED_UI_UPDATE_ALLOW_HOSTS',
    'UNIFIED_UI_UPDATE_API_TIMEOUT',
    'UNIFIED_UI_UPDATE_CONNECT_TIMEOUT',
    'UNIFIED_UI_UPDATE_DOWNLOAD_TIMEOUT',
    'UNIFIED_UI_UPDATE_MAX_BYTES',
    'UNIFIED_UI_UPDATE_MAX_CHECKSUM_BYTES',
    'UNIFIED_UI_UPDATE_REQUIRE_SHA',
    'UNIFIED_UI_UPDATE_SHA_STRICT',
    'UNIFIED_AUTH_LOGIN_WINDOW_SECONDS',
    'UNIFIED_AUTH_LOGIN_MAX_ATTEMPTS',
    'UNIFIED_AUTH_LOGIN_LOCKOUT_SECONDS',
    'UNIFIED_UI_MAX_CONTENT_LENGTH',
    'UNIFIED_JSON_BODY_MAX_BYTES',
    'UNIFIED_JSON_HEAVY_MAX_BYTES',
    'UNIFIED_MIHOMO_JSON_MAX_BYTES',
    'UNIFIED_GEODAT_UPLOAD_MAX_BYTES',
    'UNIFIED_ROUTING_SAVE_MAX_BYTES',
    'UNIFIED_CONFIG_EXCHANGE_MAX_BYTES',
    'UNIFIED_DAT_ALLOW_HOSTS',
    'UNIFIED_DAT_ALLOW_HTTP',
    'UNIFIED_DAT_ALLOW_CUSTOM_URLS',
    'UNIFIED_DAT_ALLOW_PRIVATE_HOSTS',
    'UNIFIED_GEODAT_ALLOW_HOSTS',
    'UNIFIED_GEODAT_ALLOW_HTTP',
    'UNIFIED_GEODAT_ALLOW_CUSTOM_URLS',
    'UNIFIED_GEODAT_ALLOW_PRIVATE_HOSTS',
  ]);

  // Большинство переменных читаются на старте (константы/инициализация blueprint'ов).
  // Для них изменения надёжнее применять через Restart UI.
  const ENV_RESTART_KEYS = new Set([
    'UNIFIED_UI_PORT',
    'UNIFIED_UI_STATE_DIR',
    'UNIFIED_UI_ENV_FILE',
    'UNIFIED_UI_SECRET_KEY',
    'UNIFIED_UI_PANEL_SECTIONS_WHITELIST',
    'UNIFIED_UI_DEVTOOLS_SECTIONS_WHITELIST',
    'UNIFIED_LOG_DIR',
    'UNIFIED_GITHUB_OWNER',
    'UNIFIED_GITHUB_REPO',
    'UNIFIED_GITHUB_BRANCH',
    'UNIFIED_GITHUB_REPO_URL',
    'UNIFIED_CONFIG_SERVER_BASE',
    'UNIFIED_PTY_MAX_BUF_CHARS',
    'UNIFIED_PTY_IDLE_TTL_SECONDS',
    'UNIFIED_REMOTEFM_ENABLE',
    'UNIFIED_REMOTEFM_MAX_SESSIONS',
    'UNIFIED_REMOTEFM_SESSION_TTL',
    'UNIFIED_REMOTEFM_MAX_UPLOAD_MB',
    'UNIFIED_REMOTEFM_TMP_DIR',
    'UNIFIED_REMOTEFM_STATE_DIR',
    'UNIFIED_REMOTEFM_CA_FILE',
    'UNIFIED_REMOTEFM_KNOWN_HOSTS',
    'UNIFIED_LOCALFM_ROOTS',
    'UNIFIED_PROTECT_MNT_LABELS',
    'UNIFIED_PROTECTED_MNT_ROOT',
    'UNIFIED_TRASH_DIR',
    'UNIFIED_TRASH_MAX_BYTES',
    'UNIFIED_TRASH_MAX_GB',
    'UNIFIED_TRASH_TTL_DAYS',
    'UNIFIED_TRASH_WARN_RATIO',
    'UNIFIED_TRASH_STATS_CACHE_SECONDS',
    'UNIFIED_TRASH_PURGE_INTERVAL_SECONDS',
    'UNIFIED_FILEOPS_WORKERS',
    'UNIFIED_FILEOPS_MAX_JOBS',
    'UNIFIED_FILEOPS_JOB_TTL',
    'UNIFIED_FILEOPS_REMOTE2REMOTE_DIRECT',
    'UNIFIED_FILEOPS_FXP',
    'UNIFIED_FILEOPS_SPOOL_DIR',
    'UNIFIED_FILEOPS_SPOOL_MAX_MB',
    'UNIFIED_FILEOPS_SPOOL_CLEANUP_AGE',
    'UNIFIED_MAX_ZIP_MB',
    'UNIFIED_MAX_ZIP_ESTIMATE_ITEMS',
    'UNIFIED_ALLOW_SHELL',
    'UNIFIED_XRAY_LOG_TZ_OFFSET',
    'UNIFIED_XRAY_CONFIGS_DIR',
    'UNIFIED_XRAY_JSONC_DIR',
    'UNIFIED_XRAY_ROUTING_FILE',
    'UNIFIED_XRAY_INBOUNDS_FILE',
    'UNIFIED_XRAY_OUTBOUNDS_FILE',
    'UNIFIED_XRAY_ROUTING_FILE_RAW',
    'UNIFIED_PORT_PROXYING_FILE',
    'UNIFIED_PORT_EXCLUDE_FILE',
    'UNIFIED_IP_EXCLUDE_FILE',
    'UNIFIED_RESTART_LOG_FILE',
  ]);

  ENV_NO_RESTART_KEYS.add('UNIFIED_ALLOW_SHELL');
  ENV_NO_RESTART_KEYS.add('UNIFIED_AUTH_LOGIN_WINDOW_SECONDS');
  ENV_NO_RESTART_KEYS.add('UNIFIED_AUTH_LOGIN_MAX_ATTEMPTS');
  ENV_NO_RESTART_KEYS.add('UNIFIED_AUTH_LOGIN_LOCKOUT_SECONDS');
  ENV_NO_RESTART_KEYS.add('UNIFIED_UI_MAX_CONTENT_LENGTH');
  ENV_NO_RESTART_KEYS.add('UNIFIED_JSON_BODY_MAX_BYTES');
  ENV_NO_RESTART_KEYS.add('UNIFIED_JSON_HEAVY_MAX_BYTES');
  ENV_NO_RESTART_KEYS.add('UNIFIED_MIHOMO_JSON_MAX_BYTES');
  ENV_NO_RESTART_KEYS.add('UNIFIED_GEODAT_UPLOAD_MAX_BYTES');
  ENV_NO_RESTART_KEYS.add('UNIFIED_ROUTING_SAVE_MAX_BYTES');
  ENV_NO_RESTART_KEYS.add('UNIFIED_CONFIG_EXCHANGE_MAX_BYTES');
  ENV_NO_RESTART_KEYS.add('UNIFIED_DAT_ALLOW_HOSTS');
  ENV_NO_RESTART_KEYS.add('UNIFIED_DAT_ALLOW_HTTP');
  ENV_NO_RESTART_KEYS.add('UNIFIED_DAT_ALLOW_CUSTOM_URLS');
  ENV_NO_RESTART_KEYS.add('UNIFIED_DAT_ALLOW_PRIVATE_HOSTS');
  ENV_NO_RESTART_KEYS.add('UNIFIED_GEODAT_ALLOW_HOSTS');
  ENV_NO_RESTART_KEYS.add('UNIFIED_GEODAT_ALLOW_HTTP');
  ENV_NO_RESTART_KEYS.add('UNIFIED_GEODAT_ALLOW_CUSTOM_URLS');
  ENV_NO_RESTART_KEYS.add('UNIFIED_GEODAT_ALLOW_PRIVATE_HOSTS');
  ENV_NO_RESTART_KEYS.add('UNIFIED_MIHOMO_HWID');
  ENV_NO_RESTART_KEYS.add('UNIFIED_HAPP_HELPER_CMD');
  ENV_NO_RESTART_KEYS.add('UNIFIED_HAPP_DECRYPTOR_CMD');
  ENV_NO_RESTART_KEYS.add('UNIFIED_HAPP_DECRYPTOR_REMOTE_URL');
  ENV_NO_RESTART_KEYS.add('UNIFIED_HAPP_HELPER_TIMEOUT');
  ENV_NO_RESTART_KEYS.add('UNIFIED_HAPP_DECRYPTOR_TIMEOUT');
  ENV_NO_RESTART_KEYS.add('UNIFIED_HAPP_HELPER_HWID');
  ENV_NO_RESTART_KEYS.add('UNIFIED_SUBSCRIPTION_HAPP_USER_AGENT');
  ENV_NO_RESTART_KEYS.add('UNIFIED_XRAY_TEST_TIMEOUT');
  ENV_RESTART_KEYS.delete('UNIFIED_ALLOW_SHELL');
  ENV_RESTART_KEYS.delete('UNIFIED_AUTH_LOGIN_WINDOW_SECONDS');
  ENV_RESTART_KEYS.delete('UNIFIED_AUTH_LOGIN_MAX_ATTEMPTS');
  ENV_RESTART_KEYS.delete('UNIFIED_AUTH_LOGIN_LOCKOUT_SECONDS');
  ENV_RESTART_KEYS.delete('UNIFIED_ROUTING_SAVE_MAX_BYTES');
  ENV_RESTART_KEYS.delete('UNIFIED_CONFIG_EXCHANGE_MAX_BYTES');
  ENV_RESTART_KEYS.delete('UNIFIED_UI_MAX_CONTENT_LENGTH');
  ENV_RESTART_KEYS.delete('UNIFIED_JSON_BODY_MAX_BYTES');
  ENV_RESTART_KEYS.delete('UNIFIED_JSON_HEAVY_MAX_BYTES');
  ENV_RESTART_KEYS.delete('UNIFIED_MIHOMO_JSON_MAX_BYTES');
  ENV_RESTART_KEYS.delete('UNIFIED_GEODAT_UPLOAD_MAX_BYTES');
  ENV_RESTART_KEYS.delete('UNIFIED_DAT_ALLOW_HOSTS');
  ENV_RESTART_KEYS.delete('UNIFIED_DAT_ALLOW_HTTP');
  ENV_RESTART_KEYS.delete('UNIFIED_DAT_ALLOW_CUSTOM_URLS');
  ENV_RESTART_KEYS.delete('UNIFIED_DAT_ALLOW_PRIVATE_HOSTS');
  ENV_RESTART_KEYS.delete('UNIFIED_GEODAT_ALLOW_HOSTS');
  ENV_RESTART_KEYS.delete('UNIFIED_GEODAT_ALLOW_HTTP');
  ENV_RESTART_KEYS.delete('UNIFIED_GEODAT_ALLOW_CUSTOM_URLS');
  ENV_RESTART_KEYS.delete('UNIFIED_GEODAT_ALLOW_PRIVATE_HOSTS');
  ENV_RESTART_KEYS.delete('UNIFIED_MIHOMO_HWID');
  ENV_RESTART_KEYS.delete('UNIFIED_HAPP_HELPER_CMD');
  ENV_RESTART_KEYS.delete('UNIFIED_HAPP_DECRYPTOR_CMD');
  ENV_RESTART_KEYS.delete('UNIFIED_HAPP_DECRYPTOR_REMOTE_URL');
  ENV_RESTART_KEYS.delete('UNIFIED_HAPP_HELPER_TIMEOUT');
  ENV_RESTART_KEYS.delete('UNIFIED_HAPP_DECRYPTOR_TIMEOUT');
  ENV_RESTART_KEYS.delete('UNIFIED_HAPP_HELPER_HWID');
  ENV_RESTART_KEYS.delete('UNIFIED_SUBSCRIPTION_HAPP_USER_AGENT');
  ENV_RESTART_KEYS.delete('UNIFIED_XRAY_TEST_TIMEOUT');
  ENV_RESTART_KEYS.add('UNIFIED_INIT_SCRIPT');

  let _envSnapshot = { items: [], envFile: '' };
  let _envFilter = '';
  const ENV_GROUP_EXPANDED_STORAGE_KEY = 'unified.devtools.env.expandedGroups.v1';
  let _envExpandedGroups = new Set();

  function _envRestartHint(key) {
    const k = String(key || '');
    // Keep it short to fit into the help table on small screens.
    // User asked for a strict yes/no here.
    if (ENV_NO_RESTART_KEYS.has(k)) return 'нет';
    if (ENV_RESTART_KEYS.has(k)) return 'да';
    // Safe default: assume restart is required.
    return 'да';
  }

  function _setEnvSnapshot(items, envFile) {
    try { _envSnapshot.items = Array.isArray(items) ? items : []; } catch (e) { _envSnapshot.items = []; }
    try { _envSnapshot.envFile = envFile ? String(envFile) : ''; } catch (e) { _envSnapshot.envFile = ''; }
  }

  function _escapeHtml(s) {
    const str = String(s == null ? '' : s);
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function _basename(p) {
    const s = String(p == null ? '' : p);
    if (!s) return '';
    // Support both Unix and Windows separators.
    const parts = s.split(/[/\\]+/);
    return parts[parts.length - 1] || s;
  }

  const ENV_GROUPS = [
    {
      id: 'core',
      title: 'UI и безопасность',
      desc: 'Порт, сессии, логин и общие лимиты запросов.',
      keys: [
        'UNIFIED_UI_STATE_DIR',
        'UNIFIED_UI_ENV_FILE',
        'UNIFIED_UI_SECRET_KEY',
        'UNIFIED_UI_PORT',
        'UNIFIED_UI_MAX_CONTENT_LENGTH',
        'UNIFIED_JSON_BODY_MAX_BYTES',
        'UNIFIED_JSON_HEAVY_MAX_BYTES',
        'UNIFIED_ROUTING_SAVE_MAX_BYTES',
        'UNIFIED_CONFIG_EXCHANGE_MAX_BYTES',
      ],
      prefixes: ['UNIFIED_AUTH_LOGIN_'],
    },
    {
      id: 'mihomo',
      title: 'Mihomo и HWID',
      desc: 'Лимиты Mihomo API и HWID для premium/HWID-подписок.',
      keys: [
        'UNIFIED_MIHOMO_JSON_MAX_BYTES',
        'UNIFIED_MIHOMO_HWID',
        'UNIFIED_HAPP_HELPER_CMD',
        'UNIFIED_HAPP_DECRYPTOR_CMD',
        'UNIFIED_HAPP_DECRYPTOR_REMOTE_URL',
        'UNIFIED_HAPP_HELPER_TIMEOUT',
        'UNIFIED_HAPP_DECRYPTOR_TIMEOUT',
        'UNIFIED_HAPP_HELPER_HWID',
        'UNIFIED_SUBSCRIPTION_HAPP_USER_AGENT',
      ],
      prefixes: [],
    },
    {
      id: 'dat',
      title: 'DAT / GeoIP',
      desc: 'Ограничения и allow-list для загрузки geoip/geosite/DAT.',
      keys: ['UNIFIED_GEODAT_UPLOAD_MAX_BYTES'],
      prefixes: ['UNIFIED_DAT_', 'UNIFIED_GEODAT_'],
    },
    {
      id: 'updates',
      title: 'Обновления UI',
      desc: 'GitHub-репозиторий, канал, ветка, таймауты и проверки скачивания.',
      keys: [],
      prefixes: ['UNIFIED_UI_UPDATE_'],
    },
    {
      id: 'visibility',
      title: 'Видимость разделов',
      desc: 'Whitelist блоков панели и DevTools.',
      keys: ['UNIFIED_UI_PANEL_SECTIONS_WHITELIST', 'UNIFIED_UI_DEVTOOLS_SECTIONS_WHITELIST'],
      prefixes: [],
    },
    {
      id: 'logs',
      title: 'Логи',
      desc: 'Каталоги, уровни логирования, ротация и смещение времени.',
      keys: ['UNIFIED_RESTART_LOG_FILE', 'UNIFIED_XRAY_LOG_TZ_OFFSET'],
      prefixes: ['UNIFIED_LOG_'],
    },
    {
      id: 'github',
      title: 'GitHub и config-server',
      desc: 'Импорт конфигов из GitHub и внешний сервер конфигураций.',
      keys: ['UNIFIED_CONFIG_SERVER_BASE'],
      prefixes: ['UNIFIED_GITHUB_'],
    },
    {
      id: 'terminal',
      title: 'Терминал',
      desc: 'PTY-буфер, TTL сессий и доступ к shell-командам.',
      keys: ['UNIFIED_ALLOW_SHELL'],
      prefixes: ['UNIFIED_PTY_'],
    },
    {
      id: 'files',
      title: 'Файловый менеджер',
      desc: 'RemoteFM, локальные корни, защита /tmp/mnt и корзина.',
      keys: ['UNIFIED_LOCALFM_ROOTS', 'UNIFIED_PROTECT_MNT_LABELS', 'UNIFIED_PROTECTED_MNT_ROOT'],
      prefixes: ['UNIFIED_REMOTEFM_', 'UNIFIED_TRASH_'],
    },
    {
      id: 'fileops',
      title: 'FileOps и ZIP',
      desc: 'Копирование, перемещение, спул и лимиты ZIP-архивов.',
      keys: [],
      prefixes: ['UNIFIED_FILEOPS_', 'UNIFIED_MAX_ZIP_'],
    },
    {
      id: 'xray',
      title: 'Xray и списки UnifiedUI',
      desc: 'Пути фрагментов Xray, preflight-таймаут и файлы списков портов/IP.',
      keys: ['UNIFIED_XRAY_TEST_TIMEOUT', 'UNIFIED_CONFIG_FILE'],
      prefixes: ['UNIFIED_XRAY_', 'UNIFIED_PORT_', 'UNIFIED_IP_'],
    },
    {
      id: 'other',
      title: 'Прочее',
      desc: 'Редкие служебные переменные.',
      keys: [],
      prefixes: [],
    },
  ];

  const ENV_GROUP_BY_ID = ENV_GROUPS.reduce((acc, group) => {
    acc[group.id] = group;
    return acc;
  }, {});

  function _loadEnvExpandedGroups() {
    try {
      const raw = window.localStorage ? window.localStorage.getItem(ENV_GROUP_EXPANDED_STORAGE_KEY) : '';
      if (!raw) return new Set();
      const arr = JSON.parse(raw);
      const valid = new Set(ENV_GROUPS.map((group) => String(group.id || '')).filter(Boolean));
      return new Set((Array.isArray(arr) ? arr : []).map((id) => String(id || '')).filter((id) => valid.has(id)));
    } catch (e) {
      return new Set();
    }
  }

  function _saveEnvExpandedGroups() {
    try {
      if (!window.localStorage) return;
      window.localStorage.setItem(ENV_GROUP_EXPANDED_STORAGE_KEY, JSON.stringify(Array.from(_envExpandedGroups)));
    } catch (e) {}
  }

  _envExpandedGroups = _loadEnvExpandedGroups();

  function _envGroupForKey(key) {
    const k = String(key || '');
    for (const group of ENV_GROUPS) {
      if (group.id === 'other') continue;
      if (Array.isArray(group.keys) && group.keys.includes(k)) return group;
      if (Array.isArray(group.prefixes) && group.prefixes.some((p) => k.startsWith(String(p || '')))) return group;
    }
    return ENV_GROUP_BY_ID.other || ENV_GROUPS[ENV_GROUPS.length - 1];
  }

  function _normalSearchText(s) {
    return String(s == null ? '' : s).toLowerCase();
  }

  function _envItemMatchesFilter(item, group, query) {
    const q = _normalSearchText(query).trim();
    if (!q) return true;
    const key = String(item && item.key ? item.key : '');
    const help = ENV_HELP[key] || '';
    const haystack = _normalSearchText([
      key,
      group && group.title,
      group && group.desc,
      help,
      item && item.current,
      item && item.configured,
      item && item.effective,
    ].join(' '));
    return q.split(/\s+/).filter(Boolean).every((part) => haystack.includes(part));
  }

  function _createEnvGroupRow(group, visibleCount, totalCount, hasSearch) {
    const tr = document.createElement('tr');
    tr.className = 'dt-env-group-row';
    tr.dataset.group = group.id;

    const td = document.createElement('td');
    td.colSpan = 4;

    const collapsed = !hasSearch && !_envExpandedGroups.has(group.id);
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'dt-env-group-toggle';
    btn.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
    btn.title = collapsed ? 'Развернуть группу ENV' : 'Свернуть группу ENV';

    const icon = document.createElement('span');
    icon.className = 'dt-env-group-icon';
    icon.textContent = collapsed ? '+' : '-';

    const text = document.createElement('span');
    text.className = 'dt-env-group-text';

    const title = document.createElement('strong');
    title.textContent = group.title;

    const desc = document.createElement('span');
    desc.className = 'dt-env-group-desc';
    desc.textContent = group.desc || '';

    text.appendChild(title);
    text.appendChild(desc);

    const count = document.createElement('span');
    count.className = 'dt-env-group-count';
    count.textContent = hasSearch ? (String(visibleCount) + '/' + String(totalCount)) : (String(totalCount) + ' шт.');

    btn.appendChild(icon);
    btn.appendChild(text);
    btn.appendChild(count);
    btn.addEventListener('click', () => {
      if (_envExpandedGroups.has(group.id)) _envExpandedGroups.delete(group.id);
      else _envExpandedGroups.add(group.id);
      _saveEnvExpandedGroups();
      renderEnv((_envSnapshot && _envSnapshot.items) || [], (_envSnapshot && _envSnapshot.envFile) || '');
    });

    td.appendChild(btn);
    tr.appendChild(td);
    return tr;
  }

  function _buildEnvHelpHtml() {
    const envFile = _envSnapshot && _envSnapshot.envFile ? String(_envSnapshot.envFile) : '';
    let keys = [];
    try {
      // Prefer the authoritative whitelist from backend snapshot (it may include keys
      // that are not yet described in ENV_HELP).
      const snap = (_envSnapshot && Array.isArray(_envSnapshot.items)) ? _envSnapshot.items : [];
      keys = snap.map((it) => String((it && it.key) ? it.key : '')).filter((k) => !!k);
    } catch (e) { keys = []; }
    // Merge in documented keys too (defensive), then uniq+sort.
    try { keys = keys.concat(Object.keys(ENV_HELP || {})); } catch (e2) {}
    keys = Array.from(new Set(keys)).slice().sort();

    const parts = [];
    parts.push('<div style="line-height:1.55;">');

    parts.push('<p style="margin-top:0;"><strong>ENV (whitelist)</strong> — это список разрешённых переменных окружения, которые можно безопасно менять из UI. Значения сохраняются в env‑файл <code>devtools.env</code> и (частично) применяются сразу.</p>');

    parts.push('<h3 style="margin:12px 0 6px 0;">Колонки</h3>');
    parts.push('<ul style="margin-top:0;">');
    parts.push('<li><strong>Current</strong> — эффективное значение (то, что UI использует сейчас), включая дефолты.</li>');
    parts.push('<li><strong>Value</strong> — значение, которое будет записано в env‑файл (если переменная не задана — UI использует дефолт).</li>');
    parts.push('</ul>');

    parts.push('<h3 style="margin:12px 0 6px 0;">Кнопки Save / Unset</h3>');
    parts.push('<ul style="margin-top:0;">');
    parts.push('<li><strong>Save</strong> — записывает значение в env‑файл (devtools.env) и выставляет его в окружение текущего процесса. Для части настроек нужен <strong>Restart UI</strong>, см. ниже.</li>');
    parts.push('<li><strong>Unset</strong> — удаляет переменную из env‑файла и из окружения процесса. После этого UI вернётся к встроенному значению по умолчанию (или к значению, которое задаёт ваш init‑скрипт/система).</li>');
    parts.push('</ul>');

    parts.push('<h3 style="margin:12px 0 6px 0;">Когда нужен Restart UI</h3>');
    parts.push('<p style="margin-top:0;">Правило простое: если переменная влияет на <em>инициализацию</em> (регистрацию маршрутов, включение фич, пути каталогов, лимиты/TTL, безопасность, секреты), то изменения надёжно применяются только после <strong>Restart UI</strong>. Некоторые параметры логирования применяются сразу.</p>');

    parts.push('<div class="small" style="opacity:0.9; margin-bottom:6px;">Точно применяются без рестарта:</div>');
    parts.push('<ul style="margin-top:0;">');
    parts.push('<li><code>UNIFIED_LOG_CORE_ENABLE</code>, <code>UNIFIED_LOG_CORE_LEVEL</code>, <code>UNIFIED_LOG_ACCESS_ENABLE</code>, <code>UNIFIED_LOG_WS_ENABLE</code>, <code>UNIFIED_LOG_ROTATE_MAX_MB</code>, <code>UNIFIED_LOG_ROTATE_BACKUPS</code> — DevTools пытается обновить логирование сразу.</li>');
    parts.push('<li><code>UNIFIED_AUTH_LOGIN_WINDOW_SECONDS</code>, <code>UNIFIED_AUTH_LOGIN_MAX_ATTEMPTS</code>, <code>UNIFIED_AUTH_LOGIN_LOCKOUT_SECONDS</code> — защита страницы входа применяется для новых попыток сразу.</li>');
    parts.push('<li><code>UNIFIED_UI_MAX_CONTENT_LENGTH</code>, <code>UNIFIED_JSON_BODY_MAX_BYTES</code>, <code>UNIFIED_JSON_HEAVY_MAX_BYTES</code>, <code>UNIFIED_MIHOMO_JSON_MAX_BYTES</code>, <code>UNIFIED_GEODAT_UPLOAD_MAX_BYTES</code>, <code>UNIFIED_ROUTING_SAVE_MAX_BYTES</code>, <code>UNIFIED_CONFIG_EXCHANGE_MAX_BYTES</code> — новые лимиты запросов применяются сразу для следующих API-вызовов.</li>');
    parts.push('</ul>');

    parts.push('<div class="small" style="opacity:0.9; margin-bottom:6px;">Рекомендуется делать Restart UI после изменений (самое частое):</div>');
    parts.push('<ul style="margin-top:0;">');
    parts.push('<li>UI/сессии: <code>UNIFIED_UI_STATE_DIR</code>, <code>UNIFIED_UI_SECRET_KEY</code>, <code>UNIFIED_UI_ENV_FILE</code>.</li>');
    parts.push('<li>Включение/инициализация фич: <code>UNIFIED_REMOTEFM_*</code>, <code>UNIFIED_PTY_*</code>, <code>UNIFIED_ALLOW_SHELL</code>.</li>');
    parts.push('<li>Пути/каталоги: <code>UNIFIED_LOG_DIR</code>, <code>UNIFIED_TRASH_DIR</code>, <code>UNIFIED_FILEOPS_SPOOL_DIR</code> и т.п.</li>');
    parts.push('<li>GitHub/Config‑server: <code>UNIFIED_GITHUB_*</code>, <code>UNIFIED_CONFIG_SERVER_BASE</code>.</li>');
    parts.push('</ul>');

    parts.push('<h3 style="margin:12px 0 6px 0;">Как вернуть всё по умолчанию</h3>');
    parts.push('<ul style="margin-top:0;">');
    parts.push('<li>Для одной переменной: нажмите <strong>Unset</strong> — UI вернётся к дефолту.</li>');
    parts.push('<li>Для полного сброса: удалите все заданные значения (Unset для нужных строк) или удалите файл <code>devtools.env</code> целиком (через SSH/файловый менеджер). Затем сделайте <strong>Restart UI</strong>.</li>');
    parts.push('<li>Если меняли <code>UNIFIED_UI_SECRET_KEY</code>: Unset вернёт использование ключа из <code>&lt;UI_STATE_DIR&gt;/secret.key</code>. Чтобы сгенерировать новый ключ «как с нуля» — удалите файл <code>secret.key</code> (через SSH) и перезапустите UI.</li>');
    parts.push('</ul>');

    parts.push('<h3 style="margin:12px 0 6px 0;">Список переменных (whitelist)</h3>');
    parts.push('<div class="small" style="opacity:0.85; margin-bottom:8px;">В таблице ниже: назначение и подсказка по необходимости Restart UI.</div>');

    parts.push('<div class="dt-env-help-table-wrap">');
    parts.push('<table class="dt-env-help-table">');
    parts.push('<thead><tr>');
    parts.push('<th class="dt-env-help-col-key">Key</th>');
    parts.push('<th class="dt-env-help-col-desc">Описание</th>');
    parts.push('<th class="dt-env-help-col-restart">Restart UI</th>');
    parts.push('</tr></thead>');
    parts.push('<tbody>');

    for (const k of keys) {
      const desc = ENV_HELP[k] || ('Переменная окружения: ' + k);
      parts.push('<tr>');
      parts.push('<td class="dt-env-help-td-key"><code>' + _escapeHtml(k) + '</code></td>');
      parts.push('<td class="dt-env-help-td-desc">' + _escapeHtml(desc) + '</td>');
      parts.push('<td class="dt-env-help-td-restart">' + _escapeHtml(_envRestartHint(k)) + '</td>');
      parts.push('</tr>');
    }

    parts.push('</tbody></table></div>');

    parts.push('<div class="small" style="opacity:0.8; margin-top:10px;">Подсказка: наведение на ключ в таблице ENV тоже показывает краткое описание (tooltip).</div>');

    parts.push('</div>');
    return parts.join('');
  }

  function _showEnvHelpModal() {
    const modal = byId('dt-env-help-modal');
    const body = byId('dt-env-help-body');
    if (!modal || !body) return;
    try {
      body.innerHTML = _buildEnvHelpHtml();
    } catch (e) {
      body.textContent = 'Не удалось построить справку: ' + (e && e.message ? e.message : String(e));
    }

    openModal(modal, 'devtools_env_help');
  }

  function _hideEnvHelpModal() {
    const modal = byId('dt-env-help-modal');
    if (!modal) return;
    closeModal(modal, 'devtools_env_help');
  }

  function _wireEnvHelp() {
    const btn = byId('dt-env-help-btn');
    const modal = byId('dt-env-help-modal');
    const btnClose = byId('dt-env-help-close-btn');
    const btnOk = byId('dt-env-help-ok-btn');

    if (btn) btn.addEventListener('click', () => _showEnvHelpModal());
    if (btnClose) btnClose.addEventListener('click', () => _hideEnvHelpModal());
    if (btnOk) btnOk.addEventListener('click', () => _hideEnvHelpModal());

    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e && e.target === modal) _hideEnvHelpModal();
      });
    }

    document.addEventListener('keydown', (e) => {
      if (!e) return;
      if (e.key !== 'Escape' && e.key !== 'Esc') return;
      try {
        const isOpen = modal && !modal.classList.contains('hidden');
        if (isOpen) _hideEnvHelpModal();
      } catch (e2) {}
    });
  }

  function _wireEnvSearch() {
    const input = byId('dt-env-search');
    const clear = byId('dt-env-search-clear');
    if (!input) return;

    const apply = () => {
      _envFilter = String(input.value || '');
      renderEnv((_envSnapshot && _envSnapshot.items) || [], (_envSnapshot && _envSnapshot.envFile) || '');
      if (clear) {
        clear.classList.toggle('is-visible', _envFilter.trim() !== '');
        clear.disabled = _envFilter.trim() === '';
      }
    };

    input.addEventListener('input', apply);
    if (clear) {
      clear.disabled = true;
      clear.addEventListener('click', () => {
        input.value = '';
        input.focus();
        apply();
      });
    }
  }





  function _appendEnvItemRow(tbody, it, group) {
    const tr = document.createElement('tr');
    const key = String(it.key || '');
    const cur = (it.current === null || typeof it.current === 'undefined') ? '' : String(it.current);
    const conf = (it.configured === null || typeof it.configured === 'undefined') ? '' : String(it.configured);
    const eff = (it.effective === null || typeof it.effective === 'undefined') ? '' : String(it.effective);
    const isSensitive = !!it.is_sensitive;
    const isReadonly = !!it.readonly;

    tr.className = 'dt-env-row';
    if (group && group.id) tr.dataset.group = group.id;

    // Prefer configured value (env-file). Otherwise fall back to effective (incl. defaults), then current.
    const valuePrefill = conf !== '' ? conf : (eff !== '' ? eff : cur);

    const help = ENV_HELP[key] || ('Переменная окружения: ' + key);

    const tdKey = document.createElement('td');
    tdKey.textContent = key;
    tdKey.title = help;
    tdKey.style.whiteSpace = 'nowrap';

    const tdCur = document.createElement('td');
    // Show effective value (what UI will actually use). If empty, fall back to current.
    tdCur.textContent = eff !== '' ? eff : cur;
    tdCur.title = tdCur.textContent || '';
    tdCur.style.maxWidth = '220px';
    tdCur.style.overflow = 'hidden';
    tdCur.style.textOverflow = 'ellipsis';
    tdCur.style.minWidth = '220px';

    const tdVal = document.createElement('td');
    tdVal.style.minWidth = '260px';
    const inp = document.createElement('input');
    inp.type = 'text';
    inp.className = 'dt-env-input';
    inp.value = isSensitive ? '' : valuePrefill;
    inp.disabled = !!isReadonly;
    inp.placeholder = isReadonly ? '(read-only)' : (isSensitive ? '(секрет — вводите новое значение)' : '');
    inp.title = isReadonly ? (help + ' (read-only)') : (isSensitive ? (help + ' Значение не отображается: вводите новое и нажимайте Save.') : help);
    inp.style.width = '100%';
    inp.dataset.key = key;
    tdVal.appendChild(inp);
    if (key === 'UNIFIED_HAPP_DECRYPTOR_REMOTE_URL') {
      const examples = document.createElement('div');
      examples.className = 'dt-env-inline-examples';
      const intro = document.createElement('span');
      intro.className = 'dt-env-inline-examples-label';
      intro.textContent = 'Примеры сервисов:';
      examples.appendChild(intro);
      for (const item of HAPP_REMOTE_URL_EXAMPLES) {
        const row = document.createElement('span');
        row.className = 'dt-env-inline-example';

        const link = document.createElement('a');
        link.className = 'dt-env-inline-example-link';
        link.href = item.href;
        link.target = '_blank';
        link.rel = 'noreferrer noopener';
        link.textContent = item.label;
        link.title = item.href;
        row.appendChild(link);

        if (item.fillValue) {
          const fillBtn = document.createElement('button');
          fillBtn.type = 'button';
          fillBtn.className = 'dt-env-inline-example-fill';
          fillBtn.textContent = item.fillLabel || 'Подставить';
          fillBtn.title = 'Подставить в поле совместимый endpoint без автосохранения';
          fillBtn.addEventListener('click', () => {
            inp.value = String(item.fillValue || '');
            try { inp.focus(); } catch (e) {}
          });
          row.appendChild(fillBtn);
        }

        if (item.note) {
          const note = document.createElement('span');
          note.className = 'dt-env-inline-example-note';
          note.textContent = item.note;
          row.appendChild(note);
        }

        examples.appendChild(row);
      }
      tdVal.appendChild(examples);
    }

    const tdAct = document.createElement('td');
    tdAct.style.whiteSpace = 'nowrap';
    tdAct.style.minWidth = '140px';

    const btnSave = document.createElement('button');
    btnSave.type = 'button';
    btnSave.className = 'btn-secondary';
    btnSave.textContent = 'Save';
    btnSave.title = 'Сохранить значение в env‑файл (devtools.env) и применить в текущем процессе. Для части настроек нужен Restart UI.';
    if (isReadonly) {
      btnSave.disabled = true;
      btnSave.title = 'Read-only';
    }
    btnSave.addEventListener('click', async () => {
      const v = String(inp.value || '');
      try {
        const data = await postJSON('/api/devtools/env', { updates: { [key]: v } });
        toast('Saved: ' + key);
        renderEnv(data.items || [], data.env_file || '');
      } catch (e) {
        toast('Save failed: ' + key + ' — ' + (e && e.message ? e.message : String(e)), true);
      }
    });

    const btnUnset = document.createElement('button');
    btnUnset.type = 'button';
    btnUnset.className = 'btn-danger';
    btnUnset.textContent = 'Unset';
    btnUnset.title = 'Удалить переменную из env‑файла (devtools.env) и из окружения процесса. Для части настроек нужен Restart UI.';
    btnUnset.style.marginLeft = '6px';
    if (isReadonly) {
      btnUnset.disabled = true;
      btnUnset.title = 'Read-only';
    }
    btnUnset.addEventListener('click', async () => {
      try {
        const data = await postJSON('/api/devtools/env', { updates: { [key]: null } });
        toast('Unset: ' + key);
        renderEnv(data.items || [], data.env_file || '');
      } catch (e) {
        toast('Unset failed: ' + key + ' — ' + (e && e.message ? e.message : String(e)), true);
      }
    });

    tdAct.appendChild(btnSave);
    tdAct.appendChild(btnUnset);

    tr.appendChild(tdKey);
    tr.appendChild(tdCur);
    tr.appendChild(tdVal);
    tr.appendChild(tdAct);
    tbody.appendChild(tr);
  }

  function renderEnv(items, envFile) {
    const tbody = byId('dt-env-tbody');
    const envFileEl = byId('dt-env-file');
    if (envFileEl) {
      const full = envFile ? String(envFile) : '';
      const name = full ? _basename(full) : '';
      // Don't show full local paths (e.g. macOS dev environment). Keep it short.
      envFileEl.textContent = name ? ('env‑файл: ' + name) : '';
      envFileEl.title = full || '';
    }
    _setEnvSnapshot(items, envFile);
    if (!tbody) return;
    tbody.innerHTML = '';

    if (!items || !items.length) {
      renderEnvTableMessage('(empty)');
      return;
    }

    // Also sync quick logging controls
    syncLoggingControls(items);

    const query = _envFilter || '';
    const hasSearch = _normalSearchText(query).trim() !== '';
    const groups = ENV_GROUPS.map((group) => ({ group, total: 0, rows: [] }));
    const groupBuckets = groups.reduce((acc, bucket) => {
      acc[bucket.group.id] = bucket;
      return acc;
    }, {});

    for (const it of items) {
      const group = _envGroupForKey(it && it.key);
      const bucket = groupBuckets[group.id] || groupBuckets.other;
      bucket.total += 1;
      if (_envItemMatchesFilter(it, group, query)) bucket.rows.push(it);
    }

    const visibleTotal = groups.reduce((sum, bucket) => sum + bucket.rows.length, 0);
    if (!visibleTotal) {
      renderEnvTableMessage(hasSearch ? ('Ничего не найдено: ' + query) : '(empty)');
      return;
    }

    for (const bucket of groups) {
      if (!bucket.rows.length) continue;
      const group = bucket.group;
      const collapsed = !hasSearch && !_envExpandedGroups.has(group.id);
      tbody.appendChild(_createEnvGroupRow(group, bucket.rows.length, bucket.total, hasSearch));
      if (collapsed) continue;
      for (const it of bucket.rows) {
        _appendEnvItemRow(tbody, it, group);
      }
    }
  }

  async function loadEnv() {
    try {
      const data = await getJSON('/api/devtools/env');
      renderEnv(data.items || [], data.env_file || '');
    } catch (e) {
      renderEnvTableMessage('Ошибка: ' + (e && e.message ? e.message : String(e)));
    }
  }

  async function saveLoggingSettings() {
    const coreEn = byId('dt-log-core-enable');
    const lvl = byId('dt-log-core-level');
    const acc = byId('dt-log-access-enable');
    const ws = byId('dt-log-ws-enable');
    const rot = byId('dt-log-rotate-mb');
    const bak = byId('dt-log-rotate-backups');

    const updates = {};
    if (coreEn) {
      try { updates.UNIFIED_LOG_CORE_ENABLE = (coreEn.checked) ? '1' : '0'; } catch (e) {}
    }
    try { updates.UNIFIED_LOG_CORE_LEVEL = String(lvl && lvl.value ? lvl.value : 'INFO'); } catch (e) { updates.UNIFIED_LOG_CORE_LEVEL = 'INFO'; }
    // Access log toggle may be hidden in simplified UI; don't change it unless the control exists.
    if (acc) {
      try { updates.UNIFIED_LOG_ACCESS_ENABLE = (acc.checked) ? '1' : '0'; } catch (e) {}
    }
    try { updates.UNIFIED_LOG_WS_ENABLE = (ws && ws.checked) ? '1' : '0'; } catch (e) { updates.UNIFIED_LOG_WS_ENABLE = '0'; }

    let rotMb = 2;
    let backups = 3;
    try { rotMb = parseInt(String(rot && rot.value ? rot.value : '2'), 10); } catch (e) {}
    try { backups = parseInt(String(bak && bak.value ? bak.value : '3'), 10); } catch (e) {}
    if (!rotMb || rotMb < 1) rotMb = 1;
    if (!backups || backups < 1) backups = 1;
    updates.UNIFIED_LOG_ROTATE_MAX_MB = String(rotMb);
    updates.UNIFIED_LOG_ROTATE_BACKUPS = String(backups);

    try {
      const data = await postJSON('/api/devtools/env', { updates });
      toast('Logging settings saved');
      renderEnv(data.items || [], data.env_file || '');

      // Refresh logs list/tail (if module is present)
      const logs = DT.devtoolsLogs || null;
      if (logs && typeof logs.loadLogList === 'function') await logs.loadLogList(true);
      if (logs && typeof logs.loadLogTail === 'function') await logs.loadLogTail(false);
    } catch (e) {
      toast('Save logging settings failed: ' + (e && e.message ? e.message : String(e)), true);
    }
  }

  function init() {
    if (_inited) return;
    _inited = true;

    // Logging quick settings
    const logSave = byId('dt-log-settings-save');
    if (logSave) logSave.addEventListener('click', saveLoggingSettings);

    // ENV help
    try { _wireEnvHelp(); } catch (e) {}
    try { _wireEnvSearch(); } catch (e) {}

    // Initial load
    loadEnv();
  }

  setDevtoolsNamespaceApi('devtoolsEnv', {
    init,
    loadEnv,
    renderEnv,
    saveLoggingSettings,
    syncLoggingControls,
  });
})();
