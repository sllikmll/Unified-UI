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
import urllib.request
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
from services.awg_native import NativeAwgRuntime, NativeAwgSpec, build_native_awg_spec, native_mihomo_proxy_yaml

PROTOCOLS: dict[str, dict[str, Any]] = {
    "wireguard": {"label": "WireGuard", "schemes": ["wireguard://"], "mihomo": True},
    "amnezia": {"label": "Amnezia AWG", "schemes": ["awg://", "awg3://", "amneziawg://"], "mihomo": True},
    "hysteria2": {"label": "Hysteria2", "schemes": ["hysteria2://", "hy2://", "hysteria://"], "mihomo": True},
    "vless": {"label": "VLESS", "schemes": ["vless://"], "mihomo": True},
    "trojan": {"label": "Trojan", "schemes": ["trojan://"], "mihomo": True},
    "vmess": {"label": "VMess", "schemes": ["vmess://"], "mihomo": True},
    "shadowsocks": {"label": "Shadowsocks", "schemes": ["ss://"], "mihomo": True},
    "mieru": {"label": "Mieru", "schemes": ["mieru://", "mierus://"], "mihomo": True},
    "naiveproxy": {"label": "NaiveProxy", "schemes": ["naive://", "naive+https://", "https://"], "mihomo": True},
    "telegram": {"label": "Telegram MTProxy", "schemes": ["tg://proxy"], "mihomo": False},
}

START_MARK = "# unified-managed-proxies:start"
END_MARK = "# unified-managed-proxies:end"
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
    raw = os.environ.get("UNIFIED_UI_STATE_DIR") or os.environ.get("UNIFIED_STATE_DIR") or "/opt/var/lib/unified-ui"
    return Path(raw).expanduser().resolve()


def _registry_path() -> Path:
    raw = os.environ.get("UNIFIED_PROXY_CONNECTIONS_FILE")
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
    payload = str(link or "").strip()
    scheme = payload.split("://", 1)[0].lower() if "://" in payload else ""
    if scheme not in {"wireguard", "awg", "awg3", "amneziawg"}:
        return payload
    encoded = payload.split("://", 1)[1].split("#", 1)[0]
    encoded = encoded.split("?", 1)[0]
    try:
        raw = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return payload


def _wireguard_from_uri(link: str) -> str:
    """Convert the 3x-ui ``wireguard://`` subscription URI to wg-quick text."""
    raw = str(link or "").strip()
    u = urlparse(raw)
    if (u.scheme or "").lower() != "wireguard" or not u.hostname or not u.username:
        return _wireguard_from_data_url(raw)
    query = {key.lower(): values[0] for key, values in parse_qs(u.query, keep_blank_values=True).items() if values}
    private_key = unquote(u.username)
    public_key = unquote(query.get("publickey") or query.get("public-key") or "")
    if not public_key:
        raise ValueError("WireGuard URI has no peer public key")
    endpoint_host = u.hostname
    if ":" in endpoint_host and not endpoint_host.startswith("["):
        endpoint_host = f"[{endpoint_host}]"
    endpoint = f"{endpoint_host}:{int(u.port or 51820)}"
    address = unquote(query.get("address") or "10.0.0.2/32")
    allowed_ips = unquote(query.get("allowedips") or query.get("allowed-ips") or "0.0.0.0/0")
    lines = ["[Interface]", f"PrivateKey = {private_key}", f"Address = {address}"]
    if query.get("dns"):
        lines.append(f"DNS = {unquote(query['dns'])}")
    if query.get("mtu"):
        lines.append(f"MTU = {query['mtu']}")
    lines.extend(["", "[Peer]", f"PublicKey = {public_key}"])
    preshared = query.get("presharedkey") or query.get("preshared-key")
    if preshared:
        lines.append(f"PresharedKey = {unquote(preshared)}")
    lines.extend([f"Endpoint = {endpoint}", f"AllowedIPs = {allowed_ips}"])
    keepalive = query.get("keepalive") or query.get("persistentkeepalive")
    if keepalive:
        lines.append(f"PersistentKeepalive = {keepalive}")
    return "\n".join(lines) + "\n"


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


