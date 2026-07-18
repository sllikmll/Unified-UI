"""Mihomo Clash API integration for the Xkeen UI panel.

This blueprint exposes a small safe subset of Mihomo's external-controller API
through the authenticated Xkeen UI origin. It lets users manage runtime
selectors from :8088 without opening the standalone dashboard on :9090.
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import shutil
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
