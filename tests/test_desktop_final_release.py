from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.5.0"
TAG = "v0.5.0-desktop-final-nonqt"
FINAL_ARTIFACTS = [
    "Unified-UI-Avalonia-Final-0.5.0-win-x64.zip",
    "Unified-UI-WPF-Final-0.5.0-win-x64.zip",
    "Unified-UI-Cpp-Win32-Final-0.5.0-win-x64.zip",
]
FORBIDDEN_USER_FACING = ["UserTest", "User Test", "user-test", "Preview.exe", "Preview v", "Production Candidate"]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_final_release_line_is_not_preview_or_user_test():
    sources = {
        "manifest": read("scripts/build_desktop_previews_manifest.py"),
        "readme": read("README.md"),
        "avalonia": read("desktop/previews/avalonia/Program.cs") + read("desktop/previews/avalonia/UnifiedUiAvaloniaPreview.csproj"),
        "wpf": read("desktop/previews/wpf/MainWindow.xaml") + read("desktop/previews/wpf/MainWindow.xaml.cs") + read("desktop/previews/wpf/UnifiedUiWpfPreview.csproj"),
        "cpp": read("desktop/previews/cpp-native/windows/main.cpp") + read("desktop/previews/cpp-native/windows/build-win32-preview.bat"),
        "bridge": read("desktop/previews/shared/native_bridge.py"),
    }
    assert TAG in sources["manifest"]
    assert TAG in sources["readme"]
    assert 'BRIDGE_VERSION = "0.5.0"' in sources["bridge"]
    for artifact in FINAL_ARTIFACTS:
        assert artifact in sources["manifest"]
        assert artifact in sources["readme"]
    for name, source in sources.items():
        assert VERSION in source, name
    user_facing = sources["manifest"] + sources["readme"] + sources["avalonia"] + sources["wpf"] + sources["cpp"]
    for forbidden in FORBIDDEN_USER_FACING:
        assert forbidden not in user_facing, f"user-facing final build must not contain {forbidden}"


def test_final_stack_is_non_qt_and_bridge_uses_non_qt_core():
    bridge = read("desktop/previews/shared/native_bridge.py")
    core = read("desktop/previews/shared/native_core.py")
    assert "from desktop.previews.shared.native_core import" in bridge
    for token in ["PySide6", "QtWidgets", "QApplication", "QMainWindow", "desktop.native.unified_ui_native"]:
        assert token not in bridge
        assert token not in core
    assert "qt_dependency" in read("scripts/build_desktop_previews_manifest.py")
    assert '"qt_dependency": False' in read("scripts/build_desktop_previews_manifest.py")


def test_final_apps_keep_full_qt_native_page_map_and_lifecycle_actions():
    pages = [
        "Маршрутизация", "Mihomo", "Соединения", "VLESS", "WireGuard", "AmneziaWG", "Hysteria2", "Trojan", "Mieru", "NaiveProxy",
        "Логи", "Mihomo Генератор", "Конфиг", "Ручной список", "Маршруты DNS", "Интерфейс", "Настройки",
    ]
    actions = [
        "/api/status", "/api/runtime/start", "/api/runtime/restart", "/api/runtime/stop", "/api/proxies", "/api/inventory",
        "/api/config", "/api/config/save", "/api/config/apply", "/api/subscription/add", "/api/subscription/update",
        "/api/subscription/delete", "/api/import/static", "/api/static/delete", "/api/dns/resolve", "/api/logs",
    ]
    sources = [
        read("desktop/previews/avalonia/Program.cs"),
        read("desktop/previews/wpf/MainWindow.xaml") + read("desktop/previews/wpf/MainWindow.xaml.cs"),
        read("desktop/previews/cpp-native/windows/main.cpp"),
    ]
    bridge = read("desktop/previews/shared/native_bridge.py")
    for source in sources:
        for page in pages:
            assert page in source
        for phrase in ["Mihomo runtime", "proxy-providers", "rule-providers", "config.yaml", "manual-proxy.yaml", "selector tiles"]:
            assert phrase in source
    for action in actions:
        assert action in bridge
