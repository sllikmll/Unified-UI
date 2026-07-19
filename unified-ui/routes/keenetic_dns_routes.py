from __future__ import annotations

import ipaddress
import json
import os
import re
import socket
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from flask import Blueprint, jsonify, request

NDMC = os.environ.get("UNIFIED_NDMC_BIN", "/bin/ndmc")
BACKUP_DIR = os.environ.get("UNIFIED_DNS_ROUTES_BACKUP_DIR", "/opt/var/lib/unified-ui/backups/dns-routes")

DOMAIN_RE = re.compile(r"^(?=.{1,253}$)(?:\*\.)?(?:[a-zA-Z0-9_](?:[a-zA-Z0-9_-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}\.?$")
LIST_ID_RE = re.compile(r"^domain-list\d+$")
IFACE_RE = re.compile(r"^[A-Za-z0-9_.:/-]+$")

SERVICE_PRESETS: Dict[str, Dict[str, Any]] = {
    "youtube": {
        "label": "YouTube",
        "domains": [
            "youtube.com", "youtu.be", "ytimg.com", "googlevideo.com", "ggpht.com",
            "youtube-nocookie.com", "youtubei.googleapis.com", "youtubeembeddedplayer.googleapis.com",
            "yt-video-upload.l.google.com", "wide-youtube.l.google.com", "ytimg.l.google.com",
            "jnn-pa.googleapis.com", "yt3.googleusercontent.com", "returnyoutubedislikeapi.com",
        ],
    },
    "telegram": {
        "label": "Telegram",
        "domains": [
            "telegram.org", "telegram.me", "t.me", "telegra.ph", "telegram-cdn.org",
            "cdn-telegram.org", "telesco.pe", "tdesktop.com", "graph.org", "comments.app",
            "fragment.com", "contest.com", "quiz.directory", "tg.dev", "tx.me", "usercontent.dev", "ton.org",
        ],
        "ips": [
            "91.105.192.0/23", "91.108.4.0/22", "91.108.8.0/22", "91.108.12.0/22",
            "91.108.16.0/22", "91.108.20.0/22", "91.108.56.0/22", "149.154.160.0/20",
            "185.76.151.0/24", "149.154.164.0/22", "95.161.64.0/20", "5.28.128.0/17",
        ],
    },
    "meta": {
        "label": "Meta / Instagram / Facebook",
        "domains": [
            "meta.com", "facebook.com", "fb.com", "facebook.net", "fbcdn.net", "fbsbx.com",
            "instagram.com", "cdninstagram.com", "ig.me", "threads.net", "threads.com",
            "whatsapp.com", "whatsapp.net", "whatsapp.biz", "wa.me", "oculus.com",
        ],
        "ips": ["31.13.0.0/16", "57.144.0.0/14", "66.220.0.0/16", "69.63.0.0/16", "69.171.0.0/16", "129.134.0.0/16", "157.240.0.0/16", "163.70.0.0/16", "173.252.0.0/16", "179.60.0.0/16", "185.60.0.0/16"],
    },
    "chatgpt": {
        "label": "ChatGPT / OpenAI",
        "domains": [
            "openai.com", "chatgpt.com", "oaistatic.com", "oaiusercontent.com", "oaidalleapiprodscus.blob.core.windows.net",
            "auth0.openai.com", "platform.openai.com", "api.openai.com",
        ],
    },
    "github": {
        "label": "GitHub",
        "domains": [
            "github.com", "api.github.com", "raw.githubusercontent.com", "githubusercontent.com", "objects.githubusercontent.com",
            "githubassets.com", "github.io", "githubstatus.com",
        ],
    },
    "discord": {
        "label": "Discord",
        "domains": ["discord.com", "discord.gg", "discordapp.com", "discordapp.net", "discordcdn.com", "discord.media"],
    },
    "spotify": {
        "label": "Spotify",
        "domains": ["spotify.com", "scdn.co", "spoti.fi", "spotifycdn.com", "spotifycdn.net", "audio-ak-spotify-com.akamaized.net"],
    },
    "netflix": {
        "label": "Netflix",
        "domains": ["netflix.com", "nflxvideo.net", "nflximg.net", "nflxext.com", "nflxso.net"],
    },
}


@dataclass
class DnsList:
    name: str
    description: str = ""
    items: List[str] = field(default_factory=list)
    interface: str = ""
    route_line: str = ""


def _run_ndmc(command: str, *, timeout: int = 20) -> Tuple[int, str]:
    try:
        cp = subprocess.run([NDMC, "-c", command], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=timeout)
        return cp.returncode, cp.stdout or ""
    except FileNotFoundError:
        return 127, f"ndmc not found: {NDMC}"
    except subprocess.TimeoutExpired as exc:
        return 124, exc.stdout or "timeout"