def _parse_mieru(link: str, custom_name: str | None = None) -> ProxyParseResult:
    raw = str(link or "").strip()
    u = urlparse(raw)
    if (u.scheme or "").lower() not in {"mieru", "mierus"}:
        raise ValueError("Not a Mieru URI")
    query = {key.lower(): values[0] for key, values in parse_qs(u.query, keep_blank_values=True).items() if values}
    server = u.hostname or ""
    username = unquote(u.username or "")
    password = unquote(u.password or "")
    raw_port = query.get("port") or str(u.port or "")
    if not server or not username or not password or not raw_port.isdigit():
        raise ValueError("Invalid Mieru URI")
    port = int(raw_port)
    if port < 1 or port > 65535:
        raise ValueError("Invalid Mieru port")
    transport = str(query.get("protocol") or "TCP").upper()
    if transport not in {"TCP", "UDP"}:
        raise ValueError("Invalid Mieru transport")
    name = custom_name or unquote(query.get("profile") or "") or (unquote(u.fragment) if u.fragment else "") or server
    lines = [
        f"- name: {_yaml_str(name)}",
        "  type: mieru",
        f"  server: {_yaml_str(server)}",
        f"  port-range: {port}-{port}",
        f"  transport: {transport}",
        "  udp: true",
        f"  username: {_yaml_str(username)}",
        f"  password: {_yaml_str(password)}",
    ]
    return ProxyParseResult(name=name, yaml="\n".join(lines) + "\n")


def _parse_telegram_action(link: str, custom_name: str | None = None) -> ProxyParseResult:
    raw = str(link or "").strip()
    u = urlparse(raw)
    query = parse_qs(u.query, keep_blank_values=True)
    if (u.scheme or "").lower() != "tg" or (u.netloc or "").lower() != "proxy":
        raise ValueError("Not a Telegram proxy URI")
    if not all(query.get(key, [""])[0] for key in ("server", "port", "secret")):
        raise ValueError("Invalid Telegram proxy URI")
    name = custom_name or "Telegram MTProxy"
    return ProxyParseResult(name=name, yaml=f"# {name} is a Telegram action, not a Mihomo outbound.\n")


