"""Managed proxy connection registry for unified Unified UI.

This module stores user-imported proxy connections (WireGuard, AmneziaWG,
Hysteria2, VLESS, Trojan, Mieru, NaiveProxy) and can inject Mihomo-compatible
proxy YAML into the active config.yaml using a fenced managed block.  The code is
router-friendly: JSON/text mutations only, no PyYAML dependency required.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from flask import Blueprint, jsonify, request

try:
    from mihomo_server_core import CONFIG_PATH, restart_mihomo_and_get_log
except Exception:  # pragma: no cover - dev fallback
    CONFIG_PATH = Path(os.environ.get("MIHOMO_CONFIG", "/opt/etc/mihomo/config.yaml"))

    def restart_mihomo_and_get_log(new_content: str | None = None) -> str:  # type: ignore
        return "restart unavailable in dev fallback"

from services.mihomo_proxy_parsers import (
    ProxyParseResult,
    _yaml_str,
    parse_hysteria2,
    parse_proxy_uri,
    parse_trojan,
    parse_vless,
    parse_wireguard,
)
from services.mihomo_proxy_config import insert_proxy_into_groups, remove_proxy_from_groups
from services.mihomo_yaml import validate_yaml_syntax

PROTOCOLS: dict[str, dict[str, Any]] = {
    "wireguard": {"label": "WireGuard", "schemes": ["wireguard://"], "mihomo": True},
    "amnezia": {"label": "Amnezia", "schemes": ["awg://", "amneziawg://"], "mihomo": True},
    "hysteria2": {"label": "Hysteria2", "schemes": ["hysteria2://", "hy2://", "hysteria://"], "mihomo": True},
    "vless": {"label": "VLESS", "schemes": ["vless://"], "mihomo": True},
    "trojan": {"label": "Trojan", "schemes": ["trojan://"], "mihomo": True},
    "mieru": {"label": "Meiru", "schemes": ["mieru://", "mierus://"], "mihomo": False},
    "naiveproxy": {"label": "NaiveProxy", "schemes": ["naive://", "naive+https://", "https://"], "mihomo": True},
}

START_MARK = "# xkeen-managed-proxies:start"
END_MARK = "# xkeen-managed-proxies:end"
DEFAULT_SELECTOR_HINTS = ["Ручной список", "AI", "AI Selector", "CDN", "GLOBAL", "Заблок. сервисы"]


def _dedupe_strings(values: list[Any] | tuple[Any, ...] | set[Any]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        item = str(value or "").strip()
        if not item or item in seen:
            continue
        out.append(item)
        seen.add(item)
    return out


def _default_selectors_for_config(config_text: str) -> list[str]:
    """By product decision, enabled imported proxies should be available in every selector by default."""
    selectors = _selector_names_from_config(config_text)
    if selectors:
        return selectors
    return DEFAULT_SELECTOR_HINTS[:]


def _effective_selectors(conn: dict[str, Any], config_text: str) -> list[str]:
    raw = conn.get("selectors") if isinstance(conn.get("selectors"), list) else []
    selected = _dedupe_strings(raw)
    if selected:
        return selected
    return _default_selectors_for_config(config_text)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _state_dir() -> Path:
    raw = os.environ.get("XKEEN_UI_STATE_DIR") or os.environ.get("XKEEN_STATE_DIR") or "/opt/var/lib/xkeen-ui"
    return Path(raw).expanduser().resolve()


def _registry_path() -> Path:
    raw = os.environ.get("XKEEN_PROXY_CONNECTIONS_FILE")
    if raw:
        return Path(raw).expanduser().resolve()
    return _state_dir() / "proxy-connections.json"


def _mihomo_config_path() -> Path:
    raw = os.environ.get("MIHOMO_CONFIG") or os.environ.get("MIHOMO_CONFIG_FILE")
    if raw:
        return Path(raw).expanduser().resolve()
    return Path(CONFIG_PATH).expanduser()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _load_registry() -> dict[str, Any]:
    path = _registry_path()
    if not path.exists():
        return {"version": 1, "connections": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "connections": []}
    if not isinstance(data, dict):
        return {"version": 1, "connections": []}
    conns = data.get("connections")
    if not isinstance(conns, list):
        data["connections"] = []
    data.setdefault("version", 1)
    return data


def _save_registry(data: dict[str, Any]) -> None:
    path = _registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = dict(data)
    data["updatedAt"] = _now_iso()
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _slug(value: str) -> str:
    text = re.sub(r"[^0-9A-Za-zА-Яа-я._-]+", "-", str(value or "").strip())
    text = re.sub(r"-+", "-", text).strip("-._")
    return text[:64] or "proxy"


def _conn_id(protocol: str, name: str, source: str) -> str:
    digest = hashlib.sha256((protocol + "\n" + name + "\n" + source).encode("utf-8", errors="replace")).hexdigest()[:12]
    return f"{_slug(protocol)}-{_slug(name)}-{digest}"


def _strip_proxy_yaml_header(yaml_text: str) -> str:
    text = str(yaml_text or "").replace("\r\n", "\n").replace("\r", "\n").strip("\n")
    if text.lstrip().startswith("proxies:"):
        lines = text.splitlines()
        out: list[str] = []
        for line in lines[1:]:
            if line.startswith("  - "):
                out.append(line[2:])
            elif line.startswith("    "):
                out.append(line[2:])
            else:
                out.append(line)
        text = "\n".join(out)
    return text.rstrip() + "\n"


def _name_from_yaml(yaml_text: str) -> str:
    m = re.search(r"^\s*-\s*name:\s*(.+?)\s*$", str(yaml_text or ""), flags=re.M)
    if not m:
        return ""
    raw = m.group(1).strip()
    if (raw.startswith("'") and raw.endswith("'")) or (raw.startswith('"') and raw.endswith('"')):
        raw = raw[1:-1].replace("''", "'")
    return raw


def _wireguard_from_data_url(link: str) -> str:
    payload = str(link or "")
    if not payload.lower().startswith("wireguard://"):
        return payload
    encoded = payload.split("wireguard://", 1)[1].split("#", 1)[0]
    encoded = encoded.split("?", 1)[0]
    try:
        raw = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return payload


def _parse_naiveproxy(link: str, custom_name: str | None = None) -> ProxyParseResult:
    raw = str(link or "").strip()
    u = urlparse(raw)
    if (u.scheme or "").lower() in {"naive", "naive+https"}:
        # naive+https://user:pass@host:443#name or naive://user:pass@host:443
        server = u.hostname or ""
        port = int(u.port or 443)
        username = unquote(u.username or "")
        password = unquote(u.password or "")
        name = custom_name or (unquote(u.fragment) if u.fragment else "") or server or "NaiveProxy"
    elif (u.scheme or "").lower() == "https" and (u.username or u.password):
        server = u.hostname or ""
        port = int(u.port or 443)
        username = unquote(u.username or "")
        password = unquote(u.password or "")
        name = custom_name or (unquote(u.fragment) if u.fragment else "") or server or "NaiveProxy"
    else:
        raise ValueError("Not a NaiveProxy URI")
    if not server or not username:
        raise ValueError("Invalid NaiveProxy URI")
    lines = [
        f"- name: {_yaml_str(name)}",
        "  type: http",
        f"  server: {_yaml_str(server)}",
        f"  port: {port}",
        f"  username: {_yaml_str(username)}",
        f"  password: {_yaml_str(password)}",
        "  tls: true",
        f"  sni: {_yaml_str(server)}",
    ]
    return ProxyParseResult(name=name, yaml="\n".join(lines) + "\n")


def _parse_mieru_placeholder(link: str, custom_name: str | None = None) -> ProxyParseResult:
    raw = str(link or "").strip()
    u = urlparse(raw)
    if (u.scheme or "").lower() not in {"mieru", "mierus"}:
        raise ValueError("Not a Mieru URI")
    name = custom_name or (unquote(u.fragment) if u.fragment else "") or (u.hostname or "Mieru")
    # Mihomo does not have a stable Mieru outbound type in all builds. Keep it
    # in registry and expose metadata; it will not be injected as a live proxy.
    yaml = f"# Mieru connection {name} is stored, but current Mihomo injection is disabled.\n"
    return ProxyParseResult(name=name, yaml=yaml)


def _parse_connection(protocol: str, source_text: str, custom_name: str | None = None) -> dict[str, Any]:
    proto = str(protocol or "").strip().lower()
    text = str(source_text or "").strip()
    if not proto or proto not in PROTOCOLS:
        proto = _detect_protocol(text)
    if not text:
        raise ValueError("empty connection content")

    if proto in {"wireguard", "amnezia"}:
        conf = _wireguard_from_data_url(text)
        result = parse_wireguard(conf, custom_name=custom_name)
        yaml_text = result.yaml
        if proto == "amnezia":
            # Mihomo wireguard outbound can use ordinary WG fields. AWG-specific
            # Jc/Jmin/S*/H* are preserved in raw metadata for external clients.
            result = ProxyParseResult(name=custom_name or result.name, yaml=yaml_text)
    elif proto == "vless":
        result = parse_vless(text, custom_name=custom_name)
        yaml_text = result.yaml
    elif proto == "trojan":
        result = parse_trojan(text, custom_name=custom_name)
        yaml_text = result.yaml
    elif proto == "hysteria2":
        result = parse_hysteria2(text, custom_name=custom_name)
        yaml_text = result.yaml
    elif proto == "naiveproxy":
        result = _parse_naiveproxy(text, custom_name=custom_name)
        yaml_text = result.yaml
    elif proto == "mieru":
        result = _parse_mieru_placeholder(text, custom_name=custom_name)
        yaml_text = result.yaml
    else:
        result = parse_proxy_uri(text, custom_name=custom_name)
        yaml_text = result.yaml
    yaml_text = _strip_proxy_yaml_header(yaml_text)
    name = custom_name or result.name or _name_from_yaml(yaml_text) or PROTOCOLS.get(proto, {}).get("label", proto)
    if custom_name and yaml_text.lstrip().startswith("- name:"):
        yaml_text = re.sub(r"^(\s*-\s*name:\s*).*$", r"\1" + _yaml_str(custom_name), yaml_text, count=1, flags=re.M)
        name = custom_name
    return {
        "id": _conn_id(proto, name, text),
        "protocol": proto,
        "protocolLabel": PROTOCOLS.get(proto, {}).get("label", proto),
        "name": name,
        "sourceType": "import",
        "raw": text,
        "mihomoSupported": bool(PROTOCOLS.get(proto, {}).get("mihomo")),
        "proxyYaml": yaml_text,
        "createdAt": _now_iso(),
        "updatedAt": _now_iso(),
        "enabled": True,
        "selectors": [],
    }


def _detect_protocol(text: str) -> str:
    s = str(text or "").strip().lower()
    if "[interface]" in s and "[peer]" in s:
        if any(k in s for k in ["jc", "jmin", "jmax", "s1", "h1"]):
            return "amnezia"
        return "wireguard"
    for proto, spec in PROTOCOLS.items():
        for scheme in (spec.get("schemes") or []):
            if s.startswith(str(scheme).lower()):
                if proto == "naiveproxy" and scheme == "https://" and "@" not in s:
                    continue
                return proto
    return "vless" if s.startswith("vless://") else "wireguard"


def _connection_public(conn: dict[str, Any], usage: dict[str, list[str]] | None = None) -> dict[str, Any]:
    out = {k: v for k, v in conn.items() if k not in {"raw"}}
    out["usedBySelectors"] = sorted((usage or {}).get(str(conn.get("name") or ""), []))
    out["hasRaw"] = bool(conn.get("raw"))
    return out


def _managed_connections(data: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    data = data or _load_registry()
    conns = data.get("connections") if isinstance(data, dict) else []
    out = []
    for item in conns if isinstance(conns, list) else []:
        if isinstance(item, dict):
            out.append(item)
    return out


def _format_managed_block(connections: list[dict[str, Any]]) -> str:
    """Return list entries intended to be placed inside top-level `proxies:`."""
    blocks = []
    for conn in connections:
        if not conn.get("enabled", True):
            continue
        if not conn.get("mihomoSupported", True):
            continue
        yaml_text = str(conn.get("proxyYaml") or "").strip("\n")
        if not yaml_text.lstrip().startswith("- name:"):
            continue
        proto = conn.get("protocol") or "proxy"
        cid = conn.get("id") or ""
        blocks.append(f"  # {proto} / {cid}\n" + _indent_block(yaml_text, "  "))
    return "\n".join(blocks).rstrip() + ("\n" if blocks else "")


def _indent_block(text: str, prefix: str) -> str:
    return "\n".join(prefix + line if line.strip() else line for line in str(text).splitlines())


def _managed_block_text(block: str) -> str:
    body = str(block or "").rstrip()
    if body:
        return f"  {START_MARK}\n{body}\n  {END_MARK}\n"
    return f"  {START_MARK}\n  {END_MARK}\n"


def _replace_managed_block(config_text: str, block: str) -> str:
    """Replace/insert managed proxy list inside the top-level `proxies:` section."""
    text = str(config_text or "").replace("\r\n", "\n").replace("\r", "\n")
    managed = _managed_block_text(block)
    pattern = re.compile(r"(?ms)^\s*" + re.escape(START_MARK) + r"\n.*?^\s*" + re.escape(END_MARK) + r"\n?")
    if pattern.search(text):
        return pattern.sub(managed, text)

    lines = text.splitlines()
    out: list[str] = []
    inserted = False
    for line in lines:
        out.append(line)
        if not inserted and re.match(r"^proxies\s*:\s*(?:#.*)?$", line):
            out.append(managed.rstrip("\n"))
            inserted = True
    if inserted:
        return "\n".join(out) + "\n"
    prefix = "proxies:\n" + managed
    if text and not text.endswith("\n"):
        text += "\n"
    return prefix + ("\n" if text else "") + text


def _managed_proxy_names_from_block(config_text: str) -> set[str]:
    text = str(config_text or "").replace("\r\n", "\n").replace("\r", "\n")
    start = text.find(START_MARK)
    end = text.find(END_MARK, start + len(START_MARK)) if start != -1 else -1
    if start == -1 or end == -1:
        return set()
    block = text[start:end]
    names: set[str] = set()
    for match in re.finditer(r"^\s*-\s*name:\s*(.+?)\s*$", block, flags=re.M):
        name = _clean_yaml_scalar(match.group(1))
        if name:
            names.add(name)
    return names


def _current_managed_proxy_names(connections: list[dict[str, Any]]) -> set[str]:
    names: set[str] = set()
    for conn in connections:
        if not conn.get("enabled", True) or not conn.get("mihomoSupported", True):
            continue
        name = str(conn.get("name") or _name_from_yaml(str(conn.get("proxyYaml") or ""))).strip()
        if name:
            names.add(name)
    return names


def _apply_selectors(config_text: str, connections: list[dict[str, Any]]) -> str:
    out = config_text
    for conn in connections:
        if not conn.get("enabled", True) or not conn.get("mihomoSupported", True):
            continue
        name = str(conn.get("name") or _name_from_yaml(str(conn.get("proxyYaml") or ""))).strip()
        selectors = _effective_selectors(conn, out)
        if name and selectors:
            out = insert_proxy_into_groups(out, name, selectors)
    return out


def _selector_usage_from_config(config_text: str, proxy_names: set[str]) -> dict[str, list[str]]:
    usage: dict[str, list[str]] = {name: [] for name in proxy_names}
    lines = str(config_text or "").splitlines()
    in_groups = False
    current = ""
    in_proxies = False

    def mark_all_current() -> None:
        if not current:
            return
        for proxy_name in usage:
            if current not in usage[proxy_name]:
                usage[proxy_name].append(current)

    for line in lines:
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if indent == 0 and stripped.startswith("proxy-groups:"):
            in_groups = True; current = ""; in_proxies = False; continue
        if in_groups and indent == 0 and stripped and not stripped.startswith("#"):
            in_groups = False; current = ""; in_proxies = False
        if not in_groups:
            continue
        if stripped.startswith("- name:"):
            current = _clean_yaml_scalar(stripped.split(":", 1)[1])
            in_proxies = False
            continue
        if current and stripped.startswith("include-all:"):
            value = _clean_yaml_scalar(stripped.split(":", 1)[1]).lower()
            if value in {"true", "yes", "on", "1"}:
                mark_all_current()
            continue
        if current and stripped.startswith("proxies:"):
            in_proxies = True
            # inline list
            if "[" in stripped and "]" in stripped:
                inner = stripped.split("[", 1)[1].rsplit("]", 1)[0]
                for item in inner.split(","):
                    name = _clean_yaml_scalar(item)
                    if name in usage and current not in usage[name]: usage[name].append(current)
            continue
        if current and in_proxies and stripped.startswith("-"):
            name = _clean_yaml_scalar(stripped[1:])
            if name in usage and current not in usage[name]: usage[name].append(current)
    return usage


def _selector_names_from_config(config_text: str) -> list[str]:
    names: list[str] = []
    lines = str(config_text or "").splitlines()
    in_groups = False
    for line in lines:
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if indent == 0 and stripped.startswith("proxy-groups:"):
            in_groups = True
            continue
        if in_groups and indent == 0 and stripped and not stripped.startswith("#"):
            break
        if in_groups and stripped.startswith("- name:"):
            name = _clean_yaml_scalar(stripped.split(":", 1)[1])
            if name and name not in names:
                names.append(name)
    return names


def _clean_yaml_scalar(raw: str) -> str:
    s = str(raw or "").strip().split("#", 1)[0].strip()
    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
        s = s[1:-1].replace("''", "'")
    return s.strip()


def _backup_config(path: Path) -> Path | None:
    if not path.exists():
        return None
    backup_dir = path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / (path.name + ".xkeen-proxy-connections-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    shutil.copy2(path, backup)
    return backup


def _apply_to_mihomo(*, restart: bool = False) -> dict[str, Any]:
    data = _load_registry()
    conns = _managed_connections(data)
    cfg_path = _mihomo_config_path()
    cfg = _read_text(cfg_path)
    if not cfg.strip():
        raise RuntimeError(f"Mihomo config is empty or missing: {cfg_path}")
    stale_names = _managed_proxy_names_from_block(cfg) | _current_managed_proxy_names(conns)
    block = _format_managed_block(conns)
    cleaned = remove_proxy_from_groups(cfg, stale_names)
    patched = _replace_managed_block(cleaned, block)
    patched = _apply_selectors(patched, conns)
    ok, err = validate_yaml_syntax(patched)
    if not ok:
        raise RuntimeError("generated Mihomo YAML is invalid: " + str(err))
    backup = None
    changed = patched != cfg
    if changed:
        backup = _backup_config(cfg_path)
        cfg_path.write_text(patched, encoding="utf-8")
    log = ""
    if restart:
        log = restart_mihomo_and_get_log(patched)
    return {
        "ok": True,
        "changed": changed,
        "config": str(cfg_path),
        "backup": str(backup) if backup else None,
        "count": len([c for c in conns if c.get("enabled", True) and c.get("mihomoSupported", True)]),
        "restartLog": log[-4000:] if log else "",
    }


def _sync_usage(data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, list[str]], list[str]]:
    cfg = _read_text(_mihomo_config_path())
    conns = _managed_connections(data)
    names = {str(c.get("name") or "") for c in conns if c.get("name")}
    usage = _selector_usage_from_config(cfg, names)
    selectors = _selector_names_from_config(cfg)
    for conn in conns:
        name = str(conn.get("name") or "")
        if name:
            conn["usedBySelectors"] = usage.get(name, [])
    return data, usage, selectors


def create_proxy_connections_blueprint() -> Blueprint:
    bp = Blueprint("proxy_connections", __name__)

    @bp.get("/api/proxy-connections/protocols")
    def api_protocols():
        return jsonify({"ok": True, "protocols": [{"id": k, **v} for k, v in PROTOCOLS.items()]})

    @bp.get("/api/proxy-connections")
    def api_list():
        protocol = str(request.args.get("protocol") or "").strip().lower()
        data = _load_registry()
        data, usage, selectors = _sync_usage(data)
        conns = _managed_connections(data)
        if protocol:
            conns = [c for c in conns if str(c.get("protocol") or "") == protocol]
        return jsonify({
            "ok": True,
            "connections": [_connection_public(c, usage) for c in conns],
            "count": len(conns),
            "selectors": selectors,
            "protocols": [{"id": k, **v} for k, v in PROTOCOLS.items()],
            "registry": str(_registry_path()),
        })

    @bp.post("/api/proxy-connections/import")
    def api_import():
        body = request.get_json(silent=True) or {}
        protocol = str(body.get("protocol") or "").strip().lower()
        name = str(body.get("name") or "").strip() or None
        content = str(body.get("content") or body.get("link") or body.get("config") or "").strip()
        selectors = body.get("selectors") if isinstance(body.get("selectors"), list) else []
        conn = _parse_connection(protocol, content, custom_name=name)
        conn["selectors"] = _dedupe_strings(selectors) or _default_selectors_for_config(_read_text(_mihomo_config_path()))
        data = _load_registry()
        conns = _managed_connections(data)
        # Upsert by id or by protocol/name.
        replaced = False
        for idx, old in enumerate(conns):
            if old.get("id") == conn["id"] or (old.get("protocol") == conn["protocol"] and old.get("name") == conn["name"]):
                conn["createdAt"] = old.get("createdAt") or conn["createdAt"]
                conns[idx] = conn
                replaced = True
                break
        if not replaced:
            conns.append(conn)
        data["connections"] = conns
        _save_registry(data)
        return jsonify({"ok": True, "connection": _connection_public(conn), "replaced": replaced}), 201 if not replaced else 200

    @bp.patch("/api/proxy-connections/<conn_id>")
    def api_update(conn_id: str):
        body = request.get_json(silent=True) or {}
        data = _load_registry()
        conns = _managed_connections(data)
        for conn in conns:
            if str(conn.get("id") or "") != conn_id:
                continue
            if "name" in body and str(body.get("name") or "").strip():
                conn["name"] = str(body.get("name")).strip()
            if "enabled" in body:
                conn["enabled"] = bool(body.get("enabled"))
                if conn["enabled"] and not _dedupe_strings(conn.get("selectors") if isinstance(conn.get("selectors"), list) else []):
                    conn["selectors"] = _default_selectors_for_config(_read_text(_mihomo_config_path()))
            if "selectors" in body and isinstance(body.get("selectors"), list):
                raw_selectors = body.get("selectors") or []
                conn["selectors"] = _dedupe_strings(raw_selectors) or _default_selectors_for_config(_read_text(_mihomo_config_path()))
            conn["updatedAt"] = _now_iso()
            data["connections"] = conns
            _save_registry(data)
            return jsonify({"ok": True, "connection": _connection_public(conn)})
        return jsonify({"ok": False, "error": "connection not found", "id": conn_id}), 404

    @bp.delete("/api/proxy-connections/<conn_id>")
    def api_delete(conn_id: str):
        data = _load_registry()
        conns = _managed_connections(data)
        next_conns = [c for c in conns if str(c.get("id") or "") != conn_id]
        if len(next_conns) == len(conns):
            return jsonify({"ok": False, "error": "connection not found", "id": conn_id}), 404
        removed = [c for c in conns if str(c.get("id") or "") == conn_id][0]
        data["connections"] = next_conns
        _save_registry(data)
        apply_now = str(request.args.get("apply") or "").lower() in {"1", "true", "yes", "on"}
        restart = str(request.args.get("restart") or "").lower() in {"1", "true", "yes", "on"}
        result: dict[str, Any] | None = None
        if apply_now:
            result = _apply_to_mihomo(restart=restart)
        return jsonify({"ok": True, "id": conn_id, "removedName": removed.get("name"), "apply": result})

    @bp.post("/api/proxy-connections/apply")
    def api_apply():
        body = request.get_json(silent=True) or {}
        restart = bool(body.get("restart"))
        try:
            return jsonify(_apply_to_mihomo(restart=restart))
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc)}), 500

    @bp.post("/api/proxy-connections/preview")
    def api_preview():
        data = _load_registry()
        conns = _managed_connections(data)
        block = _format_managed_block(conns)
        cfg = _read_text(_mihomo_config_path())
        if cfg:
            stale_names = _managed_proxy_names_from_block(cfg) | _current_managed_proxy_names(conns)
            patched = _apply_selectors(_replace_managed_block(remove_proxy_from_groups(cfg, stale_names), block), conns)
        else:
            patched = block
        ok, err = validate_yaml_syntax(patched) if patched else (True, "")
        return jsonify({"ok": bool(ok), "error": str(err or ""), "block": block, "configPreview": patched[-20000:]})

    return bp


__all__ = ["create_proxy_connections_blueprint", "PROTOCOLS"]
