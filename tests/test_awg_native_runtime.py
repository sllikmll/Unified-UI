import base64
import importlib
import json
from pathlib import Path
import stat

import yaml


AWG2_CONF = """[Interface]
PrivateKey = client-private-key
Address = 10.8.1.9/32
DNS = 1.1.1.1
MTU = 1420
Jc = 4
Jmin = 40
Jmax = 70
S1 = 12
S2 = 12
S3 = 12
S4 = 12
H1 = 10101
H2 = 20202
H3 = 30303
H4 = 40404

[Peer]
PublicKey = server-public-key
PresharedKey = preshared-key
Endpoint = 109.172.101.43:33415
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""

AWG3_CONF = """[Interface]
PrivateKey = client-private-key
Address = 10.203.183.2/32
DNS = 1.1.1.1
MTU = 1280
Jc = 4
Jmin = 10
Jmax = 50
S1 = 128
S2 = 64
HeaderProtectionKey = awg3-header-protection-key
ContentPaddingAddition = 10-100
RekeyAfterTime = 100-120
RekeyTimeout = 3-7
RejectAfterTime = 150-180
KeepaliveTimeout = 5-15
MaxHandshakeAttempts = 15-20

[Peer]
PublicKey = server-public-key
Endpoint = almaty.example.net:9731
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""


def test_native_awg_runtime_preserves_official_setconf_fields():
    mod = importlib.import_module("services.awg_native")
    spec = mod.build_native_awg_spec("mskawg", AWG2_CONF)

    assert spec.interface == mod.native_interface_name("mskawg")
    assert len(spec.interface) <= 15
    assert spec.addresses == ["10.8.1.9/32"]
    assert spec.mtu == 1420
    assert "Address" not in spec.setconf
    assert "DNS" not in spec.setconf
    for expected in (
        "PrivateKey = client-private-key",
        "Jc = 4",
        "Jmin = 40",
        "Jmax = 70",
        "S1 = 12",
        "S2 = 12",
        "S3 = 12",
        "S4 = 12",
        "H1 = 10101",
        "H2 = 20202",
        "H3 = 30303",
        "H4 = 40404",
        "PublicKey = server-public-key",
        "PresharedKey = preshared-key",
        "Endpoint = 109.172.101.43:33415",
        "AllowedIPs = 0.0.0.0/0",
        "PersistentKeepalive = 25",
    ):
        assert expected in spec.setconf


def test_awg_import_uses_native_interface_instead_of_mihomo_wireguard():
    routes = importlib.import_module("routes.proxy_connections")
    payload = base64.urlsafe_b64encode(AWG2_CONF.encode()).decode().rstrip("=")
    conn = routes._parse_connection("", f"awg://{payload}#mskawg")
    proxy = yaml.safe_load(conn["proxyYaml"])[0]

    assert conn["protocol"] == "amnezia"
    assert conn["nativeRuntime"]["engine"] == "amneziawg-go"
    assert conn["nativeRuntime"]["interface"] == proxy["interface-name"]
    assert proxy == {
        "name": "mskawg",
        "type": "direct",
        "interface-name": conn["nativeRuntime"]["interface"],
        "routing-mark": conn["nativeRuntime"]["routingMark"],
        "udp": True,
    }
    assert "private-key" not in conn["proxyYaml"]
    assert "amnezia-wg-option" not in conn["proxyYaml"]


def test_awg3_import_uses_native_direct_runtime_and_preserves_official_fields():
    routes = importlib.import_module("routes.proxy_connections")
    payload = base64.urlsafe_b64encode(AWG3_CONF.encode()).decode().rstrip("=")
    conn = routes._parse_connection("", f"awg3://{payload}#awg3-msk")
    proxy = yaml.safe_load(conn["proxyYaml"])[0]
    spec = routes.build_native_awg_spec("awg3-msk", AWG3_CONF)

    assert conn["protocol"] == "amnezia"
    assert proxy["type"] == "direct"
    assert proxy["interface-name"] == spec.interface
    assert proxy["routing-mark"] == spec.routing_mark
    assert "type: wireguard" not in conn["proxyYaml"]
    assert "private-key" not in conn["proxyYaml"]
    for expected in (
        "HeaderProtectionKey = awg3-header-protection-key",
        "ContentPaddingAddition = 10-100",
        "RekeyAfterTime = 100-120",
        "RekeyTimeout = 3-7",
        "RejectAfterTime = 150-180",
        "KeepaliveTimeout = 5-15",
        "MaxHandshakeAttempts = 15-20",
    ):
        assert expected in spec.setconf


