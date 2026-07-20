# Unified UI

**Unified UI** — единая панель управления Mihomo, маршрутизацией, selector-группами, подключениями и service-rules для роутеров, серверов и desktop-устройств.

Это отдельная Unified UI сборка под инфраструктуру `sllikmll`: одна панель вместо набора разрозненных dashboard’ов и временных обёрток.

## Быстрые ссылки

| Что | Ссылка |
|---|---|
| Репозиторий | https://github.com/sllikmll/Unified-UI |
| Последний desktop/docker релиз | https://github.com/sllikmll/Unified-UI/releases/tag/v2.5.1 |
| Docker image | `ghcr.io/sllikmll/unified-ui:latest` |
| Версия Mihomo в desktop/docker сборках | `v1.19.29` |

---

## Где работает

| Платформа | UI | Runtime | Назначение |
|---|---:|---|---|
| **Keenetic / Entware** | `http://<router-ip>:8088/` | Python/Flask + standalone Mihomo | Полная роутерная панель с backend, registry, installer/self-update |
| **OpenWrt** | `http://<router-ip>/unified-ui/` | Static full-panel + CGI API + standalone Mihomo | Версия без Python stack на маленьком overlay |
| **MikroTik / RouterOS container** | `http://<router-ip>:8088/` | RouterOS container: Unified UI + Mihomo | Full-панель внутри RouterOS container |
| **Docker / Compose** | `http://localhost:8088/` | Container: Flask Unified UI + Mihomo | Серверы, NAS, homelab, desktop Docker |
| **Desktop Electron** | Нативное окно приложения | Electron + Flask backend + Mihomo | Локальный proxy или full-system TUN routing |
| **Desktop Qt** | Нативное Qt-окно | PySide6/QtWebEngine + Flask backend + Mihomo | Та же веб-панель в Qt shell |

---

## Возможности

| Раздел | Что делает |
|---|---|
| **Маршрутизация** | Runtime-переключение selector-групп Mihomo, режим плиток/списков, ping одного или всех узлов |
| **Mihomo** | Редактирование активного `config.yaml`, обновление подписок, YAML-инструменты |
| **Соединения** | Активные Mihomo connections, фильтры, детали, принудительный разрыв соединений |
| **DAT GeoIP / GeoSite** | Обновление, просмотр и редактирование локальных GeoIP/GeoSite/rule-provider данных |
| **Маршруты DNS** | Keenetic-style DNS/domain/IP/service lists с привязкой к интерфейсам роутера |
| **WireGuard / Amnezia / Hysteria2 / VLESS / Trojan / Mieru / NaiveProxy** | Импорт подключений ссылкой или файлом, добавление в selector-группы |
| **Mihomo Генератор** | Встроенный генератор конфига без iframe и отдельной страницы |
| **Файлы / Команды / Настройки** | File manager, runtime команды, обновления, env/status |

---

# Установка

## 1. Docker / Docker Compose

Готовый образ:

```text
ghcr.io/sllikmll/unified-ui:latest
ghcr.io/sllikmll/unified-ui:2.5.1
```

Быстрый запуск proxy-mode:

```sh
docker run -d \
  --name unified-ui \
  --restart unless-stopped \
  -p 8088:8088 \
  -p 9090:9090 \
  -p 7890:7890 \
  -e UNIFIED_UI_AUTH_USER=admin \
  -e UNIFIED_UI_AUTH_PASSWORD=admin \
  -v unified-ui-state:/data/unified-ui \
  -v unified-ui-mihomo:/etc/mihomo \
  ghcr.io/sllikmll/unified-ui:latest
```

После запуска:

```text
UI:          http://localhost:8088/
Mihomo API:  http://localhost:9090/
Mixed proxy: 127.0.0.1:7890
DNS:         127.0.0.1:1053 optional
```

Compose:

```sh
curl -fL -o docker-compose.yml \
  https://raw.githubusercontent.com/sllikmll/Unified-UI/main/docker-compose.yml

docker compose up -d
```

### Docker TUN / полная системная маршрутизация

По умолчанию Docker стартует безопасно: **без TUN**, только UI + mixed proxy.

Для TUN-режима:

```sh
docker compose --profile tun up -d unified-ui-tun
```

TUN profile включает:

```yaml
network_mode: host
cap_add:
  - NET_ADMIN
devices:
  - /dev/net/tun:/dev/net/tun
environment:
  MIHOMO_ENABLE_TUN: "true"
```

Если `/etc/mihomo/config.yaml` уже существует, TUN-блок добавляется idempotent-миграцией с backup:

```text
config.yaml.pre-tun.bak
```

