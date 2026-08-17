# Unified UI для OpenWrt

## Релиз

- Tag: `v3.0.0-openwrt`
- Asset: `unified-ui-openwrt-v3.0.0.tar.gz`
- Цель: OpenWrt `aarch64` с `uhttpd`, `jsonfilter`, `ip`, `kmod-tun`.

Архив включает static full-panel, CGI backend, Mihomo `v1.19.29`, official `amneziawg-go` и `awg`. Существующий `/etc/mihomo/config.yaml` при upgrade не перезаписывается.

## Установка

```sh
tar -xzf unified-ui-openwrt-v3.0.0.tar.gz -C /tmp
sh /tmp/unified-ui-openwrt/install.sh
```

UI: `http://<router>/unified-ui/`. Начальная учётная запись: `admin/admin`; пароль следует сменить сразу.

## AmneziaWG

AWG2/AWG3 импортируется в registry и поднимается official userspace runtime. PrivateKey/PSK остаются в закрытом setconf-файле `0600`. Mihomo получает только `type: direct`, `interface-name` и `routing-mark`. Сохраняются `Jc/Jmin/Jmax`, `S1-S4`, `H1-H4`.

## Проверка

```sh
/etc/init.d/mihomo status
/etc/init.d/unified-awg-native enabled
ip link show | grep uawg
ip rule show
curl -fsS http://127.0.0.1:9090/version
```

Acceptance `v3.0.0-openwrt`: clean install на OpenWrt 25.12.5/aarch64, native AWG handshake, selector apply, 3/3 HTTPS 204 и restart persistence.

## Rollback

Installer сохраняет profile backups в `/etc/unified-ui/backups`. Pre-install router backup следует хранить отдельно. Uninstall:

```sh
sh /etc/unified-ui/openwrt-uninstall.sh
```

Uninstall панели не должен удалять пользовательский Mihomo config автоматически.
