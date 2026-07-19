"""DevTools ENV editor (split from services.devtools).

This module contains the ENV allow-list, parsing/writing of the shell-compatible
`devtools.env` file, and helper functions used by the DevTools API.

IMPORTANT: Public names are re-exported by `services.devtools` to preserve
backwards-compatible imports.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple


ENV_WHITELIST: Tuple[str, ...] = (
    # UI/server
    "UNIFIED_UI_STATE_DIR",
    "UNIFIED_UI_ENV_FILE",  # read-only (path to devtools.env)
    "UNIFIED_UI_SECRET_KEY",  # shown as "(set)" only
    "UNIFIED_UI_PORT",
    "UNIFIED_AUTH_LOGIN_WINDOW_SECONDS",
    "UNIFIED_AUTH_LOGIN_MAX_ATTEMPTS",
    "UNIFIED_AUTH_LOGIN_LOCKOUT_SECONDS",
    "UNIFIED_UI_MAX_CONTENT_LENGTH",
    "UNIFIED_JSON_BODY_MAX_BYTES",
    "UNIFIED_JSON_HEAVY_MAX_BYTES",
    "UNIFIED_MIHOMO_JSON_MAX_BYTES",
    "UNIFIED_GEODAT_UPLOAD_MAX_BYTES",
    "UNIFIED_ROUTING_SAVE_MAX_BYTES",
    "UNIFIED_CONFIG_EXCHANGE_MAX_BYTES",
    "UNIFIED_MIHOMO_HWID",
    "UNIFIED_HAPP_HELPER_CMD",
    "UNIFIED_HAPP_DECRYPTOR_CMD",
    "UNIFIED_HAPP_DECRYPTOR_REMOTE_URL",
    "UNIFIED_HAPP_HELPER_TIMEOUT",
    "UNIFIED_HAPP_DECRYPTOR_TIMEOUT",
    "UNIFIED_HAPP_HELPER_HWID",
    "UNIFIED_SUBSCRIPTION_HAPP_USER_AGENT",
    "UNIFIED_XRAY_TEST_TIMEOUT",
    "UNIFIED_DAT_ALLOW_HOSTS",
    "UNIFIED_DAT_ALLOW_HTTP",
    "UNIFIED_DAT_ALLOW_CUSTOM_URLS",
    "UNIFIED_DAT_ALLOW_PRIVATE_HOSTS",
    "UNIFIED_GEODAT_ALLOW_HOSTS",
    "UNIFIED_GEODAT_ALLOW_HTTP",
    "UNIFIED_GEODAT_ALLOW_CUSTOM_URLS",
    "UNIFIED_GEODAT_ALLOW_PRIVATE_HOSTS",
    "UNIFIED_INIT_SCRIPT",
    "UNIFIED_RESTART_LOG_FILE",
    # self-update (GitHub)
    "UNIFIED_UI_UPDATE_REPO",
    "UNIFIED_UI_UPDATE_CHANNEL",
    "UNIFIED_UI_UPDATE_BRANCH",
    "UNIFIED_UI_UPDATE_ASSET_NAME",
    "UNIFIED_UI_UPDATE_ALLOW_HOSTS",
    "UNIFIED_UI_UPDATE_ALLOW_HTTP",
    "UNIFIED_UI_UPDATE_MAX_BYTES",
    "UNIFIED_UI_UPDATE_MAX_CHECKSUM_BYTES",
    "UNIFIED_UI_UPDATE_CONNECT_TIMEOUT",
    "UNIFIED_UI_UPDATE_DOWNLOAD_TIMEOUT",
    "UNIFIED_UI_UPDATE_API_TIMEOUT",
    "UNIFIED_UI_UPDATE_SHA_STRICT",
    "UNIFIED_UI_UPDATE_REQUIRE_SHA",
    # UI layout/visibility (optional)
    "UNIFIED_UI_PANEL_SECTIONS_WHITELIST",
    "UNIFIED_UI_DEVTOOLS_SECTIONS_WHITELIST",
    # UI logging (core/access/ws)
    "UNIFIED_LOG_DIR",
    "UNIFIED_LOG_CORE_ENABLE",
    "UNIFIED_LOG_CORE_LEVEL",
    "UNIFIED_LOG_ACCESS_ENABLE",
    "UNIFIED_LOG_WS_ENABLE",
    "UNIFIED_LOG_ROTATE_MAX_MB",
    "UNIFIED_LOG_ROTATE_BACKUPS",
    # GitHub import
    "UNIFIED_GITHUB_OWNER",
    "UNIFIED_GITHUB_REPO",
    "UNIFIED_GITHUB_BRANCH",
    "UNIFIED_GITHUB_REPO_URL",
    # config server
    "UNIFIED_CONFIG_SERVER_BASE",
    # terminal (run_server.py)
    "UNIFIED_PTY_MAX_BUF_CHARS",
    "UNIFIED_PTY_IDLE_TTL_SECONDS",
    # local+remote file manager & file ops
    "UNIFIED_REMOTEFM_ENABLE",
    "UNIFIED_REMOTEFM_MAX_SESSIONS",
    "UNIFIED_REMOTEFM_SESSION_TTL",
    "UNIFIED_REMOTEFM_MAX_UPLOAD_MB",
    "UNIFIED_REMOTEFM_TMP_DIR",
    "UNIFIED_REMOTEFM_STATE_DIR",
    "UNIFIED_REMOTEFM_CA_FILE",
    "UNIFIED_REMOTEFM_KNOWN_HOSTS",
    "UNIFIED_LOCALFM_ROOTS",
    "UNIFIED_PROTECT_MNT_LABELS",
    "UNIFIED_PROTECTED_MNT_ROOT",
    "UNIFIED_TRASH_DIR",
    "UNIFIED_TRASH_MAX_BYTES",
    "UNIFIED_TRASH_MAX_GB",
    "UNIFIED_TRASH_TTL_DAYS",
    "UNIFIED_TRASH_WARN_RATIO",
    "UNIFIED_TRASH_STATS_CACHE_SECONDS",
    "UNIFIED_TRASH_PURGE_INTERVAL_SECONDS",
    "UNIFIED_FILEOPS_WORKERS",
    "UNIFIED_FILEOPS_MAX_JOBS",
    "UNIFIED_FILEOPS_JOB_TTL",
    "UNIFIED_FILEOPS_REMOTE2REMOTE_DIRECT",
    "UNIFIED_FILEOPS_FXP",
    "UNIFIED_FILEOPS_SPOOL_DIR",
    "UNIFIED_FILEOPS_SPOOL_MAX_MB",
    "UNIFIED_FILEOPS_SPOOL_CLEANUP_AGE",
    # zip limits
    "UNIFIED_MAX_ZIP_MB",
    "UNIFIED_MAX_ZIP_ESTIMATE_ITEMS",
    # misc
    "UNIFIED_ALLOW_SHELL",
    "UNIFIED_XRAY_LOG_TZ_OFFSET",

    # Xray fragment paths (routing/inbounds/outbounds)
    "UNIFIED_XRAY_CONFIGS_DIR",
    "UNIFIED_XRAY_JSONC_DIR",
    "UNIFIED_XRAY_ROUTING_FILE",
    "UNIFIED_XRAY_INBOUNDS_FILE",
    "UNIFIED_XRAY_OUTBOUNDS_FILE",
    "UNIFIED_XRAY_ROUTING_FILE_RAW",

    # Xkeen lists (ports / excludes)
    "UNIFIED_PORT_PROXYING_FILE",
    "UNIFIED_PORT_EXCLUDE_FILE",
    "UNIFIED_IP_EXCLUDE_FILE",
    "UNIFIED_CONFIG_FILE",
)


ENV_READONLY: Tuple[str, ...] = (
    "UNIFIED_UI_ENV_FILE",
)



_SENSITIVE_KEYS = {
    "UNIFIED_UI_SECRET_KEY",
}


@dataclass
class EnvItem:
    key: str
    current: Optional[str]
    configured: Optional[str]
    effective: Optional[str]
    is_sensitive: bool = False
    readonly: bool = False


def _default_effective_value(
    key: str,
    ui_state_dir: str,
    *,
    resolve: Optional[Callable[[str], Optional[str]]] = None,
) -> Optional[str]:
    """Return a conservative default value for a whitelisted env var.

    These defaults mirror the UI/runtime defaults used across the project so the
    DevTools ENV editor can show meaningful initial values even when variables
    are not explicitly set.

    Important: This only affects UI display ("effective" value). Nothing is
    written unless the user presses Save.
    """
    k = (key or "").strip()
    if not k:
        return None

    # Helper readers (keep conservative; defaults must match runtime code).
    def _env_str(name: str) -> Optional[str]:
        v = os.environ.get(name)
        if v is None:
            return None
        s = str(v).strip()
        return s if s != "" else None

    def _eff_str(name: str) -> Optional[str]:
        """Effective value for dependent defaults.

        Prefer the caller-provided resolver (which can include env-file values)
        and fall back to the live process environment.
        """
        if resolve is not None:
            try:
                v = resolve(name)
                if v is not None:
                    s = str(v).strip()
                    if s != "":
                        return s
            except Exception:
                pass
        return _env_str(name)

    def _env_int(name: str, default: int) -> int:
        try:
            v = _eff_str(name)
            if v is None:
                return int(default)
            return int(float(v))
        except Exception:
            return int(default)

    def _choose_base_dir(default_dir: str, fallback_dir: str) -> str:
        """Mimic app.py _choose_base_dir (writable check), best-effort."""
        try:
            os.makedirs(default_dir, exist_ok=True)
            test_path = os.path.join(default_dir, ".writetest")
            with open(test_path, "w", encoding="utf-8") as f:
                f.write("")
            os.remove(test_path)
            return default_dir
        except Exception:
            try:
                os.makedirs(fallback_dir, exist_ok=True)
            except Exception:
                pass
            return fallback_dir

    # UI/server
    if k == "UNIFIED_UI_STATE_DIR":
        # Reflect the actual directory the UI is running with.
        return ui_state_dir

    # Note: legacy UNIFIED_UI_DIR is intentionally hidden from DevTools ENV editor.
    # Runtime still supports it for backward compatibility (see app.py).

    if k == "UNIFIED_UI_SECRET_KEY":
        # Secret key is usually auto-generated and stored on disk (UI_STATE_DIR/secret.key).
        # Never reveal it here; only indicate that a value exists.
        try:
            secret_path = os.path.join(ui_state_dir, "secret.key")
            if os.path.isfile(secret_path):
                return "(generated)"
        except Exception:
            pass
        return "(generated)"

    if k == "UNIFIED_UI_ENV_FILE":
        # Path to the persisted env file used by the init script.
        return os.path.join(ui_state_dir, "devtools.env")

    if k == "UNIFIED_UI_PORT":
        # run_server.py default listener port (can be overridden in devtools.env).
        return "8088"

    if k == "UNIFIED_INIT_SCRIPT":
        # Keep DevTools aligned with the runtime resolver for old/new UnifiedUI init.d names.
        try:
            from services.unified_commands_catalog import resolve_unified_init_script

            return resolve_unified_init_script() or "/opt/etc/init.d/S05unified"
        except Exception:
            return "/opt/etc/init.d/S05unified"

    if k == "UNIFIED_RESTART_LOG_FILE":
        # app.py uses <UI_STATE_DIR>/restart.log
        return os.path.join(ui_state_dir, "restart.log")

    if k == "UNIFIED_AUTH_LOGIN_WINDOW_SECONDS":
        return "300"
    if k == "UNIFIED_AUTH_LOGIN_MAX_ATTEMPTS":
        return "5"
    if k == "UNIFIED_AUTH_LOGIN_LOCKOUT_SECONDS":
        return "900"
    if k == "UNIFIED_UI_MAX_CONTENT_LENGTH":
        return str(16 * 1024 * 1024)
    if k == "UNIFIED_JSON_BODY_MAX_BYTES":
        return str(64 * 1024)
    if k == "UNIFIED_JSON_HEAVY_MAX_BYTES":
        return str(1024 * 1024)
    if k == "UNIFIED_MIHOMO_JSON_MAX_BYTES":
        return str(4 * 1024 * 1024)
    if k == "UNIFIED_GEODAT_UPLOAD_MAX_BYTES":
        return str(16 * 1024 * 1024)
    if k == "UNIFIED_ROUTING_SAVE_MAX_BYTES":
        return str(1024 * 1024)
    if k == "UNIFIED_CONFIG_EXCHANGE_MAX_BYTES":
        return str(4 * 1024 * 1024)
    if k == "UNIFIED_MIHOMO_HWID":
        return ""
    if k == "UNIFIED_HAPP_HELPER_CMD":
        try:
            from services import happ_links

            return happ_links.helper_command()
        except Exception:
            return ""
    if k == "UNIFIED_HAPP_DECRYPTOR_CMD":
        try:
            from services import happ_links

            return happ_links.decryptor_command()
        except Exception:
            return ""
    if k == "UNIFIED_HAPP_DECRYPTOR_REMOTE_URL":
        try:
            from services import happ_links

            return happ_links.remote_decryptor_url()
        except Exception:
            return ""
    if k == "UNIFIED_HAPP_HELPER_TIMEOUT":
        return "15"
    if k == "UNIFIED_HAPP_DECRYPTOR_TIMEOUT":
        return "45"
    if k == "UNIFIED_HAPP_HELPER_HWID":
        return ""
    if k == "UNIFIED_SUBSCRIPTION_HAPP_USER_AGENT":
        return "Happ/3.18.3/Android/17771400994551771562"
    if k == "UNIFIED_DAT_ALLOW_HOSTS":
        return "github.com,raw.githubusercontent.com,objects.githubusercontent.com,release-assets.githubusercontent.com,codeload.github.com"
    if k == "UNIFIED_DAT_ALLOW_HTTP":
        return "0"
    if k == "UNIFIED_DAT_ALLOW_CUSTOM_URLS":
        return "0"
    if k == "UNIFIED_DAT_ALLOW_PRIVATE_HOSTS":
        return "0"
    if k == "UNIFIED_GEODAT_ALLOW_HOSTS":
        return "github.com,raw.githubusercontent.com,objects.githubusercontent.com,release-assets.githubusercontent.com,codeload.github.com"
    if k == "UNIFIED_GEODAT_ALLOW_HTTP":
        return "0"
    if k == "UNIFIED_GEODAT_ALLOW_CUSTOM_URLS":
        return "0"
    if k == "UNIFIED_GEODAT_ALLOW_PRIVATE_HOSTS":
        return "0"

    # Self-update defaults
    if k == "UNIFIED_UI_UPDATE_REPO":
        return "sllikmll/Unified-UI"
    if k == "UNIFIED_UI_UPDATE_CHANNEL":
        return "stable"
    if k == "UNIFIED_UI_UPDATE_BRANCH":
        return "main"
    if k == "UNIFIED_UI_UPDATE_ASSET_NAME":
        # Default project convention (stable). For main channel this is ignored.
        return "unified-ui-routing.tar.gz"
    if k == "UNIFIED_UI_UPDATE_ALLOW_HOSTS":
        return "github.com,objects.githubusercontent.com,codeload.github.com"
    if k == "UNIFIED_UI_UPDATE_ALLOW_HTTP":
        return "0"
    if k == "UNIFIED_UI_UPDATE_MAX_BYTES":
        return str(60 * 1024 * 1024)
    if k == "UNIFIED_UI_UPDATE_MAX_CHECKSUM_BYTES":
        return str(1024 * 1024)
    if k == "UNIFIED_UI_UPDATE_CONNECT_TIMEOUT":
        return "10"
    if k == "UNIFIED_UI_UPDATE_DOWNLOAD_TIMEOUT":
        return "300"
    if k == "UNIFIED_UI_UPDATE_API_TIMEOUT":
        return "10"
    if k == "UNIFIED_UI_UPDATE_SHA_STRICT":
        return "1"
    if k == "UNIFIED_UI_UPDATE_REQUIRE_SHA":
        return "1"

    # Logging defaults (services/logging_setup.py + app.py fallback on non-router dev).
    if k == "UNIFIED_LOG_DIR":
        base_var = _choose_base_dir("/opt/var", os.path.join(ui_state_dir, "var"))
        return os.path.join(base_var, "log", "unified-ui")
    if k == "UNIFIED_LOG_CORE_ENABLE":
        return "1"
    if k == "UNIFIED_LOG_CORE_LEVEL":
        return "INFO"
    if k in ("UNIFIED_LOG_ACCESS_ENABLE", "UNIFIED_LOG_WS_ENABLE"):
        return "0"
    if k == "UNIFIED_LOG_ROTATE_MAX_MB":
        return "2"
    if k == "UNIFIED_LOG_ROTATE_BACKUPS":
        return "3"

    # GitHub import defaults (app.py)
    if k == "UNIFIED_GITHUB_OWNER":
        return "sllikmll"
    if k == "UNIFIED_GITHUB_REPO":
        return "unified-ui-community-configs"
    if k == "UNIFIED_GITHUB_BRANCH":
        return "main"
    if k == "UNIFIED_GITHUB_REPO_URL":
        # app.py default: https://github.com/{owner}/{repo}
        owner = _eff_str("UNIFIED_GITHUB_OWNER") or "sllikmll"
        repo = _eff_str("UNIFIED_GITHUB_REPO") or "unified-ui-community-configs"
        return f"https://github.com/{owner}/{repo}"

    # Config server (explicit env only)
    if k == "UNIFIED_CONFIG_SERVER_BASE":
        return ""

    # Terminal (run_server.py)
    if k == "UNIFIED_PTY_MAX_BUF_CHARS":
        return "65536"
    if k == "UNIFIED_PTY_IDLE_TTL_SECONDS":
        return "1800"

    # RemoteFM / File manager / FileOps defaults (app.py + routes_remotefs.py)
    if k == "UNIFIED_REMOTEFM_ENABLE":
        return "1"
    if k == "UNIFIED_REMOTEFM_MAX_SESSIONS":
        return "6"
    if k == "UNIFIED_REMOTEFM_SESSION_TTL":
        return "900"
    if k == "UNIFIED_REMOTEFM_MAX_UPLOAD_MB":
        return "200"
    if k == "UNIFIED_REMOTEFM_TMP_DIR":
        return "/tmp"
    if k == "UNIFIED_REMOTEFM_STATE_DIR":
        # routes_remotefs.py prefers /opt/var/lib/unified-ui/remotefs
        return "/opt/var/lib/unified-ui/remotefs"
    if k == "UNIFIED_REMOTEFM_KNOWN_HOSTS":
        state_dir = _eff_str("UNIFIED_REMOTEFM_STATE_DIR") or "/opt/var/lib/unified-ui/remotefs"
        return os.path.join(state_dir, "known_hosts")
    if k == "UNIFIED_REMOTEFM_CA_FILE":
        # Keep the best-known Entware location as a reasonable default hint.
        # routes_remotefs.py also checks /etc/ssl/... and /opt/etc/ssl/...
        return "/opt/etc/ssl/certs/ca-certificates.crt"

    if k == "UNIFIED_LOCALFM_ROOTS":
        return "/opt/etc:/opt/var:/tmp"

    if k == "UNIFIED_PROTECT_MNT_LABELS":
        return "1"
    if k == "UNIFIED_PROTECTED_MNT_ROOT":
        return "/tmp/mnt"

    if k == "UNIFIED_TRASH_DIR":
        return "/opt/var/trash"
    if k == "UNIFIED_TRASH_MAX_BYTES":
        return str(3 * 1024 * 1024 * 1024)
    if k == "UNIFIED_TRASH_MAX_GB":
        return "3"
    if k == "UNIFIED_TRASH_TTL_DAYS":
        return "30"
    if k == "UNIFIED_TRASH_WARN_RATIO":
        return "0.9"
    if k == "UNIFIED_TRASH_STATS_CACHE_SECONDS":
        return "10"
    if k == "UNIFIED_TRASH_PURGE_INTERVAL_SECONDS":
        return "3600"

    if k == "UNIFIED_FILEOPS_WORKERS":
        return "1"
    if k == "UNIFIED_FILEOPS_MAX_JOBS":
        return "100"
    if k == "UNIFIED_FILEOPS_JOB_TTL":
        return "3600"
    if k == "UNIFIED_FILEOPS_REMOTE2REMOTE_DIRECT":
        return "1"
    if k == "UNIFIED_FILEOPS_FXP":
        return "1"
    if k == "UNIFIED_FILEOPS_SPOOL_DIR":
        tmp_dir = _eff_str("UNIFIED_REMOTEFM_TMP_DIR") or "/tmp"
        return os.path.join(tmp_dir, "unified_fileops_spool")
    if k == "UNIFIED_FILEOPS_SPOOL_MAX_MB":
        # routes_remotefs.py default: max_upload_mb, minimum 16
        try:
            max_upload = int(float(_eff_str("UNIFIED_REMOTEFM_MAX_UPLOAD_MB") or "200"))
        except Exception:
            max_upload = 200
        return str(max(16, max_upload))
    if k == "UNIFIED_FILEOPS_SPOOL_CLEANUP_AGE":
        return "21600"

    # ZIP limits (routes_fs.py)
    if k == "UNIFIED_MAX_ZIP_MB":
        return "0"
    if k == "UNIFIED_MAX_ZIP_ESTIMATE_ITEMS":
        return "200000"

    # Misc
    if k == "UNIFIED_ALLOW_SHELL":
        return "0"

    # Xray/Mihomo log timezone offset default (+3, see app.py).
    if k == "UNIFIED_XRAY_LOG_TZ_OFFSET":
        return "3"
    if k == "UNIFIED_XRAY_TEST_TIMEOUT":
        return "30"

    # Xray fragment/config paths (keep in sync with app.py).
    if k == "UNIFIED_XRAY_CONFIGS_DIR":
        return "/opt/etc/xray/configs"
    if k == "UNIFIED_XRAY_JSONC_DIR":
        # UI stores raw JSONC sidecars here (must be outside XRAY_CONFIGS_DIR).
        return os.path.join(ui_state_dir, "xray-jsonc")
    if k == "UNIFIED_XRAY_ROUTING_FILE":
        # Basename is relative to UNIFIED_XRAY_CONFIGS_DIR.
        return "05_routing.json"
    if k == "UNIFIED_XRAY_INBOUNDS_FILE":
        return "03_inbounds.json"
    if k == "UNIFIED_XRAY_OUTBOUNDS_FILE":
        return "04_outbounds.json"
    if k == "UNIFIED_XRAY_ROUTING_FILE_RAW":
        # Show resolved/actual path (relative overrides are treated as relative to UNIFIED_XRAY_JSONC_DIR).
        try:
            configs_dir = _eff_str("UNIFIED_XRAY_CONFIGS_DIR") or "/opt/etc/xray/configs"
            jsonc_dir = _eff_str("UNIFIED_XRAY_JSONC_DIR") or os.path.join(ui_state_dir, "xray-jsonc")
            routing = _eff_str("UNIFIED_XRAY_ROUTING_FILE") or "05_routing.json"
            main_abs = routing if routing.startswith("/") else os.path.join(configs_dir, routing)
            base = os.path.basename(main_abs)
            if base.lower().endswith(".jsonc"):
                jsonc_base = base
            elif base.lower().endswith(".json"):
                jsonc_base = base + "c"  # 05_routing*.json -> 05_routing*.jsonc
            else:
                jsonc_base = base + ".jsonc"
            return os.path.join(jsonc_dir, jsonc_base)
        except Exception:
            return os.path.join(ui_state_dir, "xray-jsonc", "05_routing.jsonc")

    # UnifiedUI list paths
    if k == "UNIFIED_PORT_PROXYING_FILE":
        return "/opt/etc/unified/port_proxying.lst"
    if k == "UNIFIED_PORT_EXCLUDE_FILE":
        return "/opt/etc/unified/port_exclude.lst"
    if k == "UNIFIED_IP_EXCLUDE_FILE":
        return "/opt/etc/unified/ip_exclude.lst"
    if k == "UNIFIED_CONFIG_FILE":
        return "/opt/etc/unified/unified.json"

    return None


def _env_file_path(ui_state_dir: str) -> str:
    """Resolve env-file path.

    Override with ``UNIFIED_UI_ENV_FILE``.
    """
    p = (os.getenv("UNIFIED_UI_ENV_FILE") or "").strip()
    if p:
        return p
    return os.path.join(ui_state_dir, "devtools.env")


_LINE_RE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$")


def _unquote_shell_value(raw: str) -> str:
    s = raw.strip()
    if not s:
        return ""
    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
        s2 = s[1:-1]
        # Minimal unescape for "..." (we keep it conservative)
        if raw.strip().startswith('"'):
            s2 = s2.replace("\\\"", '"').replace("\\\\", "\\")
        return s2
    return s


def read_env_file(path: str) -> Dict[str, str]:
    """Parse shell-compatible env file into dict."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return {}
    except OSError:
        return {}

    out: Dict[str, str] = {}
    for line in lines:
        ln = line.strip()
        if not ln or ln.startswith("#"):
            continue
        m = _LINE_RE.match(line)
        if not m:
            continue
        k = m.group(1)
        v_raw = m.group(2)
        out[k] = _unquote_shell_value(v_raw)
    return out


