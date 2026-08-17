from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "openwrt" / "install-openwrt-prototype.sh"
COMPAT = ROOT / "openwrt" / "openwrt-fetch-compat.js"
BUILDER = ROOT / "scripts" / "build_openwrt_archive.py"


def test_openwrt_cgi_contains_full_panel_subscription_contract(tmp_path: Path):
    text = INSTALLER.read_text(encoding="utf-8")
    assert "/proxy-subscription-import)" in text
    assert "/proxy-subscription-status)" in text
    assert "/proxy-subscription-telegram-action)" in text
    assert "subscription_mieru_yaml" in text
    assert "unified-panel-subscription:start" in text
    assert "validate_profile_content" in text
    assert "panel-subscription-$ts.yaml" in text
    assert "cp \"$backup\" \"$profile_real\"" in text
    assert "UNIFIED_UI_AUTH_PASSWORD='%s'" in text
    assert "AWG_NATIVE_HELPER=\"/usr/sbin/unified-awg-native\"" in text
    assert "amneziawg-go" in text
    assert "awg setconf" not in text  # invoked as "$AWG_BIN" setconf for path safety
    assert "routing-mark:" in text
    assert "interface-name:" in text

    match = re.search(r"cat > \"\$CGI_PATH\" <<'CGI'\n(?P<body>.*?)\nCGI\n", text, re.S)
    assert match, "embedded OpenWrt CGI was not found"
    cgi = tmp_path / "unified-ui-api"
    cgi.write_text(match.group("body") + "\n", encoding="utf-8")
    subprocess.run(["sh", "-n", str(cgi)], check=True)


def test_openwrt_browser_maps_subscription_and_action_endpoints():
    compat = COMPAT.read_text(encoding="utf-8")
    assert "/api/proxy-connections/subscription/import" in compat
    assert "/proxy-subscription-import" in compat
    assert "/proxy-subscription-telegram-action" in compat


def test_openwrt_native_awg_contract_uses_direct_outbound_and_private_state():
    text = INSTALLER.read_text(encoding="utf-8")
    assert "install_bundled_awg_runtime" in text
    assert "sha256sum -c SHA256SUMS" in text
    assert "OFFICIAL_AWG_PROVENANCE.json" in text
    assert "AWG_BIN_DIR=\"${UNIFIED_AWG_BIN_DIR:-/usr/bin}\"" in text
    assert "chmod 600 \"$dst\"" in text
    assert "chmod 600 \"$conf\"" in text
    assert "PrivateKey" in text
    assert "PublicKey" in text
    assert "PresharedKey" in text
    assert "AllowedIPs" in text
    assert "Jc" in text or "k==\"jc\"" in text
    assert "k==\"s3\"" in text
    assert "k==\"s4\"" in text
    assert "type: direct" in text
    assert "interface-name:" in text
    assert "routing-mark:" in text
    assert "type: wireguard" not in text
    assert "amnezia-wg-option" not in text


def test_openwrt_archive_builder_bundles_official_awg_runtime_when_present():
    text = BUILDER.read_text(encoding="utf-8")
    assert "copy_official_awg_runtime" in text
    assert 'required = ["amneziawg-go", "awg", "SHA256SUMS", "OFFICIAL_AWG_PROVENANCE.json"]' in text
    assert "AWG_RUNTIME_DIR = UNIFIED_UI_DIR / \"bin\"" in text
    assert "copy_official_awg_runtime(tmp_root)" in text


def test_openwrt_clean_install_bundles_mihomo_and_procd_without_overwriting_config():
    installer = INSTALLER.read_text(encoding="utf-8")
    builder = BUILDER.read_text(encoding="utf-8")
    assert "MIHOMO_ARM64_SRC" in builder
    assert "copy_mihomo_arm64_runtime(tmp_root)" in builder
    assert "MIHOMO_SHA256" in builder
    assert "install_bundled_mihomo" in installer
    assert 'if [ ! -s /etc/mihomo/config.yaml ]; then' in installer
    assert 'if [ ! -f /etc/init.d/mihomo ]; then' in installer
    assert "USE_PROCD=1" in installer
    assert "procd_set_param respawn" in installer
    assert "ipv6: false" in installer
    assert "/usr/bin/mihomo -t" in installer


def test_openwrt_snapshot_whitelist_keeps_all_protocol_views():
    builder = BUILDER.read_text(encoding="utf-8")
    for section in (
        "protocol-subscription",
        "protocol-wireguard",
        "protocol-amnezia",
        "protocol-hysteria2",
        "protocol-vless",
        "protocol-trojan",
        "protocol-vmess",
        "protocol-shadowsocks",
        "protocol-mieru",
        "protocol-naiveproxy",
        "protocol-telegram",
    ):
        assert f'"{section}"' in builder
