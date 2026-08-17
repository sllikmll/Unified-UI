# Unified UI Native Desktop

## Релиз

Tag: `v2.6.8-native`.

Поддерживаемые пакеты:

- macOS Apple Silicon `.app.zip`;
- Windows x64 portable ZIP, onefile EXE и NSIS installer;
- Linux x64 portable tar, DEB и RPM.

Это Qt Widgets/PySide6 приложение без WebView и Flask UI. Mihomo загружается/проверяется приложением и управляется через controller API.

## Сборка

- macOS: `desktop/native/unified-ui-native.spec`;
- Windows onefile: `desktop/native/unified-ui-native-onefile.spec`;
- Windows CI: `.github/workflows/build-native-windows.yml`;
- Linux packages: `scripts/build_linux_native_packages.py`;
- manifest/checksums: `scripts/build_native_release_manifest.py`.

## Проверка

Каждая frozen сборка должна пройти `--smoke`. Для Windows дополнительно проверяется реальное появление главного окна на win11/MINI перед публикацией. macOS candidate проверен запуском `.app` и Qt screenshot grab.

## Удаление/rollback

- portable: удалить каталог приложения;
- Windows installer: штатный `Uninstall.exe`;
- DEB: `sudo apt remove unified-ui-native`;
- RPM: `sudo rpm -e unified-ui-native`.

Пользовательские runtime/config данные удаляются отдельно и не должны молча стираться uninstall-пакетом.
