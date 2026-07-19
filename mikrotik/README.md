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

Do not keep secrets in RouterOS env after first boot. RouterOS logs container env values on start. First boot writes auth/config into persistent container storage, then sensitive env vars can be removed from `UNIFIED_UI_MIKROTIK`.

See `routeros-install-template.rsc` for a repeatable template. Fill secrets locally; do not commit them.