def test_native_interface_name_is_stable_unique_and_linux_safe():
    mod = importlib.import_module("services.awg_native")
    one = mod.native_interface_name("mskawg")
    assert one == mod.native_interface_name("mskawg")
    assert one != mod.native_interface_name("admfinawg")
    assert len(one) <= 15
    assert one.replace("_", "").isalnum()


def test_runtime_reconcile_writes_private_config_and_policy_route(tmp_path):
    mod = importlib.import_module("services.awg_native")
    spec = mod.build_native_awg_spec("mskawg", AWG2_CONF)
    commands = []

    runtime = mod.NativeAwgRuntime(
        tmp_path / "awg-native",
        amneziawg_go="/bundle/amneziawg-go",
        awg="/bundle/awg",
        ip="/sbin/ip",
        runner=lambda command, required: commands.append((command, required)),
    )
    runtime._wait_for_socket = lambda interface: None
    result = runtime.reconcile([spec])

    config_path = runtime.config_dir / f"{spec.interface}.conf"
    assert stat.S_IMODE(config_path.stat().st_mode) == 0o600
    assert "PrivateKey = client-private-key" in config_path.read_text()
    assert result["interfaces"] == [spec.interface]
    assert (["/bundle/amneziawg-go", spec.interface], True) in commands
    assert (["/bundle/awg", "setconf", spec.interface, str(config_path)], True) in commands
    assert (["/sbin/ip", "route", "replace", "default", "dev", spec.interface, "table", str(spec.routing_table)], True) in commands
    assert (["/sbin/ip", "rule", "add", "priority", str(spec.rule_priority), "fwmark", str(spec.routing_mark), "table", str(spec.routing_table)], True) in commands
    assert not any(cmd[:5] == ["/sbin/ip", "route", "replace", "default", "dev"] and "table" not in cmd for cmd, _ in commands)

    manifest = json.loads(runtime.manifest_path.read_text())
    assert manifest["interfaces"][0]["interface"] == spec.interface
    assert "PrivateKey" not in runtime.manifest_path.read_text()
    active = json.loads(runtime.active_desired_path.read_text())
    assert active["specs"][0]["setconf"] == spec.setconf
    assert "PrivateKey = client-private-key" in runtime.active_desired_path.read_text()


def test_runtime_reconcile_rolls_back_to_previous_active_desired_on_start_failure(tmp_path):
    mod = importlib.import_module("services.awg_native")
    old_spec = mod.build_native_awg_spec("old-awg", AWG2_CONF)
    new_spec = mod.build_native_awg_spec("new-awg", AWG2_CONF.replace("10.8.1.9/32", "10.9.1.9/32"))
    commands = []
    fail_new_setconf = False

    def runner(command, required):
        commands.append((command, required))
        if fail_new_setconf and command[:2] == ["/bundle/awg", "setconf"] and command[2] == new_spec.interface:
            raise RuntimeError("injected setconf failure")

    runtime = mod.NativeAwgRuntime(
        tmp_path / "awg-native",
        amneziawg_go="/bundle/amneziawg-go",
        awg="/bundle/awg",
        ip="/sbin/ip",
        runner=runner,
    )
    runtime._wait_for_socket = lambda interface: None
    runtime.reconcile([old_spec])

    commands.clear()
    fail_new_setconf = True
    try:
        runtime.reconcile([new_spec])
    except RuntimeError as exc:
        assert "injected setconf failure" in str(exc)
    else:
        raise AssertionError("reconcile unexpectedly succeeded")

    manifest = json.loads(runtime.manifest_path.read_text())
    active = json.loads(runtime.active_desired_path.read_text())
    assert [item["interface"] for item in manifest["interfaces"]] == [old_spec.interface]
    assert [item["interface"] for item in active["specs"]] == [old_spec.interface]
    assert active["specs"][0]["setconf"] == old_spec.setconf
    assert "10.9.1.9/32" not in runtime.active_desired_path.read_text()
    assert (["/bundle/amneziawg-go", old_spec.interface], True) in commands
    assert any(command[:5] == ["/sbin/ip", "link", "del", "dev", new_spec.interface] for command, _ in commands)