def _parse_connection(protocol: str, source_text: str, custom_name: str | None = None) -> dict[str, Any]:
    proto = str(protocol or "").strip().lower()
    text = str(source_text or "").strip()
    if not proto or proto not in PROTOCOLS:
        proto = _detect_protocol(text)
    if not text:
        raise ValueError("empty connection content")

    native_runtime: dict[str, Any] | None = None
    if proto in {"wireguard", "amnezia"}:
        conf = _wireguard_from_uri(text) if proto == "wireguard" else _wireguard_from_data_url(text)
        result = parse_wireguard(conf, custom_name=custom_name)
        yaml_text = result.yaml
        if proto == "amnezia":
            fragment_name = unquote(urlparse(text).fragment).strip() if "://" in text else ""
            native_name = custom_name or fragment_name or result.name
            spec = build_native_awg_spec(native_name, conf)
            result = ProxyParseResult(
                name=native_name,
                yaml=native_mihomo_proxy_yaml(native_name, spec.interface, spec.routing_mark),
            )
            yaml_text = result.yaml
            native_runtime = {
                "engine": "amneziawg-go",
                "interface": spec.interface,
                "routingMark": spec.routing_mark,
                "routingTable": spec.routing_table,
                "rulePriority": spec.rule_priority,
            }
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
        result = _parse_mieru(text, custom_name=custom_name)
        yaml_text = result.yaml
    elif proto == "telegram":
        result = _parse_telegram_action(text, custom_name=custom_name)
        yaml_text = result.yaml
    else:
        result = parse_proxy_uri(text, custom_name=custom_name)
        yaml_text = result.yaml
    yaml_text = _strip_proxy_yaml_header(yaml_text)
    name = custom_name or result.name or _name_from_yaml(yaml_text) or PROTOCOLS.get(proto, {}).get("label", proto)
    if custom_name and yaml_text.lstrip().startswith("- name:"):
        yaml_text = re.sub(r"^(\s*-\s*name:\s*).*$", r"\1" + _yaml_str(custom_name), yaml_text, count=1, flags=re.M)
        name = custom_name
    connection = {
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
    if native_runtime is not None:
        connection["nativeRuntime"] = native_runtime
    return connection


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
    out["readOnly"] = str(conn.get("sourceType") or "").startswith("subscription-")
    out["usedBySelectors"] = sorted((usage or {}).get(str(conn.get("name") or ""), []))
    out["hasRaw"] = bool(conn.get("raw"))
    out["actionAvailable"] = str(conn.get("protocol") or "") == "telegram" and bool(conn.get("raw"))
    return out


def _managed_connections(data: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    data = data or _load_registry()
    conns = data.get("connections") if isinstance(data, dict) else []
    out = []
    for item in conns if isinstance(conns, list) else []:
        if isinstance(item, dict):
            out.append(item)
    return out


def _upgrade_native_awg_connections(
    connections: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[NativeAwgSpec], bool]:
    """Migrate local AWG records from Mihomo WireGuard to native interfaces."""
    migrated: list[dict[str, Any]] = []
    specs: list[NativeAwgSpec] = []
    changed = False
    for original in connections:
        conn = dict(original)
        protocol = str(conn.get("protocol") or "").lower()
        source_type = str(conn.get("sourceType") or "")
        raw = str(conn.get("raw") or "").strip()
        if protocol != "amnezia" or source_type == "subscription-provider" or not raw:
            migrated.append(conn)
            continue

        name = str(conn.get("name") or "AmneziaWG")
        parsed = _parse_connection("amnezia", raw, custom_name=name)
        conf = _wireguard_from_data_url(raw)
        spec = build_native_awg_spec(name, conf)
        if conn.get("enabled", True):
            specs.append(spec)

        for key in ("proxyYaml", "nativeRuntime", "protocolLabel", "mihomoSupported"):
            conn[key] = parsed[key]
        if conn != original:
            changed = True
        migrated.append(conn)
    return migrated, specs, changed


def _native_awg_runtime(specs: list[NativeAwgSpec]) -> dict[str, object]:
    state_dir = _state_dir() / "awg-native"
    go_bin = os.environ.get("UNIFIED_AWG_GO_BIN") or "/opt/bin/amneziawg-go"
    awg_bin = os.environ.get("UNIFIED_AWG_BIN") or "/opt/bin/awg"
    ip_bin = os.environ.get("UNIFIED_IP_BIN") or shutil.which("ip") or "/sbin/ip"
    if specs:
        missing = [path for path in (go_bin, awg_bin, ip_bin) if not os.path.isfile(path) or not os.access(path, os.X_OK)]
        if missing:
            raise RuntimeError("official AmneziaWG runtime is missing: " + ", ".join(missing))
    return NativeAwgRuntime(
        state_dir,
        amneziawg_go=go_bin,
        awg=awg_bin,
        ip=ip_bin,
    ).reconcile(specs)


def _native_awg_active_specs() -> list[NativeAwgSpec]:
    return NativeAwgRuntime(_state_dir() / "awg-native").load_active_specs()


def _native_awg_restore(specs: list[NativeAwgSpec]) -> None:
    _native_awg_runtime(specs)


def reconcile_native_awg_startup() -> dict[str, object]:
    data = _load_registry()
    connections, specs, changed = _upgrade_native_awg_connections(_managed_connections(data))
    result = _native_awg_runtime(specs)
    if changed:
        data["connections"] = connections
        _save_registry(data)
    return result


def _format_managed_block(connections: list[dict[str, Any]]) -> str:
    """Return list entries intended to be placed inside top-level `proxies:`."""
    blocks = []
    for conn in connections:
        # Provider-owned nodes are loaded by Mihomo from subscription_1. Keep
        # them visible in the UI registry without duplicating static proxies.
        if str(conn.get("sourceType") or "") == "subscription-provider":
            continue
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
            in_groups = True
            current = ""
            in_proxies = False
            continue
        if in_groups and indent == 0 and stripped and not stripped.startswith("#"):
            in_groups = False
            current = ""
            in_proxies = False
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
    backup = backup_dir / (path.name + ".unified-proxy-connections-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    shutil.copy2(path, backup)
    return backup


def _apply_to_mihomo(*, restart: bool = False) -> dict[str, Any]:
    data = _load_registry()
    conns, native_specs, registry_changed = _upgrade_native_awg_connections(_managed_connections(data))
    data["connections"] = conns
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
    previous_native_specs = _native_awg_active_specs()
    native_result = _native_awg_runtime(native_specs)
    backup = None
    changed = patched != cfg
    log = ""
    try:
        if changed:
            backup = _backup_config(cfg_path)
            cfg_path.write_text(patched, encoding="utf-8")
        if restart:
            log = restart_mihomo_and_get_log(patched)
        if registry_changed:
            _save_registry(data)
    except Exception:
        try:
            if changed:
                cfg_path.write_text(cfg, encoding="utf-8")
        finally:
            _native_awg_restore(previous_native_specs)
        raise
    return {
        "ok": True,
        "changed": changed,
        "config": str(cfg_path),
        "backup": str(backup) if backup else None,
        "count": len([c for c in conns if c.get("enabled", True) and c.get("mihomoSupported", True)]),
        "nativeAwg": native_result,
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


def _decode_subscription_content(content: str | bytes) -> list[str]:
    if isinstance(content, bytes):
        text = content.decode("utf-8", errors="replace").strip()
    else:
        text = str(content or "").strip()
    if not text:
        raise ValueError("empty subscription")
    if "://" not in text:
        compact = re.sub(r"\s+", "", text)
        try:
            text = base64.urlsafe_b64decode(compact + "=" * (-len(compact) % 4)).decode("utf-8")
        except Exception as exc:
            raise ValueError("subscription is neither URI lines nor valid base64") from exc
    lines = [line.strip() for line in text.replace("\r", "").split("\n") if line.strip()]
    if not lines or len(lines) > 1000:
        raise ValueError("subscription has an invalid number of entries")
    return lines


def _fetch_subscription(url: str) -> list[str]:
    source = str(url or "").strip()
    parsed = urlparse(source)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("subscription URL must use http or https")
    req = urllib.request.Request(source, headers={"User-Agent": "Unified-UI/1 subscription-import"})
    with urllib.request.urlopen(req, timeout=20) as response:
        payload = response.read(2 * 1024 * 1024 + 1)
    if len(payload) > 2 * 1024 * 1024:
        raise ValueError("subscription is larger than 2 MiB")
    return _decode_subscription_content(payload)


def _parse_subscription(lines: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    parsed: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for index, line in enumerate(lines, 1):
        try:
            parsed.append(_parse_connection("", line))
        except Exception as exc:
            scheme = line.split("://", 1)[0].lower() if "://" in line else "unknown"
            errors.append({"index": str(index), "scheme": scheme, "error": str(exc)[:300]})

    name_counts: dict[str, int] = {}
    for conn in parsed:
        key = str(conn.get("name") or "").casefold()
        name_counts[key] = name_counts.get(key, 0) + 1
    for conn in parsed:
        old_name = str(conn.get("name") or "")
        if name_counts.get(old_name.casefold(), 0) < 2:
            continue
        label = str(conn.get("protocolLabel") or conn.get("protocol") or "Proxy")
        new_name = f"{label} · {old_name}"
        yaml_text = str(conn.get("proxyYaml") or "")
        if yaml_text.lstrip().startswith("- name:"):
            yaml_text = re.sub(
                r"^(\s*-\s*name:\s*).*$",
                lambda match: match.group(1) + _yaml_str(new_name),
                yaml_text,
                count=1,
                flags=re.M,
            )
        conn["name"] = new_name
        conn["proxyYaml"] = yaml_text
        conn["id"] = _conn_id(str(conn.get("protocol") or "proxy"), new_name, str(conn.get("raw") or ""))
    return parsed, errors


def _upsert_connections(
    data: dict[str, Any],
    incoming: list[dict[str, Any]],
    *,
    default_selectors: list[str],
) -> tuple[list[dict[str, Any]], int, int]:
    # Refresh replaces only the previous read-only subscription set. Local
    # user-managed records survive intact.
    conns = [
        item
        for item in _managed_connections(data)
        if not str(item.get("sourceType") or "").startswith("subscription-")
    ]
    created = 0
    replaced = 0
    for conn in incoming:
        proto = str(conn.get("protocol") or "")
        if proto == "telegram":
            conn["sourceType"] = "subscription-action"
        elif proto == "mieru":
            conn["sourceType"] = "subscription-static"
        else:
            conn["sourceType"] = "subscription-provider"
        found = None
        for idx, old in enumerate(conns):
            if old.get("id") == conn["id"] or (
                old.get("protocol") == conn["protocol"] and old.get("name") == conn["name"]
            ):
                found = idx
                conn["createdAt"] = old.get("createdAt") or conn["createdAt"]
                conn["enabled"] = old.get("enabled", True)
                conn["selectors"] = _dedupe_strings(old.get("selectors") or []) or default_selectors
                break
        if found is None:
            conn["selectors"] = default_selectors
            conns.append(conn)
            created += 1
        else:
            conns[found] = conn
            replaced += 1
    data["connections"] = conns
    return conns, created, replaced


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

    @bp.post("/api/proxy-connections/subscription/import")
    def api_subscription_import():
        body = request.get_json(silent=True) or {}
        content = str(body.get("content") or "").strip()
        lines = _decode_subscription_content(content) if content else _fetch_subscription(str(body.get("url") or ""))
        incoming, errors = _parse_subscription(lines)
        if not incoming:
            return jsonify({"ok": False, "error": "subscription has no supported entries", "errors": errors}), 400
        before = _load_registry()
        data = json.loads(json.dumps(before))
        defaults = _default_selectors_for_config(_read_text(_mihomo_config_path()))
        _, created, replaced = _upsert_connections(data, incoming, default_selectors=defaults)
        _save_registry(data)
        apply_result = None
        if bool(body.get("apply")):
            try:
                apply_result = _apply_to_mihomo(restart=bool(body.get("restart")))
            except Exception:
                _save_registry(before)
                raise
        public = [_connection_public(conn) for conn in incoming]
        counts: dict[str, int] = {}
        for conn in incoming:
            protocol = str(conn.get("protocol") or "unknown")
            counts[protocol] = counts.get(protocol, 0) + 1
        return jsonify({
            "ok": True,
            "imported": len(incoming),
            "created": created,
            "replaced": replaced,
            "protocols": counts,
            "errors": errors,
            "connections": public,
            "apply": apply_result,
        })

    @bp.get("/api/proxy-connections/<conn_id>/action")
    def api_action(conn_id: str):
        data = _load_registry()
        conn = next((item for item in _managed_connections(data) if str(item.get("id") or "") == conn_id), None)
        if conn is None:
            return jsonify({"ok": False, "error": "connection not found"}), 404
        if str(conn.get("protocol") or "") != "telegram" or not str(conn.get("raw") or "").startswith("tg://proxy"):
            return jsonify({"ok": False, "error": "no explicit action for this connection"}), 400
        return jsonify({"ok": True, "action": "open", "url": str(conn.get("raw"))})

    @bp.patch("/api/proxy-connections/<conn_id>")
    def api_update(conn_id: str):
        body = request.get_json(silent=True) or {}
        data = _load_registry()
        conns = _managed_connections(data)
        for conn in conns:
            if str(conn.get("id") or "") != conn_id:
                continue
            if str(conn.get("sourceType") or "").startswith("subscription-"):
                return jsonify({"ok": False, "error": "subscription-managed connection is read-only"}), 409
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
        if str(removed.get("sourceType") or "").startswith("subscription-"):
            return jsonify({"ok": False, "error": "subscription-managed connection is read-only"}), 409
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
