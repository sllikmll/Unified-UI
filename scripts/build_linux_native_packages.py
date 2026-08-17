#!/usr/bin/env python3
"""Build Linux x64 release packages for Unified UI Native.

Input is a PyInstaller onedir directory named "Unified UI Native". The script
produces:

* Unified-UI-Native-<version>-linux-x64-portable.tar.gz
* Unified-UI-Native-<version>-linux-x64.deb
* Unified-UI-Native-<version>-linux-x64.rpm
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

APP_NAME = "Unified UI Native"
PACKAGE_NAME = "unified-ui-native"
INSTALL_DIR = Path("/opt/unified-ui-native")
WRAPPER_PATH = Path("/usr/bin/unified-ui-native")
DESKTOP_PATH = Path("/usr/share/applications/unified-ui-native.desktop")
DEFAULT_EPOCH = 1_700_000_000

DEB_DEPENDS = (
    "libc6",
    "libgcc-s1",
    "libstdc++6",
    "libx11-6",
    "libxext6",
    "libxrender1",
    "libxcb1",
    "libxcb-cursor0",
    "libxcb-icccm4",
    "libxcb-image0",
    "libxcb-keysyms1",
    "libxcb-randr0",
    "libxcb-render0",
    "libxcb-render-util0",
    "libxcb-shape0",
    "libxcb-shm0",
    "libxcb-sync1",
    "libxcb-xfixes0",
    "libxcb-xinerama0",
    "libxcb-xkb1",
    "libxkbcommon0",
    "libxkbcommon-x11-0",
    "libdbus-1-3",
    "libfontconfig1",
    "libfreetype6",
    "libglib2.0-0",
    "libgl1",
    "libegl1",
)

RPM_REQUIRES = (
    "glibc",
    "libgcc",
    "libstdc++",
    "libX11",
    "libXext",
    "libXrender",
    "libxcb",
    "xcb-util-cursor",
    "xcb-util-wm",
    "xcb-util-image",
    "xcb-util-keysyms",
    "xcb-util-renderutil",
    "libxkbcommon",
    "libxkbcommon-x11",
    "dbus-libs",
    "fontconfig",
    "freetype",
    "glib2",
    "mesa-libGL",
    "mesa-libEGL",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="Release version used in output filenames and package metadata")
    parser.add_argument("--app-dir", type=Path, default=Path("dist") / APP_NAME, help='PyInstaller onedir directory named "Unified UI Native"')
    parser.add_argument("--out-dir", type=Path, default=Path("dist-artifacts"), help="Directory for release artifacts")
    parser.add_argument("--workdir", type=Path, default=Path("build/native-linux-packaging"), help="Temporary packaging workspace")
    parser.add_argument("--source-date-epoch", type=int, default=int(os.environ.get("SOURCE_DATE_EPOCH", DEFAULT_EPOCH)), help="Timestamp used for reproducible archives")
    parser.add_argument("--skip-build", action="store_true", help="Write package trees/specs but do not invoke tar, dpkg-deb, or rpmbuild")
    return parser.parse_args()


def output_names(version: str) -> dict[str, str]:
    return {
        "portable": f"Unified-UI-Native-{version}-linux-x64-portable.tar.gz",
        "deb": f"Unified-UI-Native-{version}-linux-x64.deb",
        "rpm": f"Unified-UI-Native-{version}-linux-x64.rpm",
    }


def validate_version(version: str) -> None:
    if not re.fullmatch(r"[0-9A-Za-z._+~]+", version):
        raise ValueError("version must contain only letters, digits, '.', '_', '+', or '~' for DEB/RPM metadata")


def validate_app_dir(app_dir: Path) -> Path:
    app_dir = app_dir.resolve()
    if app_dir.name != APP_NAME:
        raise FileNotFoundError(f'app dir must be named "{APP_NAME}": {app_dir}')
    if not app_dir.is_dir():
        raise FileNotFoundError(f"app dir not found: {app_dir}")
    executable = app_dir / APP_NAME
    if not executable.is_file():
        raise FileNotFoundError(f"main executable not found: {executable}")
    return app_dir


def find_tool(name: str) -> str:
    found = shutil.which(name)
    if not found:
        raise FileNotFoundError(f"required tool not found: {name}. Install it or add it to PATH.")
    return found


def wrapper_script() -> str:
    return f"""#!/bin/sh
