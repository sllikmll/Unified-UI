from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import re
import subprocess
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "openwrt" / "install-openwrt-prototype.sh"
COMPAT = ROOT / "openwrt" / "openwrt-fetch-compat.js"
BUILDER = ROOT / "scripts" / "build_openwrt_archive.py"
SPEC = importlib.util.spec_from_file_location("build_openwrt_archive", BUILDER)
assert SPEC is not None and SPEC.loader is not None
openwrt_builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(openwrt_builder)


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
    assert "printf '%s\\n' \"$addresses\"" in text
    assert "usleep 100000" in text
    assert '"$AWG_GO_BIN" -f "$iface"' in text
    assert '/proc/[0-9]*/cmdline' in text
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
    assert 'ACTIVE_DESIRED="$STATE_DIR/active-desired"' in text
    assert 'ACTIVE_CONFIG_DIR="$STATE_DIR/active-configs"' in text
    assert "persist_active_desired()" in text
    assert 'active_conf="$ACTIVE_CONFIG_DIR/$iface.conf"' in text
    assert '[ ! -s "$ACTIVE_DESIRED" ] || reconcile_file "$ACTIVE_DESIRED" || true' in text
    assert ': > "$ACTIVE_DESIRED"' in text


def test_openwrt_proxy_and_subscription_apply_restore_awg_on_commit_or_restart_failure():
    text = INSTALLER.read_text(encoding="utf-8")
    assert 'AWG_ACTIVE_DESIRED_FILE="$AWG_STATE_DIR/active-desired"' in text
    assert "awg_snapshot_state()" in text
    assert "awg_restore_state()" in text
    proxy_apply = text.split("apply_proxy_connections_openwrt()", 1)[1].split("PANEL_SUBSCRIPTION_URL_FILE=", 1)[0]
    assert 'awg_snapshot_state "$tmp_dir/awg-snapshot"' in proxy_apply
    assert 'return 33' in proxy_apply and 'awg_restore_state "$tmp_dir/awg-snapshot"' in proxy_apply
    assert 'return 35' in proxy_apply and 'awg_restore_state "$tmp_dir/awg-snapshot"' in proxy_apply
    assert 'return 37' in proxy_apply and "mihomo_get /version" in proxy_apply
    subscription_apply = text.split("subscription_import_openwrt()", 1)[1].split("DNS_ROUTES_DIR=", 1)[0]
    assert 'awg_snapshot_state "$tmp_dir/awg-snapshot"' in subscription_apply
    assert 'return 18' in subscription_apply and 'awg_restore_state "$tmp_dir/awg-snapshot"' in subscription_apply
    assert 'return 44' in subscription_apply and 'awg_restore_state "$tmp_dir/awg-snapshot"' in subscription_apply
    assert 'return 19' in subscription_apply and "mihomo_get /version" in subscription_apply


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


def test_openwrt_native_awg_registry_upserts_and_deletes_only_requested_id():
    text = INSTALLER.read_text(encoding="utf-8")
    assert "registry_upsert_record()" in text
    assert 'jsonfilter -i "$PROXY_REGISTRY" -e "@.connections[$idx]"' in text
    assert 'registry_upsert_record "$record" "$id" "$name" amnezia' in text
    assert "registry_delete_id()" in text
    item_route = text.split("/proxy-connections-item/*)", 1)[1].split("/dns-routes)", 1)[0]
    assert 'registry_delete_id "$id"' in item_route
    assert 'rm -f "$PROXY_REGISTRY"' not in item_route
    assert "connection_not_found" in item_route
    assert 'mv "$registry_backup" "$PROXY_REGISTRY"' in item_route


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


def _stage_openwrt_archive_payload(root: Path, *, source_date_epoch: int) -> Path:
    payload = root / openwrt_builder.ARCHIVE_ROOT
    (payload / "bin").mkdir(parents=True)
    (payload / "www" / "unified-ui").mkdir(parents=True)
    (payload / "install.sh").write_text("#!/bin/sh\necho install\n", encoding="utf-8")
    (payload / "install.sh").chmod(0o755)
    (payload / "README.md").write_text("readme\n", encoding="utf-8")
    (payload / "bin" / "mihomo").write_bytes(b"mihomo")
    (payload / "bin" / "mihomo").chmod(0o755)
    (payload / "www" / "unified-ui" / "index.html").write_text("<!doctype html>\n", encoding="utf-8")
    openwrt_builder.write_build_json(
        payload / "BUILD.json",
        version="1.2.3",
        update_url="https://example.test/update.tar.gz",
        source_date_epoch=source_date_epoch,
    )
    return payload


def test_openwrt_archive_is_reproducible_and_normalizes_metadata(tmp_path: Path):
    builder_text = BUILDER.read_text(encoding="utf-8")
    assert 'sess["csrf"] = "openwrt-static-csrf"' in builder_text
    assert 'html = html.replace(str(state), "/etc/unified-ui")' in builder_text

    epoch = 1_700_000_123
    archives: list[Path] = []
    for idx in range(2):
        build_dir = tmp_path / f"build-{idx}"
        payload = _stage_openwrt_archive_payload(build_dir, source_date_epoch=epoch)
        archive = tmp_path / f"out-{idx}" / "unified-ui-openwrt.tar.gz"
        openwrt_builder.build_archive(payload, archive, source_date_epoch=epoch)
        archives.append(archive)

    first_bytes = archives[0].read_bytes()
    second_bytes = archives[1].read_bytes()
    assert first_bytes == second_bytes
    assert hashlib.sha256(first_bytes).hexdigest() == hashlib.sha256(second_bytes).hexdigest()

    sha_path = tmp_path / "unified-ui-openwrt.tar.gz.sha256"
    digest = openwrt_builder.write_sha256(archives[0], sha_path)
    assert sha_path.read_text(encoding="utf-8") == f"{digest}  {archives[0].name}\n"

    header = first_bytes[:10]
    assert header[:3] == b"\x1f\x8b\x08"
    assert int.from_bytes(header[4:8], "little") == epoch
    assert not (header[3] & gzip.FNAME)

    with tarfile.open(archives[0], "r:gz") as tar:
        members = tar.getmembers()
        names = [member.name for member in members]
        assert names == sorted(names)

        by_name = {member.name: member for member in members}
        build_json = by_name[f"{openwrt_builder.ARCHIVE_ROOT}/BUILD.json"]
        install = by_name[f"{openwrt_builder.ARCHIVE_ROOT}/install.sh"]
        readme = by_name[f"{openwrt_builder.ARCHIVE_ROOT}/README.md"]
        mihomo = by_name[f"{openwrt_builder.ARCHIVE_ROOT}/bin/mihomo"]
        index = by_name[f"{openwrt_builder.ARCHIVE_ROOT}/www/unified-ui/index.html"]

        for member in members:
            assert member.uid == 0
            assert member.gid == 0
            assert member.uname == ""
            assert member.gname == ""
            assert member.mtime == epoch
            if member.isdir():
                assert member.mode == 0o755

        assert install.mode == 0o755
        assert mihomo.mode == 0o755
        assert readme.mode == 0o644
        assert build_json.mode == 0o644
        assert index.mode == 0o644

        extracted_build = json.loads(tar.extractfile(build_json).read().decode("utf-8"))
        assert extracted_build == {
            "version": "1.2.3",
            "release_date": "2023-11-14T22:15:23Z",
            "update_url": "https://example.test/update.tar.gz",
        }