> `UNIFIED_UI_AUTH_PASSWORD` и `MIHOMO_SUB_URL` нужны только на первом запуске. После создания `/data/unified-ui/auth.json` и `/etc/mihomo/config.yaml` их лучше убрать из env/compose.

---

## 2. Desktop Electron

Артефакты релиза `v2.5.1`:

| ОС | Файл |
|---|---|
| macOS Apple Silicon | `Unified-UI-2.5.1-arm64.dmg` |
| Windows x64 | `Unified-UI-Setup-2.5.1-x64.exe` |
| Linux Debian/Ubuntu | `Unified-UI-2.5.1-amd64.deb` |
| Linux RPM distros | `Unified-UI-2.5.1-x86_64.rpm` |
| Linux portable | `Unified-UI-2.5.1-x86_64.AppImage` |

Локальные порты Electron-сборки:

```text
Unified UI:  http://127.0.0.1:18088/
Mihomo API:  http://127.0.0.1:19090/
Mixed proxy: 127.0.0.1:17890
DNS:         127.0.0.1:15353
```

На первом запуске приложение:

1. создаёт runtime-папку в профиле пользователя;
2. скачивает подходящий Mihomo binary, если его нет;
3. создаёт Python venv;
4. ставит зависимости из `unified-ui/requirements.txt`;
5. запускает локальный Flask backend и Mihomo.

### Electron TUN mode

Включение из меню:

```text
Routing → Full-system TUN routing
```

Или через env:

```sh
UNIFIED_UI_ENABLE_TUN=1 "Unified UI.app/Contents/MacOS/Unified UI"
```

В TUN-режиме Unified UI добавляет в Mihomo:

```yaml
tun:
  enable: true
  stack: system
  auto-route: true
  auto-detect-interface: true
  strict-route: false
  dns-hijack:
    - any:53
```

На macOS Mihomo запрашивает administrator prompt через `osascript`, потому что `utun/routes` без повышенных прав не поднять. На Linux нужны root/capabilities. На Windows — запуск с правами администратора для Wintun/system routes.

Обычный режим без TUN безопасный: только локальный proxy, без перехвата всего трафика системы.

---

## 3. Desktop Qt

Qt-сборка — отдельная нативная оболочка:

```text
Unified UI Qt
```

Артефакт:

```text
Unified-UI-Qt-2.5.1-arm64.dmg
```

Что внутри:

- PySide6;
- QtWebEngine;
- нативное окно;
- верхняя панель в стиле Unified UI;
- кнопки `Обновить`, `Runtime`, `TUN ON/OFF`;
- тот же Flask backend;
- тот же Mihomo runtime;
- тот же веб-интерфейс внутри окна.

Порты Qt-сборки:

```text
Unified UI:  http://127.0.0.1:18188/
Mihomo API:  http://127.0.0.1:19190/
Mixed proxy: 127.0.0.1:17990
DNS:         127.0.0.1:15354
```

Проверка из исходников:

```sh
python3 -m pip install -r desktop/qt/requirements-qt.txt
python3 desktop/qt/unified_ui_qt.py --smoke
python3 desktop/qt/unified_ui_qt.py
```

Сборка macOS `.app/.dmg`:

```sh
pyinstaller --noconfirm \
  --distpath dist/qt \
  --workpath build/qt \
  desktop/qt/unified-ui-qt.spec

hdiutil create -volname 'Unified UI Qt' \
  -srcfolder 'dist/qt/Unified UI Qt.app' \
  -ov -format UDZO \
  'dist/qt/Unified-UI-Qt-2.5.1-arm64.dmg'
```

---

## 4. Keenetic / Entware

### Требования

- установлен Entware;
- есть shell-доступ к роутеру;
- свободен порт `8088` или доступен запасной порт;
- желательно уже иметь рабочий Mihomo config.

### Установка

```sh
cd /opt
curl -fL -o unified-ui-routing.tar.gz \
  "https://github.com/sllikmll/Unified-UI/releases/latest/download/unified-ui-routing.tar.gz"
tar -xzf unified-ui-routing.tar.gz
cd unified-ui
sh install.sh
```

После установки:

```text
http://<IP_роутера>:8088/
```

### Что ставит Keenetic installer

- Python/Flask/gevent панель;
- bundled wheelhouse для Python-зависимостей;
- standalone Mihomo core;
- layout `/opt/etc/mihomo`;
- symlink `config.yaml -> profiles/default.yaml`;
- `/opt/etc/mihomo/restart-mihomo.sh`;
- optional `xk-geodat`;
- optional proxy-client artifacts;
- init-сервис `/opt/etc/init.d/S99unified-ui001`.

### Обновление Keenetic

Через UI:

