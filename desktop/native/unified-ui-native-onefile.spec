# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

ROOT = Path.cwd()
NAME = os.environ.get('UNIFIED_UI_NATIVE_ONEFILE_NAME', 'Unified-UI-Native-windows-x64')

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
    a.binaries,
    a.datas,
    [],
    name=NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    uac_admin=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
