#!/usr/bin/env python3
"""Unified UI Native desktop app.

A real Qt Widgets application for Mihomo/Unified UI desktop usage.
No QWebEngine, no embedded Flask panel, no local web UI server inside the window.
The app talks directly to Mihomo's external-controller API and manages local
runtime files itself.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import gzip
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

MIHOMO_VERSION = "1.19.29"
APP_NAME = "Unified UI Native"
DEFAULT_CONTROLLER_PORT = int(os.environ.get("MIHOMO_CONTROLLER_PORT", "19190"))
DEFAULT_MIXED_PORT = int(os.environ.get("MIHOMO_MIXED_PORT", "17990"))
DEFAULT_DNS_PORT = int(os.environ.get("MIHOMO_DNS_PORT", "15354"))

REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_UI_DIR = REPO_ROOT / "unified-ui"
if WEB_UI_DIR.exists() and str(WEB_UI_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_UI_DIR))

try:
    from services.mihomo_generator_proxies import ensure_leading_dash_for_yaml_block
    from services.mihomo_proxy_parsers import (
        ProxyParseResult,
        parse_openvpn,
        parse_proxy_uri,
        parse_tailscale,
        parse_wireguard,
    )
except Exception as exc:  # pragma: no cover - surfaced in GUI diagnostics
    ProxyParseResult = Any  # type: ignore
    _WEB_PARSER_IMPORT_ERROR = exc
else:
    _WEB_PARSER_IMPORT_ERROR = None

DARK_QSS = """
QMainWindow, QWidget { background: #07111f; color: #e8f0ff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
QTabWidget::pane { border: 1px solid #1f3454; border-radius: 10px; top: -1px; }
QTabBar::tab { background: #101d31; color: #b9c7df; border: 1px solid #203857; padding: 9px 14px; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 4px; }
QTabBar::tab:selected { background: #1d4ed8; color: white; border-color: #3b82f6; }
QPushButton { background: #132238; color: #e8f0ff; border: 1px solid #2b4264; border-radius: 8px; padding: 8px 12px; }
QPushButton:hover { background: #1b3152; }
QPushButton:pressed { background: #0f1d31; }
QPushButton#danger { border-color: #7f1d1d; background: #3b1116; color: #fecaca; }
QPushButton#primary { border-color: #2563eb; background: #1d4ed8; color: white; }
QLabel#title { font-size: 22px; font-weight: 800; color: #f8fbff; }
QLabel#muted { color: #93a4bf; }
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox { background: #0b1628; color: #e8f0ff; border: 1px solid #263d5e; border-radius: 8px; padding: 7px; selection-background-color: #2563eb; }
QTableWidget { background: #0b1628; alternate-background-color: #0f1d31; gridline-color: #203857; border: 1px solid #203857; border-radius: 10px; }
QHeaderView::section { background: #132238; color: #d8e4f8; border: 0; border-right: 1px solid #203857; padding: 8px; font-weight: 700; }
QGroupBox { border: 1px solid #203857; border-radius: 10px; margin-top: 12px; padding: 12px; font-weight: 700; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #d8e4f8; }
QStatusBar { background: #0b1628; color: #93a4bf; }
"""


def app_support_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Unified UI Native"
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", str(Path.home()))) / "Unified UI Native"
    return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))) / "unified-ui-native"


def mihomo_asset() -> tuple[str, str]:
    arch = platform.machine().lower()
    if arch in {"x86_64", "amd64"}:
        a = "amd64"
    elif arch in {"arm64", "aarch64"}:
        a = "arm64"
    else:
        raise RuntimeError(f"Unsupported arch: {arch}")
    if sys.platform == "darwin":
        return f"mihomo-darwin-{a}-v{MIHOMO_VERSION}.gz", "mihomo"
    if sys.platform == "win32":
        return f"mihomo-windows-{a}-v{MIHOMO_VERSION}.zip", "mihomo.exe"
    return f"mihomo-linux-{a}-v{MIHOMO_VERSION}.gz", "mihomo"


def ensure_mihomo(runtime: Path) -> Path:
    bin_dir = runtime / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    asset, bin_name = mihomo_asset()
    binary = bin_dir / bin_name
    if binary.exists():
        return binary
    url = f"https://github.com/MetaCubeX/mihomo/releases/download/v{MIHOMO_VERSION}/{asset}"
    tmp = runtime / asset
    print(f"[native] downloading {url}", flush=True)
    urllib.request.urlretrieve(url, tmp)
    if asset.endswith(".gz"):
        with gzip.open(tmp, "rb") as src, binary.open("wb") as dst:
            shutil.copyfileobj(src, dst)
    elif asset.endswith(".zip"):
        with zipfile.ZipFile(tmp) as z:
            member = next((n for n in z.namelist() if n.lower().endswith(".exe")), None)
            if not member:
                raise RuntimeError("mihomo.exe not found in archive")
            with z.open(member) as src, binary.open("wb") as dst:
                shutil.copyfileobj(src, dst)
    else:
        raise RuntimeError(f"Unsupported asset format: {asset}")
    tmp.unlink(missing_ok=True)
    if sys.platform != "win32":
        binary.chmod(0o755)
    return binary


def ensure_config(runtime: Path) -> Path:
    mihomo_dir = runtime / "mihomo"
    rules_dir = mihomo_dir / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    manual = rules_dir / "manual-proxy.yaml"
    if not manual.exists():
        manual.write_text("payload: []\n", encoding="utf-8")
    cfg = mihomo_dir / "config.yaml"
    if cfg.exists():
        return cfg
    cfg.write_text(f"""mixed-port: {DEFAULT_MIXED_PORT}
allow-lan: true
bind-address: 127.0.0.1
mode: rule
log-level: info
ipv6: false
external-controller: 127.0.0.1:{DEFAULT_CONTROLLER_PORT}
secret: ''
profile:
  store-selected: true
  store-fake-ip: false
unified-delay: true
tcp-concurrent: true
dns:
  enable: true
  listen: 127.0.0.1:{DEFAULT_DNS_PORT}
  ipv6: false
  enhanced-mode: fake-ip
  fake-ip-range: 198.18.0.1/16
  default-nameserver: [1.1.1.1, 8.8.8.8]
  nameserver: [https://1.1.1.1/dns-query, https://8.8.8.8/dns-query]
proxies: []
proxy-groups:
  - name: Маршрутизация
    type: select
    proxies: [DIRECT]
  - name: Ручной список
    type: select
    proxies: [DIRECT, Маршрутизация]
  - name: YouTube
    type: select
    proxies: [DIRECT, Маршрутизация]
  - name: Telegram
    type: select
    proxies: [DIRECT, Маршрутизация]
  - name: GitHub
    type: select
    proxies: [DIRECT, Маршрутизация]
  - name: AI
    type: select
    proxies: [DIRECT, Маршрутизация]
  - name: Остальное
    type: select
    proxies: [DIRECT, Маршрутизация]
rule-providers:
  manual-proxy:
    type: file
    behavior: classical
    format: yaml
    path: {manual.as_posix()}
rules:
  - RULE-SET,manual-proxy,Ручной список
  - DOMAIN-SUFFIX,ru,DIRECT
  - DOMAIN-SUFFIX,su,DIRECT
  - DOMAIN-SUFFIX,рф,DIRECT
  - DOMAIN-SUFFIX,youtube.com,YouTube
  - DOMAIN-SUFFIX,googlevideo.com,YouTube
  - DOMAIN-SUFFIX,telegram.org,Telegram
  - DOMAIN-SUFFIX,t.me,Telegram
  - DOMAIN-SUFFIX,github.com,GitHub
  - DOMAIN-SUFFIX,openai.com,AI
  - DOMAIN-SUFFIX,chatgpt.com,AI
  - MATCH,Остальное
""", encoding="utf-8")
    return cfg


@dataclass
class ImportResult:
    name: str
    yaml: str
    kind: str
    source: str = ""


class NativeConfigManager:
    """Local config/import/apply layer for the native desktop app."""

    def __init__(self, runtime: "MihomoRuntime") -> None:
        self.runtime = runtime

    @property
    def config_path(self) -> Path:
        return self.runtime.config_path

    @property
    def backups_dir(self) -> Path:
        return self.runtime.runtime / "backups"

    @property
    def subscriptions_path(self) -> Path:
        return self.runtime.runtime / "subscriptions.json"

    def read_config(self) -> str:
        ensure_config(self.runtime.runtime)
        return self.config_path.read_text(encoding="utf-8")

    def validate_text(self, text: str) -> tuple[bool, str]:
        try:
            parsed = yaml.safe_load(text) or {}
            if not isinstance(parsed, dict):
                return False, "config.yaml должен быть YAML-объектом"
            if "proxies" not in parsed:
                return False, "В config.yaml нет секции proxies"
            if "proxy-groups" not in parsed:
                return False, "В config.yaml нет секции proxy-groups"
        except Exception as exc:
            return False, f"YAML parse error: {exc}"
        try:
            mihomo = ensure_mihomo(self.runtime.runtime)
            cfg_dir = self.config_path.parent
            cfg_dir.mkdir(parents=True, exist_ok=True)
            test_cfg = cfg_dir / ".unified-ui-native-test-config.yaml"
            test_cfg.write_text(text, encoding="utf-8")
            try:
                result = subprocess.run(
                    [str(mihomo), "-t", "-d", str(cfg_dir), "-f", str(test_cfg)],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=30,
                    **self.runtime._subprocess_window_kwargs(),
                )
            finally:
                test_cfg.unlink(missing_ok=True)
            output = (result.stdout or "") + ("\n" if result.stdout and result.stderr else "") + (result.stderr or "")
            if result.returncode != 0:
                return False, output.strip() or f"mihomo -t failed: {result.returncode}"
            return True, output.strip() or "OK"
        except Exception as exc:
            return False, f"mihomo validation error: {exc}"

    def backup_current(self) -> Path:
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        digest = hashlib.sha1(self.read_config().encode("utf-8", errors="ignore")).hexdigest()[:8]
        dst = self.backups_dir / f"config-{stamp}-{digest}.yaml"
        shutil.copy2(self.config_path, dst)
        return dst

    def save_text(self, text: str, *, validate: bool = True) -> tuple[Path | None, str]:
        if validate:
            ok, msg = self.validate_text(text)
            if not ok:
                raise RuntimeError(msg)
        backup = self.backup_current() if self.config_path.exists() else None
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")
        return backup, "config.yaml сохранён"

    def save_and_restart(self, text: str) -> tuple[Path | None, str]:
        backup, msg = self.save_text(text, validate=True)
        self.runtime.restart()
        return backup, msg + "; Mihomo перезапущен"

    def _load_yaml_dict(self, text: str) -> dict[str, Any]:
        data = yaml.safe_load(text) or {}
        if not isinstance(data, dict):
            raise ValueError("config.yaml должен быть YAML-объектом")
        data.setdefault("proxies", [])
        data.setdefault("proxy-groups", [])
        if data.get("proxies") is None:
            data["proxies"] = []
        if not isinstance(data.get("proxies"), list):
            raise ValueError("proxies должен быть списком")
        if not isinstance(data.get("proxy-groups"), list):
            raise ValueError("proxy-groups должен быть списком")
        return data

    def group_names(self) -> list[str]:
        data = self._load_yaml_dict(self.read_config())
        names: list[str] = []
        for group in data.get("proxy-groups") or []:
            if isinstance(group, dict) and str(group.get("name") or "").strip():
                names.append(str(group.get("name")).strip())
        return names

    def _unique_proxy_name(self, data: dict[str, Any], desired: str) -> str:
        existing = {str(p.get("name") or "") for p in data.get("proxies") or [] if isinstance(p, dict)}
        base = desired.strip() or "Imported Proxy"
        if base not in existing:
            return base
        for i in range(2, 1000):
            candidate = f"{base} {i}"
            if candidate not in existing:
                return candidate
        raise RuntimeError("Не удалось подобрать уникальное имя прокси")

    def parse_import(self, text: str, *, name: str = "", kind: str = "auto") -> list[ImportResult]:
        raw = str(text or "").strip()
        if not raw:
            raise ValueError("Пустой импорт")
        kind_l = (kind or "auto").strip().lower()
        if _WEB_PARSER_IMPORT_ERROR is not None:
            raise RuntimeError(f"web-парсеры недоступны: {_WEB_PARSER_IMPORT_ERROR}")

        # Multi-line URI subscription pasted directly.
        uri_lines = [line.strip() for line in raw.splitlines() if "://" in line and not line.strip().startswith("#")]
        if kind_l in {"auto", "uri", "link"} and uri_lines and len(uri_lines) > 1:
            return [self._parse_single_uri(line, name if len(uri_lines) == 1 else "") for line in uri_lines]

        if kind_l in {"auto", "uri", "link"} and "://" in raw.splitlines()[0]:
            return [self._parse_single_uri(raw, name)]

        if kind_l in {"auto", "wireguard", "awg", "amneziawg"} and "[Interface]" in raw and "[Peer]" in raw:
            res = parse_wireguard(raw, custom_name=name or None)
            return [ImportResult(name=res.name, yaml=res.yaml, kind="wireguard", source="wireguard-conf")]

        if kind_l in {"auto", "openvpn"} and ("client" in raw.lower() and "remote " in raw.lower()):
            res = parse_openvpn(raw, custom_name=name or None)
            return [ImportResult(name=res.name, yaml=res.yaml, kind="openvpn", source="openvpn-conf")]

        if kind_l in {"auto", "tailscale"} and ("auth-key" in raw or "accept-routes" in raw):
            res = parse_tailscale(raw, custom_name=name or None)
            return [ImportResult(name=res.name, yaml=res.yaml, kind="tailscale", source="tailscale-settings")]

        # YAML proxy block or full Mihomo config.
        data = yaml.safe_load(raw)
        if isinstance(data, dict) and isinstance(data.get("proxies"), list):
            imports = []
            for item in data["proxies"]:
                if isinstance(item, dict) and item.get("name"):
                    imports.append(ImportResult(name=str(item["name"]), yaml=yaml.safe_dump([item], allow_unicode=True, sort_keys=False), kind=str(item.get("type") or "yaml"), source="mihomo-yaml"))
            if imports:
                return imports
        if isinstance(data, list):
            imports = []
            for item in data:
                if isinstance(item, dict) and item.get("name"):
                    imports.append(ImportResult(name=str(item["name"]), yaml=yaml.safe_dump([item], allow_unicode=True, sort_keys=False), kind=str(item.get("type") or "yaml"), source="proxy-yaml"))
            if imports:
                return imports
        if isinstance(data, dict) and data.get("name"):
            return [ImportResult(name=str(data["name"]), yaml=yaml.safe_dump([data], allow_unicode=True, sort_keys=False), kind=str(data.get("type") or "yaml"), source="proxy-yaml")]
        raise ValueError("Не понял формат. Поддерживаются URI, WG/AWG .conf, OpenVPN, Tailscale, proxy YAML и полный Mihomo YAML.")

    def _parse_single_uri(self, text: str, name: str = "") -> ImportResult:
        line = text.strip()
        # Some subscriptions are base64 with URI lines inside.
        if "://" not in line:
            try:
                decoded = base64.b64decode(line + "=" * (-len(line) % 4)).decode("utf-8", errors="ignore")
                line = next((x.strip() for x in decoded.splitlines() if "://" in x), line)
            except Exception:
                pass
        res = parse_proxy_uri(line, custom_name=name or None)
        return ImportResult(name=res.name, yaml=res.yaml, kind=line.split(":", 1)[0].lower(), source="uri")

    def apply_imports(self, imports: list[ImportResult], groups: list[str] | None = None, *, restart: bool = True) -> tuple[list[str], Path | None, str]:
        if not imports:
            raise ValueError("Нет прокси для импорта")
        data = self._load_yaml_dict(self.read_config())
        group_names = self.group_names()
        target_groups = [g for g in (groups or []) if g]
        if not target_groups:
            target_groups = [group_names[0]] if group_names else []
        added: list[str] = []
        for imp in imports:
            block = ensure_leading_dash_for_yaml_block(imp.yaml)
            parsed = yaml.safe_load(block)
            if not isinstance(parsed, list) or not parsed or not isinstance(parsed[0], dict):
                raise ValueError(f"Импорт {imp.name}: парсер вернул невалидный YAML")
            proxy = parsed[0]
            proxy["name"] = self._unique_proxy_name(data, str(proxy.get("name") or imp.name))
            data["proxies"].append(proxy)
            added.append(str(proxy["name"]))
            for group in data.get("proxy-groups") or []:
                if not isinstance(group, dict):
                    continue
                gname = str(group.get("name") or "").strip()
                if target_groups and gname not in target_groups:
                    continue
                proxies = group.get("proxies")
                if proxies is None:
                    proxies = []
                    group["proxies"] = proxies
                if isinstance(proxies, list) and proxy["name"] not in proxies:
                    proxies.append(proxy["name"])
        new_text = yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=140)
        backup, msg = self.save_text(new_text, validate=True)
        if restart:
            self.runtime.restart()
            msg += "; Mihomo перезапущен"
        return added, backup, msg

    def add_subscription_provider(self, url: str, name: str = "subscription_1", interval: int = 3600, *, restart: bool = True) -> tuple[Path | None, str]:
        url = str(url or "").strip()
        name = str(name or "subscription_1").strip()
        if not url.startswith(("http://", "https://")):
            raise ValueError("Subscription URL должен начинаться с http:// или https://")
        data = self._load_yaml_dict(self.read_config())
        providers = data.get("proxy-providers")
        if not isinstance(providers, dict):
            providers = {}
            data["proxy-providers"] = providers
        providers[name] = {
            "type": "http",
            "url": url,
            "interval": int(interval),
            "path": f"./providers/{name}.yaml",
            "health-check": {"enable": True, "url": "https://www.gstatic.com/generate_204", "interval": 300},
        }
        groups = data.get("proxy-groups") or []
        for group in groups:
            if isinstance(group, dict) and str(group.get("type") or "").lower() in {"select", "url-test", "fallback", "load-balance"}:
                use = group.get("use")
                if use is None:
                    use = []
                    group["use"] = use
                if isinstance(use, list) and name not in use:
                    use.append(name)
        new_text = yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=140)
        backup, msg = self.save_text(new_text, validate=True)
        if restart:
            self.runtime.restart()
            msg += "; Mihomo перезапущен"
        return backup, f"provider {name} добавлен; {msg}"


@dataclass
class MihomoRuntime:
    runtime: Path
    controller: str
    proc: subprocess.Popen | None = None

    @classmethod
    def create(cls) -> "MihomoRuntime":
        runtime = app_support_dir() / "runtime"
        runtime.mkdir(parents=True, exist_ok=True)
        return cls(runtime=runtime, controller=f"http://127.0.0.1:{DEFAULT_CONTROLLER_PORT}")

    @property
    def config_path(self) -> Path:
        return self.runtime / "mihomo" / "config.yaml"

    @property
    def manual_rules_path(self) -> Path:
        return self.runtime / "mihomo" / "rules" / "manual-proxy.yaml"

    def _subprocess_window_kwargs(self) -> dict[str, Any]:
        """Hide helper console windows on Windows builds.

        PyInstaller --windowed removes our app console, but child console
        programs can still spawn their own black window unless CREATE_NO_WINDOW
        is set. Mihomo is a console binary on Windows, so this is mandatory for
        a real desktop app.
        """
        if sys.platform != "win32":
            return {}
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return {
            "startupinfo": startupinfo,
            "creationflags": subprocess.CREATE_NO_WINDOW,
        }

    def start(self) -> None:
        mihomo = ensure_mihomo(self.runtime)
        cfg = ensure_config(self.runtime)
        logs = self.runtime / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        popen_kwargs = self._subprocess_window_kwargs()
        test = subprocess.run(
            [str(mihomo), "-t", "-d", str(cfg.parent), "-f", str(cfg)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **popen_kwargs,
        )
        if test.returncode != 0:
            raise RuntimeError(f"Mihomo config invalid\nSTDOUT:\n{test.stdout}\nSTDERR:\n{test.stderr}")
        log_file = (logs / "mihomo-native.log").open("ab")
        self.proc = subprocess.Popen(
            [str(mihomo), "-d", str(cfg.parent), "-f", str(cfg)],
            stdout=log_file,
            stderr=log_file,
            **popen_kwargs,
        )
        deadline = time.time() + 35
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError(f"Mihomo exited during startup with code {self.proc.returncode}; see {logs / 'mihomo-native.log'}")
            try:
                self.get("/version")
                return
            except Exception:
                time.sleep(0.35)
        raise RuntimeError(f"Mihomo controller did not become ready; see {logs / 'mihomo-native.log'}")

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.proc = None

    def restart(self) -> None:
        self.stop()
        time.sleep(0.4)
        self.start()

    def _request(self, method: str, path: str, body: bytes | None = None) -> Any:
        url = self.controller + path
        req = urllib.request.Request(url, data=body, method=method)
        if body is not None:
            req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=8) as r:
            data = r.read()
        if not data:
            return None
        return json.loads(data.decode("utf-8"))

    def get(self, path: str) -> Any:
        return self._request("GET", path)

    def put_json(self, path: str, payload: dict[str, Any]) -> Any:
        return self._request("PUT", path, json.dumps(payload).encode("utf-8"))

    def delete(self, path: str) -> Any:
        return self._request("DELETE", path)

    def version(self) -> str:
        data = self.get("/version")
        if isinstance(data, dict):
            return data.get("version") or data.get("meta") or json.dumps(data, ensure_ascii=False)
        return str(data)

    def proxies(self) -> dict[str, Any]:
        data = self.get("/proxies")
        return data.get("proxies", {}) if isinstance(data, dict) else {}

    def connections(self) -> list[dict[str, Any]]:
        data = self.get("/connections")
        if not isinstance(data, dict):
            return []
        connections = data.get("connections")
        return connections if isinstance(connections, list) else []

    def traffic(self) -> dict[str, Any]:
        # Mihomo's /traffic endpoint is a streaming endpoint. Do not call it
        # through the normal blocking JSON request path or the GUI freezes
        # before the main window is shown. A future version should consume it
        # from a background worker.
        return {}

    def close_connection(self, conn_id: str) -> None:
        self.delete(f"/connections/{urllib.parse.quote(conn_id)}")

    def select_proxy(self, group: str, proxy: str) -> None:
        quoted = urllib.parse.quote(group, safe="")
        self.put_json(f"/proxies/{quoted}", {"name": proxy})

    def delay(self, proxy: str) -> int | None:
        quoted = urllib.parse.quote(proxy, safe="")
        try:
            data = self.get(f"/proxies/{quoted}/delay?timeout=5000&url=https%3A%2F%2Fwww.gstatic.com%2Fgenerate_204")
            return int(data.get("delay")) if isinstance(data, dict) and data.get("delay") is not None else None
        except Exception:
            return None


def human_bytes(value: Any) -> str:
    try:
        n = float(value)
    except Exception:
        return "—"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while n >= 1024 and i < len(units) - 1:
        n /= 1024
        i += 1
    return f"{n:.1f} {units[i]}"


def run_gui(runtime: MihomoRuntime, gui_smoke_seconds: float | None = None) -> int:
    from PySide6.QtCore import QTimer, Qt
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QFileDialog,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QPlainTextEdit,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )

    cfg_mgr = NativeConfigManager(runtime)

    class SelectorsTab(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self.layout = QVBoxLayout(self)
            header = QHBoxLayout()
            self.mode = QComboBox()
            self.mode.addItems(["Списки", "Плитки позже"])
            refresh = QPushButton("Обновить селекторы")
            refresh.clicked.connect(self.refresh)
            ping = QPushButton("Обновить все пинги")
            ping.clicked.connect(self.ping_all)
            header.addWidget(QLabel("Вид:"))
            header.addWidget(self.mode)
            header.addStretch(1)
            header.addWidget(ping)
            header.addWidget(refresh)
            self.layout.addLayout(header)
            self.groups_box = QVBoxLayout()
            self.layout.addLayout(self.groups_box)
            self.layout.addStretch(1)

        def clear_groups(self) -> None:
            while self.groups_box.count():
                item = self.groups_box.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

        def refresh(self) -> None:
            self.clear_groups()
            proxies = runtime.proxies()
            for name, data in proxies.items():
                if data.get("type") not in {"Selector", "URLTest", "Fallback", "LoadBalance"}:
                    continue
                group = QGroupBox(name)
                row = QHBoxLayout(group)
                current = QLabel(f"Сейчас: {data.get('now', '—')}")
                current.setObjectName("muted")
                combo = QComboBox()
                all_names = data.get("all") or []
                combo.addItems(all_names)
                now = data.get("now")
                if now in all_names:
                    combo.setCurrentText(now)
                apply = QPushButton("Выбрать")
                apply.setObjectName("primary")
                apply.clicked.connect(lambda _=False, g=name, c=combo: self.select(g, c.currentText()))
                row.addWidget(current)
                row.addWidget(combo, 1)
                row.addWidget(apply)
                self.groups_box.addWidget(group)

        def select(self, group: str, proxy: str) -> None:
            try:
                runtime.select_proxy(group, proxy)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, APP_NAME, f"Не удалось выбрать proxy:\n{e}")

        def ping_all(self) -> None:
            proxies = runtime.proxies()
            for name, data in proxies.items():
                if data.get("type") not in {"Direct", "Reject", "Selector", "URLTest", "Fallback", "LoadBalance"}:
                    delay = runtime.delay(name)
                    if delay is not None:
                        data["history"] = [{"delay": delay}]
            self.refresh()

    class ConnectionsTab(QWidget):
        def __init__(self) -> None:
            super().__init__()
            layout = QVBoxLayout(self)
            top = QHBoxLayout()
            self.filter = QLineEdit()
            self.filter.setPlaceholderText("Фильтр по host/source/destination/proxy")
            self.filter.textChanged.connect(self.refresh)
            refresh = QPushButton("Обновить")
            refresh.clicked.connect(self.refresh)
            close = QPushButton("Разорвать выбранное")
            close.setObjectName("danger")
            close.clicked.connect(self.close_selected)
            top.addWidget(self.filter, 1)
            top.addWidget(close)
            top.addWidget(refresh)
            layout.addLayout(top)
            self.table = QTableWidget(0, 7)
            self.table.setHorizontalHeaderLabels(["ID", "Источник", "Назначение", "Host", "Proxy", "Upload", "Download"])
            self.table.setAlternatingRowColors(True)
            self.table.setSelectionBehavior(QTableWidget.SelectRows)
            layout.addWidget(self.table, 1)

        def refresh(self) -> None:
            flt = self.filter.text().strip().lower()
            rows = []
            for c in runtime.connections():
                meta = c.get("metadata") or {}
                chains = c.get("chains") or []
                row = [
                    str(c.get("id", "")),
                    str(c.get("metadata", {}).get("sourceIP") or c.get("metadata", {}).get("sourceIPAddr") or ""),
                    str(meta.get("destinationIP") or meta.get("dstIP") or ""),
                    str(meta.get("host") or meta.get("destinationHost") or ""),
                    " → ".join(map(str, chains)),
                    human_bytes(c.get("upload")),
                    human_bytes(c.get("download")),
                ]
                if flt and flt not in " ".join(row).lower():
                    continue
                rows.append(row)
            self.table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                for col, value in enumerate(row):
                    self.table.setItem(r, col, QTableWidgetItem(value))
            self.table.resizeColumnsToContents()

        def close_selected(self) -> None:
            row = self.table.currentRow()
            if row < 0:
                return
            conn_id = self.table.item(row, 0).text()
            try:
                runtime.close_connection(conn_id)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, APP_NAME, f"Не удалось разорвать соединение:\n{e}")

    class ManualTab(QWidget):
        def __init__(self) -> None:
            super().__init__()
            layout = QVBoxLayout(self)
            self.editor = QPlainTextEdit()
            buttons = QHBoxLayout()
            save = QPushButton("Сохранить")
            save.setObjectName("primary")
            save.clicked.connect(self.save)
            reload_btn = QPushButton("Перечитать")
            reload_btn.clicked.connect(self.load)
            buttons.addStretch(1)
            buttons.addWidget(reload_btn)
            buttons.addWidget(save)
            layout.addWidget(QLabel(str(runtime.manual_rules_path)))
            layout.addWidget(self.editor, 1)
            layout.addLayout(buttons)
            self.load()

        def load(self) -> None:
            runtime.manual_rules_path.parent.mkdir(parents=True, exist_ok=True)
            if not runtime.manual_rules_path.exists():
                runtime.manual_rules_path.write_text("payload: []\n", encoding="utf-8")
            self.editor.setPlainText(runtime.manual_rules_path.read_text(encoding="utf-8"))

        def save(self) -> None:
            runtime.manual_rules_path.write_text(self.editor.toPlainText(), encoding="utf-8")
            QMessageBox.information(self, APP_NAME, "Ручной список сохранён. Для правил обычно достаточно перезапуска Mihomo.")

    class ConfigTab(QWidget):
        def __init__(self) -> None:
            super().__init__()
            layout = QVBoxLayout(self)
            top = QHBoxLayout()
            open_btn = QPushButton("Открыть файл…")
            open_btn.clicked.connect(self.open_file)
            validate_btn = QPushButton("Проверить")
            validate_btn.clicked.connect(self.validate)
            save = QPushButton("Сохранить без restart")
            save.clicked.connect(self.save_only)
            apply = QPushButton("Применить + restart")
            apply.setObjectName("primary")
            apply.clicked.connect(self.apply_restart)
            reload_btn = QPushButton("Перечитать active")
            reload_btn.clicked.connect(self.load)
            top.addWidget(open_btn)
            top.addWidget(validate_btn)
            top.addStretch(1)
            top.addWidget(reload_btn)
            top.addWidget(save)
            top.addWidget(apply)
            self.path_label = QLabel(str(runtime.config_path))
            self.path_label.setObjectName("muted")
            self.editor = QPlainTextEdit()
            self.status = QLabel("Готово")
            self.status.setObjectName("muted")
            layout.addWidget(self.path_label)
            layout.addLayout(top)
            layout.addWidget(self.editor, 1)
            layout.addWidget(self.status)
            self.load()

        def load(self) -> None:
            self.editor.setPlainText(cfg_mgr.read_config())
            self.status.setText(f"Загружен active config: {runtime.config_path}")

        def open_file(self) -> None:
            path, _ = QFileDialog.getOpenFileName(self, "Открыть Mihomo config", str(Path.home()), "YAML (*.yaml *.yml);;All files (*)")
            if not path:
                return
            self.editor.setPlainText(Path(path).read_text(encoding="utf-8"))
            self.status.setText(f"Открыт файл: {path}")

        def validate(self) -> None:
            ok, msg = cfg_mgr.validate_text(self.editor.toPlainText())
            self.status.setText(("OK: " if ok else "Ошибка: ") + msg[:500])
            if ok:
                QMessageBox.information(self, APP_NAME, "Config валиден. Mihomo принял `-t`.")
            else:
                QMessageBox.critical(self, APP_NAME, f"Config невалиден:\n\n{msg[:4000]}")

        def save_only(self) -> None:
            try:
                backup, msg = cfg_mgr.save_text(self.editor.toPlainText(), validate=True)
                self.status.setText(f"{msg}. Backup: {backup or 'нет'}")
                QMessageBox.information(self, APP_NAME, f"{msg}\nBackup: {backup or 'нет'}")
            except Exception as e:
                QMessageBox.critical(self, APP_NAME, f"Не удалось сохранить config:\n{e}")

        def apply_restart(self) -> None:
            try:
                backup, msg = cfg_mgr.save_and_restart(self.editor.toPlainText())
                self.status.setText(f"{msg}. Backup: {backup or 'нет'}")
                QMessageBox.information(self, APP_NAME, f"{msg}\nBackup: {backup or 'нет'}")
            except Exception as e:
                QMessageBox.critical(self, APP_NAME, f"Не удалось применить config:\n{e}")

    class ImportTab(QWidget):
        def __init__(self) -> None:
            super().__init__()
            layout = QVBoxLayout(self)
            title = QLabel("Импорт прокси / подписок")
            title.setObjectName("title")
            form = QHBoxLayout()
            self.kind = QComboBox()
            self.kind.addItems(["auto", "uri", "wireguard", "openvpn", "tailscale", "yaml", "subscription"])
            self.name = QLineEdit()
            self.name.setPlaceholderText("Имя прокси/provider (опционально)")
            self.group = QComboBox()
            self.group.setEditable(True)
            self.restart = QCheckBox("Применить и restart Mihomo")
            self.restart.setChecked(True)
            form.addWidget(QLabel("Формат:"))
            form.addWidget(self.kind)
            form.addWidget(QLabel("Имя:"))
            form.addWidget(self.name, 1)
            form.addWidget(QLabel("Группа:"))
            form.addWidget(self.group, 1)
            form.addWidget(self.restart)
            buttons = QHBoxLayout()
            file_btn = QPushButton("Загрузить из файла…")
            file_btn.clicked.connect(self.load_file)
            preview_btn = QPushButton("Распознать")
            preview_btn.clicked.connect(self.preview)
            apply_btn = QPushButton("Импортировать")
            apply_btn.setObjectName("primary")
            apply_btn.clicked.connect(self.apply)
            buttons.addWidget(file_btn)
            buttons.addStretch(1)
            buttons.addWidget(preview_btn)
            buttons.addWidget(apply_btn)
            self.input = QPlainTextEdit()
            self.input.setPlaceholderText("Вставь vless:// / vmess:// / trojan:// / hysteria2://, WireGuard/AmneziaWG .conf, OpenVPN .ovpn, YAML proxy block/full config или subscription URL")
            self.preview_box = QPlainTextEdit()
            self.preview_box.setReadOnly(True)
            self.preview_box.setPlaceholderText("Здесь появится распознанный proxy YAML")
            self.status = QLabel("Поддержка: VLESS, VMess, Trojan, SS, Hysteria2, WireGuard/AmneziaWG, OpenVPN, Tailscale, YAML, subscription provider")
            self.status.setObjectName("muted")
            layout.addWidget(title)
            layout.addLayout(form)
            layout.addWidget(QLabel("Ввод:"))
            layout.addWidget(self.input, 2)
            layout.addLayout(buttons)
            layout.addWidget(QLabel("Preview:"))
            layout.addWidget(self.preview_box, 1)
            layout.addWidget(self.status)
            self.refresh_groups()

        def refresh_groups(self) -> None:
            current = self.group.currentText()
            self.group.clear()
            names = cfg_mgr.group_names()
            self.group.addItems(names)
            if current:
                self.group.setCurrentText(current)
            elif names:
                self.group.setCurrentText(names[0])

        def load_file(self) -> None:
            path, _ = QFileDialog.getOpenFileName(self, "Импортировать файл", str(Path.home()), "Configs (*.conf *.ovpn *.yaml *.yml *.txt);;All files (*)")
            if not path:
                return
            self.input.setPlainText(Path(path).read_text(encoding="utf-8", errors="ignore"))
            if not self.name.text().strip():
                self.name.setText(Path(path).stem)
            self.status.setText(f"Загружен файл: {path}")

        def _parse(self) -> list[ImportResult]:
            kind = self.kind.currentText().strip().lower()
            if kind == "subscription":
                return []
            return cfg_mgr.parse_import(self.input.toPlainText(), name=self.name.text().strip(), kind=kind)

        def preview(self) -> None:
            try:
                if self.kind.currentText().strip().lower() == "subscription":
                    url = self.input.toPlainText().strip()
                    name = self.name.text().strip() or "subscription_1"
                    self.preview_box.setPlainText(f"proxy-providers:\n  {name}:\n    type: http\n    url: {url}\n    interval: 3600\n")
                    self.status.setText("Subscription provider будет добавлен в proxy-providers и use у selector-групп")
                    return
                imports = self._parse()
                self.preview_box.setPlainText("\n---\n".join(imp.yaml.strip() for imp in imports))
                self.status.setText(f"Распознано прокси: {', '.join(imp.name for imp in imports)}")
            except Exception as e:
                QMessageBox.critical(self, APP_NAME, f"Не удалось распознать импорт:\n{e}")

        def apply(self) -> None:
            try:
                if self.kind.currentText().strip().lower() == "subscription":
                    provider = self.name.text().strip() or "subscription_1"
                    backup, msg = cfg_mgr.add_subscription_provider(self.input.toPlainText().strip(), provider, restart=self.restart.isChecked())
                    self.status.setText(f"{msg}. Backup: {backup or 'нет'}")
                    QMessageBox.information(self, APP_NAME, f"{msg}\nBackup: {backup or 'нет'}")
                    self.refresh_groups()
                    return
                imports = self._parse()
                group_text = self.group.currentText().strip()
                groups = [group_text] if group_text else []
                added, backup, msg = cfg_mgr.apply_imports(imports, groups, restart=self.restart.isChecked())
                self.preview_box.setPlainText("\n---\n".join(imp.yaml.strip() for imp in imports))
                self.status.setText(f"Добавлено: {', '.join(added)}. {msg}. Backup: {backup or 'нет'}")
                QMessageBox.information(self, APP_NAME, f"Добавлено: {', '.join(added)}\n{msg}\nBackup: {backup or 'нет'}")
                self.refresh_groups()
            except Exception as e:
                QMessageBox.critical(self, APP_NAME, f"Импорт не выполнен:\n{e}")

    class LogsTab(QWidget):
        def __init__(self) -> None:
            super().__init__()
            layout = QVBoxLayout(self)
            buttons = QHBoxLayout()
            reload_btn = QPushButton("Обновить логи")
            reload_btn.clicked.connect(self.load)
            buttons.addStretch(1)
            buttons.addWidget(reload_btn)
            self.logs = QPlainTextEdit()
            self.logs.setReadOnly(True)
            layout.addWidget(QLabel(str(runtime.runtime / "logs")))
            layout.addLayout(buttons)
            layout.addWidget(self.logs, 1)
            self.load()

        def load(self) -> None:
            parts = []
            for name in ("native-app.log", "mihomo-native.log"):
                path = runtime.runtime / "logs" / name
                parts.append(f"===== {path} =====")
                if path.exists():
                    text = path.read_text(encoding="utf-8", errors="replace")
                    parts.append("\n".join(text.splitlines()[-250:]))
                else:
                    parts.append("<нет файла>")
            self.logs.setPlainText("\n".join(parts))

    class DashboardTab(QWidget):
        def __init__(self) -> None:
            super().__init__()
            layout = QVBoxLayout(self)
            title = QLabel("Unified UI Native")
            title.setObjectName("title")
            self.version = QLabel("Mihomo: —")
            self.version.setObjectName("muted")
            self.traffic = QLabel("Traffic: —")
            self.traffic.setObjectName("muted")
            layout.addWidget(title)
            layout.addWidget(QLabel("Нативное Qt-приложение: без WebView, без Flask UI, прямой Mihomo API."))
            layout.addWidget(self.version)
            layout.addWidget(self.traffic)
            layout.addStretch(1)

        def refresh(self) -> None:
            self.version.setText(f"Mihomo: {runtime.version()}")
            self.traffic.setText("Traffic: потоковый счётчик будет подключён отдельным фоновым worker'ом")

    class MainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle(APP_NAME)
            self.resize(1320, 860)
            tabs = QTabWidget()
            self.dashboard = DashboardTab()
            self.selectors = SelectorsTab()
            self.connections = ConnectionsTab()
            self.manual = ManualTab()
            self.config = ConfigTab()
            self.imports = ImportTab()
            self.logs = LogsTab()
            tabs.addTab(self.dashboard, "Обзор")
            tabs.addTab(self.selectors, "Селекторы")
            tabs.addTab(self.connections, "Соединения")
            tabs.addTab(self.imports, "Импорт")
            tabs.addTab(self.manual, "Ручной список")
            tabs.addTab(self.config, "Конфиг")
            tabs.addTab(self.logs, "Логи")
            self.setCentralWidget(tabs)
            self.statusBar().showMessage(f"Runtime: {runtime.runtime}")
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.refresh_light)
            self.timer.start(4000)
            self.refresh_all()

        def refresh_light(self) -> None:
            try:
                self.dashboard.refresh()
                self.connections.refresh()
            except Exception as e:
                self.statusBar().showMessage(str(e))

        def refresh_all(self) -> None:
            self.dashboard.refresh()
            self.selectors.refresh()
            self.connections.refresh()

        def closeEvent(self, event) -> None:  # type: ignore[override]
            log_native_event("main window closeEvent")
            runtime.stop()
            event.accept()

    import threading
    import traceback

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyleSheet(DARK_QSS)
    app.setQuitOnLastWindowClosed(False)
    app.aboutToQuit.connect(lambda: log_native_event("app aboutToQuit"))

    startup = QWidget()
    startup.setWindowTitle(APP_NAME)
    startup.resize(520, 180)
    startup_layout = QVBoxLayout(startup)
    startup_title = QLabel("Unified UI Native")
    startup_title.setObjectName("title")
    startup_status = QLabel("Запускаю Mihomo runtime…")
    startup_status.setObjectName("muted")
    startup_layout.addWidget(startup_title)
    startup_layout.addWidget(QLabel("Окно приложения уже живое. Если Mihomo тупит — теперь это будет видно, а не чёрная магия без окна."))
    startup_layout.addWidget(startup_status)
    startup_layout.addStretch(1)
    startup.show()

    result: dict[str, Any] = {}
    holder: dict[str, Any] = {"window": None}

    def log_native_event(text: str) -> Path:
        log_dir = runtime.runtime / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        path = log_dir / "native-app.log"
        with path.open("a", encoding="utf-8") as f:
            f.write("\n=== Unified UI Native ===\n")
            f.write(text)
            f.write("\n")
        return path

    def log_native_error(text: str) -> Path:
        return log_native_event("STARTUP ERROR\n" + text)

    startup_log_path = log_native_event(f"startup begin; runtime={runtime.runtime}; controller={runtime.controller}")

    def excepthook(exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        text = "".join(traceback.format_exception(exc_type, exc, tb))
        log_native_error("UNHANDLED EXCEPTION\n" + text)
        try:
            QMessageBox.critical(startup, APP_NAME, f"Необработанная ошибка.\n\nЛог: {startup_log_path}\n\n{text[-2500:]}")
        except Exception:
            pass

    sys.excepthook = excepthook

    def start_runtime_in_background() -> None:
        try:
            log_native_event("mihomo runtime start requested")
            runtime.start()
            log_native_event("mihomo runtime started successfully")
            result["ok"] = True
        except Exception:
            tb = traceback.format_exc()
            log_path = log_native_error(tb)
            result["error"] = tb
            result["log_path"] = str(log_path)

    threading.Thread(target=start_runtime_in_background, daemon=True).start()

    def poll_startup() -> None:
        if not result:
            return
        startup.timer.stop()  # type: ignore[attr-defined]
        if result.get("ok"):
            try:
                startup_status.setText("Mihomo готов. Открываю главное окно…")
                log_native_event("creating main window")
                win = MainWindow()
                holder["window"] = win
                win.show()
                win.raise_()
                win.activateWindow()
                app.setQuitOnLastWindowClosed(True)
                log_native_event("main window shown")
                startup.close()
                if gui_smoke_seconds is not None:
                    QTimer.singleShot(int(gui_smoke_seconds * 1000), app.quit)
            except Exception:
                tb = traceback.format_exc()
                log_path = log_native_error("MAIN WINDOW ERROR\n" + tb)
                startup_status.setText(f"Ошибка главного окна. Лог: {log_path}")
                QMessageBox.critical(startup, APP_NAME, f"Mihomo запущен, но главное окно не открылось.\n\nЛог: {log_path}\n\n{tb[-2500:]}")
            return
        msg = result.get("error", "Unknown startup error")
        log_path = result.get("log_path", str(runtime.runtime / "logs" / "native-app.log"))
        startup_status.setText(f"Ошибка запуска. Лог: {log_path}")
        QMessageBox.critical(startup, APP_NAME, f"Не удалось запустить Mihomo runtime.\n\nЛог: {log_path}\n\n{msg[-2500:]}")

    startup.timer = QTimer(startup)  # type: ignore[attr-defined]
    startup.timer.timeout.connect(poll_startup)  # type: ignore[attr-defined]
    startup.timer.start(250)  # type: ignore[attr-defined]
    return app.exec()


def run_smoke(runtime: MihomoRuntime) -> int:
    runtime.start()
    try:
        result = {
            "ok": True,
            "controller": runtime.controller,
            "version": runtime.version(),
            "proxy_count": len(runtime.proxies()),
            "connection_count": len(runtime.connections()),
            "config": str(runtime.config_path),
            "manual_rules": str(runtime.manual_rules_path),
            "webview": False,
            "flask_ui": False,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    finally:
        runtime.stop()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--gui-smoke", type=float, default=None, metavar="SECONDS", help="Open the real GUI, keep it alive for N seconds, then exit")
    args = parser.parse_args()
    runtime = MihomoRuntime.create()
    if args.smoke:
        return run_smoke(runtime)
    return run_gui(runtime, gui_smoke_seconds=args.gui_smoke)


if __name__ == "__main__":
    # urllib.parse is only needed at runtime in methods above; import here keeps top-level audit simple.
    import urllib.parse

    raise SystemExit(main())