```text
Настройки → Проверить обновления → Установить
```

Или вручную:

```sh
/opt/etc/unified-ui/scripts/update_unified_ui.sh
```

---

## 5. OpenWrt / standalone Mihomo

OpenWrt-сборка — full-panel snapshot той же Unified UI, но без Flask/Python на роутере.

### Требования

- OpenWrt с `apk` или совместимым shell;
- `uhttpd` с `/www` и `/cgi-bin`;
- установленный Mihomo binary;
- активный config `/etc/mihomo/config.yaml`;
- controller `127.0.0.1:9090`;
- mixed proxy обычно `7890`.

### Установка

```sh
cd /tmp
curl -fL -o unified-ui-openwrt.tar.gz \
  "https://github.com/sllikmll/Unified-UI/releases/latest/download/unified-ui-openwrt.tar.gz"
rm -rf unified-ui-openwrt
tar -xzf unified-ui-openwrt.tar.gz -C /tmp
sh /tmp/unified-ui-openwrt/install.sh
```

После установки:

```text
http://<IP_роутера>/unified-ui/
```

OpenWrt-версия ставит:

- `/www/unified-ui/` — static full-panel UI;
- `/www/cgi-bin/unified-ui-api` — CGI API bridge;
- `/etc/unified-ui/openwrt.env`;
- `/etc/unified-ui/BUILD.json`;
- `/etc/unified-ui/openwrt-update.sh`;
- backups в `/etc/unified-ui/backups/`.

Она **не ставит Python/Flask**, не тянет Nikki и не использует LuCI/Nikki UI.

---

# Важные пути

## Keenetic / Entware

| Путь | Назначение |
|---|---|
| `/opt/etc/unified-ui` | Код панели |
| `/opt/var/lib/unified-ui` | State/registry |
| `/opt/etc/mihomo/config.yaml` | Активный config Mihomo |
| `/opt/etc/mihomo/profiles/default.yaml` | Default profile |
| `/opt/etc/mihomo/rules/manual-proxy.yaml` | Ручной список |
| `/opt/etc/mihomo/restart-mihomo.sh` | Реальный restart Mihomo |
| `/opt/etc/init.d/S99unified-ui001` | Init-сервис панели |

## OpenWrt

| Путь | Назначение |
|---|---|
| `/www/unified-ui` | Static full-panel UI |
| `/www/cgi-bin/unified-ui-api` | CGI API bridge |
| `/etc/unified-ui` | env/build/update/backups |
| `/etc/mihomo/config.yaml` | Активный config Mihomo |
| `/etc/mihomo/rules/manual-proxy.yaml` | Ручной список/provider file |
| `/etc/init.d/mihomo` | Init-сервис Mihomo |

## Desktop runtime

| Shell | Runtime path |
|---|---|
| Electron macOS | `~/Library/Application Support/unified-ui/runtime` |
| Qt macOS | `~/Library/Application Support/Unified UI Qt/runtime` |
| Docker | `/data/unified-ui` + `/etc/mihomo` volumes |

---

# Разработка

Базовые проверки:

```sh
python3 -m py_compile unified-ui/app_factory.py
npm run frontend:build
node scripts/verify_frontend_build.mjs
```

Desktop Electron:

```sh
npx electron-builder --mac dmg --arm64
npx electron-builder --win nsis --x64
npx electron-builder --linux deb rpm AppImage --x64
```

Desktop Qt:

```sh
python3 -m pip install -r desktop/qt/requirements-qt.txt
python3 desktop/qt/unified_ui_qt.py --smoke
pyinstaller --noconfirm --distpath dist/qt --workpath build/qt desktop/qt/unified-ui-qt.spec
```

Docker:

```sh
docker build -t ghcr.io/sllikmll/unified-ui:latest .
docker run --rm -p 8088:8088 -p 9090:9090 ghcr.io/sllikmll/unified-ui:latest
```

---

# Проверено в `v2.5.1`

| Проверка | Результат |
|---|---|
| Electron packaged macOS app | UI стартует, Mihomo `v1.19.29`, ports `18088/19090` listen |
| Qt packaged macOS app | `--smoke` зелёный, UI `200`, Mihomo `v1.19.29` |
| Docker normal mode | container `healthy`, UI `/login`, Mihomo API отвечает |
| Docker TUN config | `tun`, `auto-route`, `dns-hijack` добавляются в config |
| DMG validation | Electron DMG и Qt DMG checksum valid |
| GHCR | `2.5.1` и `latest` manifest доступны |

---

# Происхождение

Сейчас это отдельный **Unified UI** проект: одна панель для Keenetic, OpenWrt, MikroTik, Docker и desktop-устройств.
