#!/usr/bin/env bash
set -euo pipefail

log() { printf '[unified-mikrotik] %s\n' "$*" >&2; }

mkdir -p /etc/mihomo/rules /etc/mihomo/profiles /etc/mihomo/templates /data/unified-ui /var/log/unified-ui

: "${UNIFIED_UI_AUTH_USER:=pavel}"
: "${UNIFIED_UI_AUTH_PASSWORD:=admin}"
: "${UNIFIED_UI_SECRET_KEY:=}"
: "${MIHOMO_SUB_URL:=${SUB1:-}}"
: "${MIHOMO_MIXED_PORT:=1080}"
: "${MIHOMO_DNS_PORT:=1053}"
: "${MIHOMO_CONTROLLER:=0.0.0.0:9090}"
: "${MIHOMO_LOG_LEVEL:=info}"
: "${MIHOMO_ENABLE_TUN:=false}"

export UNIFIED_UI_AUTH_USER UNIFIED_UI_AUTH_PASSWORD UNIFIED_UI_SECRET_KEY
export UNIFIED_UI_STATE_DIR=/data/unified-ui
export UNIFIED_UI_DIR=/data/unified-ui
export MIHOMO_CONFIG=/etc/mihomo/config.yaml
export MIHOMO_CONFIG_FILE=/etc/mihomo/config.yaml
export MIHOMO_CONTROLLER_URL=http://127.0.0.1:9090
export MIHOMO_CONTROLLER_HOST=127.0.0.1
export MIHOMO_CONTROLLER_PORT=9090

python - <<'PY'
import os, json
from pathlib import Path
from werkzeug.security import generate_password_hash
state=Path('/data/unified-ui')
state.mkdir(parents=True, exist_ok=True)
auth=state/'auth.json'
user=os.environ.get('UNIFIED_UI_AUTH_USER','pavel')
password=os.environ.get('UNIFIED_UI_AUTH_PASSWORD','admin')
if not auth.exists() and user and password:
    auth.write_text(json.dumps({'username':user,'password_hash':generate_password_hash(password)}, ensure_ascii=False, indent=2)+'\n')
    auth.chmod(0o600)
secret=os.environ.get('UNIFIED_UI_SECRET_KEY') or ''
if secret:
    (state/'secret.key').write_text(secret+'\n')
    (state/'secret.key').chmod(0o600)
PY

if [ ! -s /etc/mihomo/rules/manual-proxy.yaml ]; then
  cat > /etc/mihomo/rules/manual-proxy.yaml <<'YAML'
payload: []
YAML
fi

if [ ! -s /etc/mihomo/config.yaml ]; then
  log "creating default Mihomo config from bundled Keenetic template"
  python - <<'PY'
import os
from pathlib import Path
import yaml

template = Path('/app/unified-ui/opt/etc/mihomo/templates/keenetic-default.yaml')
if not template.exists():
    raise SystemExit(f'bundled default template not found: {template}')

sub = (os.environ.get('MIHOMO_SUB_URL') or os.environ.get('SUB1') or '').strip()
cfg = yaml.safe_load(template.read_text(encoding='utf-8')) or {}

# Runtime/container-safe settings. The template carries routing policy; the
# entrypoint adapts ports/paths to the image and keeps secrets out of the image.
cfg['mixed-port'] = int(os.environ.get('MIHOMO_MIXED_PORT', '1080'))
cfg['allow-lan'] = True
cfg['bind-address'] = '*'
cfg['mode'] = cfg.get('mode') or 'rule'
cfg['log-level'] = os.environ.get('MIHOMO_LOG_LEVEL', cfg.get('log-level') or 'info')
cfg['ipv6'] = False
cfg['external-controller'] = os.environ.get('MIHOMO_CONTROLLER', cfg.get('external-controller') or '0.0.0.0:9090')
cfg['secret'] = ''
cfg['find-process-mode'] = 'off'

