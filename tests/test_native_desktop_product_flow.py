from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from desktop.native.unified_ui_native import ImportResult, NativeConfigManager


def test_selectable_options_do_not_leak_unwired_provider_nodes():
    config = {
        "proxy-groups": [
            {"name": "AI", "type": "select", "proxies": ["DIRECT", "Fastest"], "use": ["subscription_ai"]},
            {"name": "GitHub", "type": "select", "proxies": ["DIRECT"], "use": ["subscription_dev"]},
        ]
    }
    live_selector = {"all": ["DIRECT", "Fastest"]}
    providers = {
        "subscription_ai": {"proxies": [{"name": "VLESS-ai"}]},
        "subscription_dev": {"proxies": [{"name": "VLESS-github"}]},
    }

    assert NativeConfigManager.selectable_options_for_group(config, "AI", live_selector, providers) == [
        "DIRECT",
        "Fastest",
        "VLESS-ai",
    ]


def test_apply_imports_without_group_adds_proxy_to_all_selectors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runtime_dir = tmp_path / "runtime"
    mihomo_dir = runtime_dir / "mihomo"
    mihomo_dir.mkdir(parents=True)
    config_path = mihomo_dir / "config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "proxies": [],
                "proxy-groups": [
                    {"name": "AI", "type": "select", "proxies": ["DIRECT"]},
                    {"name": "GitHub", "type": "select", "proxies": ["DIRECT"]},
                    {"name": "Load", "type": "url-test", "proxies": ["DIRECT"]},
                ],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    runtime = SimpleNamespace(runtime=runtime_dir, config_path=config_path, restart=lambda: None)
    manager = NativeConfigManager(runtime)  # type: ignore[arg-type]
    monkeypatch.setattr(manager, "validate_text", lambda text: (True, "OK"))

    imports = [
        ImportResult(
            name="VLESS-msk",
            yaml="- name: VLESS-msk\n  type: vless\n  server: 1.2.3.4\n  port: 443\n  uuid: 00000000-0000-0000-0000-000000000000\n  network: tcp\n  tls: true\n",
            kind="vless",
            source="test",
        )
    ]

    added, _backup, _msg = manager.apply_imports(imports, groups=[], restart=False)
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert added == ["VLESS-msk"]
    for group in data["proxy-groups"]:
        assert "VLESS-msk" in group["proxies"]


def test_runtime_normalization_enables_tun_and_wires_all_selectors(tmp_path: Path):
    runtime_dir = tmp_path / "runtime"
    mihomo_dir = runtime_dir / "mihomo"
    mihomo_dir.mkdir(parents=True)
    config_path = mihomo_dir / "config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "mixed-port": 7890,
                "proxies": [{"name": "VLESS-msk", "type": "vless", "server": "1.2.3.4", "port": 443}],
                "proxy-providers": {"subscription_1": {"type": "http", "url": "https://example.test/sub"}},
                "proxy-groups": [
                    {"name": "AI", "type": "select", "proxies": ["DIRECT"]},
                    {"name": "GitHub", "type": "select", "proxies": ["DIRECT"], "use": []},
                ],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    runtime = SimpleNamespace(runtime=runtime_dir, config_path=config_path, restart=lambda: None)
    manager = NativeConfigManager(runtime)  # type: ignore[arg-type]
    monkeypatch_validate = lambda text: (True, "OK")
    manager.validate_text = monkeypatch_validate  # type: ignore[method-assign]

    data = manager.config_data()
    changed = manager._normalize_runtime_config_data(data)
    changed = manager.ensure_all_selectors_have_all_nodes(data) or changed

    assert changed is True
    assert data["mixed-port"] == 17990
    assert data["tun"] == {
        "enable": True,
        "stack": "system",
        "auto-route": True,
        "auto-detect-interface": True,
        "dns-hijack": ["any:53"],
    }
    for group in data["proxy-groups"]:
        assert "VLESS-msk" in group["proxies"]
        assert "subscription_1" in group["use"]
