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
    awg_uri_helper = text.split("awg_uri_to_conf()", 1)[1].split("awg_fragment_name()", 1)[0]
    assert 'uri_raw="$1"' in awg_uri_helper
    assert '\n  raw="$1"' not in awg_uri_helper

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


def test_openwrt_native_awg_import_persists_selected_selector_publicly():
    text = INSTALLER.read_text(encoding="utf-8")
    assert "sanitize_awg_selector()" in text
    assert "tr -d '\\r\\n|'" in text
    assert 'selector="GLOBAL"' in text
    assert "jsonfilter -e '@.selectors[0]'" in text
    assert 'conn_json="$(import_awg_connection "$proto" "$name" "$content" "$selector")"' in text
    assert '"selectors":["%s"],"usedBySelectors":["%s"]' in text


def test_openwrt_native_awg_apply_syncs_group_memberships_by_marker_only():
    text = INSTALLER.read_text(encoding="utf-8")
    assert 'AWG_GROUP_MARKER="# unified-managed-awg"' in text
    assert "proxy_sync_awg_group_memberships()" in text
    assert 'index($0, marker) == 0 { print }' in text
    assert 'print indent "- " proxy_names[i] " " marker' in text
    assert 'printf \'%s\\t%s\\n\' "$selector" "$(yaml_single_quote "$name")" >> "$members"' in text


def test_openwrt_native_awg_apply_fails_before_live_mutation_when_selector_missing():
    text = INSTALLER.read_text(encoding="utf-8")
    sync_call = (
        'proxy_sync_awg_group_memberships "$candidate" "$members" "$candidate_with_groups" '
        '|| { rm -rf "$tmp_dir"; return 36; }'
    )
    assert sync_call in text
    assert "if (!inserted[i]) exit 43" in text
    assert text.index(sync_call) < text.index('validation="$(cat "$candidate" | validate_profile_content)"')
    assert text.index(sync_call) < text.index('mv "$target_tmp" "$profile_real"')


def test_openwrt_native_awg_apply_preserves_unmarked_group_memberships():
    text = INSTALLER.read_text(encoding="utf-8")
    awg_sync = text.split("proxy_sync_awg_group_memberships()", 1)[1].split("apply_proxy_connections_openwrt()", 1)[0]
    assert "remove_proxy_from_groups" not in awg_sync
    assert "AWG-old" not in awg_sync
    assert 'index($0, marker) == 0 { print }' in awg_sync
    assert 'if (item != "") print indent "  - " item' in awg_sync


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
