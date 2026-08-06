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