def _shell_quote_single(s: str) -> str:
    """Quote a value for safe single-quoted shell assignment."""
    # ' -> '\'' pattern
    return "'" + s.replace("'", "'\"'\"'") + "'"


def write_env_file(path: str, values: Mapping[str, str]) -> None:
    """Write env file with `export KEY='value'` lines."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("# Generated by Unified UI DevTools\n")
        f.write("# Format: export KEY='value'\n\n")
        for k in sorted(values.keys()):
            v = values.get(k, "")
            f.write(f"export {k}={_shell_quote_single(str(v))}\n")
    try:
        os.replace(tmp, path)
    except Exception:
        # last resort
        try:
            with open(path, "w", encoding="utf-8") as f2:
                with open(tmp, "r", encoding="utf-8") as f1:
                    f2.write(f1.read())
        finally:
            try:
                os.remove(tmp)
            except Exception:
                pass


def get_env_items(ui_state_dir: str, whitelist: Tuple[str, ...] = ENV_WHITELIST) -> List[EnvItem]:
    env_path = _env_file_path(ui_state_dir)
    cfg = read_env_file(env_path)

    # Two-pass render:
    # 1) gather current/configured values
    # 2) fill missing values with defaults that may depend on other effective values
    base_effective: Dict[str, Optional[str]] = {}
    rows: List[Dict[str, Any]] = []

    for k in whitelist:
        cur = os.environ.get(k)
        conf = cfg.get(k)

        # Backward-compatibility: UNIFIED_UI_DIR was a legacy alias for
        # UNIFIED_UI_STATE_DIR. DevTools no longer exposes UNIFIED_UI_DIR, but we
        # still show its value under UNIFIED_UI_STATE_DIR so users can migrate.
        if k == "UNIFIED_UI_STATE_DIR":
            if cur is None:
                cur = os.environ.get("UNIFIED_UI_DIR")
            if conf is None:
                conf = cfg.get("UNIFIED_UI_DIR")
        is_sensitive = k in _SENSITIVE_KEYS
        if is_sensitive:
            # Never leak secrets
            cur_disp = "(set)" if cur else None
            conf_disp = "(set)" if conf else None
            eff0 = cur_disp if cur_disp is not None else conf_disp
            rows.append({
                "key": k,
                "current": cur_disp,
                "configured": conf_disp,
                "effective0": eff0,
                "is_sensitive": True,
                "readonly": (k in set(ENV_READONLY)),
            })
            base_effective[k] = eff0
        else:
            eff0 = cur if cur is not None else conf
            rows.append({
                "key": k,
                "current": cur,
                "configured": conf,
                "effective0": eff0,
                "is_sensitive": False,
                "readonly": (k in set(ENV_READONLY)),
            })
            base_effective[k] = eff0

    def _resolve(name: str) -> Optional[str]:
        try:
            v = base_effective.get(name)
            if v is None:
                return None
            s = str(v).strip()
            return s if s != "" else None
        except Exception:
            return None

    items: List[EnvItem] = []
    for r in rows:
        k = str(r.get("key") or "")
        eff = r.get("effective0")
        if eff is None:
            eff = _default_effective_value(k, ui_state_dir, resolve=_resolve)
        items.append(
            EnvItem(
                key=k,
                current=r.get("current"),
                configured=r.get("configured"),
                effective=eff,
                is_sensitive=bool(r.get("is_sensitive")),
                readonly=bool(r.get("readonly")),
            )
        )

    # Post-process: show resolved/actual path for the routing JSONC sidecar.
    # Runtime resolves relative UNIFIED_XRAY_ROUTING_FILE_RAW against UNIFIED_XRAY_JSONC_DIR.
    try:
        m = {it.key: it for it in items}
        it_raw = m.get("UNIFIED_XRAY_ROUTING_FILE_RAW")
        if it_raw and not it_raw.is_sensitive:
            cfg_dir = (m.get("UNIFIED_XRAY_CONFIGS_DIR").effective if m.get("UNIFIED_XRAY_CONFIGS_DIR") else None) or "/opt/etc/xray/configs"
            jsonc_dir = (m.get("UNIFIED_XRAY_JSONC_DIR").effective if m.get("UNIFIED_XRAY_JSONC_DIR") else None) or os.path.join(ui_state_dir, "xray-jsonc")
            routing = (m.get("UNIFIED_XRAY_ROUTING_FILE").effective if m.get("UNIFIED_XRAY_ROUTING_FILE") else None) or "05_routing.json"

            try:
                cfg_dir = str(cfg_dir).strip() or "/opt/etc/xray/configs"
            except Exception:
                cfg_dir = "/opt/etc/xray/configs"
            try:
                jsonc_dir = str(jsonc_dir).strip() or os.path.join(ui_state_dir, "xray-jsonc")
            except Exception:
                jsonc_dir = os.path.join(ui_state_dir, "xray-jsonc")
            try:
                routing = str(routing).strip() or "05_routing.json"
            except Exception:
                routing = "05_routing.json"

            main_abs = routing if routing.startswith("/") else os.path.join(cfg_dir, routing)
            base = os.path.basename(main_abs)
            if base.lower().endswith(".jsonc"):
                jsonc_base = base
            elif base.lower().endswith(".json"):
                jsonc_base = base + "c"
            else:
                jsonc_base = base + ".jsonc"

            # If user configured an override, resolve it; otherwise use canonical mapping.
            override = None
            try:
                if it_raw.current is not None and str(it_raw.current).strip() != "":
                    override = str(it_raw.current).strip()
                elif it_raw.configured is not None and str(it_raw.configured).strip() != "":
                    override = str(it_raw.configured).strip()
            except Exception:
                override = None

            if override:
                it_raw.effective = override if override.startswith("/") else os.path.join(jsonc_dir, override)
            else:
                it_raw.effective = os.path.join(jsonc_dir, jsonc_base)
    except Exception:
        pass

    return items


def set_env(ui_state_dir: str, updates: Mapping[str, Optional[str]], whitelist: Tuple[str, ...] = ENV_WHITELIST) -> List[EnvItem]:
    """Apply whitelisted env updates and persist to env-file.

    ``updates``: key -> value (None/"" to unset).
    """
    allowed = set(whitelist)
    env_path = _env_file_path(ui_state_dir)
    cfg = read_env_file(env_path)

    changed = False
    for k, v in updates.items():
        if k not in allowed:
            continue
        if k in set(ENV_READONLY):
            continue
        if k in _SENSITIVE_KEYS:
            # We do allow setting secret, but we never show it back.
            pass

        # Migration: UNIFIED_UI_DIR is a legacy alias for UNIFIED_UI_STATE_DIR.
        # It is hidden from the DevTools ENV editor, but we still clean it up
        # when the user updates/unsets UNIFIED_UI_STATE_DIR so there is no
        # confusing duplication in the persisted env file.
        if k == "UNIFIED_UI_STATE_DIR":
            if "UNIFIED_UI_DIR" in cfg:
                cfg.pop("UNIFIED_UI_DIR", None)
                changed = True
            try:
                os.environ.pop("UNIFIED_UI_DIR", None)
            except Exception:
                pass

        if v is None or str(v) == "":
            if k in cfg:
                cfg.pop(k, None)
                changed = True
            try:
                os.environ.pop(k, None)
            except Exception:
                pass
            continue

        vv = str(v)
        if cfg.get(k) != vv:
            cfg[k] = vv
            changed = True
        try:
            os.environ[k] = vv
        except Exception:
            pass

    if changed:
        write_env_file(env_path, cfg)

    return get_env_items(ui_state_dir, whitelist=whitelist)
