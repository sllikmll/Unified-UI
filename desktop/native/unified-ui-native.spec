# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
ROOT = Path.cwd()

# Keep this intentionally narrow: the native app uses Qt Widgets only.
# Do NOT collect all PySide6 submodules, otherwise PyInstaller drags in
# QtWebEngine and the build stops being a clean non-webview desktop app.
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'yaml',
    'services.mihomo_proxy_parsers',
    'services.mihomo_generator_proxies',
    'services.mihomo_proxy_config',
]

a = Analysis(
    [str(ROOT / 'desktop' / 'native' / 'unified_ui_native.py')],
    pathex=[str(ROOT), str(ROOT / 'unified-ui')],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'flask', 'gevent', 'geventwebsocket'],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Unified UI Native',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Unified UI Native',
)
app = BUNDLE(
    coll,
    name='Unified UI Native.app',
    icon=None,
    bundle_identifier='ru.dogonin.unifiedui.native',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'CFBundleName': 'Unified UI Native',
        'CFBundleDisplayName': 'Unified UI Native',
    },
)
