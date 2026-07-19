"""Catalog of supported UnifiedUI CLI flags for the UI.

Extracted from legacy app.py to keep UI rendering stable while allowing app.py refactor.
"""

from __future__ import annotations

import os
import shutil
from typing import Mapping, Optional

from services.utils.env import _env_bool

# NOTE: Keep structure and text stable; UI uses this for rendering.
# "tone" is used only for UI color accents (see styles.css + panel.html).
COMMAND_GROUPS = [
    {
        "title": "Установка",
        "tone": "warn",
        "items": [
            {"flag": "-i",    "desc": "Основной режим установки UnifiedUI + Xray + GeoFile/GeoIPSET + Mihomo"},
            {"flag": "-io",   "desc": "OffLine установка UnifiedUI"},
            {"flag": "-toff", "desc": "Отключение таймаута при медленной загрузке с GitHub"},
        ],
    },
    {
        "title": "Обновление",
        "tone": "warn",
        "items": [
            {"flag": "-uk", "desc": "UnifiedUI"},
            {"flag": "-ug", "desc": "GeoFile/GeoIPSET"},
            {"flag": "-ux", "desc": "Xray (повышение/понижение версии)"},
            {"flag": "-um", "desc": "Mihomo (повышение/понижение версии)"},
        ],
    },
    {
        "title": "Запланированная задача автообновления GeoFile/GeoIPSET",
        "tone": "warn",
        "items": [
            {"flag": "-ugc", "desc": "Создание"},
        ],
    },
    {
        "title": "Регистрация в системе",
        "tone": "warn",
        "items": [
            {"flag": "-rrk", "desc": "UnifiedUI"},
            {"flag": "-rrx", "desc": "Xray"},
            {"flag": "-rrm", "desc": "Mihomo"},
            {"flag": "-ri",  "desc": "Автозапуск UnifiedUI средствами init.d"},
        ],
    },
    {
        "title": "Удаление | Утилиты и компоненты",
        "tone": "danger",
        "items": [
            {"flag": "-remove", "desc": "Полная деинсталляция UnifiedUI"},
            {"flag": "-dgs",    "desc": "GeoSite"},
            {"flag": "-dgi",    "desc": "GeoIP"},
            {"flag": "-dgips",  "desc": "GeoIPSET"},
            {"flag": "-dx",     "desc": "Xray"},
            {"flag": "-dm",     "desc": "Mihomo"},
            {"flag": "-dk",     "desc": "UnifiedUI"},
        ],
    },
    {
        "title": "Удаление | Задачи автообновления",
        "tone": "danger",
        "items": [
            {"flag": "-dgc", "desc": "GeoFile/GeoIPSET"},
        ],
    },
    {
        "title": "Удаление | Регистрации в системе",
        "tone": "danger",
        "items": [
            {"flag": "-drk", "desc": "UnifiedUI"},
            {"flag": "-drx", "desc": "Xray"},
            {"flag": "-drm", "desc": "Mihomo"},
        ],
    },
    {
        "title": "Порты | Через которые работает прокси-клиент",
        "tone": "ok",
        "items": [
            {"flag": "-ap", "desc": "Добавить"},
            {"flag": "-dp", "desc": "Удалить"},
            {"flag": "-cp", "desc": "Посмотреть"},
        ],
    },
    {
        "title": "Порты | Исключенные из работы прокси-клиента",
        "tone": "ok",
        "items": [
            {"flag": "-ape", "desc": "Добавить"},
            {"flag": "-dpe", "desc": "Удалить"},
            {"flag": "-cpe", "desc": "Посмотреть"},
        ],
    },
    {
        "title": "Переустановка",
        "tone": "ok",
        "items": [
            {"flag": "-k", "desc": "UnifiedUI"},
            {"flag": "-g", "desc": "GeoFile"},
            {"flag": "-gips", "desc": "GeoIPSET"},
        ],
    },
    {
        "title": "Резервная копия UnifiedUI",
        "tone": "ok",
        "items": [
            {"flag": "-kb",  "desc": "Создание"},
            {"flag": "-kbr", "desc": "Восстановление"},
        ],
    },
    {
        "title": "Резервная копия конфигурации Xray",
        "tone": "ok",
        "items": [
            {"flag": "-xb",  "desc": "Создание"},
            {"flag": "-xbr", "desc": "Восстановление"},
        ],
    },
    {
        "title": "Резервная копия конфигурации Mihomo",
        "tone": "ok",
        "items": [
            {"flag": "-mb",  "desc": "Создание"},
            {"flag": "-mbr", "desc": "Восстановление"},
        ],
    },
    {
        "title": "Управление прокси-клиентом",
        "tone": "info",
        "items": [
            {"flag": "-start",   "desc": "Запуск"},
            {"flag": "-stop",    "desc": "Остановка"},
            {"flag": "-restart", "desc": "Перезапуск"},
            {"flag": "-status",  "desc": "Статус работы"},
            {"flag": "-tp",      "desc": "Порты, шлюз и протокол прокси-клиента"},
            {"flag": "-auto",    "desc": "Включить | Отключить автозапуск прокси-клиента"},
            {"flag": "-d",       "desc": "Установить задержку автозапуска прокси-клиента"},
            {"flag": "-fd",      "desc": "Включить | Отключить контроль файловых дескрипторов прокси-клиента"},
            {"flag": "-diag",    "desc": "Выполнить диагностику"},
            {"flag": "-channel", "desc": "Переключить канал получения обновлений UnifiedUI (Stable/Dev версия)"},
            {"flag": "-xray",    "desc": "Переключить UnifiedUI на ядро Xray"},
            {"flag": "-mihomo",  "desc": "Переключить UnifiedUI на ядро Mihomo"},
            {"flag": "-ipv6",    "desc": "Включить | Отключить протокол IPv6 в KeeneticOS"},
            {"flag": "-dns",     "desc": "Включить | Отключить перенаправление DNS в прокси"},
            {"flag": "-pr",      "desc": "Включить | Отключить проксирование трафика Entware"},
            {"flag": "-extmsg",  "desc": "Включить | Отключить расширенные сообщения при запуске UnifiedUI"},
            {"flag": "-cbk",     "desc": "Включить | Отключить резервное копирование UnifiedUI при обновлении"},
            {"flag": "-aghfix",  "desc": "Включить | Отключить отображение клиентов UnifiedUI под своими IP в журнале AdGuard Home"},
        ],
    },
    {
        "title": "Управление модулями",
        "tone": "info",
        "items": [
            {"flag": "-modules",    "desc": "Перенос модулей для UnifiedUI в пользовательскую директорию"},
            {"flag": "-delmodules", "desc": "Удаление модулей из пользовательской директории"},
        ],
    },
    {
        "title": "Информация",
        "tone": "info",
        "items": [
            {"flag": "-about", "desc": "О программе"},
            {"flag": "-ad",    "desc": "Поддержать разработчиков"},
            {"flag": "-af",    "desc": "Обратная связь"},
            {"flag": "-v",     "desc": "Версия UnifiedUI"},
        ],
    },
]

