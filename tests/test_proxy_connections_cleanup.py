import importlib
import json
import sys
from pathlib import Path


def _reload(name: str):
    if name in sys.modules:
        return importlib.reload(sys.modules[name])
    return importlib.import_module(name)


AWG2_CONF = """[Interface]
PrivateKey = client-private-key
Address = 10.8.1.9/32
MTU = 1420
Jc = 4

[Peer]
PublicKey = server-public-key
Endpoint = 109.172.101.43:33415
AllowedIPs = 0.0.0.0/0
"""


def test_remove_proxy_from_groups_removes_inline_and_block_lists():
    mod = _reload("services.mihomo_proxy_config")
    content = """proxies:
  # unified-managed-proxies:start
  # amnezia / amnezia-old
  - name: AWG-old
    type: wireguard
  # unified-managed-proxies:end
proxy-groups:
  - name: AI
    type: select
    proxies: [DIRECT, AWG-old, VLESS-live]
  - name: YouTube
    type: select
    proxies:
      - DIRECT
      - AWG-old
      - VLESS-live
rules: []
"""
    out = mod.remove_proxy_from_groups(content, {"AWG-old"})
    assert "AWG-old" not in out.split("proxy-groups:", 1)[1]
    assert "VLESS-live" in out


def test_apply_rebuild_removes_deleted_managed_proxy_from_selectors(tmp_path: Path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    registry = tmp_path / "proxy-connections.json"
    cfg.write_text("""proxies:
  # unified-managed-proxies:start
  # amnezia / amnezia-old
  - name: AWG-old
    type: wireguard
  # unified-managed-proxies:end
proxy-groups:
  - name: AI
    type: select
    proxies: [DIRECT, AWG-old, VLESS-live]
  - name: YouTube
    type: select
    proxies:
      - DIRECT
      - AWG-old
      - VLESS-live
rules: []
""", encoding="utf-8")
    registry.write_text('{"version":1,"connections":[]}', encoding="utf-8")
    monkeypatch.setenv("MIHOMO_CONFIG", str(cfg))
    monkeypatch.setenv("UNIFIED_PROXY_CONNECTIONS_FILE", str(registry))

    mod = _reload("routes.proxy_connections")
    result = mod._apply_to_mihomo(restart=False)
    assert result["ok"] is True
    assert result["changed"] is True
    text = cfg.read_text(encoding="utf-8")
    assert "AWG-old" not in text.split("proxy-groups:", 1)[1]
    assert "unified-managed-proxies:start" in text
    assert "unified-managed-proxies:end" in text
    assert "VLESS-live" in text


def test_apply_restart_failure_restores_previous_config_and_native_awg(tmp_path: Path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    registry = tmp_path / "proxy-connections.json"
    old_config = """proxies:
proxy-groups:
  - name: GLOBAL
    type: select
    proxies: [DIRECT]
rules: []
"""
    cfg.write_text(old_config, encoding="utf-8")
    registry.write_text(
        json.dumps(
            {
                "version": 1,
                "connections": [
                    {
                        "id": "awg-new",
                        "protocol": "amnezia",
                        "name": "new-awg",
                        "sourceType": "import",
                        "raw": AWG2_CONF,
                        "enabled": True,
                        "selectors": ["GLOBAL"],
                        "mihomoSupported": True,
                        "proxyYaml": "- name: old\n  type: wireguard\n",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MIHOMO_CONFIG", str(cfg))
    monkeypatch.setenv("UNIFIED_PROXY_CONNECTIONS_FILE", str(registry))

    mod = _reload("routes.proxy_connections")
    previous_spec = mod.build_native_awg_spec("previous-awg", AWG2_CONF)
    applied = []
    restored = []
    monkeypatch.setattr(mod, "_native_awg_active_specs", lambda: [previous_spec])
    monkeypatch.setattr(mod, "_native_awg_runtime", lambda specs: applied.append(specs) or {"ok": True, "count": len(specs)})
    monkeypatch.setattr(mod, "_native_awg_restore", lambda specs: restored.append(specs))

    def fail_restart(new_content=None):
        raise RuntimeError("restart failed")

    monkeypatch.setattr(mod, "restart_mihomo_and_get_log", fail_restart)

    try:
        mod._apply_to_mihomo(restart=True)
    except RuntimeError as exc:
        assert "restart failed" in str(exc)
    else:
        raise AssertionError("apply unexpectedly succeeded")

    assert cfg.read_text(encoding="utf-8") == old_config
    assert applied and [spec.name for spec in applied[0]] == ["new-awg"]
    assert restored == [[previous_spec]]
    assert '"nativeRuntime"' not in registry.read_text(encoding="utf-8")