exec "{INSTALL_DIR / APP_NAME}" "$@"
"""


def desktop_file() -> str:
    return f"""[Desktop Entry]
Type=Application
Name={APP_NAME}
Exec={WRAPPER_PATH.name}
Terminal=false
Categories=Network;Utility;
"""


def deb_control(version: str) -> str:
    return f"""Package: {PACKAGE_NAME}
Version: {version}
Section: utils
Priority: optional
Architecture: amd64
Maintainer: sllikmll
Depends: {", ".join(DEB_DEPENDS)}
Description: Unified UI Native desktop application
 Native Qt desktop application for Unified UI.
"""


def rpm_spec(version: str) -> str:
    requires = "\n".join(f"Requires: {dep}" for dep in RPM_REQUIRES)
    return f"""Name: {PACKAGE_NAME}
Version: {version}
Release: 1
Summary: Unified UI Native desktop application
License: Proprietary
URL: https://github.com/sllikmll/Unified-UI
Source0: %{{name}}-%{{version}}.tar.gz
BuildArch: x86_64
{requires}
AutoReqProv: no

%global _build_id_links none

%description
Native Qt desktop application for Unified UI.

%prep
%setup -q -n payload

%build

%install
rm -rf "%{{buildroot}}"
mkdir -p "%{{buildroot}}"
cp -a opt usr "%{{buildroot}}/"