def test_existing_registry_awg_is_migrated_from_raw_config():
    routes = importlib.import_module("routes.proxy_connections")
    original = {
        "id": "amnezia-mskawg-old",
        "protocol": "amnezia",
        "name": "mskawg",
        "sourceType": "import",
        "raw": AWG2_CONF,
        "proxyYaml": "- name: 'mskawg'\n  type: wireguard\n",
        "enabled": True,
        "selectors": ["GLOBAL"],
        "createdAt": "2026-08-01T00:00:00+00:00",
    }

    migrated, specs, changed = routes._upgrade_native_awg_connections([original])

    assert changed is True
    assert len(specs) == 1
    assert migrated[0]["id"] == original["id"]
    assert migrated[0]["selectors"] == ["GLOBAL"]
    assert migrated[0]["createdAt"] == original["createdAt"]
    assert migrated[0]["nativeRuntime"]["engine"] == "amneziawg-go"
    assert "type: direct" in migrated[0]["proxyYaml"]
    assert "type: wireguard" not in migrated[0]["proxyYaml"]


def test_startup_reconcile_restores_enabled_native_awg(monkeypatch):
    routes = importlib.import_module("routes.proxy_connections")
    original = {
        "id": "amnezia-mskawg-old",
        "protocol": "amnezia",
        "name": "mskawg",
        "sourceType": "import",
        "raw": AWG2_CONF,
        "proxyYaml": "- name: 'mskawg'\n  type: wireguard\n",
        "enabled": True,
        "selectors": ["GLOBAL"],
    }
    saved = []
    reconciled = []
    monkeypatch.setattr(routes, "_load_registry", lambda: {"version": 1, "connections": [original]})
    monkeypatch.setattr(routes, "_save_registry", lambda data: saved.append(data))
    monkeypatch.setattr(routes, "_native_awg_runtime", lambda specs: reconciled.extend(specs) or {"ok": True, "count": len(specs)})

    result = routes.reconcile_native_awg_startup()

    assert result == {"ok": True, "count": 1}
    assert [spec.name for spec in reconciled] == ["mskawg"]
    assert len(saved) == 1
    assert "type: direct" in saved[0]["connections"][0]["proxyYaml"]