def _running_config() -> str:
    rc, out = _run_ndmc("show running-config", timeout=35)
    if rc != 0 and not out.strip():
        raise RuntimeError(f"ndmc show running-config failed rc={rc}")
    return out.replace("\r\n", "\n").replace("\r", "\n")


def _parse_dns_lists(text: str) -> List[DnsList]:
    lists: Dict[str, DnsList] = {}
    current: Optional[DnsList] = None
    in_dns_proxy = False
    for raw in text.splitlines():
        line = raw.rstrip()
        m = re.match(r"^object-group\s+fqdn\s+(domain-list\d+)\s*$", line)
        if m:
            current = DnsList(name=m.group(1))
            lists[current.name] = current
            in_dns_proxy = False
            continue
        if line and not line.startswith(" ") and not line.startswith("!"):
            if not line.startswith("dns-proxy"):
                in_dns_proxy = False
            current = None if not m else current
        if current and line.startswith("    description "):
            val = line.strip()[len("description "):].strip()
            current.description = val.strip('"')
            continue
        if current and line.startswith("    include "):
            val = line.strip()[len("include "):].strip()
            current.items.append(val.strip('"'))
            continue
        if line.strip() == "dns-proxy":
            in_dns_proxy = True
            current = None
            continue
        if in_dns_proxy:
            rm = re.match(r"^\s*route\s+object-group\s+(domain-list\d+)\s+(\S+)(.*)$", line)
            if rm:
                name, iface, tail = rm.group(1), rm.group(2), rm.group(3).strip()
                dl = lists.setdefault(name, DnsList(name=name))
                dl.interface = iface
                dl.route_line = f"route object-group {name} {iface} {tail}".strip()
    return [lists[k] for k in sorted(lists.keys(), key=lambda s: int(s.replace("domain-list", "")))]


def _parse_interfaces(text: str) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    current: Optional[Dict[str, str]] = None
    allowed_prefixes = ("Wireguard", "OpenVPN", "PPPoE", "SSTP", "L2TP", "PPTP", "GigabitEthernet", "Bridge")
    for raw in text.splitlines():
        line = raw.rstrip()
        m = re.match(r"^interface\s+(\S+)", line)
        if m:
            name = m.group(1)
            current = {"name": name, "description": ""}
            if name.startswith(allowed_prefixes):
                out.append(current)
            continue
        if current and line.startswith("    description "):
            current["description"] = line.strip()[len("description "):].strip().strip('"')
    # policy-like pseudo choices that NDMS commonly exposes
    seen = {x["name"] for x in out}
    for name in ("PPPoE0", "GigabitEthernet0/Vlan4", "GigabitEthernet1", "Bridge0"):
        if name not in seen:
            out.append({"name": name, "description": ""})
    return out


def _normalize_item(item: str) -> str:
    s = str(item or "").strip().lower().strip(',;')
    if not s:
        return ""
    if s.startswith("*."):
        s = s[2:]
    if s.endswith("."):
        s = s[:-1]
    try:
        if "/" in s:
            return str(ipaddress.ip_network(s, strict=False))
        return str(ipaddress.ip_address(s))
    except Exception:
        pass
    if not DOMAIN_RE.match(s):
        raise ValueError(f"Некорректный домен/IP: {item}")
    return s