ALLOWED_FLAGS = {item["flag"] for group in COMMAND_GROUPS for item in group["items"]}

# Binary name for UnifiedUI (usually available in PATH)
UNIFIED_BIN = os.getenv("UNIFIED_BIN", "unified")

_CONTROL_FLAG_TO_ACTION = {
    "-start": "start",
    "-stop": "stop",
    "-restart": "restart",
    "-status": "status",
}


def _is_executable_file(path: str) -> bool:
    try:
        return bool(path) and os.path.isfile(path) and os.access(path, os.X_OK)
    except Exception:
        return False


def _command_available(cmd: str) -> bool:
    try:
        raw = str(cmd or "").strip()
        if not raw:
            return False
        if os.path.isabs(raw) or os.sep in raw:
            return _is_executable_file(raw)
        return bool(shutil.which(raw))
    except Exception:
        return False


def resolve_unified_init_script() -> Optional[str]:
    """Resolve UnifiedUI init.d script path for old/new router releases.

    Order:
      1. explicit env override (`UNIFIED_INIT_SCRIPT`, `UNIFIED_INITD_FILE`, `UNIFIED_INITD_SCRIPT`)
      2. new beta path `/opt/etc/init.d/S05unified`
      3. legacy path `/opt/etc/init.d/S99unified`
    """
    candidates: list[str] = []

    for env_name in ("UNIFIED_INIT_SCRIPT", "UNIFIED_INITD_FILE", "UNIFIED_INITD_SCRIPT"):
        val = str(os.getenv(env_name, "") or "").strip()
        if val:
            candidates.append(val)

    candidates.extend((
        "/opt/etc/init.d/S05unified",
        "/opt/etc/init.d/S99unified",
    ))

    seen: set[str] = set()
    for cand in candidates:
        path = str(cand or "").strip()
        if not path or path in seen:
            continue
        seen.add(path)
        if _is_executable_file(path):
            return path
    return None


