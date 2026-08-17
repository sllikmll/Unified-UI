FROM node:20-alpine AS frontend-build

RUN apk add --no-cache python3

WORKDIR /src
COPY package.json package-lock.json ./
RUN npm ci
COPY scripts/ scripts/
COPY vite.config.mjs ./
COPY unified-ui/ unified-ui/
RUN npm run frontend:build && node scripts/verify_frontend_build.mjs

FROM golang:1.25-alpine AS awg-go-build

ARG AWG_GO_TAG=v3.1.20260814
ARG AWG_GO_COMMIT=1b86b2ae0e493e7ea93f8c1a0f0cb6735b1551f1

RUN apk add --no-cache ca-certificates git && update-ca-certificates
WORKDIR /src
RUN git clone --filter=blob:none https://github.com/amnezia-vpn/amneziawg-go.git amneziawg-go && \
    git -C amneziawg-go checkout --detach "${AWG_GO_TAG}" && \
    test "$(git -C amneziawg-go rev-parse HEAD)" = "${AWG_GO_COMMIT}" && \
    mkdir -p /out && \
    cd amneziawg-go && \
    CGO_ENABLED=0 GOOS=linux GOARCH=arm64 go build -trimpath -ldflags="-s -w" -o /out/amneziawg-go .

FROM alpine:3.20 AS awg-tools-build

ARG AWG_TOOLS_TAG=v3.1.20260812
ARG AWG_TOOLS_COMMIT=ee0f0a9aa34ff0a0da4b3433b9512781cfe02843

RUN apk add --no-cache build-base ca-certificates git linux-headers && update-ca-certificates
WORKDIR /src
RUN git clone --filter=blob:none https://github.com/amnezia-vpn/amneziawg-tools.git amneziawg-tools && \
    git -C amneziawg-tools checkout --detach "${AWG_TOOLS_TAG}" && \
    test "$(git -C amneziawg-tools rev-parse HEAD)" = "${AWG_TOOLS_COMMIT}" && \
    mkdir -p /out && \
    make -C amneziawg-tools/src clean && \
    make -C amneziawg-tools/src && \
    cp amneziawg-tools/src/wg /out/awg

FROM alpine:3.20 AS awg-runtime

ARG AWG_GO_TAG=v3.1.20260814
ARG AWG_GO_COMMIT=1b86b2ae0e493e7ea93f8c1a0f0cb6735b1551f1
ARG AWG_TOOLS_TAG=v3.1.20260812
ARG AWG_TOOLS_COMMIT=ee0f0a9aa34ff0a0da4b3433b9512781cfe02843

COPY --from=awg-go-build /out/amneziawg-go /out/amneziawg-go
COPY --from=awg-tools-build /out/awg /out/awg
RUN chmod 755 /out/amneziawg-go /out/awg && \
    printf '%s\n' \
      '{' \
      '  "amneziawg-go": {' \
      '    "repository": "https://github.com/amnezia-vpn/amneziawg-go.git",' \
      "    \"tag\": \"${AWG_GO_TAG}\"," \
      "    \"commit\": \"${AWG_GO_COMMIT}\"" \
      '  },' \
      '  "amneziawg-tools": {' \
      '    "repository": "https://github.com/amnezia-vpn/amneziawg-tools.git",' \
      "    \"tag\": \"${AWG_TOOLS_TAG}\"," \
      "    \"commit\": \"${AWG_TOOLS_COMMIT}\"" \
      '  },' \
      '  "target": "linux/arm64",' \
      '  "tools_libc": "musl (Alpine 3.20)"' \
      '}' \
      > /out/OFFICIAL_AWG_PROVENANCE.json && \
    (cd /out && sha256sum amneziawg-go awg > SHA256SUMS)

FROM python:3.12-alpine

ARG TARGETARCH

RUN apk add --no-cache bash curl ca-certificates tini tzdata iproute2 nftables procps jq && \
    update-ca-certificates

RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir Flask 'gevent<26' gevent-websocket PyYAML requests

RUN mkdir -p /app /etc/mihomo/rules /etc/mihomo/profiles /data/unified-ui /var/log/unified-ui
COPY mikrotik/assets/mihomo-linux-arm64 /usr/local/bin/mihomo
COPY --from=awg-runtime /out/amneziawg-go /opt/bin/amneziawg-go
COPY --from=awg-runtime /out/awg /opt/bin/awg
COPY --from=awg-runtime /out/OFFICIAL_AWG_PROVENANCE.json /opt/bin/OFFICIAL_AWG_PROVENANCE.json
COPY --from=awg-runtime /out/SHA256SUMS /opt/bin/SHA256SUMS
COPY unified-ui/ /app/unified-ui/
COPY --from=frontend-build /src/unified-ui/static/frontend-build/ /app/unified-ui/static/frontend-build/
COPY --from=frontend-build /src/unified-ui/static/vendor/ /app/unified-ui/static/vendor/
COPY mikrotik/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh /usr/local/bin/mihomo /opt/bin/amneziawg-go /opt/bin/awg && \
    (cd /opt/bin && sha256sum -c SHA256SUMS)

ENV UNIFIED_UI_PORT=8088 \
    UNIFIED_UI_STATE_DIR=/data/unified-ui \
    UNIFIED_UI_DIR=/data/unified-ui \
    MIHOMO_CONFIG=/etc/mihomo/config.yaml \
    MIHOMO_CONTROLLER_URL=http://127.0.0.1:9090 \
    MIHOMO_CONTROLLER_HOST=127.0.0.1 \
    MIHOMO_CONTROLLER_PORT=9090 \
    MIHOMO_ROOT=/etc/mihomo \
    MIHOMO_TEMPLATES_DIR=/etc/mihomo/templates \
    UNIFIED_UI_NAME='Unified UI MikroTik' \
    UNIFIED_UI_AVAILABLE_CORES=mihomo \
    UNIFIED_AWG_GO_BIN=/opt/bin/amneziawg-go \
    UNIFIED_AWG_BIN=/opt/bin/awg \
    PYTHONUNBUFFERED=1

WORKDIR /app/unified-ui
EXPOSE 8088 9090 1080 1053
ENTRYPOINT ["/sbin/tini", "--", "/entrypoint.sh"]
