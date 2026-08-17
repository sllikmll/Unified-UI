# Unified UI для MikroTik RouterOS

## Релиз

- Tag: `v3.0.0-mikrotik`
- Asset: `unified-ui-mikrotik-docker-archive-v3.0.0.tar.gz`
- Цель: RouterOS 7 ARM64 с package `container`, device-mode `container=yes`, writable storage и veth.

Docker archive содержит full-panel, Mihomo `v1.19.29`, official `amneziawg-go` и `awg`.

## Требования

Container должен иметь TUN/сетевые capabilities, нужные userspace AWG. Текущий RouterOS container syntax поддерживает `devices`, поэтому шаблон передает `devices=/dev/net/tun`. Проверенный RB5009/RouterOS 7.23.3 предоставляет рабочий `/dev/net/tun` container runtime и требует NET_ADMIN-equivalent network capability внутри container runtime. Если runtime недоступен, startup пропускает native AWG restore и продолжает запуск UI/Mihomo; ручной AWG Apply падает с явной ошибкой preflight. Нужны veth gateway и masquerade/маршрут для container subnet.

Шаблон: [`mikrotik/routeros-install-template.rsc`](../../mikrotik/routeros-install-template.rsc).

## AmneziaWG

Импорт AWG2/AWG3 использует native `uawg*` interface. Mihomo config содержит только direct outbound с `interface-name`/`routing-mark`; private key и PSK в YAML не пишутся. После Apply entrypoint-safe reload выполняется через Mihomo controller `PUT /configs?force=true`.

## Проверка

- container state `R`;
- UI `/login` отвечает `200`;
- import `201`, apply `200`;
- native count `1`;
- delay через AWG proxy успешен;
- selector переключается;
- HTTPS через mixed proxy возвращает `204`;
- stop/start container восстанавливает AWG.

Acceptance `v3.0.0-mikrotik`: RB5009, RouterOS 7.23.3 ARM64, delay 22–26 ms, 3/3 HTTPS 204, restart persistence.

## Rollback

Остановите/удалите только Unified UI container, его root-dir, veth/bridge/NAT с соответствующим comment. Не удаляйте shared storage или чужие container layers.
