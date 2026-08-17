from pathlib import Path


def test_native_linux_x64_uses_upstream_compatible_mihomo_asset():
    source = (Path(__file__).resolve().parents[1] / "desktop/native/unified_ui_native.py").read_text(encoding="utf-8")
    assert 'mihomo-linux-amd64-compatible-v{MIHOMO_VERSION}.gz' in source
    assert 'if a == "amd64":' in source
