"""Native AmneziaWG runtime helpers.

The data plane is provided by the official ``amneziawg-go`` and ``awg``
programs.  Mihomo receives a lightweight DIRECT outbound bound to the managed
AWG interface; private keys and Amnezia options never enter Mihomo YAML.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from typing import Callable, List


@dataclass(frozen=True)
class NativeAwgSpec:
    name: str
    interface: str
    addresses: List[str]
    mtu: int | None
    setconf: str
    routing_mark: int
    routing_table: int
    rule_priority: int


@dataclass(frozen=True)
class NativeAwgPreflight:
    ok: bool
    reasons: list[str]
    tun: str = "/dev/net/tun"
    amneziawg_go: str = "/opt/bin/amneziawg-go"
    awg: str = "/opt/bin/awg"
    net_admin: bool = False

    def status(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "available": self.ok,
            "reasons": self.reasons,
            "tun": self.tun,
            "amneziawgGo": self.amneziawg_go,
            "awg": self.awg,
            "netAdmin": self.net_admin,
        }

    def error(self) -> str:
        return "native AmneziaWG runtime is unavailable: " + "; ".join(self.reasons)


def _has_cap_net_admin(status_path: str | Path = "/proc/self/status") -> bool:
    try:
        text = Path(status_path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    match = re.search(r"^CapEff:\s*([0-9a-fA-F]+)\s*$", text, flags=re.M)
    if not match:
        return False
    return bool(int(match.group(1), 16) & (1 << 12))


def preflight_native_awg_runtime(
    *,
    tun: str = "/dev/net/tun",
    amneziawg_go: str = "/opt/bin/amneziawg-go",
    awg: str = "/opt/bin/awg",
    require_net_admin: bool = True,
) -> NativeAwgPreflight:
    reasons: list[str] = []
    tun_path = Path(tun)
    if not tun_path.exists():
        reasons.append(f"{tun} is missing")
    elif not tun_path.is_char_device():
        reasons.append(f"{tun} is not a character device")
    for label, path in (("amneziawg-go", amneziawg_go), ("awg", awg)):
        binary = Path(path)
        if not binary.is_file() or not os.access(binary, os.X_OK):
            reasons.append(f"{label} is missing or not executable at {path}")
    net_admin = _has_cap_net_admin()
    if require_net_admin and not net_admin:
        reasons.append("CAP_NET_ADMIN is not available inside the container")
    return NativeAwgPreflight(
        ok=not reasons,
        reasons=reasons,
        tun=tun,
        amneziawg_go=amneziawg_go,
        awg=awg,
        net_admin=net_admin,
    )


def native_interface_name(name: str) -> str:
    """Return a deterministic Linux-safe interface name (IFNAMSIZ <= 15)."""
    digest = hashlib.sha256(str(name or "awg").encode("utf-8", errors="replace")).hexdigest()[:10]
    return f"uawg{digest}"


def _routing_identity(name: str) -> tuple[int, int, int]:
    value = int(hashlib.sha256(str(name or "awg").encode()).hexdigest()[:8], 16) % 10000
    return 50000 + value, 20000 + value, 30000 + value


def _parse_sections(conf_text: str) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    section = ""
    interface: list[tuple[str, str]] = []
    peer: list[tuple[str, str]] = []
    for raw_line in str(conf_text or "").replace("\r\n", "\n").replace("\r", "\n").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().lower()
            continue
        if "=" not in line:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        if section == "interface":
            interface.append((key, value))
        elif section == "peer":
            peer.append((key, value))
    return interface, peer


def _first(entries: list[tuple[str, str]], key: str, default: str = "") -> str:
    wanted = key.casefold().replace("-", "")
    for item_key, value in entries:
        if item_key.casefold().replace("-", "") == wanted:
            return value.strip()
    return default


def build_native_awg_spec(name: str, conf_text: str) -> NativeAwgSpec:
    interface, peer = _parse_sections(conf_text)
    if not _first(interface, "PrivateKey") or not _first(peer, "PublicKey") or not _first(peer, "Endpoint"):
        raise ValueError("Invalid AmneziaWG config: missing PrivateKey, PublicKey or Endpoint")

    addresses = [part.strip() for part in _first(interface, "Address").split(",") if part.strip()]
    mtu_raw = _first(interface, "MTU")
    mtu = int(mtu_raw) if mtu_raw and re.fullmatch(r"\d+", mtu_raw) else None

    # Address, DNS, MTU and wg-quick-only routing directives belong to the OS
    # lifecycle, not to the UAPI consumed by ``awg setconf``.
    skipped = {"address", "dns", "mtu", "table", "preup", "postup", "predown", "postdown", "name"}
    setconf_lines = ["[Interface]"]
    for key, value in interface:
        if key.casefold().replace("-", "") in skipped:
            continue
        setconf_lines.append(f"{key} = {value}")
    setconf_lines.append("")
    setconf_lines.append("[Peer]")
    for key, value in peer:
        if key.casefold().replace("-", "") == "name":
            continue
        setconf_lines.append(f"{key} = {value}")

    routing_mark, routing_table, rule_priority = _routing_identity(name)
    return NativeAwgSpec(
        name=str(name or "AmneziaWG"),
        interface=native_interface_name(name),
        addresses=addresses,
        mtu=mtu,
        setconf="\n".join(setconf_lines).rstrip() + "\n",
        routing_mark=routing_mark,
        routing_table=routing_table,
        rule_priority=rule_priority,
    )


def native_mihomo_proxy_yaml(name: str, interface: str, routing_mark: int | None = None) -> str:
    escaped_name = str(name).replace("'", "''")
    escaped_interface = str(interface).replace("'", "''")
    routing_line = f"  routing-mark: {int(routing_mark)}\n" if routing_mark is not None else ""
    return (
        f"- name: '{escaped_name}'\n"
        "  type: direct\n"
        f"  interface-name: '{escaped_interface}'\n"
        f"{routing_line}"
        "  udp: true\n"
    )


class NativeAwgRuntime:
    """Reconcile official userspace AWG interfaces from parsed specs."""

    def __init__(
        self,
        state_dir: str | Path,
        *,
        amneziawg_go: str = "/opt/bin/amneziawg-go",
        awg: str = "/opt/bin/awg",
        ip: str = "/opt/sbin/ip",
        runner: Callable[[list[str], bool], None] | None = None,
    ) -> None:
        self.state_dir = Path(state_dir)
        self.config_dir = self.state_dir / "configs"
        self.manifest_path = self.state_dir / "manifest.json"
        self.active_desired_path = self.state_dir / "active-desired.json"
        self.amneziawg_go = amneziawg_go
        self.awg = awg
        self.ip = ip
        self._runner = runner

    def _run(self, command: list[str], required: bool = True) -> None:
        if self._runner is not None:
            self._runner(command, required)
            return
        result = subprocess.run(command, text=True, capture_output=True, timeout=20)
        if required and result.returncode != 0:
            detail = (result.stderr or result.stdout or "command failed").strip()
            raise RuntimeError(f"{' '.join(command)}: {detail[:500]}")

    def _socket_paths(self, interface: str) -> list[Path]:
        return [Path("/var/run/amneziawg") / f"{interface}.sock"]

    def _wait_for_socket(self, interface: str) -> None:
        deadline = time.monotonic() + 5
        paths = self._socket_paths(interface)
        while time.monotonic() < deadline:
            if any(path.exists() for path in paths):
                return
            time.sleep(0.1)
        raise RuntimeError(f"amneziawg-go did not create UAPI socket for {interface}")

    def _config_path(self, spec: NativeAwgSpec) -> Path:
        return self.config_dir / f"{spec.interface}.conf"

    def _pid_path(self, interface: str) -> Path:
        return self.state_dir / f"{interface}.pid"

    def _stop_process(self, interface: str) -> None:
        if self._runner is not None:
            return
        pid_path = self._pid_path(interface)
        pids: set[int] = set()
        try:
            pids.add(int(pid_path.read_text(encoding="utf-8").strip()))
        except (FileNotFoundError, ValueError, OSError):
            pass
        # Migration cleanup for older daemonizing launches that left a stale
        # parent PID. Match only amneziawg-go processes for this interface.
        for cmdline in Path("/proc").glob("[0-9]*/cmdline"):
            try:
                parts = [part.decode(errors="replace") for part in cmdline.read_bytes().split(b"\0") if part]
                if parts and "amneziawg-go" in Path(parts[0]).name and interface in parts[1:]:
                    pids.add(int(cmdline.parent.name))
            except (OSError, ValueError):
                continue
        for pid in pids:
            try:
                os.kill(pid, 15)
            except ProcessLookupError:
                continue
            except OSError:
                continue
        deadline = time.monotonic() + 2
        while pids and time.monotonic() < deadline:
            alive: set[int] = set()
            for pid in pids:
                try:
                    os.kill(pid, 0)
                    alive.add(pid)
                except OSError:
                    pass
            pids = alive
            if pids:
                time.sleep(0.05)
        for pid in pids:
            try:
                os.kill(pid, 9)
            except OSError:
                pass
        try:
            pid_path.unlink()
        except FileNotFoundError:
            pass

    def _start_process(self, interface: str) -> None:
        command = [self.amneziawg_go, "-f", interface]
        if self._runner is not None:
            self._run(command)
            return
        proc = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        pid_path = self._pid_path(interface)
        pid_path.write_text(f"{proc.pid}\n", encoding="utf-8")
        os.chmod(pid_path, 0o600)
        try:
            self._wait_for_socket(interface)
            if proc.poll() is not None:
                raise RuntimeError(f"amneziawg-go exited before interface startup: {interface}")
        except Exception:
            self._stop_process(interface)
            raise

    def _spec_to_dict(self, spec: NativeAwgSpec) -> dict[str, object]:
        return {
            "name": spec.name,
            "interface": spec.interface,
            "addresses": spec.addresses,
            "mtu": spec.mtu,
            "setconf": spec.setconf,
            "routingMark": spec.routing_mark,
            "routingTable": spec.routing_table,
            "rulePriority": spec.rule_priority,
        }

    def _spec_from_dict(self, data: dict[str, object]) -> NativeAwgSpec:
        addresses_raw = data.get("addresses")
        addresses = [str(item) for item in addresses_raw] if isinstance(addresses_raw, list) else []
        mtu_raw = data.get("mtu")
        mtu = int(mtu_raw) if mtu_raw not in (None, "") else None
        return NativeAwgSpec(
            name=str(data.get("name") or "AmneziaWG"),
            interface=str(data.get("interface") or native_interface_name(str(data.get("name") or "AmneziaWG"))),
            addresses=addresses,
            mtu=mtu,
            setconf=str(data.get("setconf") or ""),
            routing_mark=int(data.get("routingMark") or 0),
            routing_table=int(data.get("routingTable") or 0),
            rule_priority=int(data.get("rulePriority") or 0),
        )

    def load_active_specs(self) -> list[NativeAwgSpec]:
        if not self.active_desired_path.exists():
            return []
        try:
            payload = json.loads(self.active_desired_path.read_text(encoding="utf-8"))
        except Exception:
            return []
        items = payload.get("specs") if isinstance(payload, dict) else []
        specs: list[NativeAwgSpec] = []
        for item in items if isinstance(items, list) else []:
            if isinstance(item, dict):
                spec = self._spec_from_dict(item)
                if spec.interface and spec.setconf:
                    specs.append(spec)
        return specs

    def _write_json_private(self, path: Path, payload: dict[str, object]) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.chmod(tmp, 0o600)
        tmp.replace(path)

    def _manifest_payload(self, specs: list[NativeAwgSpec]) -> dict[str, object]:
        return {
            "version": 1,
            "interfaces": [
                {
                    "name": spec.name,
                    "interface": spec.interface,
                    "routingMark": spec.routing_mark,
                    "routingTable": spec.routing_table,
                    "rulePriority": spec.rule_priority,
                }
                for spec in specs
            ],
        }

    def _active_desired_payload(self, specs: list[NativeAwgSpec]) -> dict[str, object]:
        return {"version": 1, "specs": [self._spec_to_dict(spec) for spec in specs]}

    def _teardown_identity(self, interface: str, routing_mark: int, routing_table: int, rule_priority: int) -> None:
        self._stop_process(interface)
        self._run(
            [self.ip, "rule", "del", "priority", str(rule_priority), "fwmark", str(routing_mark), "table", str(routing_table)],
            False,
        )
        self._run([self.ip, "route", "flush", "table", str(routing_table)], False)
        self._run([self.ip, "link", "del", "dev", interface], False)
        for path in self._socket_paths(interface):
            try:
                path.unlink()
            except FileNotFoundError:
                pass

    def apply(self, spec: NativeAwgSpec) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(self.config_dir, 0o700)
        config_path = self._config_path(spec)
        config_path.write_text(spec.setconf, encoding="utf-8")
        os.chmod(config_path, 0o600)

        self._teardown_identity(spec.interface, spec.routing_mark, spec.routing_table, spec.rule_priority)
        try:
            self._start_process(spec.interface)
            if self._runner is not None:
                self._wait_for_socket(spec.interface)
            self._run([self.awg, "setconf", spec.interface, str(config_path)])
            for address in spec.addresses:
                self._run([self.ip, "address", "add", address, "dev", spec.interface])
            if spec.mtu:
                self._run([self.ip, "link", "set", "mtu", str(spec.mtu), "dev", spec.interface])
            self._run([self.ip, "link", "set", "up", "dev", spec.interface])
            self._run([self.ip, "route", "replace", "default", "dev", spec.interface, "table", str(spec.routing_table)])
            self._run(
                [self.ip, "rule", "add", "priority", str(spec.rule_priority), "fwmark", str(spec.routing_mark), "table", str(spec.routing_table)]
            )
        except Exception:
            self._teardown_identity(spec.interface, spec.routing_mark, spec.routing_table, spec.rule_priority)
            raise

    def _restore_specs(self, specs: list[NativeAwgSpec]) -> None:
        for spec in specs:
            self.apply(spec)
        desired = {spec.interface for spec in specs}
        previous: list[dict[str, object]] = []
        if self.manifest_path.exists():
            try:
                previous = json.loads(self.manifest_path.read_text(encoding="utf-8")).get("interfaces", [])
            except Exception:
                previous = []
        for old in previous:
            interface = str(old.get("interface") or "")
            if interface and interface not in desired:
                self._teardown_identity(
                    interface,
                    int(old.get("routingMark") or 0),
                    int(old.get("routingTable") or 0),
                    int(old.get("rulePriority") or 0),
                )
        self._write_json_private(self.manifest_path, self._manifest_payload(specs))
        self._write_json_private(self.active_desired_path, self._active_desired_payload(specs))

    def reconcile(self, specs: list[NativeAwgSpec]) -> dict[str, object]:
        if not specs and not self.manifest_path.exists():
            return {"ok": True, "count": 0, "interfaces": []}
        previous_specs = self.load_active_specs()
        previous: list[dict[str, object]] = []
        if self.manifest_path.exists():
            try:
                previous = json.loads(self.manifest_path.read_text(encoding="utf-8")).get("interfaces", [])
            except Exception:
                previous = []
        desired = {spec.interface for spec in specs}
        try:
            for spec in specs:
                self.apply(spec)
            for old in previous:
                interface = str(old.get("interface") or "")
                if interface and interface not in desired:
                    self._teardown_identity(
                        interface,
                        int(old.get("routingMark") or 0),
                        int(old.get("routingTable") or 0),
                        int(old.get("rulePriority") or 0),
                    )
                    try:
                        (self.config_dir / f"{interface}.conf").unlink()
                    except FileNotFoundError:
                        pass
        except Exception:
            for spec in specs:
                self._teardown_identity(spec.interface, spec.routing_mark, spec.routing_table, spec.rule_priority)
            if previous_specs:
                self._restore_specs(previous_specs)
            raise

        self._write_json_private(self.manifest_path, self._manifest_payload(specs))
        self._write_json_private(self.active_desired_path, self._active_desired_payload(specs))
        return {"ok": True, "count": len(specs), "interfaces": [spec.interface for spec in specs]}


__all__ = [
    "NativeAwgSpec",
    "NativeAwgPreflight",
    "build_native_awg_spec",
    "native_interface_name",
    "native_mihomo_proxy_yaml",
    "preflight_native_awg_runtime",
    "NativeAwgRuntime",
]
