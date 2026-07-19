"""Mihomo Clash API integration for the Unified UI panel.

This blueprint exposes a small safe subset of Mihomo's external-controller API
through the authenticated Unified UI origin. It lets users manage runtime
selectors from :8088 without opening the standalone dashboard on :9090.
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Blueprint, jsonify, request

try:
    from mihomo_server_core import CONFIG_PATH
except Exception:  # pragma: no cover - startup fallback
    CONFIG_PATH = Path(os.environ.get("MIHOMO_CONFIG", "/opt/etc/mihomo/config.yaml"))


_SELECTOR_TYPES = {"Selector", "Fallback", "URLTest", "LoadBalance"}
_NO_DELAY_TYPES = {"reject", "reject-drop", "dns", "pass", "relay"}


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    try:
        return int(str(raw).strip()) if raw is not None else default
    except Exception:
        return default


def _controller_base() -> str:
    raw = (os.environ.get("MIHOMO_CONTROLLER_URL") or "").strip()
    if raw:
        return raw.rstrip("/")
    host = (os.environ.get("MIHOMO_CONTROLLER_HOST") or "127.0.0.1").strip() or "127.0.0.1"
    port = _env_int("MIHOMO_CONTROLLER_PORT", 9090)
    return f"http://{host}:{port}"


def _controller_secret() -> str:
    return (os.environ.get("MIHOMO_CONTROLLER_SECRET") or os.environ.get("MIHOMO_SECRET") or "").strip()


def _request_mihomo(method: str, path: str, payload: Any | None = None, timeout: float = 8.0) -> tuple[int, Any]:
    url = _controller_base() + "/" + str(path or "").lstrip("/")
    data = None
    headers = {"Accept": "application/json"}
    secret = _controller_secret()
    if secret:
        headers["Authorization"] = f"Bearer {secret}"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(body) if body else {}
            except Exception:
                parsed = {"raw": body}
            return int(getattr(resp, "status", 200) or 200), parsed
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body) if body else {}
        except Exception:
            parsed = {"raw": body}
        return int(exc.code or 502), parsed


def _proxy_delay(proxy: dict[str, Any]) -> int | None:
    if str(proxy.get("type") or "").lower() in _NO_DELAY_TYPES:
        return None
    hist = proxy.get("history")
    if isinstance(hist, list) and hist:
        last = hist[-1]
        if isinstance(last, dict):
            try:
                delay = last.get("delay")
                if delay is None:
                    return None
                return int(delay)
            except Exception:
                return None
    return None


def _provider_nodes(raw: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, str]]:
    providers = raw.get("providers") if isinstance(raw, dict) else None
    if not isinstance(providers, dict):
        return [], {}
    nodes: list[dict[str, Any]] = []
    provider_by_node: dict[str, str] = {}
    for provider_name, provider in providers.items():
        if not isinstance(provider, dict):
            continue
        proxies = provider.get("proxies")
        if not isinstance(proxies, list):
            continue
        for proxy in proxies:
            if not isinstance(proxy, dict):
                continue
            name = str(proxy.get("name") or "").strip()
            if not name:
                continue
            provider_by_node[name] = str(provider_name)
            nodes.append({
                "name": name,
                "type": proxy.get("type"),
                "now": proxy.get("now"),
                "all": proxy.get("all") if isinstance(proxy.get("all"), list) else [],
                "alive": proxy.get("alive"),
                "udp": proxy.get("udp"),
                "delay": _proxy_delay(proxy),
                "provider": str(provider_name),
                "hidden": proxy.get("hidden"),
            })
    return nodes, provider_by_node


def _summarize_proxies(raw: dict[str, Any], provider_raw: dict[str, Any] | None = None) -> dict[str, Any]:
    proxies = raw.get("proxies") if isinstance(raw, dict) else None
    if not isinstance(proxies, dict):
        proxies = {}
    selectors = []
    nodes_by_name: dict[str, dict[str, Any]] = {}
    provider_nodes, provider_by_node = _provider_nodes(provider_raw or {})
    for node in provider_nodes:
        nodes_by_name[str(node.get("name") or "")] = node
    for name, value in proxies.items():
        if not isinstance(value, dict):
            continue
        item = {
            "name": str(name),
            "type": value.get("type"),
            "now": value.get("now"),
            "all": value.get("all") if isinstance(value.get("all"), list) else [],
            "alive": value.get("alive"),
            "udp": value.get("udp"),
            "delay": _proxy_delay(value),
            "provider": value.get("provider-name"),
            "hidden": value.get("hidden"),
        }
        if str(value.get("type") or "") in _SELECTOR_TYPES and item["all"]:
            selectors.append(item)
        else:
            nodes_by_name[str(name)] = item
    selectors.sort(key=lambda x: str(x.get("name") or "").lower())
    nodes = sorted(nodes_by_name.values(), key=lambda x: str(x.get("name") or "").lower())
    return {
        "selectors": selectors,
        "nodes": nodes,
        "providerByNode": provider_by_node,
        "raw_count": len(proxies),
        "provider_node_count": len(provider_nodes),
        "controller": _controller_base(),
    }


def _mihomo_root() -> Path:
    try:
        cfg = Path(CONFIG_PATH)
        # CONFIG_PATH is often /opt/etc/mihomo/config.yaml -> profiles/default.yaml.
        # The Mihomo root is the symlink location parent, not the resolved target parent.
        return cfg.expanduser().parent.resolve()
    except Exception:
        pass
    return Path(os.environ.get("MIHOMO_ROOT", "/opt/etc/mihomo")).expanduser().resolve()


def _manual_rule_file() -> Path:
    raw = (os.environ.get("MIHOMO_MANUAL_RULE_FILE") or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return (_mihomo_root() / "rules" / "manual-proxy.yaml").resolve()


def _safe_manual_path() -> Path:
    path = _manual_rule_file()
    root = _mihomo_root().resolve()
    try:
        if not (str(path).startswith(str(root) + os.sep) or path == root):
            raise RuntimeError("manual rule file must be inside MIHOMO_ROOT")
    except Exception as exc:
        raise RuntimeError(f"unsafe manual rule path: {path}") from exc
    return path


def _normalize_manual_payload(text: str) -> str:
    raw = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    stripped = raw.strip()
    if not stripped:
        return "payload:\n"
    if stripped.startswith("payload:"):
        return stripped + "\n"
    lines = []
    for line in raw.split("\n"):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("-"):
            s = s[1:].strip()
        if s:
            lines.append(f"  - {s}")
    return "payload:\n" + "\n".join(lines) + ("\n" if lines else "")



def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(text) if text.strip() else {}
        return data if isinstance(data, dict) else {}
    except Exception:
        pass
    return _parse_mihomo_config_minimal(text)



def _parse_inline_yaml_map(raw: str) -> dict[str, str]:
    value = str(raw or "").strip()
    if not (value.startswith("{") and value.endswith("}")):
        return {}
    inner = value[1:-1].strip()
    out: dict[str, str] = {}
    parts: list[str] = []
    buf: list[str] = []
    quote = ""
    for ch in inner:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = ""
            continue
        if ch in {"'", '"'}:
            quote = ch
            buf.append(ch)
            continue
        if ch == ",":
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf).strip())
    for part in parts:
        if ":" not in part:
            continue
        k, v = part.split(":", 1)
        out[k.strip()] = v.strip().strip('"\'')
    return out

def _parse_mihomo_config_minimal(text: str) -> dict[str, Any]:
    """Tiny parser for the config fragments we need: rule-providers and rules.

    Entware installs are not guaranteed to have PyYAML. This keeps the inspector
    useful without pulling dependencies just to read provider paths/URLs.
    """
    out: dict[str, Any] = {"rule-providers": {}, "rules": []}
    lines = str(text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    section = None
    current_name = None
    current_indent = 0
    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent == 0 and stripped.endswith(":"):
            section = stripped[:-1]
            current_name = None
            continue
        if section == "rule-providers":
            if indent == 2 and ":" in stripped:
                name_part, rest = stripped.split(":", 1)
                if name_part.strip():
                    current_name = name_part.strip().strip('"\'')
                    out["rule-providers"].setdefault(current_name, {})
                    current_indent = indent
                    inline = _parse_inline_yaml_map(rest.strip())
                    if inline:
                        out["rule-providers"][current_name].update(inline)
                    continue
            if current_name and indent > current_indent and ":" in stripped:
                k, v = stripped.split(":", 1)
                k = k.strip()
                v = v.strip().strip('"\'')
                if k == "<<":
                    continue
                out["rule-providers"][current_name][k] = v
        elif section == "rules":
            if stripped.startswith("-"):
                out["rules"].append(stripped[1:].strip().strip('"\''))
    return out


def _mihomo_config_mapping() -> dict[str, Any]:
    path = Path(CONFIG_PATH).expanduser()
    try:
        if path.is_symlink():
            # Keep relative symlink target under config dir working.
            target = os.readlink(path)
            path = (path.parent / target).resolve() if not os.path.isabs(target) else Path(target).resolve()
        else:
            path = path.resolve()
    except Exception:
        pass
    return _load_yaml_mapping(path)


def _rule_providers_from_config() -> dict[str, dict[str, Any]]:
    cfg = _mihomo_config_mapping()
    providers = cfg.get("rule-providers") if isinstance(cfg, dict) else {}
    return providers if isinstance(providers, dict) else {}


def _rules_from_config() -> list[str]:
    cfg = _mihomo_config_mapping()
    rules = cfg.get("rules") if isinstance(cfg, dict) else []
    return [str(x) for x in rules] if isinstance(rules, list) else []



def _resolve_rule_provider_name(name: str, providers: dict[str, dict[str, Any]] | None = None) -> str:
    raw = str(name or "").strip()
    providers = providers if isinstance(providers, dict) else _rule_providers_from_config()
    if raw in providers:
        return raw
    for suffix in ("@classical", "@domain", "@ipcidr"):
        cand = raw + suffix
        if cand in providers:
            return cand
    for key in providers.keys():
        if str(key).split("@", 1)[0] == raw:
            return str(key)
    return raw

def _provider_path_from_config(provider: str, meta: dict[str, Any] | None = None) -> Path | None:
    meta = meta if isinstance(meta, dict) else _rule_providers_from_config().get(provider, {})
    raw = str(meta.get("path") or "").strip()
    if not raw:
        raw = f"rules/{provider}.yaml"
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = (_mihomo_root() / path).resolve()
    else:
        path = path.resolve()
    root = _mihomo_root().resolve()
    if not (str(path).startswith(str(root) + os.sep) or path == root):
        raise RuntimeError("unsafe rule provider path")
    return path


def _provider_is_editable(name: str, meta: dict[str, Any] | None = None) -> bool:
    meta = meta if isinstance(meta, dict) else _rule_providers_from_config().get(name, {})
    ptype = str(meta.get("type") or "").strip().lower()
    has_url = bool(str(meta.get("url") or "").strip())
    behavior = str(meta.get("behavior") or "").strip().lower()
    return (ptype in {"file", ""} and not has_url and behavior in {"domain", "ipcidr", "classical", ""}) or name == "manual-proxy"


def _format_rule_payload_from_lines(lines: list[str]) -> str:
    clean: list[str] = []
    for item in lines:
        value = str(item or "").strip()
        if not value or value.startswith("#"):
            continue
        if value.startswith("-"):
            value = value[1:].strip()
        if value:
            clean.append(value)
    return "payload:\n" + "\n".join(f"  - {item}" for item in clean) + ("\n" if clean else "")


def _rule_provider_cache_dir() -> Path:
    raw = str(os.environ.get("XKEEN_RULE_PROVIDER_CACHE_DIR") or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return Path(os.environ.get("BASE_VAR_DIR", "/opt/var")).expanduser().resolve() / "cache" / "xkeen-ui" / "rule-providers"


def _safe_cache_name(name: str) -> str:
    value = str(name or "provider").strip() or "provider"
    return "".join(ch if ch.isalnum() or ch in {"-", "_", ".", "@"} else "_" for ch in value)[:180]


def _rule_provider_cache_path(name: str) -> Path:
    return _rule_provider_cache_dir() / (_safe_cache_name(name) + ".yaml")


def _read_rule_provider_cache(name: str) -> str | None:
    path = _rule_provider_cache_path(name)
    try:
        if path.exists() and path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            if text.strip():
                return text if text.endswith("\n") else text + "\n"
    except Exception:
        return None
    return None


def _write_rule_provider_cache(name: str, text: str) -> None:
    try:
        path = _rule_provider_cache_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(text or ""), encoding="utf-8")
    except Exception:
        pass


def _download_rule_provider_source(url: str, *, max_bytes: int = 16 * 1024 * 1024, timeout: float | None = None) -> bytes:
    raw = str(url or "").strip()
    if not raw.lower().startswith(("https://", "http://")):
        raise RuntimeError("unsupported provider url")
    if timeout is None:
        try:
            timeout = float(os.environ.get("XKEEN_RULE_PROVIDER_DOWNLOAD_TIMEOUT") or "4")
        except Exception:
            timeout = 5.0
    timeout = max(2.0, min(float(timeout), 12.0))
    req = urllib.request.Request(raw, headers={"User-Agent": "Unified-UI/selector-inspector", "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = resp.read(256 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise RuntimeError("provider file too large")
            chunks.append(chunk)
    return b"".join(chunks)


def _decode_mrs_provider(meta: dict[str, Any], resolved: str) -> tuple[str, dict[str, Any]]:
    url = str(meta.get("url") or "").strip()
    behavior = str(meta.get("behavior") or "domain").strip().lower() or "domain"
    if behavior == "classical":
        behavior = "classical"
    if behavior not in {"domain", "ipcidr", "classical"}:
        behavior = "domain"
    blob = _download_rule_provider_source(url)
    mihomo_bin = str(os.environ.get("MIHOMO_BIN") or "/opt/sbin/mihomo")
    with tempfile.TemporaryDirectory(prefix="xkeen-rp-") as td:
        src = Path(td) / (resolved.replace("/", "_") + ".mrs")
        dst = Path(td) / "out.txt"
        src.write_bytes(blob)
        proc = subprocess.run(
            [mihomo_bin, "convert-ruleset", behavior, "mrs", str(src), str(dst)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=20,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError((proc.stderr or proc.stdout or "mrs decode failed")[:500])
        lines = dst.read_text(encoding="utf-8", errors="replace").splitlines() if dst.exists() else []
    text = _format_rule_payload_from_lines(lines)
    _write_rule_provider_cache(resolved, text)
    meta2 = dict(meta)
    meta2["decoded"] = True
    meta2["decoded_format"] = "mrs"
    meta2["decoded_count"] = len([x for x in lines if str(x).strip()])
    meta2["cached"] = False
    return text, meta2


def _read_remote_rule_provider_text(resolved: str, meta: dict[str, Any]) -> tuple[Path, str, bool, dict[str, Any]]:
    fmt = str(meta.get("format") or "").strip().lower()
    url = str(meta.get("url") or "").strip()
    pseudo_path = _provider_path_from_config(resolved, meta)
    meta_base = dict(meta)
    if not url:
        return pseudo_path, "payload:\n", False, meta_base
    # Inspector must be instant: show previously decoded payload first.
    # Network refresh belongs to the explicit "Обновить provider" action, not every click.
    cached_first = _read_rule_provider_cache(resolved)
    if cached_first:
        meta_cached = dict(meta_base)
        meta_cached["decoded"] = True
        meta_cached["cached"] = True
        meta_cached["decoded_count"] = len([x for x in cached_first.splitlines() if x.strip().startswith("-")])
        return pseudo_path, cached_first, False, meta_cached
    try:
        if fmt == "mrs" or url.lower().endswith(".mrs"):
            text, meta2 = _decode_mrs_provider(meta_base, resolved)
            return pseudo_path, text, False, meta2
        blob = _download_rule_provider_source(url)
        raw = blob.decode("utf-8", errors="replace")
        if "payload:" in raw.lstrip()[:80]:
            text = raw.strip() + "\n"
        else:
            text = _format_rule_payload_from_lines(raw.splitlines())
        _write_rule_provider_cache(resolved, text)
        meta2 = dict(meta_base)
        meta2["decoded"] = True
        meta2["decoded_format"] = fmt or "text"
        meta2["decoded_count"] = len([x for x in text.splitlines() if x.strip().startswith("-")])
        meta2["cached"] = False
        return pseudo_path, text, False, meta2
    except Exception as exc:
        cached = _read_rule_provider_cache(resolved)
        meta2 = dict(meta_base)
        meta2["decoded"] = bool(cached)
        meta2["cached"] = bool(cached)
        meta2["decode_error"] = str(exc)
        if cached:
            meta2["decoded_count"] = len([x for x in cached.splitlines() if x.strip().startswith("-")])
            return pseudo_path, cached, False, meta2
        msg = str(exc).replace("\n", " ")[:500]
        return pseudo_path, f"payload:\n  # Не удалось быстро загрузить provider {resolved}: {msg}\n  # Нажми «Обновить provider» или попробуй позже. UI больше не ждёт 30 секунд.\n", False, meta2


def _read_rule_provider_text(name: str) -> tuple[Path, str, bool, dict[str, Any]]:
    providers = _rule_providers_from_config()
    resolved = _resolve_rule_provider_name(name, providers)
    meta = providers.get(resolved, {}) if isinstance(providers, dict) else {}
    if str(name) == "manual-proxy" and not meta:
        path = _safe_manual_path()
        return path, path.read_text(encoding="utf-8") if path.exists() else "payload:\n", True, {"type": "file", "behavior": "classical", "path": str(path), "resolved_name": resolved}
    meta = dict(meta) if isinstance(meta, dict) else {}
    meta["resolved_name"] = resolved
    editable = _provider_is_editable(resolved, meta)
    if not editable and str(meta.get("url") or "").strip():
        return _read_remote_rule_provider_text(resolved, meta)
    path = _provider_path_from_config(resolved, meta)
    text = path.read_text(encoding="utf-8") if path and path.exists() else "payload:\n"
    return path, text, editable, meta


def _strip_inline_comment(value: str) -> str:
    return str(value or "").split("#", 1)[0].strip()


def _rules_targeting_selector(selector: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    target = str(selector or "").strip()
    aliases = {target}
    if target.endswith(" Selector"):
        aliases.add(target[:-9].strip())
    aliases.add(target.replace(" Selector", "").strip())
    for idx, rule in enumerate(_rules_from_config()):
        parts = [p.strip() for p in str(rule).split(",")]
        if len(parts) < 3:
            continue
        rule_target = _strip_inline_comment(parts[-1])
        if rule_target not in aliases:
            continue
        provider = parts[1] if parts[0].upper() == "RULE-SET" and len(parts) >= 3 else ""
        out.append({"index": idx, "rule": rule, "provider": provider})
    return out


def _list_rule_providers_payload() -> dict[str, Any]:
    providers = _rule_providers_from_config()
    rules = _rules_from_config()
    usage: dict[str, list[dict[str, Any]]] = {}
    for idx, rule in enumerate(rules):
        parts = [p.strip() for p in str(rule).split(",")]
        if len(parts) >= 3 and parts[0].upper() == "RULE-SET":
            usage.setdefault(parts[1], []).append({"index": idx, "rule": rule, "target": parts[-1]})
    items = []
    for name, meta in sorted(providers.items(), key=lambda kv: str(kv[0]).lower()):
        if not isinstance(meta, dict):
            meta = {}
        path = None
        try:
            path = str(_provider_path_from_config(str(name), meta))
        except Exception:
            path = str(meta.get("path") or "")
        items.append({
            "name": str(name),
            "type": meta.get("type"),
            "behavior": meta.get("behavior"),
            "url": meta.get("url"),
            "path": path,
            "editable": _provider_is_editable(str(name), meta),
            "usedBy": usage.get(str(name), []),
        })
    return {"providers": items, "count": len(items), "controller": _controller_base()}


def _runtime_selector_payload(selector: str) -> tuple[str, dict[str, Any]]:
    status, data = _request_mihomo("GET", "/proxies", timeout=8.0)
    lines: list[str] = []
    meta: dict[str, Any] = {"runtime": True}
    if 200 <= status < 300 and isinstance(data, dict):
        proxies = data.get("proxies") if isinstance(data.get("proxies"), dict) else {}
        item = proxies.get(str(selector)) if isinstance(proxies, dict) else None
        if isinstance(item, dict):
            all_items = item.get("all") if isinstance(item.get("all"), list) else []
            now = item.get("now")
            meta.update({"type": item.get("type"), "now": now, "runtime_count": len(all_items)})
            lines = [str(x) for x in all_items if str(x or "").strip()]
    return _format_rule_payload_from_lines(lines), meta


def _selector_inspector_payload(selector: str) -> dict[str, Any]:
    matches = _rules_targeting_selector(selector)
    providers = _list_rule_providers_payload().get("providers", [])
    by_name = {str(p.get("name")): p for p in providers if isinstance(p, dict)}
    linked: list[dict[str, Any]] = []
    for match in matches:
        pname = str(match.get("provider") or "")
        if not pname:
            continue
        item = dict(by_name.get(pname) or {"name": pname})
        item["rule"] = match.get("rule")
        item["ruleIndex"] = match.get("index")
        linked.append(item)

    editable = False
    primary = linked[0] if len(linked) == 1 else None
    text_parts: list[str] = []
    if primary:
        path, text, editable, meta = _read_rule_provider_text(str(primary.get("name") or ""))
        resolved_name = str((meta or {}).get("resolved_name") or primary.get("name") or "")
        primary["name"] = resolved_name
        primary["path"] = str(path)
        primary["meta"] = meta
        text_parts.append(text)
    elif linked:
        def read_linked_provider(item: dict[str, Any]) -> tuple[dict[str, Any], str]:
            pname = str(item.get("name") or "")
            try:
                path, text, _editable_one, meta = _read_rule_provider_text(pname)
                out_item = dict(item)
                out_item["path"] = str(path)
                out_item["meta"] = meta
                return out_item, f"# Provider: {pname}\n" + text
            except Exception as exc:
                return dict(item), f"payload:\n  # Не удалось прочитать provider {pname}: {exc}\n"

        workers = max(1, min(6, len(linked)))
        new_linked: list[dict[str, Any]] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            for item, text in executor.map(read_linked_provider, linked):
                new_linked.append(item)
                text_parts.append(text)
        linked = new_linked
    else:
        text, meta = _runtime_selector_payload(selector)
        if text.strip() == "payload:":
            text = "payload:\n  # Runtime selector пуст или Mihomo не вернул список all.\n"
        text_parts.append(text)
        primary = {"name": "runtime:" + str(selector), "meta": meta, "path": "runtime selector / no RULE-SET"}

    return {
        "ok": True,
        "selector": selector,
        "providers": linked,
        "content": "\n".join(text_parts),
        "editable": bool(editable and primary and linked),
        "primaryProvider": primary,
    }


def _latest_provider_node(provider_name: str, proxy_name: str) -> dict[str, Any] | None:
    status, data = _request_mihomo("GET", f"/providers/proxies/{urllib.parse.quote(provider_name, safe='')}", timeout=10.0)
    if not (200 <= status < 300) or not isinstance(data, dict):
        return None
    proxies = data.get("proxies")
    if not isinstance(proxies, list):
        return None
    for proxy in proxies:
        if isinstance(proxy, dict) and str(proxy.get("name") or "") == proxy_name:
            return proxy
    return None


def _provider_for_proxy(proxy_name: str) -> str | None:
    status, data = _request_mihomo("GET", "/providers/proxies", timeout=10.0)
    if not (200 <= status < 300):
        return None
    _, provider_by_node = _provider_nodes(data)
    return provider_by_node.get(proxy_name)


def _healthcheck_provider_for_proxy(proxy_name: str, timeout_ms: int) -> tuple[int, dict[str, Any]]:
    provider = _provider_for_proxy(proxy_name)
    if not provider:
        return 404, {"message": "proxy not found in providers"}
    enc_provider = urllib.parse.quote(provider, safe="")
    _request_mihomo("GET", f"/providers/proxies/{enc_provider}/healthcheck", timeout=(timeout_ms / 1000.0) + 8.0)
    proxy = _latest_provider_node(provider, proxy_name)
    if not proxy:
        return 404, {"message": "proxy not found after provider healthcheck", "provider": provider}
    return 200, {"provider": provider, "delay": _proxy_delay(proxy), "alive": proxy.get("alive")}


def create_mihomo_clash_blueprint() -> Blueprint:
    bp = Blueprint("mihomo_clash", __name__)

    @bp.get("/api/mihomo/clash/status")
    def api_mihomo_clash_status():
        try:
            status, data = _request_mihomo("GET", "/version", timeout=4.0)
            return jsonify({"ok": 200 <= status < 300, "status": status, "data": data, "controller": _controller_base()})
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc), "controller": _controller_base()}), 502

    @bp.get("/api/mihomo/clash/proxies")
    def api_mihomo_clash_proxies():
        try:
            status, data = _request_mihomo("GET", "/proxies", timeout=10.0)
            if not (200 <= status < 300):
                return jsonify({"ok": False, "status": status, "error": data}), 502
            provider_status, provider_data = _request_mihomo("GET", "/providers/proxies", timeout=10.0)
            if not (200 <= provider_status < 300):
                provider_data = {}
            summary = _summarize_proxies(data, provider_data)
            summary["ok"] = True
            return jsonify(summary)
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc), "controller": _controller_base()}), 502

    @bp.put("/api/mihomo/clash/proxies/<path:selector>")
    def api_mihomo_clash_select(selector: str):
        body = request.get_json(silent=True) or {}
        name = str(body.get("name") or body.get("proxy") or "").strip()
        if not name:
            return jsonify({"ok": False, "error": "missing proxy name"}), 400
        enc = urllib.parse.quote(str(selector), safe="")
        try:
            status, data = _request_mihomo("PUT", f"/proxies/{enc}", {"name": name}, timeout=8.0)
            ok = 200 <= status < 300
            return jsonify({"ok": ok, "status": status, "data": data, "selector": selector, "name": name}), (200 if ok else 502)
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc), "selector": selector, "name": name}), 502

    @bp.post("/api/mihomo/clash/proxies/<path:proxy>/delay")
    def api_mihomo_clash_delay(proxy: str):
        body = request.get_json(silent=True) or {}
        timeout_ms = int(body.get("timeout") or os.environ.get("MIHOMO_DELAY_TIMEOUT_MS") or 5000)
        test_url = str(body.get("url") or os.environ.get("MIHOMO_DELAY_TEST_URL") or "https://www.gstatic.com/generate_204")
        timeout_ms = max(1000, min(timeout_ms, 15000))
        enc = urllib.parse.quote(str(proxy), safe="")
        qs = urllib.parse.urlencode({"timeout": str(timeout_ms), "url": test_url})
        try:
            status, data = _request_mihomo("GET", f"/proxies/{enc}/delay?{qs}", timeout=(timeout_ms / 1000.0) + 3.0)
            if status == 404:
                status, data = _healthcheck_provider_for_proxy(proxy, timeout_ms)
            ok = 200 <= status < 300
            delay = data.get("delay") if isinstance(data, dict) else None
            try:
                delay = int(delay) if delay is not None else None
            except Exception:
                delay = None
            return jsonify({"ok": ok, "status": status, "proxy": proxy, "delay": delay, "data": data}), (200 if ok else 502)
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc), "proxy": proxy}), 502

    @bp.post("/api/mihomo/clash/proxies/delay-all")
    def api_mihomo_clash_delay_all():
        body = request.get_json(silent=True) or {}
        raw_names = body.get("names") or []
        names: list[str] = []
        seen: set[str] = set()
        for item in raw_names if isinstance(raw_names, list) else []:
            name = str(item or "").strip()
            if not name or name in seen:
                continue
            seen.add(name)
            names.append(name)
        names = names[:80]
        timeout_ms = int(body.get("timeout") or os.environ.get("MIHOMO_DELAY_TIMEOUT_MS") or 5000)
        test_url = str(body.get("url") or os.environ.get("MIHOMO_DELAY_TEST_URL") or "https://www.gstatic.com/generate_204")
        timeout_ms = max(1000, min(timeout_ms, 15000))
        workers = max(1, min(int(body.get("workers") or os.environ.get("MIHOMO_DELAY_WORKERS") or 6), 12))

        provider_status, provider_data = _request_mihomo("GET", "/providers/proxies", timeout=10.0)
        provider_by_node: dict[str, str] = {}
        if 200 <= provider_status < 300:
            _, provider_by_node = _provider_nodes(provider_data)
        provider_names = sorted({provider_by_node[name] for name in names if name in provider_by_node})
        provider_results: dict[str, dict[str, Any]] = {}

        def healthcheck_provider(provider: str) -> tuple[str, dict[str, Any]]:
            enc = urllib.parse.quote(provider, safe="")
            try:
                status, data = _request_mihomo("GET", f"/providers/proxies/{enc}/healthcheck", timeout=(timeout_ms / 1000.0) + 8.0)
                return provider, {"ok": 200 <= status < 300, "status": status, "data": data}
            except Exception as exc:  # noqa: BLE001
                return provider, {"ok": False, "error": str(exc)}

        if provider_names:
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(workers, max(1, len(provider_names)))) as executor:
                for provider, result in executor.map(healthcheck_provider, provider_names):
                    provider_results[provider] = result

        latest_provider_nodes: dict[str, dict[str, Any]] = {}
        if provider_names:
            latest_status, latest_data = _request_mihomo("GET", "/providers/proxies", timeout=10.0)
            if 200 <= latest_status < 300:
                provider_nodes, _ = _provider_nodes(latest_data)
                latest_provider_nodes = {str(node.get("name") or ""): node for node in provider_nodes}

        direct_names = [name for name in names if name not in provider_by_node]

        def one_direct(name: str) -> dict[str, Any]:
            enc = urllib.parse.quote(name, safe="")
            qs = urllib.parse.urlencode({"timeout": str(timeout_ms), "url": test_url})
            try:
                status, data = _request_mihomo("GET", f"/proxies/{enc}/delay?{qs}", timeout=(timeout_ms / 1000.0) + 3.0)
                delay = data.get("delay") if isinstance(data, dict) else None
                try:
                    delay = int(delay) if delay is not None else None
                except Exception:
                    delay = None
                return {"ok": 200 <= status < 300, "status": status, "proxy": name, "delay": delay, "data": data}
            except Exception as exc:  # noqa: BLE001
                return {"ok": False, "proxy": name, "delay": None, "error": str(exc)}

        direct_results: list[dict[str, Any]] = []
        if direct_names:
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(workers, max(1, len(direct_names)))) as executor:
                future_map = {executor.submit(one_direct, name): name for name in direct_names}
                for future in concurrent.futures.as_completed(future_map):
                    direct_results.append(future.result())

        result_by_name: dict[str, dict[str, Any]] = {str(item.get("proxy")): item for item in direct_results}
        for name in names:
            provider = provider_by_node.get(name)
            if not provider:
                continue
            node = latest_provider_nodes.get(name)
            provider_result = provider_results.get(provider, {})
            if node:
                result_by_name[name] = {
                    "ok": bool(provider_result.get("ok", True)),
                    "status": int(provider_result.get("status", 200) or 200),
                    "proxy": name,
                    "provider": provider,
                    "delay": node.get("delay"),
                    "alive": node.get("alive"),
                }
            else:
                result_by_name[name] = {"ok": False, "proxy": name, "provider": provider, "delay": None, "error": "provider node not found"}
        results = [result_by_name.get(name, {"ok": False, "proxy": name, "delay": None, "error": "not checked"}) for name in names]
        return jsonify({"ok": True, "results": results, "count": len(results), "providers": provider_results})


    @bp.get("/api/mihomo/clash/connections")
    def api_mihomo_clash_connections():
        try:
            status, data = _request_mihomo("GET", "/connections", timeout=6.0)
            ok = 200 <= status < 300
            return jsonify({"ok": ok, "status": status, "data": data, "controller": _controller_base()}), (200 if ok else 502)
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc), "controller": _controller_base()}), 502

    @bp.delete("/api/mihomo/clash/connections/<path:connection_id>")
    def api_mihomo_clash_connection_close(connection_id: str):
        enc = urllib.parse.quote(str(connection_id), safe="")
        try:
            status, data = _request_mihomo("DELETE", f"/connections/{enc}", timeout=6.0)
            ok = 200 <= status < 300
            return jsonify({"ok": ok, "status": status, "data": data, "id": connection_id}), (200 if ok else 502)
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc), "id": connection_id}), 502

    @bp.delete("/api/mihomo/clash/connections")
    def api_mihomo_clash_connections_close_all():
        try:
            status, data = _request_mihomo("DELETE", "/connections", timeout=8.0)
            ok = 200 <= status < 300
            return jsonify({"ok": ok, "status": status, "data": data}), (200 if ok else 502)
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc)}), 502

    @bp.get("/api/mihomo/clash/providers/proxies")
    def api_mihomo_clash_proxy_providers():
        try:
            status, data = _request_mihomo("GET", "/providers/proxies", timeout=10.0)
            ok = 200 <= status < 300
            return jsonify({"ok": ok, "status": status, "data": data, "controller": _controller_base()}), (200 if ok else 502)
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc), "controller": _controller_base()}), 502

    @bp.put("/api/mihomo/clash/providers/proxies/<path:provider>")
    def api_mihomo_clash_proxy_provider_update(provider: str):
        enc = urllib.parse.quote(str(provider), safe="")
        try:
            status, data = _request_mihomo("PUT", f"/providers/proxies/{enc}", timeout=60.0)
            ok = 200 <= status < 300
            return jsonify({"ok": ok, "status": status, "data": data, "provider": provider}), (200 if ok else 502)
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc), "provider": provider}), 502

    @bp.post("/api/mihomo/clash/providers/proxies/update-all")
    def api_mihomo_clash_proxy_providers_update_all():
        try:
            status, data = _request_mihomo("GET", "/providers/proxies", timeout=10.0)
            if not (200 <= status < 300) or not isinstance(data, dict):
                return jsonify({"ok": False, "status": status, "error": data}), 502
            providers = data.get("providers")
            names = []
            if isinstance(providers, dict):
                for name, provider in providers.items():
                    if not isinstance(provider, dict):
                        continue
                    # Mihomo uses providerType/proxyProviderType depending on version; skip compatible/direct pseudo providers.
                    ptype = str(provider.get("type") or provider.get("vehicleType") or provider.get("providerType") or "").lower()
                    if name and ptype not in {"compatible", "direct", "reject"}:
                        names.append(str(name))
            names = names[:30]
            results = []
            for name in names:
                enc = urllib.parse.quote(name, safe="")
                try:
                    st, body = _request_mihomo("PUT", f"/providers/proxies/{enc}", timeout=60.0)
                    results.append({"provider": name, "ok": 200 <= st < 300, "status": st, "data": body})
                except Exception as exc:  # noqa: BLE001
                    results.append({"provider": name, "ok": False, "error": str(exc)})
            return jsonify({"ok": True, "count": len(results), "results": results})
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc)}), 502

    @bp.get("/api/mihomo/clash/providers/rules")
    def api_mihomo_clash_rule_providers():
        try:
            payload = _list_rule_providers_payload()
            payload["ok"] = True
            # Merge runtime Mihomo provider status when available.
            try:
                status, data = _request_mihomo("GET", "/providers/rules", timeout=10.0)
                payload["runtime"] = data if 200 <= status < 300 else None
                payload["runtime_status"] = status
            except Exception:
                payload["runtime"] = None
            return jsonify(payload)
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc), "controller": _controller_base()}), 502

    @bp.put("/api/mihomo/clash/providers/rules/<path:provider>")
    def api_mihomo_clash_rule_provider_update(provider: str):
        enc = urllib.parse.quote(str(provider), safe="")
        try:
            status, data = _request_mihomo("PUT", f"/providers/rules/{enc}", timeout=60.0)
            ok = 200 <= status < 300
            return jsonify({"ok": ok, "status": status, "data": data, "provider": provider}), (200 if ok else 502)
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc), "provider": provider}), 502

    @bp.get("/api/mihomo/rule-provider/<path:provider>")
    def api_mihomo_rule_provider_get(provider: str):
        try:
            path, text, editable, meta = _read_rule_provider_text(str(provider))
            resolved_provider = str((meta or {}).get("resolved_name") or provider)
            used_by = []
            for item in _list_rule_providers_payload().get("providers", []):
                if item.get("name") == resolved_provider:
                    used_by = item.get("usedBy") or []
                    break
            return jsonify({
                "ok": True,
                "provider": resolved_provider,
                "path": str(path),
                "content": text,
                "editable": bool(editable),
                "meta": meta,
                "usedBy": used_by,
            })
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc), "provider": provider}), 500

    @bp.post("/api/mihomo/rule-provider/<path:provider>")
    def api_mihomo_rule_provider_save(provider: str):
        body = request.get_json(silent=True) or {}
        content = _normalize_manual_payload(str(body.get("content") or ""))
        try:
            path, _old_text, editable, meta = _read_rule_provider_text(str(provider))
            if not editable:
                return jsonify({"ok": False, "error": "provider is remote or not editable", "provider": provider}), 403
            path.parent.mkdir(parents=True, exist_ok=True)
            backup = None
            if path.exists():
                backup = path.with_name(path.name + ".bak-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
                shutil.copy2(path, backup)
            path.write_text(content, encoding="utf-8")
            return jsonify({"ok": True, "provider": provider, "path": str(path), "backup": str(backup) if backup else None, "content": content, "meta": meta})
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc), "provider": provider}), 500

    @bp.get("/api/mihomo/selector-inspector/<path:selector>")
    def api_mihomo_selector_inspector(selector: str):
        try:
            return jsonify(_selector_inspector_payload(selector))
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc), "selector": selector}), 500

    @bp.get("/api/mihomo/manual-proxy")
    def api_mihomo_manual_proxy_get():
        try:
            path = _safe_manual_path()
            text = path.read_text(encoding="utf-8") if path.exists() else "payload:\n"
            return jsonify({"ok": True, "path": str(path), "content": text})
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc)}), 500

    @bp.post("/api/mihomo/manual-proxy")
    def api_mihomo_manual_proxy_save():
        body = request.get_json(silent=True) or {}
        content = _normalize_manual_payload(str(body.get("content") or ""))
        try:
            path = _safe_manual_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            backup = None
            if path.exists():
                backup = path.with_name(path.name + ".bak-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
                shutil.copy2(path, backup)
            path.write_text(content, encoding="utf-8")
            return jsonify({"ok": True, "path": str(path), "backup": str(backup) if backup else None, "content": content})
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc)}), 500

    return bp