def build_unified_cmd(flag_or_action: str) -> list[str]:
    """Build a compatible UnifiedUI command.

    For service-control actions we prefer the standard `unified` CLI because it
    matches legacy behaviour and is noticeably faster on real devices. The
    init.d script resolver is kept as a compatibility fallback for setups where
    the CLI is unavailable but `/opt/etc/init.d/S05unified` or
    `/opt/etc/init.d/S99unified` exists.
    """
    raw = str(flag_or_action or "").strip()
    if not raw:
        return [UNIFIED_BIN]

    flag = raw if raw.startswith("-") else f"-{raw}"
    action = _CONTROL_FLAG_TO_ACTION.get(flag)
    if action:
        if _command_available(UNIFIED_BIN):
            return [UNIFIED_BIN, flag]
        init_script = resolve_unified_init_script()
        if init_script:
            return [init_script, action]
    return [UNIFIED_BIN, flag]

# Timeout for background unified jobs (seconds)
COMMAND_TIMEOUT = 300

SHELL_ENABLE_ENV = "UNIFIED_ALLOW_SHELL"
SHELL_ENABLE_DEFAULT = False


def is_full_shell_enabled(env: Optional[Mapping[str, str]] = None) -> bool:
    """Return whether arbitrary shell execution is allowed right now.

    Reads the current process env by default so DevTools ENV changes can apply
    without re-importing this module.
    """
    if env is None:
        return _env_bool(SHELL_ENABLE_ENV, SHELL_ENABLE_DEFAULT)

    try:
        raw = str(env.get(SHELL_ENABLE_ENV, "") or "").strip().lower()
    except Exception:
        raw = ""
    if not raw:
        return bool(SHELL_ENABLE_DEFAULT)
    if raw in {"1", "true", "yes", "y", "on"}:
        return True
    if raw in {"0", "false", "no", "n", "off"}:
        return False
    return bool(SHELL_ENABLE_DEFAULT)


def get_full_shell_policy(env: Optional[Mapping[str, str]] = None) -> dict[str, object]:
    """Return a stable UI/API payload describing shell execution policy."""
    enabled = bool(is_full_shell_enabled(env))
    return {
        "enabled": enabled,
        "env": SHELL_ENABLE_ENV,
        "default": "1" if SHELL_ENABLE_DEFAULT else "0",
        "requires_restart": False,
        "message": "Shell-команды в UI отключены по умолчанию.",
        "hint": (
            f"Откройте DevTools -> ENV и установите {SHELL_ENABLE_ENV}=1 только если "
            "доверяете сети. Изменение применяется для новых запусков терминала."
        ),
    }


# Backward-compatible snapshot for older imports. New code should call
# is_full_shell_enabled() dynamically instead of relying on this constant.
ALLOW_FULL_SHELL = is_full_shell_enabled()

# Shell path for full shell mode
SHELL_BIN = "/bin/sh"