%files
%attr(0755,root,root) {WRAPPER_PATH}
{DESKTOP_PATH}
{INSTALL_DIR}
"""


def copy_app_dir(app_dir: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(app_dir, dest, symlinks=True)


def write_text_executable(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    path.chmod(0o755)


def write_text_file(path: Path, text: str, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    path.chmod(mode)


def normalize_tree(path: Path, epoch: int) -> None:
    for item in sorted(path.rglob("*")):
        if item.is_symlink():
            continue
        if item.is_dir():
            item.chmod(0o755)
        elif item.name == APP_NAME or item.parent == path / "usr" / "bin":
            item.chmod(0o755)
        else:
            current = item.stat().st_mode & 0o777
            item.chmod(0o755 if current & 0o111 else 0o644)
        os.utime(item, (epoch, epoch), follow_symlinks=False)
    os.utime(path, (epoch, epoch), follow_symlinks=False)


def build_install_tree(app_dir: Path, root: Path, epoch: int) -> None:
    if root.exists():
        shutil.rmtree(root)
    copy_app_dir(app_dir, root / INSTALL_DIR.relative_to("/"))
    write_text_executable(root / WRAPPER_PATH.relative_to("/"), wrapper_script())
    write_text_file(root / DESKTOP_PATH.relative_to("/"), desktop_file())
    normalize_tree(root, epoch)


def build_deb_tree(app_dir: Path, root: Path, version: str, epoch: int) -> None:
    build_install_tree(app_dir, root, epoch)
    write_text_file(root / "DEBIAN" / "control", deb_control(version))
    normalize_tree(root, epoch)


def run_checked(cmd: list[str], *, env: dict[str, str], cwd: Path | None = None) -> None:
    result = subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.returncode != 0:
        raise RuntimeError(f"command failed with exit code {result.returncode}: {' '.join(cmd)}")


def build_portable(tar: str, stage: Path, out: Path, epoch: int, env: dict[str, str]) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    run_checked(
        [
            tar,
            "--sort=name",
            f"--mtime=@{epoch}",
            "--owner=0",
            "--group=0",
            "--numeric-owner",
            "-czf",
            str(out),
            APP_NAME,
        ],
        cwd=stage,
        env=env,
    )


def build_deb(dpkg_deb: str, tree: Path, out: Path, env: dict[str, str]) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    run_checked([dpkg_deb, "--root-owner-group", "-Zgzip", "-z9", "--build", str(tree), str(out)], env=env)


def build_rpm_source(tar: str, install_tree: Path, source: Path, epoch: int, env: dict[str, str]) -> None:
    payload = source.parent / "payload"
    if payload.exists():
        shutil.rmtree(payload)
    shutil.copytree(install_tree, payload, symlinks=True)
    normalize_tree(payload, epoch)
    if source.exists():
        source.unlink()
    run_checked(
        [
            tar,
            "--sort=name",
            f"--mtime=@{epoch}",
            "--owner=0",
            "--group=0",
            "--numeric-owner",
            "-czf",
            str(source),
            "payload",
        ],
        cwd=source.parent,
        env=env,
    )


def build_rpm(rpmbuild: str, tar_tool: str, app_dir: Path, topdir: Path, out: Path, version: str, epoch: int, env: dict[str, str]) -> None:
    for sub in ("BUILD", "BUILDROOT", "RPMS", "SOURCES", "SPECS", "SRPMS"):
        (topdir / sub).mkdir(parents=True, exist_ok=True)
    install_tree = topdir / "install-tree"
    build_install_tree(app_dir, install_tree, epoch)
    source = topdir / "SOURCES" / f"{PACKAGE_NAME}-{version}.tar.gz"
    build_rpm_source(tar_tool, install_tree, source, epoch, env)
    spec = topdir / "SPECS" / f"{PACKAGE_NAME}.spec"
    write_text_file(spec, rpm_spec(version))
    run_checked(
        [
            rpmbuild,
            "-bb",
            "--target",
            "x86_64",
            "--define",
            f"_topdir {topdir}",
            "--define",
            "_source_filedigest_algorithm 8",
            "--define",
            "_binary_filedigest_algorithm 8",
            "--define",
            f"source_date_epoch {epoch}",
            "--define",
            "use_source_date_epoch_as_buildtime Y",
            "--define",
            "clamp_mtime_to_source_date_epoch Y",
            str(spec),
        ],
        env=env,
    )
    candidates = sorted((topdir / "RPMS").rglob(f"{PACKAGE_NAME}-{version}-1.x86_64.rpm"))
    if not candidates:
        raise RuntimeError(f"rpmbuild did not produce expected x86_64 rpm under {topdir / 'RPMS'}")
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    shutil.move(str(candidates[0]), out)


def main() -> int:
    args = parse_args()
    try:
        validate_version(args.version)
        app_dir = validate_app_dir(args.app_dir)
        names = output_names(args.version)
        out_dir = args.out_dir.resolve()
        workdir = args.workdir.resolve()
        portable_stage = workdir / "portable"
        deb_tree = workdir / "deb"
        rpm_topdir = workdir / "rpm"
        env = os.environ.copy()
        env["SOURCE_DATE_EPOCH"] = str(args.source_date_epoch)

        if workdir.exists():
            shutil.rmtree(workdir)
        out_dir.mkdir(parents=True, exist_ok=True)
        workdir.mkdir(parents=True, exist_ok=True)

        copy_app_dir(app_dir, portable_stage / APP_NAME)
        normalize_tree(portable_stage, args.source_date_epoch)
        build_deb_tree(app_dir, deb_tree, args.version, args.source_date_epoch)
        (rpm_topdir / "SPECS").mkdir(parents=True, exist_ok=True)
        write_text_file(rpm_topdir / "SPECS" / f"{PACKAGE_NAME}.spec", rpm_spec(args.version))

        if args.skip_build:
            print(f"wrote packaging workspace: {workdir}")
            return 0

        tar_tool = find_tool("tar")
        dpkg_deb = find_tool("dpkg-deb")
        rpmbuild = find_tool("rpmbuild")
        build_portable(tar_tool, portable_stage, out_dir / names["portable"], args.source_date_epoch, env)
        build_deb(dpkg_deb, deb_tree, out_dir / names["deb"], env)
        build_rpm(rpmbuild, tar_tool, app_dir, rpm_topdir, out_dir / names["rpm"], args.version, args.source_date_epoch, env)
        for name in names.values():
            path = out_dir / name
            if not path.is_file():
                raise RuntimeError(f"artifact not produced: {path}")
            print(f"built {path} ({path.stat().st_size} bytes)")
        return 0
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
