FROM python:3.12-slim

ARG TARGETARCH
ARG MIHOMO_VERSION=1.19.29

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    UNIFIED_UI_PORT=8088 \
    UNIFIED_UI_STATE_DIR=/data/unified-ui \
    UNIFIED_UI_DIR=/data/unified-ui \
    MIHOMO_CONFIG=/etc/mihomo/config.yaml \
    MIHOMO_CONFIG_FILE=/etc/mihomo/config.yaml \
    MIHOMO_ROOT=/etc/mihomo \
    MIHOMO_CONTROLLER_URL=http://127.0.0.1:9090 \
    MIHOMO_CONTROLLER_HOST=127.0.0.1 \
    MIHOMO_CONTROLLER_PORT=9090 \
    MIHOMO_MIXED_PORT=7890 \
    MIHOMO_DNS_PORT=1053 \
    MIHOMO_ENABLE_TUN=false \
    UNIFIED_UI_AVAILABLE_CORES=mihomo

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl tini iproute2 procps jq gzip \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir Flask 'gevent<26' gevent-websocket PyYAML requests

RUN mkdir -p /app /etc/mihomo/rules /etc/mihomo/profiles /etc/mihomo/templates /data/unified-ui /var/log/unified-ui

RUN set -eux; \
    arch="${TARGETARCH:-amd64}"; \
    case "$arch" in \
      amd64) mh_arch="amd64" ;; \
      arm64) mh_arch="arm64" ;; \
      *) echo "unsupported TARGETARCH=$arch" >&2; exit 1 ;; \
    esac; \
    curl -fsSL -o /tmp/mihomo.gz "https://github.com/MetaCubeX/mihomo/releases/download/v${MIHOMO_VERSION}/mihomo-linux-${mh_arch}-v${MIHOMO_VERSION}.gz"; \
    gzip -dc /tmp/mihomo.gz > /usr/local/bin/mihomo; \
    chmod +x /usr/local/bin/mihomo; \
    rm -f /tmp/mihomo.gz

COPY unified-ui/ /app/unified-ui/
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /app/unified-ui
EXPOSE 8088 9090 7890 1053/tcp 1053/udp
VOLUME ["/data/unified-ui", "/etc/mihomo"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:${UNIFIED_UI_PORT}/ >/dev/null && curl -fsS http://127.0.0.1:${MIHOMO_CONTROLLER_PORT}/version >/dev/null || exit 1
ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]
