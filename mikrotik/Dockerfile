FROM python:3.12-alpine

ARG TARGETARCH

RUN apk add --no-cache bash curl ca-certificates tini tzdata iproute2 nftables procps jq && \
    update-ca-certificates

RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir Flask 'gevent<26' gevent-websocket PyYAML requests

RUN mkdir -p /app /etc/mihomo/rules /etc/mihomo/profiles /data/unified-ui /var/log/unified-ui
COPY mikrotik/assets/mihomo-linux-arm64 /usr/local/bin/mihomo
COPY unified-ui/ /app/unified-ui/
COPY mikrotik/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh /usr/local/bin/mihomo

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
    PYTHONUNBUFFERED=1

WORKDIR /app/unified-ui
EXPOSE 8088 9090 1080 1053
ENTRYPOINT ["/sbin/tini", "--", "/entrypoint.sh"]
