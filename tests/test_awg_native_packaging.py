from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_release_workflow_builds_pinned_official_arm64_runtime():
    text = (ROOT / ".github/workflows/build-user-archive.yml").read_text()
    assert "ubuntu-24.04-arm" in text
    assert "https://github.com/amnezia-vpn/amneziawg-go.git" in text
    assert "v3.1.20260814" in text
    assert "1b86b2ae0e493e7ea93f8c1a0f0cb6735b1551f1" in text
    assert "https://github.com/amnezia-vpn/amneziawg-tools.git" in text
    assert "v3.1.20260812" in text
    assert "ee0f0a9aa34ff0a0da4b3433b9512781cfe02843" in text
    assert "CGO_ENABLED=0 GOOS=linux GOARCH=arm64" in text
    assert "OFFICIAL_AWG_PROVENANCE.json" in text
    assert "package-root/unified-ui/bin" in text
    assert "(cd package-root/unified-ui/bin && sha256sum -c SHA256SUMS)" in text


def test_router_installer_atomically_installs_bundled_awg_runtime():
    text = (ROOT / "unified-ui/install.sh").read_text()
    assert 'install_bundled_awg_binary "amneziawg-go"' in text
    assert 'install_bundled_awg_binary "awg"' in text
    assert 'AWG_BIN_DIR="/opt/bin"' in text
    assert 'chmod 755 "$AWG_TMP"' in text
    assert 'mv -f "$AWG_TMP" "$AWG_DEST"' in text


def test_readme_documents_official_native_awg_runtime():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "## Официальный AmneziaWG runtime" in text
    assert "amnezia-vpn/amneziawg-go" in text
    assert "amnezia-vpn/amneziawg-tools" in text
    assert "/opt/bin/amneziawg-go" in text
    assert "/opt/bin/awg" in text
    assert "S1–S4" in text
    assert "### Rollback" in text


def test_readme_keeps_platform_release_lines_separate():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "### Независимые версии платформ" in text
    assert "releases/download/v3.0.1/unified-ui-routing.tar.gz" in text
    assert "releases/download/v3.0.0-openwrt/unified-ui-openwrt-v3.0.0.tar.gz" in text
    assert "releases/download/v3.0.0-mikrotik/unified-ui-mikrotik-docker-archive-v3.0.0.tar.gz" in text
    assert "releases/tag/v2.6.8-native" in text
    assert "releases/latest/download/unified-ui-openwrt.tar.gz" not in text


def test_mikrotik_dockerfile_builds_pinned_official_native_awg_runtime():
    text = (ROOT / "mikrotik/Dockerfile").read_text()
    assert "https://github.com/amnezia-vpn/amneziawg-go.git" in text
    assert "v3.1.20260814" in text
    assert "1b86b2ae0e493e7ea93f8c1a0f0cb6735b1551f1" in text
    assert "https://github.com/amnezia-vpn/amneziawg-tools.git" in text
    assert "v3.1.20260812" in text
    assert "ee0f0a9aa34ff0a0da4b3433b9512781cfe02843" in text
    assert 'CGO_ENABLED=0 GOOS=linux GOARCH=arm64 go build -trimpath -ldflags="-s -w" -o /out/amneziawg-go .' in text
    assert "make -C amneziawg-tools/src" in text
    assert "COPY --from=awg-runtime /out/amneziawg-go /opt/bin/amneziawg-go" in text
    assert "COPY --from=awg-runtime /out/awg /opt/bin/awg" in text
    assert "COPY --from=awg-runtime /out/OFFICIAL_AWG_PROVENANCE.json /opt/bin/OFFICIAL_AWG_PROVENANCE.json" in text
    assert "COPY --from=awg-runtime /out/SHA256SUMS /opt/bin/SHA256SUMS" in text
    assert "(cd /opt/bin && sha256sum -c SHA256SUMS)" in text
    assert "UNIFIED_AWG_GO_BIN=/opt/bin/amneziawg-go" in text
    assert "UNIFIED_AWG_BIN=/opt/bin/awg" in text


def test_mikrotik_entrypoint_restores_native_awg_before_mihomo_startup():
    text = (ROOT / "mikrotik/entrypoint.sh").read_text()
    assert "/data/unified-ui/awg-native" in text
    assert "/var/run/amneziawg" in text
    assert "/dev/net/tun" in text
    assert "UNIFIED_AWG_GO_BIN" in text
    assert "UNIFIED_AWG_BIN" in text
    assert "from routes.proxy_connections import _apply_to_mihomo" in text
    assert "_apply_to_mihomo(restart=False)" in text
    assert "log \"restoring native AmneziaWG interfaces\"" in text
    assert "MIHOMO_RESTART_CMD" in text
    assert "unified-mihomo-reload" in text
    assert "/configs?force=true" in text
    assert "MIHOMO_VALIDATE_CMD" in text
    assert text.index("log \"restoring native AmneziaWG interfaces\"") < text.index("log \"validating Mihomo config\"")
    assert text.index("log \"validating Mihomo config\"") < text.index("log \"starting Mihomo\"")


def test_mikrotik_docs_and_template_document_routeros_container_contract():
    readme = (ROOT / "mikrotik/README.md").read_text(encoding="utf-8")
    template = (ROOT / "mikrotik/routeros-install-template.rsc").read_text(encoding="utf-8")
    for text in (readme, template):
        assert "NET_ADMIN" in text
        assert "/dev/net/tun" in text
    assert "/opt/bin/amneziawg-go" in readme
    assert "/opt/bin/awg" in readme
    assert "type: direct" in readme
    assert "interface-name" in readme
    assert "routing-mark" in readme