def test_apply_fails_clearly_without_native_runtime_and_preserves_config(monkeypatch, tmp_path):
    routes = importlib.import_module("routes.proxy_connections")
    awg_mod = importlib.import_module("services.awg_native")
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("proxies: []\nproxy-groups:\n- name: GLOBAL\n  type: select\n  proxies: [DIRECT]\nrules:\n- MATCH,DIRECT\n", encoding="utf-8")
    registry_path = tmp_path / "proxy-connections.json"
    original_cfg = cfg_path.read_text(encoding="utf-8")
    registry_path.write_text(
        json.dumps(
            {
                "version": 1,
                "connections": [
                    {
                        "id": "amnezia-mskawg",
                        "protocol": "amnezia",
                        "name": "mskawg",
                        "sourceType": "import",
                        "raw": AWG2_CONF,
                        "proxyYaml": "- name: 'mskawg'\n  type: wireguard\n",
                        "enabled": True,
                        "selectors": ["GLOBAL"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MIHOMO_CONFIG", str(cfg_path))
    monkeypatch.setenv("UNIFIED_PROXY_CONNECTIONS_FILE", str(registry_path))
    monkeypatch.setattr(
        routes,
        "preflight_native_awg_runtime",
        lambda **kwargs: awg_mod.NativeAwgPreflight(
            ok=False,
            reasons=["/dev/net/tun is missing", "CAP_NET_ADMIN is not available inside the container"],
        ),
    )

    try:
        routes._apply_to_mihomo(restart=False)
    except RuntimeError as exc:
        message = str(exc)
    else:
        raise AssertionError("AWG apply unexpectedly succeeded without native runtime")

    assert "native AmneziaWG runtime is unavailable" in message
    assert "/dev/net/tun is missing" in message
    assert "CAP_NET_ADMIN" in message
    assert "client-private-key" not in message
    assert cfg_path.read_text(encoding="utf-8") == original_cfg
    assert "type: wireguard" in registry_path.read_text(encoding="utf-8")


def test_apply_uses_native_awg_when_runtime_preflight_is_capable(monkeypatch, tmp_path):
    routes = importlib.import_module("routes.proxy_connections")
    awg_mod = importlib.import_module("services.awg_native")
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("proxies: []\nproxy-groups:\n- name: GLOBAL\n  type: select\n  proxies: [DIRECT]\nrules:\n- MATCH,DIRECT\n", encoding="utf-8")
    registry_path = tmp_path / "proxy-connections.json"
    registry_path.write_text(
        json.dumps(
            {
                "version": 1,
                "connections": [
                    {
                        "id": "amnezia-mskawg",
                        "protocol": "amnezia",
                        "name": "mskawg",
                        "sourceType": "import",
                        "raw": AWG2_CONF,
                        "proxyYaml": "- name: 'mskawg'\n  type: wireguard\n",
                        "enabled": True,
                        "selectors": ["GLOBAL"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    go_bin = tmp_path / "amneziawg-go"
    awg_bin = tmp_path / "awg"
    ip_bin = tmp_path / "ip"
    for path in (go_bin, awg_bin, ip_bin):
        path.write_text("#!/bin/sh\n", encoding="utf-8")
        path.chmod(0o755)
    reconciled = []

    def fake_reconcile(self, specs):
        reconciled.extend(specs)
        return {"ok": True, "count": len(specs), "interfaces": [spec.interface for spec in specs]}

    monkeypatch.setenv("MIHOMO_CONFIG", str(cfg_path))
    monkeypatch.setenv("UNIFIED_PROXY_CONNECTIONS_FILE", str(registry_path))
    monkeypatch.setenv("UNIFIED_AWG_GO_BIN", str(go_bin))
    monkeypatch.setenv("UNIFIED_AWG_BIN", str(awg_bin))
    monkeypatch.setenv("UNIFIED_IP_BIN", str(ip_bin))
    monkeypatch.setattr(
        routes,
        "preflight_native_awg_runtime",
        lambda **kwargs: awg_mod.NativeAwgPreflight(ok=True, reasons=[], net_admin=True),
    )
    monkeypatch.setattr(awg_mod.NativeAwgRuntime, "reconcile", fake_reconcile)
    monkeypatch.setattr(routes.NativeAwgRuntime, "reconcile", fake_reconcile)

    result = routes._apply_to_mihomo(restart=False)
    patched = cfg_path.read_text(encoding="utf-8")
    saved = registry_path.read_text(encoding="utf-8")

    assert result["ok"] is True
    assert result["nativeAwg"]["count"] == 1
    assert [spec.name for spec in reconciled] == ["mskawg"]
    assert "type: direct" in patched
    assert "interface-name" in patched
    assert "routing-mark" in patched
    assert "type: wireguard" not in saved
    assert "client-private-key" not in patched


def test_mikrotik_entrypoint_skips_native_restore_when_preflight_unavailable():
    root = Path(__file__).resolve().parents[1]
    text = (root / "mikrotik" / "entrypoint.sh").read_text(encoding="utf-8")

    assert "native_awg_preflight()" in text
    assert "preflight_native_awg_runtime" in text
    assert "UNIFIED_AWG_RUNTIME_STATUS" in text
    assert "if native_awg_preflight; then" in text
    assert "native AmneziaWG restore skipped; UI and Mihomo will continue without native AWG interfaces" in text
    assert text.index("if native_awg_preflight; then") < text.index("log \"validating Mihomo config\"")
