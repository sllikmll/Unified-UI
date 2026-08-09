# Контракт подписок Mihomo/Unified VPN Panel

Этот документ фиксирует, как Unified UI должен принимать и применять подписку Unified VPN Panel на Keenetic, OpenWrt, MikroTik, Docker и Native.

## Что считается рабочей подпиской

Подписка считается реально поддержанной только если выполнены все пункты:

1. URL сохранён в persistent source-файл/настройку конкретной платформы.
2. Runtime `proxy-providers` указывает на этот же URL.
3. Health-check provider использует внешний 204 endpoint, а не сам URL подписки:

```yaml
health-check:
  enable: true
  url: https://www.gstatic.com/generate_204
  expected-status: 204
```

4. Provider подключён к selector/fallback/url-test/load-balance groups через `use:`.
5. Provider-owned nodes не дублируются как обычные static `proxies:`.
6. Managed records в UI read-only и обновляются только refresh/import flow.
7. Local user-managed records сохраняются при refresh.
8. Проверен полный protocol matrix:
   - VMess;
   - VLESS Reality;
   - Trojan TLS;
   - Shadowsocks 2022;
   - WireGuard;
   - AWG 2.0;
   - Hysteria2;
   - Mieru;
   - NaiveProxy.

Telegram MTProxy (`tg://`) отображается как external action и не считается Mihomo outbound. Он не заменяет Mieru или NaiveProxy.

## Provider должен быть подключён к группам

Частая ловушка: `proxy-providers.subscription_1` есть, provider API показывает узлы, но `/proxies` и selector groups их не видят.

Причина: provider не включён в группы через `use`.

Минимальный корректный фрагмент:

```yaml
proxy-providers:
  subscription_1:
    type: http
    url: https://example.invalid/sub/[REDACTED]
    path: ./providers/subscription_1.yaml
    interval: 3600
    health-check:
      enable: true
      url: https://www.gstatic.com/generate_204
      expected-status: 204

proxy-groups:
  - name: AI
    type: select
    proxies:
      - DIRECT
    use:
      - subscription_1
```

Unified UI generator обязан добавлять `use: [subscription_1]` в группы типов:

- `select`;
- `fallback`;
- `url-test`;
- `load-balance`.

Если provider есть, но не используется группами, задача не PASS.

## Cache и stale runtime

Mihomo может держать старый provider cache даже после замены URL в config. Типичный симптом: URL снаружи отдаёт 6–8 узлов, а provider API на роутере показывает 49 старых записей.

Проверять надо три слоя:

1. Raw subscription с внешней машины.
2. Active `/etc/mihomo/config.yaml` или platform-specific symlink/source.
3. Runtime Mihomo API:

```text
/providers/proxies/subscription_1
/proxies
```

Если список старый:

- сделать provider refresh;
- при необходимости reload `/configs`;
- если процесс Mihomo не меняет state — перезапустить сам Mihomo, а не только UI wrapper.

## Health-check ≠ datapath

`alive=true/false` в Mihomo — это быстрый indicator, не абсолютная истина.

Особенно осторожно:

- WireGuard, AWG 2.0 и AWG 3.0 должны быть тремя разными provider-owned nodes; AWG 2.0/3.0 обязаны сохранять Amnezia options `jc`, `jmin`, `jmax`, `s1`, `s2`, `h1`, а для AWG3 ещё `HeaderProtectionKey`/rekey/timeout поля;
- WireGuard/AWG2/AWG3 может давать false-negative на provider health-check;
- UDP-протоколы и full-tunnel маршрутизация требуют datapath-теста;
- один LAN за Keenetic не означает одинаковый runtime-path для Keenetic, OpenWrt, MikroTik container и телефона.

Для финального PASS нужен одинаковый endpoint:

```text
https://www.gstatic.com/generate_204
```

И минимум:

- provider health-check;
- individual delay/datapath where available;
- реальная маршрутизация через выбранный node/group, если платформа открывает mixed/socks proxy;
- server-side logs/config для протоколов, которые не проходят.

## Platform rollout order

Безопасный порядок для общей подписки:

1. **Keenetic эталон** — direct internet path, актуальный Mihomo, полный UI/backend stack.
2. **OpenWrt** — после эталона; учитывать secret к controller, отсутствие Python/jq/timeout, standalone Mihomo path.
3. **MikroTik** — после OpenWrt; учитывать container DNS/NAT, RouterOS archive format и persistent root-dir.
4. Только после полного PASS — rollout на production/личные устройства.

Для инфраструктуры `sllikmll` VLESS Reality в подписках должен использовать SNI/serverName:

```text
yandex.ru
```

## Full PASS matrix

Финальный отчёт должен явно показывать:

| Устройство | Unified UI version | Mihomo version | Subscription label | Provider count | Groups use provider | VMess | VLESS | Trojan | SS2022 | WireGuard | AWG2 | AWG3 | Hysteria2 | Mieru | Naive |
|---|---|---|---|---:|---|---|---|---|---|---|---|---|---|---|---|

Если Mieru или NaiveProxy отсутствуют в подписке — писать `MISSING`, а не считать строку зелёной.
Если WireGuard, AWG 2.0 и AWG 3.0 слиты в один узел — писать `FAIL`, даже если health-check зелёный.
