from pathlib import Path

from scripts import build_windows_nsis_installer as nsis


def test_windows_nsis_script_is_unicode_and_has_no_mojibake(tmp_path: Path):
    app_exe = tmp_path / "Unified-UI-Native-2.6.4-x64.exe"
    app_exe.write_bytes(b"MZ\0fake")
    out_exe = tmp_path / "Unified-UI-Native-Setup-2.6.4-x64.exe"

    script = nsis.installer_script(version="2.6.4", app_exe=app_exe, out_exe=out_exe)

    assert "Unicode true" in script
    assert "Установка Unified UI Native" in script
    assert "Запустить Unified UI Native" in script
    assert "РЈ" not in script
    assert "Рџ" not in script
    assert "Рњ" not in script
    assert "Рќ" not in script

    nsi = tmp_path / "installer.nsi"
    nsi.write_text(script, encoding="utf-8-sig")
    assert nsi.read_bytes().startswith(b"\xef\xbb\xbf")


def test_windows_nsis_generator_skip_build_writes_bom_script(tmp_path: Path, monkeypatch):
    app_exe = tmp_path / "app.exe"
    app_exe.write_bytes(b"MZ\0fake")
    out_exe = tmp_path / "setup.exe"
    workdir = tmp_path / "work"

    monkeypatch.setattr(
        "sys.argv",
        [
            "build_windows_nsis_installer.py",
            "--version",
            "2.6.4",
            "--app-exe",
            str(app_exe),
            "--out",
            str(out_exe),
            "--workdir",
            str(workdir),
            "--skip-build",
        ],
    )

    assert nsis.main() == 0
    generated = workdir / "Unified-UI-Native-Setup.nsi"
    assert generated.is_file()
    assert generated.read_bytes().startswith(b"\xef\xbb\xbf")
    text = generated.read_text(encoding="utf-8-sig")
    assert "Unicode true" in text
    assert "Мастер установит Unified UI Native" in text
