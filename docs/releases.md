# Платформенные релизы Unified UI

Платформы выпускаются независимыми tag-линями:

| Платформа | Текущий tag | Основной asset |
|---|---|---|
| Keenetic | `v3.0.1` | `unified-ui-routing.tar.gz` |
| OpenWrt | `v3.0.0-openwrt` | `unified-ui-openwrt-v3.0.0.tar.gz` |
| MikroTik | `v3.0.0-mikrotik` | `unified-ui-mikrotik-docker-archive-v3.0.0.tar.gz` |
| Native | `v2.6.8-native` | platform-specific Mac/Windows/Linux packages |

Не используйте `releases/latest/download` для platform installer: latest может указывать на релиз другой платформы. Используйте tag-specific URL.

Документация:

- [OpenWrt](platforms/openwrt.md)
- [MikroTik](platforms/mikrotik.md)
- [Native](platforms/native.md)
- Keenetic official AWG: основной README и `v3.0.1` notes.
