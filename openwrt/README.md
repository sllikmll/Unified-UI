# Unified UI для OpenWrt

OpenWrt-версия Unified UI теперь работает **на standalone Mihomo**, без Nikki. Это лёгкий OpenWrt-native слой: статическая страница под `uhttpd` + CGI backend на `ash`, который ходит в Mihomo API.

## Почему не Flask как на Keenetic

На тестовом роутере `172.16.0.21`:

```text
OpenWrt 25.12.5
arch: aarch64_cortex-a53
root overlay: ~147.6M total / ~26M free
python3: not installed
package manager: apk, not opkg
```

Python/Flask на таком overlay — плохая идея: `apk add --simulate python3` тянет слишком большой runtime, а Flask-пакета нет. Поэтому OpenWrt-вариант сделан без Python, но по UX и функциям приближается к Keenetic Unified UI.

## Архитектура

```text
Mihomo binary           /usr/bin/mihomo
Mihomo service          /etc/init.d/mihomo
Mihomo config/profile   /etc/mihomo/config.yaml
Mihomo controller       http://127.0.0.1:9090
Unified UI static page  /www/unified-ui/index.html
Unified UI CGI backend  /www/cgi-bin/unified-ui-api
Unified UI env/build    /etc/unified-ui/openwrt.env, BUILD.json
Unified UI backups      /etc/unified-ui/backups/
```

Nikki не используется и на тестовом роутере удалён:

```text
nikki/luci-app-nikki/luci-i18n-nikki-ru: removed
/etc/nikki: removed
controller :6060: closed
standalone Mihomo :9090: active
```

## Возможности

### Runtime Mihomo

- статус Mihomo + UI version;
- просмотр selector/group/proxy дерева;
- переключение selector → proxy;
- ping/delay check по proxy;
- просмотр активных соединений;
- фильтр соединений;
- разрыв одного соединения;
- разрыв всех соединений;
- restart standalone Mihomo.

### Подключения по протоколам

Вкладка `Подключения` показывает proxy по протоколам:

- VLESS;
- WireGuard;
- Amnezia;
- Hysteria2;
- Trojan;
- Mieru;
- NaiveProxy.

Импорт сейчас добавляет YAML proxy-блок в `/etc/mihomo/config.yaml` через редактор:

- `vless://...`
- `trojan://...`
- `hysteria2://...` / `hy2://...`
- WireGuard/Amnezia-style config with `PrivateKey`, `PublicKey`, `Endpoint`.

После импорта нужно проверить YAML и нажать `Сохранить и применить`.

### Config editor

Для `/etc/mihomo/config.yaml`:

- чтение текущего конфига;
- validate через реальный `mihomo -t`;
- save только после успешной валидации;
- backup старого файла перед записью;
- save+apply через restart `/etc/init.d/mihomo`;
- backup в `/etc/unified-ui/backups/`.

## Release asset

```text
unified-ui-openwrt.tar.gz
```

Latest:

```text
https://github.com/sllikmll/Unified-UI/releases/latest/download/unified-ui-openwrt.tar.gz
```

Checksum:

```text
https://github.com/sllikmll/Unified-UI/releases/latest/download/unified-ui-openwrt.tar.gz.sha256
```

## Установка на OpenWrt

```sh
cd /tmp
curl -fL -o unified-ui-openwrt.tar.gz \
  "https://github.com/sllikmll/Unified-UI/releases/latest/download/unified-ui-openwrt.tar.gz"
mkdir -p unified-ui-openwrt
tar -xzf unified-ui-openwrt.tar.gz -C .
cd unified-ui-openwrt
sh install.sh
```

После установки:

```text
http://<router>/unified-ui/
```

## API endpoints

```text
GET  /cgi-bin/unified-ui-api/status
GET  /cgi-bin/unified-ui-api/version
GET  /cgi-bin/unified-ui-api/configs
GET  /cgi-bin/unified-ui-api/proxies
GET  /cgi-bin/unified-ui-api/connections
GET  /cgi-bin/unified-ui-api/config-get
GET  /cgi-bin/unified-ui-api/restart
POST /cgi-bin/unified-ui-api/select                { group, groupEncoded, name }
POST /cgi-bin/unified-ui-api/delay                 { name, nameEncoded, timeout, url }
POST /cgi-bin/unified-ui-api/connection-close      { id }
POST /cgi-bin/unified-ui-api/connections-close-all {}
POST /cgi-bin/unified-ui-api/config-validate       { content }
POST /cgi-bin/unified-ui-api/config-save           { content, apply }
```

## Обновление и удаление

```sh
sh /etc/unified-ui/openwrt-update.sh
```

```sh
sh /etc/unified-ui/openwrt-uninstall.sh
```

## Проверено на 172.16.0.21

Standalone state:

```text
mihomo-meta installed
nikki removed
/etc/nikki removed
PID: mihomo
ports: 7890 + 9090
```

Status:

```text
controller: http://127.0.0.1:9090
config: /etc/mihomo/config.yaml
profile: /etc/mihomo/config.yaml
```

Browser smoke:

```text
main tabs: Статус, Маршрутизация, Подключения, Соединения, Конфиг, Raw API
protocol tabs: VLESS, WireGuard, Amnezia, Hysteria2, Trojan, Mieru, NaiveProxy
VLESS count: 11
WireGuard count: 1
config editor: /etc/mihomo/config.yaml loaded
JS errors: []
```

## Сборка локального OpenWrt-архива

```sh
python3 scripts/build_openwrt_archive.py \
  --version 2.4.x-unified \
  --update-url https://github.com/sllikmll/Unified-UI/releases/download/v2.4.x-unified/unified-ui-openwrt.tar.gz
```

или

```sh
npm run archive:openwrt
```
