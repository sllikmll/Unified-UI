import importlib
import sys
from pathlib import Path


def _reload(name: str):
    if name in sys.modules:
        return importlib.reload(sys.modules[name])
    return importlib.import_module(name)


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
