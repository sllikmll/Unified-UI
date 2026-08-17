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


def test_router_installer_atomically_installs_bundled_awg_runtime():
    text = (ROOT / "unified-ui/install.sh").read_text()
    assert 'install_bundled_awg_binary "amneziawg-go"' in text
    assert 'install_bundled_awg_binary "awg"' in text
    assert 'AWG_BIN_DIR="/opt/bin"' in text
    assert 'chmod 755 "$AWG_TMP"' in text
    assert 'mv -f "$AWG_TMP" "$AWG_DEST"' in text