def _normalize_items(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for raw in items:
        for part in re.split(r"[\n\r\t ,]+", str(raw or "")):
            if not part.strip():
                continue
            val = _normalize_item(part)
            if val and val not in seen:
                seen.add(val)
                out.append(val)
    return out


def _next_list_name(lists: List[DnsList]) -> str:
    used = {int(x.name.replace("domain-list", "")) for x in lists if LIST_ID_RE.match(x.name)}
    i = 0
    while i in used:
        i += 1
    return f"domain-list{i}"


def _ndmc_config(commands: List[str], *, apply: bool = True) -> Tuple[int, str]:
    output: List[str] = []
    rc_all = 0
    for cmd in commands:
        cmd = str(cmd or "").strip()
        if not cmd or cmd == "exit":
            continue
        rc, out = _run_ndmc(cmd, timeout=25)
        output.append(f"$ ndmc -c {cmd}\n{out}".strip())
        if rc != 0:
            rc_all = rc
            break
        # NDMS often returns rc=0 for semantic errors; keep scanning the text.
        if "error[" in (out or "").lower() and "no such entry" not in (out or "").lower():
            rc_all = 1
            break
    if apply and rc_all == 0:
        rc, out = _run_ndmc("system configuration save", timeout=30)
        output.append(f"$ ndmc -c system configuration save\n{out}".strip())
        if rc != 0:
            rc_all = rc
    return rc_all, "\n\n".join(output)


def _backup_config() -> str:
    os.makedirs(BACKUP_DIR, exist_ok=True)
    path = os.path.join(BACKUP_DIR, f"running-config-dns-routes-{time.strftime('%Y%m%d-%H%M%S')}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(_running_config())
    return path


def _resolve_domains(domains: List[str], dns_server: str = "") -> List[str]:
    # Python stdlib resolver cannot select DNS server; on Keenetic/Entware it follows router DNS.
    # dns_server is kept in the API contract for UI/next implementation with nslookup if needed.
    ips: List[str] = []
    seen = set()
    for d in domains:
        try:
            for family, _, _, _, sockaddr in socket.getaddrinfo(d, None, proto=socket.IPPROTO_TCP):
                ip = sockaddr[0]
                if ":" in ip:
                    continue
                if ip not in seen:
                    seen.add(ip)
                    ips.append(ip)
        except Exception:
            continue
    return ips


def create_keenetic_dns_routes_blueprint() -> Blueprint:
    bp = Blueprint("keenetic_dns_routes", __name__)

    @bp.get("/api/keenetic/dns-routes")
    def get_dns_routes():
        text = _running_config()
        lists = _parse_dns_lists(text)
        return jsonify({
            "ok": True,
            "platform": "keenetic",
            "mode": "dns-routes",
            "lists": [dl.__dict__ for dl in lists],
            "interfaces": _parse_interfaces(text),
            "services": SERVICE_PRESETS,
        })

    @bp.post("/api/keenetic/dns-routes/preview-service")
    def preview_service():
        data = request.get_json(silent=True) or {}
        service = str(data.get("service") or "").strip().lower()
        dns_server = str(data.get("dns_server") or "").strip()
        preset = SERVICE_PRESETS.get(service)
        if not preset:
            return jsonify({"ok": False, "error": "unknown_service"}), 404
        domains = _normalize_items(list(preset.get("domains") or []))
        ips = _normalize_items(list(preset.get("ips") or []))
        resolved = _resolve_domains(domains, dns_server=dns_server)
        items = _normalize_items(domains + ips + resolved)
        return jsonify({"ok": True, "service": service, "label": preset.get("label"), "dns_server": dns_server, "domains": domains, "resolved_ips": resolved, "items": items})

    @bp.post("/api/keenetic/dns-routes/apply")
    def apply_dns_route():
        data = request.get_json(silent=True) or {}
        name = str(data.get("name") or "").strip()
        description = str(data.get("description") or "").strip() or name
        interface = str(data.get("interface") or "").strip()
        items = _normalize_items(data.get("items") or [])
        if not name:
            lists = _parse_dns_lists(_running_config())
            name = _next_list_name(lists)
        if not LIST_ID_RE.match(name):
            return jsonify({"ok": False, "error": "bad_list_name", "message": "Имя списка должно быть domain-listN"}), 400
        if not interface or not IFACE_RE.match(interface):
            return jsonify({"ok": False, "error": "bad_interface", "message": "Выберите корректный интерфейс"}), 400
        if not items:
            return jsonify({"ok": False, "error": "empty_items", "message": "Список пуст"}), 400
        current = {dl.name: dl for dl in _parse_dns_lists(_running_config())}.get(name)
        if current and current.interface and current.interface != interface:
            return jsonify({
                "ok": False,
                "error": "interface_change_not_supported_yet",
                "message": f"Смена интерфейса существующего {name} пока заблокирована безопасностью: сейчас {current.interface}, выбран {interface}. Создайте новый список или поменяйте через NDMS до добавления route removal syntax.",
                "current_interface": current.interface,
                "requested_interface": interface,
            }), 409
        backup = _backup_config()
        clean_desc = description.replace(chr(34), "")
        commands = []
        if current:
            commands += [f"no object-group fqdn {name} include {x}" for x in current.items]
        commands.append(f"object-group fqdn {name} description \"{clean_desc}\"")
        commands += [f"object-group fqdn {name} include {x}" for x in items]
        if not current or not current.interface:
            commands.append(f"dns-proxy route object-group {name} {interface} auto reject")
        rc, out = _ndmc_config(commands)
        ok = rc == 0 and "error[" not in out.lower()
        status = 200 if ok else 500
        return jsonify({"ok": ok, "backup": backup, "name": name, "interface": interface, "items": items, "ndmc": out[-4000:]}), status

    return bp
