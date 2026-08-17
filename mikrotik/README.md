# Unified UI for MikroTik RouterOS containers

This directory contains the full Unified UI + Mihomo container build for MikroTik RouterOS (`container` package, ARM64/RB5009 tested).

## What is inside

- Full Flask Unified UI from `unified-ui/`.
- Mihomo `linux-arm64` binary bundled at build time.
- `entrypoint.sh` starts:
  - Mihomo controller on `:9090`;
  - Unified UI on `:8088`;
  - mixed proxy on `:1080`;
  - DNS listener on `:1053`.
- Native AmneziaWG support is built from official pinned sources:
  - `amnezia-vpn/amneziawg-go` tag `v3.1.20260814`, commit `1b86b2ae0e493e7ea93f8c1a0f0cb6735b1551f1`;
  - `amnezia-vpn/amneziawg-tools` tag `v3.1.20260812`, commit `ee0f0a9aa34ff0a0da4b3433b9512781cfe02843`;
  - binaries are installed as `/opt/bin/amneziawg-go` and `/opt/bin/awg`;
  - provenance and binary checksums are kept in `/opt/bin/OFFICIAL_AWG_PROVENANCE.json` and `/opt/bin/SHA256SUMS`.
- Persistent state lives inside the RouterOS container root-dir, usually:
  - `/usb1/docker/unified-ui-mikrotik`.

## Build on Linux with Docker

```sh
# From repo root
sh -n mikrotik/entrypoint.sh
npm run frontend:build

docker run --privileged --rm tonistiigi/binfmt --install arm64

docker build --platform linux/arm64 \
  -f mikrotik/Dockerfile \
  -t unified-ui-mikrotik:routeros .

# RouterOS needs classic docker-archive, not OCI manifest-list.
skopeo copy \
  docker-daemon:unified-ui-mikrotik:routeros \
  docker-archive:unified-ui-mikrotik-docker-archive.tar:unified-ui-mikrotik:routeros

gzip -1 -f unified-ui-mikrotik-docker-archive.tar
```

## RouterOS install notes

RouterOS `container/add file=...` is picky:

- buildx/OCI archive can fail with `download/extract error: no config found in manifest`;
- use `skopeo ... docker-archive:...` and upload the resulting `.tar.gz`.

The installed runtime on RB5009 uses:

- container comment: `unified-ui-mikrotik`;
- veth: `MIHOMO`, `192.168.254.3/24`, gateway `192.168.254.1`;
- dstnat:
  - `172.16.0.22:8088 -> 192.168.254.3:8088`;
  - `172.16.0.22:9090 -> 192.168.254.3:9090`.

Native AmneziaWG imports require Linux networking privileges inside the container:

- NET_ADMIN-equivalent network capability inside the RouterOS container runtime;
- `/dev/net/tun` passed into the container.

Current RouterOS container documentation lists `devices` as a container property and `/dev/net/tun` as an available device node, so the template uses `devices=/dev/net/tun` on `/container/add`. Empirically on RB5009/RouterOS 7.23.x, native AWG also needs NET_ADMIN-equivalent network privileges; RouterOS does not use Docker `--cap-add` syntax in `/container/add`. Without these runtime prerequisites, imported AWG2/AWG3 connections cannot create native `uawg*` interfaces. Startup logs a non-secret native AWG preflight status, skips native restore, and continues booting Mihomo and the UI. Manual AWG Apply fails clearly until the runtime is available. The runtime never sends AWG2/AWG3 secrets to Mihomo as built-in `wireguard`; it restores official `amneziawg-go` interfaces and injects Mihomo `type: direct` outbounds with `interface-name` and `routing-mark`.

Do not keep secrets in RouterOS env after first boot. RouterOS logs container env values on start. First boot writes auth/config into persistent container storage, then sensitive env vars can be removed from `UNIFIED_UI_MIKROTIK`.

See `routeros-install-template.rsc` for a repeatable template. Fill secrets locally; do not commit them.