# Normalize file/cache paths from Keenetic Entware (/opt/etc/mihomo) to the
# container path (/etc/mihomo).
def normalize_path(value):
    if not isinstance(value, str):
        return value
    return value.replace('/opt/etc/mihomo/', '/etc/mihomo/')

for section in ('proxy-providers', 'rule-providers'):
    providers = cfg.get(section)
    if isinstance(providers, dict):
        for provider in providers.values():
            if isinstance(provider, dict) and 'path' in provider:
                provider['path'] = normalize_path(provider['path'])

# The image must not contain the user's private subscription. If MIHOMO_SUB_URL
# is provided, wire it into subscription_1. Otherwise remove subscription_1 and
# strip `use: [subscription_1]` from selector groups so first boot is valid.
providers = cfg.setdefault('proxy-providers', {})
if sub:
    provider = providers.setdefault('subscription_1', {})
    provider.update({
        'type': 'http',
        'url': sub,
        'interval': int(provider.get('interval') or 3600),
        'path': '/etc/mihomo/profiles/subscription_1.yaml',
        'health-check': provider.get('health-check') or {
            'enable': True,
            'url': 'https://www.gstatic.com/generate_204',
            'interval': 300,
        },
    })
else:
    providers.pop('subscription_1', None)
    if not providers:
        cfg['proxy-providers'] = {}
    for group in cfg.get('proxy-groups') or []:
        if not isinstance(group, dict):
            continue
        use = group.get('use')
        if isinstance(use, list):
            use = [item for item in use if item != 'subscription_1']
            if use:
                group['use'] = use
            else:
                group.pop('use', None)

# DNS listen port is container-env specific; keep the rest of the policy.
dns = cfg.setdefault('dns', {})
if isinstance(dns, dict):
    dns['enable'] = True
    dns['listen'] = f"0.0.0.0:{os.environ.get('MIHOMO_DNS_PORT','1053')}"
    dns['ipv6'] = False

if os.environ.get('MIHOMO_ENABLE_TUN','').lower() in ('1','true','yes','on'):
    cfg['tun'] = {
        'enable': True,
        'stack': 'system',
        'auto-route': True,
        'auto-detect-interface': True,
        'strict-route': False,
        'dns-hijack': ['any:53'],
    }

Path('/etc/mihomo/config.yaml').write_text(
    yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False),
    encoding='utf-8',
)
PY
fi

log "validating Mihomo config"
if ! mihomo -t -d /etc/mihomo -f /etc/mihomo/config.yaml; then
  log "mihomo config validation failed; dumping tail"
  tail -160 /etc/mihomo/config.yaml >&2 || true
  exit 1
fi

log "starting Mihomo"
mihomo -d /etc/mihomo -f /etc/mihomo/config.yaml > /var/log/unified-ui/mihomo.log 2>&1 &
MIHOMO_PID=$!

for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:9090/version >/dev/null 2>&1; then
    log "Mihomo controller is ready"
    break
  fi
  sleep 1
  if ! kill -0 "$MIHOMO_PID" 2>/dev/null; then
    log "Mihomo exited early"
    tail -200 /var/log/unified-ui/mihomo.log >&2 || true
    exit 1
  fi
  if [ "$i" = 30 ]; then
    log "Mihomo controller did not become ready"
    tail -200 /var/log/unified-ui/mihomo.log >&2 || true
  fi
done

log "starting Unified UI on :${UNIFIED_UI_PORT:-8088}"
cd /app/unified-ui
python run_server.py > /var/log/unified-ui/ui.log 2>&1 &
UI_PID=$!

term() {
  log "stopping"
  kill "$UI_PID" "$MIHOMO_PID" 2>/dev/null || true
  wait || true
}
trap term TERM INT

while true; do
  kill -0 "$MIHOMO_PID" 2>/dev/null || { log "Mihomo died"; tail -120 /var/log/unified-ui/mihomo.log >&2 || true; exit 1; }
  kill -0 "$UI_PID" 2>/dev/null || { log "Unified UI died"; tail -120 /var/log/unified-ui/ui.log >&2 || true; exit 1; }
  sleep 5
done
