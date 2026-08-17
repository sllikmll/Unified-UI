from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_windows_native_workflow_builds_and_smokes_all_artifact_forms():
    workflow = (ROOT / ".github/workflows/build-native-windows.yml").read_text(encoding="utf-8")
    onefile = (ROOT / "desktop/native/unified-ui-native-onefile.spec").read_text(encoding="utf-8")

    assert "runs-on: windows-latest" in workflow
    assert "python-version: \"3.12\"" in workflow
    assert "unified-ui-native.spec" in workflow
    assert "unified-ui-native-onefile.spec" in workflow
    assert workflow.count("--smoke") >= 2
    assert "build_windows_nsis_installer.py" in workflow
    assert "Unified-UI-Native-$env:VERSION-windows-x64-portable.zip" in workflow
    assert "Unified-UI-Native-$env:VERSION-x64.exe" in workflow
    assert "Unified-UI-Native-Setup-$env:VERSION-x64.exe" in workflow
    assert "SHA256SUMS-windows-x64" in workflow
    assert "UNIFIED_UI_NATIVE_ONEFILE_NAME" in workflow

    assert "a.binaries" in onefile
    assert "a.datas" in onefile
    assert "exclude_binaries=True" not in onefile
    assert "COLLECT(" not in onefile
    assert "BUNDLE(" not in onefile
