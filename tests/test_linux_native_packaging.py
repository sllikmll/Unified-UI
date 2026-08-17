from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_linux_native_packages.py"
SPEC = importlib.util.spec_from_file_location("build_linux_native_packages", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
linux_pkg = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(linux_pkg)


def fake_onedir(tmp_path: Path) -> Path:
    app_dir = tmp_path / linux_pkg.APP_NAME
    app_dir.mkdir()
    exe = app_dir / linux_pkg.APP_NAME
    exe.write_bytes(b"fake linux executable")
    exe.chmod(0o755)
    (app_dir / "_internal").mkdir()
    (app_dir / "_internal" / "libQt6Core.so.6").write_bytes(b"fake qt")
    return app_dir


def test_output_names_are_exact():
    assert linux_pkg.output_names("2.6.7") == {
        "portable": "Unified-UI-Native-2.6.7-linux-x64-portable.tar.gz",
        "deb": "Unified-UI-Native-2.6.7-linux-x64.deb",
        "rpm": "Unified-UI-Native-2.6.7-linux-x64.rpm",
    }


def test_deb_tree_has_required_layout_metadata_and_qt_xcb_dependencies(tmp_path: Path):
    app_dir = fake_onedir(tmp_path)
    root = tmp_path / "deb-root"

    linux_pkg.build_deb_tree(app_dir, root, "2.6.7", 1_700_000_000)

    assert (root / "opt" / "unified-ui-native" / linux_pkg.APP_NAME).is_file()
    wrapper = root / "usr" / "bin" / "unified-ui-native"
    assert wrapper.read_text(encoding="utf-8") == '#!/bin/sh\nexec "/opt/unified-ui-native/Unified UI Native" "$@"\n'
    assert wrapper.stat().st_mode & 0o777 == 0o755

    desktop = (root / "usr" / "share" / "applications" / "unified-ui-native.desktop").read_text(encoding="utf-8")
    assert "Name=Unified UI Native" in desktop
    assert "Exec=unified-ui-native" in desktop
    assert "Categories=Network;Utility;" in desktop

    control = (root / "DEBIAN" / "control").read_text(encoding="utf-8")
    assert "Package: unified-ui-native" in control
    assert "Version: 2.6.7" in control
    assert "Architecture: amd64" in control
    assert "libxcb-cursor0" in control
    assert "libxcb-xinerama0" in control
    assert "libxkbcommon-x11-0" in control
    assert "libgl1" in control
    assert "libegl1" in control


def test_rpm_spec_has_required_arch_layout_license_and_qt_xcb_dependencies():
    spec = linux_pkg.rpm_spec("2.6.7")

    assert "Name: unified-ui-native" in spec
    assert "Version: 2.6.7" in spec
    assert "License: Proprietary" in spec
    assert "Source0: %{name}-%{version}.tar.gz" in spec
    assert "BuildArch: x86_64" in spec
    assert "AutoReqProv: no" in spec
    assert "%attr(0755,root,root) /usr/bin/unified-ui-native" in spec
    assert "/usr/share/applications/unified-ui-native.desktop" in spec
    assert "/opt/unified-ui-native" in spec
    assert "Requires: xcb-util-cursor" in spec
    assert "Requires: xcb-util-wm" in spec
    assert "Requires: libxkbcommon-x11" in spec
    assert "Requires: mesa-libGL" in spec
    assert "Requires: mesa-libEGL" in spec


def test_build_commands_use_reproducible_flags_and_exact_artifact_names(tmp_path: Path, monkeypatch):
    app_dir = fake_onedir(tmp_path)
    out_dir = tmp_path / "out"
    workdir = tmp_path / "work"
    commands: list[list[str]] = []

    def fake_run_checked(cmd: list[str], *, env: dict[str, str], cwd: Path | None = None) -> None:
        commands.append(cmd)
        if cmd[0] == "tar" and "-czf" in cmd:
            Path(cmd[cmd.index("-czf") + 1]).write_bytes(b"archive")
        if cmd[0] == "dpkg-deb":
            Path(cmd[-1]).write_bytes(b"deb")
        if cmd[0] == "rpmbuild":
            rpm = workdir / "rpm" / "RPMS" / "x86_64" / "unified-ui-native-2.6.7-1.x86_64.rpm"
            rpm.parent.mkdir(parents=True, exist_ok=True)
            rpm.write_bytes(b"rpm")

    monkeypatch.setattr(linux_pkg, "run_checked", fake_run_checked)

    env = {"SOURCE_DATE_EPOCH": "1700000000"}
    portable_stage = workdir / "portable"
    linux_pkg.copy_app_dir(app_dir, portable_stage / linux_pkg.APP_NAME)
    linux_pkg.normalize_tree(portable_stage, 1_700_000_000)
    deb_tree = workdir / "deb"
    linux_pkg.build_deb_tree(app_dir, deb_tree, "2.6.7", 1_700_000_000)

    names = linux_pkg.output_names("2.6.7")
    linux_pkg.build_portable("tar", portable_stage, out_dir / names["portable"], 1_700_000_000, env)
    linux_pkg.build_deb("dpkg-deb", deb_tree, out_dir / names["deb"], env)
    linux_pkg.build_rpm("rpmbuild", "tar", app_dir, workdir / "rpm", out_dir / names["rpm"], "2.6.7", 1_700_000_000, env)

    assert (out_dir / "Unified-UI-Native-2.6.7-linux-x64-portable.tar.gz").read_bytes() == b"archive"
    assert (out_dir / "Unified-UI-Native-2.6.7-linux-x64.deb").read_bytes() == b"deb"
    assert (out_dir / "Unified-UI-Native-2.6.7-linux-x64.rpm").read_bytes() == b"rpm"

    portable_tar = commands[0]
    assert portable_tar[:5] == ["tar", "--sort=name", "--mtime=@1700000000", "--owner=0", "--group=0"]
    assert "--numeric-owner" in portable_tar
    assert commands[1][:5] == ["dpkg-deb", "--root-owner-group", "-Zgzip", "-z9", "--build"]
    assert any(cmd[0] == "rpmbuild" and "--target" in cmd and "x86_64" in cmd for cmd in commands)


def test_missing_tool_error_is_clear(monkeypatch):
    monkeypatch.setattr(linux_pkg.shutil, "which", lambda _name: None)

    try:
        linux_pkg.find_tool("rpmbuild")
    except FileNotFoundError as exc:
        assert "required tool not found: rpmbuild" in str(exc)
        assert "Install it or add it to PATH" in str(exc)
    else:
        raise AssertionError("expected missing tool error")
