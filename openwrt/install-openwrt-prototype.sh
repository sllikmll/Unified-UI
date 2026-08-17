#!/bin/sh
set -eu
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

UI_ROOT="/www/unified-ui"
CGI_PATH="/www/cgi-bin/unified-ui-api"
CONF_DIR="/etc/unified-ui"
CONF_FILE="$CONF_DIR/openwrt.env"
BUILD_FILE="$CONF_DIR/BUILD.json"
UPDATE_SCRIPT="$CONF_DIR/openwrt-update.sh"
UNINSTALL_SCRIPT="$CONF_DIR/openwrt-uninstall.sh"
BACKUP_DIR="$CONF_DIR/backups"
PROFILE_FILE="/etc/mihomo/config.yaml"
VERSION="${UNIFIED_OPENWRT_VERSION:-dev-local}"
UPDATE_URL="${UNIFIED_OPENWRT_UPDATE_URL:-}"
AWG_BIN_DIR="${UNIFIED_AWG_BIN_DIR:-/usr/bin}"
AWG_BUNDLE_DIR="$SCRIPT_DIR/bin"
MIHOMO_BUNDLE="$SCRIPT_DIR/bin/mihomo"

mkdir -p "$UI_ROOT" "$CONF_DIR" /www/cgi-bin "$BACKUP_DIR"

_auth_user="admin"
_auth_password="admin"
if [ -f "$CONF_FILE" ]; then
  UNIFIED_UI_AUTH_USER=""
  UNIFIED_UI_AUTH_PASSWORD=""
  . "$CONF_FILE"
  [ -n "${UNIFIED_UI_AUTH_USER:-}" ] && _auth_user="$UNIFIED_UI_AUTH_USER"
  [ -n "${UNIFIED_UI_AUTH_PASSWORD:-}" ] && _auth_password="$UNIFIED_UI_AUTH_PASSWORD"
  [ -z "$UPDATE_URL" ] && [ -n "${UNIFIED_UI_UPDATE_URL:-}" ] && UPDATE_URL="$UNIFIED_UI_UPDATE_URL"
fi

_secret="$(sed -n "s/^[[:space:]]*secret:[[:space:]]*['\"]\{0,1\}\([^'\"#]*\)['\"]\{0,1\}[[:space:]]*\(#.*\)\{0,1\}$/\1/p" /etc/mihomo/config.yaml 2>/dev/null | head -1 | sed 's/[[:space:]]*$//')"
_secret_q="$(printf '%s' "$_secret" | sed "s/'/'\\''/g")"
_profile_q="$(printf '%s' "$PROFILE_FILE" | sed "s/'/'\\''/g")"
_version_q="$(printf '%s' "$VERSION" | sed "s/'/'\\''/g")"
_update_url_q="$(printf '%s' "$UPDATE_URL" | sed "s/'/'\\''/g")"
_auth_user_q="$(printf '%s' "$_auth_user" | sed "s/'/'\\''/g")"
_auth_password_q="$(printf '%s' "$_auth_password" | sed "s/'/'\\''/g")"
{
  printf "%s\n" "UNIFIED_UI_NAME='Unified UI OpenWrt'"
  printf "%s\n" "MIHOMO_CONTROLLER='http://127.0.0.1:9090'"
  printf "MIHOMO_SECRET='%s'\n" "$_secret_q"
  printf "%s\n" "MIHOMO_RUN_DIR='/etc/mihomo'"
  printf "%s\n" "MIHOMO_CONFIG='/etc/mihomo/config.yaml'"
  printf "%s\n" "MIHOMO_INIT='/etc/init.d/mihomo'"
  printf "MIHOMO_PROFILE='%s'\n" "$_profile_q"
  printf "%s\n" "UNIFIED_UI_ROOT='/www/unified-ui'"
  printf "%s\n" "UNIFIED_UI_CGI='/www/cgi-bin/unified-ui-api'"
  printf "%s\n" "UNIFIED_UI_CONF_DIR='/etc/unified-ui'"
  printf "UNIFIED_UI_AUTH_USER='%s'\n" "$_auth_user_q"
  printf "UNIFIED_UI_AUTH_PASSWORD='%s'\n" "$_auth_password_q"
  printf "%s\n" "UNIFIED_UI_BUILD_FILE='/etc/unified-ui/BUILD.json'"
  printf "%s\n" "UNIFIED_UI_BACKUP_DIR='/etc/unified-ui/backups'"
  printf "UNIFIED_UI_VERSION='%s'\n" "$_version_q"
  printf "UNIFIED_UI_UPDATE_URL='%s'\n" "$_update_url_q"
} > "$CONF_FILE"
chmod 600 "$CONF_FILE"

cat > "$BUILD_FILE" <<EOF
{
  "version": "${VERSION}",
  "release_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "update_url": "${UPDATE_URL}"
}
EOF
chmod 644 "$BUILD_FILE"

install_bundled_awg_runtime() {
  [ -d "$AWG_BUNDLE_DIR" ] || return 0
  [ -f "$AWG_BUNDLE_DIR/amneziawg-go" ] || return 0
  [ -f "$AWG_BUNDLE_DIR/awg" ] || return 0
  if [ -f "$AWG_BUNDLE_DIR/SHA256SUMS" ]; then
    (cd "$AWG_BUNDLE_DIR" && sha256sum -c SHA256SUMS) >/dev/null
  fi
  mkdir -p "$AWG_BIN_DIR" "$CONF_DIR/awg-native"
  for name in amneziawg-go awg; do
    src="$AWG_BUNDLE_DIR/$name"
    dst="$AWG_BIN_DIR/$name"
    tmp="$dst.unified-ui-new.$$"
    [ -f "$src" ] || continue
    if [ -f "$dst" ] && cmp -s "$src" "$dst" 2>/dev/null; then
      chmod 755 "$dst"
      continue
    fi
    [ ! -f "$dst" ] || cp -p "$dst" "$dst.unified-ui-prev"
    cp "$src" "$tmp"
    chmod 755 "$tmp"
    mv -f "$tmp" "$dst"
  done
  [ ! -f "$AWG_BUNDLE_DIR/SHA256SUMS" ] || cp "$AWG_BUNDLE_DIR/SHA256SUMS" "$CONF_DIR/awg-native/SHA256SUMS"
  [ ! -f "$AWG_BUNDLE_DIR/OFFICIAL_AWG_PROVENANCE.json" ] || cp "$AWG_BUNDLE_DIR/OFFICIAL_AWG_PROVENANCE.json" "$CONF_DIR/awg-native/OFFICIAL_AWG_PROVENANCE.json"
  chmod 600 "$CONF_DIR"/awg-native/* 2>/dev/null || true
}

install_bundled_awg_runtime

install_bundled_mihomo() {
  [ -f "$MIHOMO_BUNDLE" ] || { echo "Bundled ARM64 Mihomo is missing" >&2; return 1; }
  if [ -f "$SCRIPT_DIR/bin/MIHOMO_SHA256" ]; then
    (cd "$SCRIPT_DIR/bin" && sha256sum -c MIHOMO_SHA256) >/dev/null
  fi
  mkdir -p /usr/bin /etc/mihomo /etc/mihomo/rules /etc/mihomo/profiles /var/log
  tmp="/usr/bin/mihomo.unified-ui-new.$$"
  cp "$MIHOMO_BUNDLE" "$tmp"
  chmod 755 "$tmp"
  mv -f "$tmp" /usr/bin/mihomo
  if [ ! -s /etc/mihomo/config.yaml ]; then
    cat > /etc/mihomo/config.yaml <<'MIHOMOCONF'
mixed-port: 7890
allow-lan: true
bind-address: '*'
mode: rule
log-level: info
ipv6: false
external-controller: 127.0.0.1:9090
secret: ''
profile:
  store-selected: true
proxies: []
proxy-groups:
  - name: GLOBAL
    type: select
    proxies:
      - DIRECT
rules:
  - MATCH,GLOBAL
MIHOMOCONF
    chmod 600 /etc/mihomo/config.yaml
  fi
  if [ ! -f /etc/init.d/mihomo ]; then
    cat > /etc/init.d/mihomo <<'MIHOMOINIT'
#!/bin/sh /etc/rc.common
START=95
STOP=10
USE_PROCD=1
start_service() {
  procd_open_instance
  procd_set_param command /usr/bin/mihomo -d /etc/mihomo -f /etc/mihomo/config.yaml
  procd_set_param respawn 3600 5 5
  procd_set_param stdout 1
  procd_set_param stderr 1
  procd_close_instance
}
service_triggers() { procd_add_reload_trigger mihomo; }
MIHOMOINIT
    chmod 755 /etc/init.d/mihomo
  fi
  /usr/bin/mihomo -t -d /etc/mihomo -f /etc/mihomo/config.yaml >/dev/null
  /etc/init.d/mihomo enable >/dev/null 2>&1 || true
  /etc/init.d/mihomo restart >/dev/null 2>&1
}

install_bundled_mihomo

cat > "$UPDATE_SCRIPT" <<'UPD'
#!/bin/sh
set -eu
CONF_FILE="/etc/unified-ui/openwrt.env"
[ -f "$CONF_FILE" ] && . "$CONF_FILE"
UPDATE_URL="${UNIFIED_UI_UPDATE_URL:-}"
[ -n "$UPDATE_URL" ] || UPDATE_URL="$(jsonfilter -i /etc/unified-ui/BUILD.json -e '@.update_url' 2>/dev/null || true)"
if [ -z "$UPDATE_URL" ]; then
  echo "No update_url configured in /etc/unified-ui/BUILD.json or env." >&2
  exit 1
fi
TMP_DIR="/tmp/unified-ui-openwrt-update-$$"
ARCHIVE="$TMP_DIR/unified-ui-openwrt.tar.gz"
mkdir -p "$TMP_DIR"
trap 'rm -rf "$TMP_DIR"' EXIT INT TERM
curl_args="-fL --max-time 120"
curl $curl_args -o "$ARCHIVE" "$UPDATE_URL"
tar -xzf "$ARCHIVE" -C "$TMP_DIR"
INSTALLER="$(find "$TMP_DIR" -maxdepth 2 -type f -name install.sh | head -1)"
[ -n "$INSTALLER" ] || { echo "install.sh not found in update archive" >&2; exit 1; }
sh "$INSTALLER"
UPD
chmod 755 "$UPDATE_SCRIPT"

ROUTER_BYPASS_INIT="/etc/init.d/unified-ui-router-bypass"
cat > "$ROUTER_BYPASS_INIT" <<'BYPASS'
#!/bin/sh /etc/rc.common
START=99
USE_PROCD=0
apply_rules() {
  for p in 8986 8987 8988 8989 8996 8997 8998 8999; do while ip rule del pref "$p" 2>/dev/null; do :; done; done
  ip rule add pref 8986 ipproto udp dport 53 lookup main
  ip rule add pref 8987 ipproto tcp dport 53 lookup main
  ip rule add pref 8988 ipproto tcp dport 80 lookup main
  ip rule add pref 8989 ipproto tcp dport 443 lookup main
}
start() { apply_rules; }
restart() { apply_rules; }
BYPASS
chmod 755 "$ROUTER_BYPASS_INIT"
"$ROUTER_BYPASS_INIT" enable >/dev/null 2>&1 || true
"$ROUTER_BYPASS_INIT" start >/dev/null 2>&1 || true

AWG_NATIVE_HELPER="/usr/sbin/unified-awg-native"
AWG_NATIVE_INIT="/etc/init.d/unified-awg-native"
cat > "$AWG_NATIVE_HELPER" <<'AWGN'
#!/bin/sh
set -eu
STATE_DIR="${UNIFIED_AWG_STATE_DIR:-/etc/unified-ui/awg-native}"
CONFIG_DIR="$STATE_DIR/configs"
MANIFEST="$STATE_DIR/manifest"
AWG_GO_BIN="${UNIFIED_AWG_GO_BIN:-/usr/bin/amneziawg-go}"
AWG_BIN="${UNIFIED_AWG_BIN:-/usr/bin/awg}"
IP_BIN="${UNIFIED_IP_BIN:-/sbin/ip}"

mkdir -p "$CONFIG_DIR"
chmod 700 "$STATE_DIR" "$CONFIG_DIR" 2>/dev/null || true

run_optional() { "$@" >/dev/null 2>&1 || true; }

wait_socket() {
  iface="$1"; i=0
  while [ "$i" -lt 50 ]; do
    [ -S "/var/run/amneziawg/$iface.sock" ] && return 0
    [ -S "/var/run/wireguard/$iface.sock" ] && return 0
    if command -v usleep >/dev/null 2>&1; then usleep 100000; else sleep 1; fi
    i=$((i + 1))
  done
  return 1
}

stop_iface() {
  iface="$1"; mark="${2:-0}"; table="${3:-0}"; prio="${4:-0}"
  [ "$prio" = 0 ] || run_optional "$IP_BIN" rule del priority "$prio" fwmark "$mark" table "$table"
  [ "$table" = 0 ] || run_optional "$IP_BIN" route flush table "$table"
  if [ -f "$STATE_DIR/$iface.pid" ]; then
    pid="$(cat "$STATE_DIR/$iface.pid" 2>/dev/null || true)"
    [ -z "$pid" ] || kill "$pid" >/dev/null 2>&1 || true
    rm -f "$STATE_DIR/$iface.pid"
  fi
  run_optional "$IP_BIN" link del dev "$iface"
  rm -f "/var/run/amneziawg/$iface.sock" "/var/run/wireguard/$iface.sock"
}

stop_all() {
  if [ -f "$MANIFEST" ]; then
    while IFS='|' read -r iface mark table prio; do
      [ -n "$iface" ] || continue
      stop_iface "$iface" "$mark" "$table" "$prio"
    done < "$MANIFEST"
  fi
}

start_one() {
  iface="$1"; conf="$2"; addresses="$3"; mtu="$4"; mark="$5"; table="$6"; prio="$7"
  [ -x "$AWG_GO_BIN" ] || { echo "missing amneziawg-go" >&2; return 10; }
  [ -x "$AWG_BIN" ] || { echo "missing awg" >&2; return 11; }
  [ -x "$IP_BIN" ] || { echo "missing ip" >&2; return 12; }
  [ -f "$conf" ] || { echo "missing config" >&2; return 13; }
  chmod 600 "$conf"
  stop_iface "$iface" "$mark" "$table" "$prio"
  "$AWG_GO_BIN" "$iface" >/dev/null 2>&1 &
  echo "$!" > "$STATE_DIR/$iface.pid"
  wait_socket "$iface" || { stop_iface "$iface" "$mark" "$table" "$prio"; echo "UAPI socket timeout for $iface" >&2; return 14; }
  "$AWG_BIN" setconf "$iface" "$conf"
  printf '%s\n' "$addresses" | tr ',' '\n' | while IFS= read -r addr; do
    [ -n "$addr" ] || continue
    "$IP_BIN" address add "$addr" dev "$iface"
  done
  [ -z "$mtu" ] || "$IP_BIN" link set mtu "$mtu" dev "$iface"
  "$IP_BIN" link set up dev "$iface"
  "$IP_BIN" route replace default dev "$iface" table "$table"
  "$IP_BIN" rule add priority "$prio" fwmark "$mark" table "$table"
}

case "${1:-}" in
  reconcile)
    desired="${2:-}"
    stop_all
    : > "$MANIFEST.new"
    if [ -n "$desired" ] && [ -f "$desired" ]; then
      while IFS='|' read -r iface conf addresses mtu mark table prio; do
        [ -n "$iface" ] || continue
        start_one "$iface" "$conf" "$addresses" "$mtu" "$mark" "$table" "$prio"
        printf '%s|%s|%s|%s\n' "$iface" "$mark" "$table" "$prio" >> "$MANIFEST.new"
      done < "$desired"
    fi
    chmod 600 "$MANIFEST.new"
    mv -f "$MANIFEST.new" "$MANIFEST"
    ;;
  stop)
    stop_all
    rm -f "$MANIFEST"
    ;;
  *)
    echo "usage: unified-awg-native reconcile <desired-file>|stop" >&2
    exit 2
    ;;
esac
AWGN
chmod 755 "$AWG_NATIVE_HELPER"

cat > "$AWG_NATIVE_INIT" <<'AWGINIT'
#!/bin/sh /etc/rc.common
START=94
STOP=12
USE_PROCD=0
start() {
  [ -x /usr/sbin/unified-awg-native ] || return 0
  [ -f /etc/unified-ui/awg-native/desired ] || return 0
  /usr/sbin/unified-awg-native reconcile /etc/unified-ui/awg-native/desired >/dev/null 2>&1 || true
}
stop() {
  [ -x /usr/sbin/unified-awg-native ] || return 0
  /usr/sbin/unified-awg-native stop >/dev/null 2>&1 || true
}
restart() { stop; start; }
AWGINIT
chmod 755 "$AWG_NATIVE_INIT"
"$AWG_NATIVE_INIT" enable >/dev/null 2>&1 || true

cat > "$UNINSTALL_SCRIPT" <<'UNINST'
#!/bin/sh
set -eu
/etc/init.d/unified-awg-native stop >/dev/null 2>&1 || true
/etc/init.d/unified-awg-native disable >/dev/null 2>&1 || true
rm -f /www/cgi-bin/unified-ui-api
rm -f /usr/sbin/unified-awg-native /etc/init.d/unified-awg-native
rm -rf /www/unified-ui
rm -rf /etc/unified-ui
printf 'Unified UI OpenWrt removed.\n'
UNINST
chmod 755 "$UNINSTALL_SCRIPT"

cat > "$CGI_PATH" <<'CGI'
#!/bin/sh
CONF_FILE="/etc/unified-ui/openwrt.env"
[ -f "$CONF_FILE" ] && . "$CONF_FILE"
MIHOMO_CONTROLLER="${MIHOMO_CONTROLLER:-http://127.0.0.1:9090}"
MIHOMO_SECRET="${MIHOMO_SECRET:-}"
MIHOMO_INIT="${MIHOMO_INIT:-/etc/init.d/mihomo}"
MIHOMO_CONFIG="${MIHOMO_CONFIG:-/etc/mihomo/config.yaml}"
MIHOMO_RUN_DIR="${MIHOMO_RUN_DIR:-/etc/mihomo}"
MIHOMO_PROFILE="${MIHOMO_PROFILE:-/etc/mihomo/config.yaml}"
UNIFIED_UI_BUILD_FILE="${UNIFIED_UI_BUILD_FILE:-/etc/unified-ui/BUILD.json}"
UNIFIED_UI_CONF_DIR="${UNIFIED_UI_CONF_DIR:-/etc/unified-ui}"
UNIFIED_UI_BACKUP_DIR="${UNIFIED_UI_BACKUP_DIR:-/etc/unified-ui/backups}"
UNIFIED_UI_VERSION="${UNIFIED_UI_VERSION:-dev-local}"
UNIFIED_UI_UPDATE_URL="${UNIFIED_UI_UPDATE_URL:-}"
UNIFIED_UI_AUTH_USER="${UNIFIED_UI_AUTH_USER:-admin}"
UNIFIED_UI_AUTH_PASSWORD="${UNIFIED_UI_AUTH_PASSWORD:-admin}"
UNIFIED_UI_SESSION_FILE="${UNIFIED_UI_SESSION_FILE:-/tmp/unified-ui-session.token}"
UNIFIED_UI_SESSION_COOKIE="UnifiedUIOpenWrtSession"

json_escape() {
  sed 's/\\/\\\\/g; s/"/\\"/g; s/\t/\\t/g; s/\r/\\r/g; s/$/\\n/' | tr -d '\n' | sed 's/\\n$//'
}

hdr_json() {
  printf 'Status: %s\r\n' "${1:-200 OK}"
  printf 'Content-Type: application/json; charset=utf-8\r\n'
  printf 'Cache-Control: no-store\r\n\r\n'
}

hdr_json_cookie() {
  status="${1:-200 OK}"
  cookie_line="${2:-}"
  printf 'Status: %s\r\n' "$status"
  printf 'Content-Type: application/json; charset=utf-8\r\n'
  printf 'Cache-Control: no-store\r\n'
  [ -n "$cookie_line" ] && printf 'Set-Cookie: %s\r\n' "$cookie_line"
  printf '\r\n'
}

cookie_value() {
  name="$1"
  printf '%s' "${HTTP_COOKIE:-}" | tr ';' '\n' | sed 's/^ *//' | sed -n "s/^$name=//p" | head -1
}

session_token() {
  if [ -f "$UNIFIED_UI_SESSION_FILE" ]; then
    cat "$UNIFIED_UI_SESSION_FILE" 2>/dev/null || true
  fi
}

new_session_token() {
  mkdir -p "$(dirname "$UNIFIED_UI_SESSION_FILE")"
  token="$(dd if=/dev/urandom bs=24 count=1 2>/dev/null | base64 | tr -d '=+/\n' | cut -c1-32)"
  [ -n "$token" ] || token="$(date +%s)-$$"
  printf '%s' "$token" > "$UNIFIED_UI_SESSION_FILE"
  chmod 600 "$UNIFIED_UI_SESSION_FILE" 2>/dev/null || true
  printf '%s' "$token"
}

is_auth_path() {
  case "${PATH_INFO:-}" in
    /auth-login|/auth-check|/auth-logout) return 0 ;;
    *) return 1 ;;
  esac
}

is_authenticated() {
  expected="$(session_token)"
  got="$(cookie_value "$UNIFIED_UI_SESSION_COOKIE")"
  [ -n "$expected" ] && [ -n "$got" ] && [ "$expected" = "$got" ]
}

require_auth_or_401() {
  if is_auth_path || is_authenticated; then return 0; fi
  hdr_json_cookie '401 Unauthorized'
  printf '{"ok":false,"authenticated":false,"error":"auth_required"}'
  exit 0
}

mihomo_get() {
  path="$1"
  if [ -n "$MIHOMO_SECRET" ]; then
    header_name="Authorization"
    header_value="Bearer $MIHOMO_SECRET"
    curl -sS --max-time 8 -H "$header_name: $header_value" "$MIHOMO_CONTROLLER$path"
  else
    curl -sS --max-time 8 "$MIHOMO_CONTROLLER$path"
  fi
}

mihomo_req() {
  method="$1"
  path="$2"
  body="${3:-}"
  if [ -n "$MIHOMO_SECRET" ]; then
    header_name="Authorization"
    header_value="Bearer $MIHOMO_SECRET"
    if [ -n "$body" ]; then
      curl -sS --max-time 12 -X "$method" -H "$header_name: $header_value" -H 'Content-Type: application/json' --data "$body" "$MIHOMO_CONTROLLER$path"
    else
      curl -sS --max-time 12 -X "$method" -H "$header_name: $header_value" "$MIHOMO_CONTROLLER$path"
    fi
  else
    if [ -n "$body" ]; then
      curl -sS --max-time 12 -X "$method" -H 'Content-Type: application/json' --data "$body" "$MIHOMO_CONTROLLER$path"
    else
      curl -sS --max-time 12 -X "$method" "$MIHOMO_CONTROLLER$path"
    fi
  fi
}

read_body() {
  len="${CONTENT_LENGTH:-0}"
  case "$len" in ''|*[!0-9]*) len=0 ;; esac
  if [ "$len" -gt 0 ]; then
    dd bs=1 count="$len" 2>/dev/null
  fi
}

ui_update_url() {
  if [ -n "$UNIFIED_UI_UPDATE_URL" ]; then
    printf '%s' "$UNIFIED_UI_UPDATE_URL"
  elif [ -f "$UNIFIED_UI_BUILD_FILE" ]; then
    jsonfilter -i "$UNIFIED_UI_BUILD_FILE" -e '@.update_url' 2>/dev/null || true
  fi
}

build_version() { jsonfilter -i "$UNIFIED_UI_BUILD_FILE" -e '@.version' 2>/dev/null || printf '%s' "$UNIFIED_UI_VERSION"; }
build_date() { jsonfilter -i "$UNIFIED_UI_BUILD_FILE" -e '@.release_date' 2>/dev/null || true; }
update_repo() { printf '%s' "${UNIFIED_UI_UPDATE_REPO:-sllikmll/Unified-UI}"; }
update_channel() { printf '%s' "${UNIFIED_UI_UPDATE_CHANNEL:-stable}"; }
update_branch() { printf '%s' "${UNIFIED_UI_UPDATE_BRANCH:-main}"; }

curl_github() {
  url="$1"
  curl -fsSL --max-time 20 "$url" 2>/tmp/unified-ui-gh.err
}

github_latest_json() {
  repo="$(update_repo)"
  tmp="/tmp/unified-ui-gh-latest-$$.json"
  if curl_github "https://api.github.com/repos/$repo/releases/latest" > "$tmp"; then
    tag="$(jsonfilter -i "$tmp" -e '@.tag_name' 2>/dev/null || true)"
    pub="$(jsonfilter -i "$tmp" -e '@.published_at' 2>/dev/null || true)"
    html="$(jsonfilter -i "$tmp" -e '@.html_url' 2>/dev/null || true)"
    assets="$(jsonfilter -i "$tmp" -e '@.assets[*].name' 2>/dev/null | awk 'BEGIN{printf "["} {gsub(/"/,"\\\""); if(NR>1)printf ","; printf "{\"name\":\"%s\"}",$0} END{printf "]"}')"
    rm -f "$tmp"
    [ -n "$assets" ] || assets='[]'
    printf '{"ok":true,"latest":{"kind":"stable","tag":"%s","published_at":"%s","url":"%s","assets":%s}}' "$(printf '%s' "$tag" | json_escape)" "$(printf '%s' "$pub" | json_escape)" "$(printf '%s' "$html" | json_escape)" "$assets"
  else
    err="$(cat /tmp/unified-ui-gh.err 2>/dev/null | json_escape)"
    rm -f "$tmp"
    printf '{"ok":false,"error":"github_unavailable","hint":"GitHub недоступен с роутера напрямую","meta":{"message":"%s"}}' "$err"
  fi
}

validate_profile_content() {
  tmp="/tmp/unified-ui-validate-$$.yaml"
  cat > "$tmp"
  out="$({ /usr/bin/mihomo -t -d "$MIHOMO_RUN_DIR" -f "$tmp"; } 2>&1)"
  code=$?
  rm -f "$tmp"
  printf '%s\n__EXIT__%s' "$out" "$code"
}


json_string_value() {
  key="$1"
  sed -n "s/.*\"$key\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p" | head -1
}

shell_quote_value() {
  printf "%s" "$1" | sed "s/'/'\\''/g; s/^/'/; s/$/'/"
}

set_env_value() {
  key="$1"
  value="$2"
  mkdir -p "$(dirname "$CONF_FILE")"
  touch "$CONF_FILE"
  tmp="$CONF_FILE.tmp.$$"
  q="$(shell_quote_value "$value")"
  if grep -q "^$key=" "$CONF_FILE" 2>/dev/null; then
    sed "s|^$key=.*|$key=$q|" "$CONF_FILE" > "$tmp"
  else
    cat "$CONF_FILE" > "$tmp"
    printf '%s=%s\n' "$key" "$q" >> "$tmp"
  fi
  mv "$tmp" "$CONF_FILE"
  chmod 600 "$CONF_FILE" 2>/dev/null || true
}

url_decode() {
  printf '%s' "$1" | sed 's/+/ /g; s/%2[Ff]/\//g; s/%3[Aa]/:/g; s/%20/ /g; s/%2[Dd]/-/g; s/%5[Ff]/_/g; s/%2[Ee]/./g'
}

query_param() {
  key="$1"
  qs="${QUERY_STRING:-}"
  if [ -z "$qs" ] && [ -n "${REQUEST_URI:-}" ]; then
    case "$REQUEST_URI" in *\?*) qs="${REQUEST_URI#*?}" ;; esac
  fi
  printf '%s' "$qs" | tr '&' '\n' | sed -n "s/^$key=//p" | head -1 | while IFS= read -r v; do url_decode "$v"; done
}

json_escape_str() {
  printf '%s' "$1" | json_escape
}

openwrt_fs_safe_path() {
  p="$1"
  [ -n "$p" ] || p="/tmp"
  case "$p" in
    /opt/var|/opt/var/*|/opt/etc|/opt/etc/*) p="/etc" ;;
  esac
  case "$p" in
    /*) ;;
    *) p="/$p" ;;
  esac
  # Keep this intentionally conservative for the browser file manager.
  case "$p" in
    /|/etc|/etc/*|/tmp|/tmp/*|/www|/www/*|/root|/root/*|/rom|/rom/*|/overlay|/overlay/*|/mnt|/mnt/*) printf '%s' "$p" ;;
    *) printf '/tmp' ;;
  esac
}

rule_provider_file() {
  name="$1"
  case "$name" in
    manual-proxy|manual-proxy@classical|manual|Ручной*) printf '%s/rules/manual-proxy.yaml' "$MIHOMO_RUN_DIR" ;;
    *) printf '%s/rules/%s.yaml' "$MIHOMO_RUN_DIR" "$name" ;;
  esac
}

PROXY_REGISTRY="${UNIFIED_UI_CONF_DIR:-/etc/unified-ui}/proxy-connections.json"
AWG_STATE_DIR="${UNIFIED_UI_CONF_DIR:-/etc/unified-ui}/awg-native"
AWG_CONFIG_DIR="$AWG_STATE_DIR/configs"
AWG_DESIRED_FILE="$AWG_STATE_DIR/desired"
AWG_HELPER="${UNIFIED_AWG_HELPER:-/usr/sbin/unified-awg-native}"
AWG_GO_BIN="${UNIFIED_AWG_GO_BIN:-/usr/bin/amneziawg-go}"
AWG_BIN="${UNIFIED_AWG_BIN:-/usr/bin/awg}"
PROXY_MANAGED_START="# unified-managed-proxies:start"
PROXY_MANAGED_END="# unified-managed-proxies:end"
AWG_GROUP_MARKER="# unified-managed-awg"
proxy_protocols_json() {
  printf '[{"id":"wireguard","label":"WireGuard"},{"id":"amnezia","label":"Amnezia"},{"id":"hysteria2","label":"Hysteria2"},{"id":"vless","label":"VLESS"},{"id":"trojan","label":"Trojan"},{"id":"vmess","label":"VMess"},{"id":"shadowsocks","label":"Shadowsocks"},{"id":"mieru","label":"Mieru"},{"id":"naiveproxy","label":"NaiveProxy"},{"id":"telegram","label":"Telegram MTProxy"}]'
}
selector_names_json() {
  awk '
    /^proxy-groups:/ { in_groups=1; next }
    in_groups && /^[a-zA-Z0-9_-]+:/ { in_groups=0 }
    in_groups && /^[[:space:]]*-[[:space:]]*name:/ {
      sub(/^[[:space:]]*-[[:space:]]*name:[[:space:]]*/, "");
      gsub(/^["'"'"']|["'"'"']$/, "");
      gsub(/\\/, "\\\\"); gsub(/"/, "\\\"");
      print "\"" $0 "\"";
    }
  ' "$MIHOMO_PROFILE" 2>/dev/null | awk 'BEGIN{printf "["} {if(NR>1)printf ","; printf "%s",$0} END{printf "]"}'
}
registry_json() {
  if [ -f "$PROXY_REGISTRY" ]; then cat "$PROXY_REGISTRY"; else printf '{"connections":[]}'; fi
}

safe_id() {
  printf '%s' "$1" | tr -cs 'A-Za-z0-9_.-' '-' | sed 's/^-//;s/-$//' | cut -c1-96
}

hash10() {
  printf '%s' "$1" | sha256sum | awk '{print substr($1,1,10)}'
}

awg_iface_name() {
  printf 'uawg%s' "$(hash10 "$1")"
}

awg_identity() {
  hex="$(printf '%s' "$1" | sha256sum | awk '{print substr($1,1,8)}')"
  value="$(printf '%d' "0x$hex" 2>/dev/null || echo 0)"
  value=$((value % 10000))
  printf '%s|%s|%s' "$((50000 + value))" "$((20000 + value))" "$((30000 + value))"
}

sanitize_awg_selector() {
  selector="$(printf '%s' "$1" | tr -d '\r\n|')"
  [ -n "$selector" ] || selector="GLOBAL"
  printf '%s' "$selector"
}

awg_uri_to_conf() {
  uri_raw="$1"
  case "$uri_raw" in
    awg://*|awg3://*|amneziawg://*)
      encoded="${uri_raw#*://}"
      encoded="${encoded%%#*}"
      encoded="${encoded%%\?*}"
      pad=$(( (4 - (${#encoded} % 4)) % 4 ))
      while [ "$pad" -gt 0 ]; do encoded="${encoded}="; pad=$((pad - 1)); done
      printf '%s' "$encoded" | tr '_-' '/+' | base64 -d 2>/dev/null
      ;;
    *) printf '%s' "$uri_raw" ;;
  esac
}

awg_fragment_name() {
  fragment_raw="$1"
  case "$fragment_raw" in
    *://*#*) url_decode "${fragment_raw#*#}" ;;
    *) printf '' ;;
  esac
}

awg_conf_value_file() {
  file="$1"; section="$2"; key="$3"
  awk -F= -v section="$section" -v key="$key" '
    function norm(s){ gsub(/^[ \t]+|[ \t]+$/, "", s); gsub(/[-_]/, "", s); return tolower(s) }
    /^[ \t]*\[/ {
      current=$0
      gsub(/^[ \t]*\[|\][ \t]*$/, "", current)
      current=tolower(current)
      next
    }
    current == tolower(section) && index($0, "=") {
      k=$1; v=$0; sub(/^[^=]*=/, "", v)
      if (norm(k) == norm(key)) {
        gsub(/^[ \t]+|[ \t]+$/, "", v)
        print v
        exit
      }
    }
  ' "$file"
}

awg_conf_has_native_options() {
  file="$1"
  awk -F= '
    function norm(s){ gsub(/^[ \t]+|[ \t]+$/, "", s); gsub(/[-_]/, "", s); return tolower(s) }
    /^[ \t]*\[/ { current=$0; gsub(/^[ \t]*\[|\][ \t]*$/, "", current); current=tolower(current); next }
    current == "interface" && index($0, "=") {
      k=norm($1)
      if (k=="jc" || k=="jmin" || k=="jmax" || k=="s1" || k=="s2" || k=="s3" || k=="s4" || k=="h1" || k=="h2" || k=="h3" || k=="h4") found=1
    }
    END { exit found ? 0 : 1 }
  ' "$file"
}

awg_write_setconf() {
  src="$1"; dst="$2"
  # Preserve AWG UAPI material generically: PrivateKey/PublicKey/PresharedKey,
  # Endpoint/AllowedIPs, and Amnezia fields Jc/Jmin/Jmax/S1-S4/H1-H4.
  awk -F= '
    function norm(s){ gsub(/^[ \t]+|[ \t]+$/, "", s); gsub(/[-_]/, "", s); return tolower(s) }
    function trim(s){ gsub(/^[ \t]+|[ \t]+$/, "", s); return s }
    /^[ \t]*(#|;|$)/ { next }
    /^[ \t]*\[/ {
      current=$0
      gsub(/^[ \t]*\[|\][ \t]*$/, "", current)
      current=tolower(current)
      if (current=="interface") print "[Interface]"
      else if (current=="peer") { print ""; print "[Peer]" }
      next
    }
    current == "interface" && index($0, "=") {
      k=trim($1); v=$0; sub(/^[^=]*=/, "", v); v=trim(v); nk=norm(k)
      if (nk=="address" || nk=="dns" || nk=="mtu" || nk=="table" || nk=="preup" || nk=="postup" || nk=="predown" || nk=="postdown" || nk=="name") next
      print k " = " v
      next
    }
    current == "peer" && index($0, "=") {
      k=trim($1); v=$0; sub(/^[^=]*=/, "", v); v=trim(v); nk=norm(k)
      if (nk=="name") next
      print k " = " v
    }
  ' "$src" > "$dst"
  chmod 600 "$dst"
}

awg_direct_proxy_yaml_file() {
  name="$1"; iface="$2"; mark="$3"; out="$4"
  qname="$(yaml_single_quote "$name")"
  qiface="$(yaml_single_quote "$iface")"
  {
    printf -- "- name: %s\n" "$qname"
    printf '%s\n' "  type: direct"
    printf '  interface-name: %s\n' "$qiface"
    printf '  routing-mark: %s\n' "$mark"
    printf '%s\n' "  udp: true"
  } > "$out"
}

connection_public_json_from_files() {
  id="$1"; name="$2"; proto="$3"; selector="$4"; yaml_file="$5"; iface="$6"; mark="$7"; table="$8"; prio="$9"
  proxy_yaml="$(json_escape < "$yaml_file")"
  selector_json="$(printf '%s' "$selector" | json_escape)"
  printf '{"id":"%s","name":"%s","protocol":"%s","protocolLabel":"%s","enabled":true,"mihomoSupported":true,"selectors":["%s"],"usedBySelectors":["%s"],"proxyYaml":"%s","hasRaw":true,"nativeRuntime":{"engine":"amneziawg-go","interface":"%s","routingMark":%s,"routingTable":%s,"rulePriority":%s}}' \
    "$(printf '%s' "$id" | json_escape)" "$(printf '%s' "$name" | json_escape)" "$(printf '%s' "$proto" | json_escape)" "$(printf '%s' "$proto" | json_escape)" "$selector_json" "$selector_json" "$proxy_yaml" "$(printf '%s' "$iface" | json_escape)" "$mark" "$table" "$prio"
}

import_awg_connection() {
  proto="$1"; name="$2"; content="$3"; selector="$(sanitize_awg_selector "${4:-}")"
  tmp_dir="/tmp/unified-awg-import-$$"
  mkdir -p "$tmp_dir" "$UNIFIED_UI_CONF_DIR" "$AWG_CONFIG_DIR"
  chmod 700 "$tmp_dir" "$AWG_STATE_DIR" "$AWG_CONFIG_DIR" 2>/dev/null || true
  raw="$tmp_dir/raw.conf"; setconf="$tmp_dir/setconf.conf"; yaml="$tmp_dir/proxy.yaml"
  awg_uri_to_conf "$content" > "$raw" || { rm -rf "$tmp_dir"; return 20; }
  [ -n "$name" ] || name="$(awg_fragment_name "$content")"
  [ -n "$name" ] || name="AmneziaWG"
  priv="$(awg_conf_value_file "$raw" Interface PrivateKey)"
  pub="$(awg_conf_value_file "$raw" Peer PublicKey)"
  endpoint="$(awg_conf_value_file "$raw" Peer Endpoint)"
  [ -n "$priv" ] && [ -n "$pub" ] && [ -n "$endpoint" ] || { rm -rf "$tmp_dir"; return 21; }
  iface="$(awg_iface_name "$name")"
  identity="$(awg_identity "$name")"
  mark="${identity%%|*}"; rest="${identity#*|}"; table="${rest%%|*}"; prio="${rest##*|}"
  addresses="$(awg_conf_value_file "$raw" Interface Address | tr -d ' ')"
  mtu="$(awg_conf_value_file "$raw" Interface MTU)"
  awg_write_setconf "$raw" "$setconf"
  awg_direct_proxy_yaml_file "$name" "$iface" "$mark" "$yaml"
  id="$(safe_id "$proto-$name-$(hash10 "$content")")"
  raw_esc="$(json_escape < "$raw")"
  proxy_yaml="$(json_escape < "$yaml")"
  selector_json="$(printf '%s' "$selector" | json_escape)"
  mkdir -p "$UNIFIED_UI_CONF_DIR"
  tmp="$PROXY_REGISTRY.tmp.$$"
  printf '{"version":1,"connections":[{"id":"%s","name":"%s","protocol":"amnezia","protocolLabel":"Amnezia","sourceType":"import","enabled":true,"mihomoSupported":true,"selectors":["%s"],"usedBySelectors":["%s"],"proxyYaml":"%s","rawContent":"%s","nativeRuntime":{"engine":"amneziawg-go","interface":"%s","routingMark":%s,"routingTable":%s,"rulePriority":%s,"addresses":"%s","mtu":"%s"}}]}\n' \
    "$(printf '%s' "$id" | json_escape)" "$(printf '%s' "$name" | json_escape)" "$selector_json" "$selector_json" "$proxy_yaml" "$raw_esc" "$(printf '%s' "$iface" | json_escape)" "$mark" "$table" "$prio" "$(printf '%s' "$addresses" | json_escape)" "$(printf '%s' "$mtu" | json_escape)" > "$tmp"
  mv "$tmp" "$PROXY_REGISTRY"
  chmod 600 "$PROXY_REGISTRY"
  connection_public_json_from_files "$id" "$name" amnezia "$selector" "$yaml" "$iface" "$mark" "$table" "$prio"
  rm -rf "$tmp_dir"
}

proxy_replace_managed_block() {
  source_config="$1"; proxy_body="$2"; destination="$3"
  cleaned="$destination.cleaned"
  awk -v start="$PROXY_MANAGED_START" -v end="$PROXY_MANAGED_END" '
    $0 ~ "^[[:space:]]*" start "$" { skip=1; next }
    $0 ~ "^[[:space:]]*" end "$" { skip=0; next }
    !skip { print }
  ' "$source_config" > "$cleaned"
  awk -v body="$proxy_body" -v start="$PROXY_MANAGED_START" -v end="$PROXY_MANAGED_END" '
    !inserted && /^proxies:[[:space:]]*(\[\])?[[:space:]]*$/ {
      print "proxies:"
      print "  " start
      while ((getline line < body) > 0) print "  " line
      close(body)
      print "  " end
      inserted=1
      next
    }
    { print }
    END {
      if (!inserted) {
        print "proxies:" > "/dev/stderr"
        exit 42
      }
    }
  ' "$cleaned" > "$destination"
  rc=$?
  rm -f "$cleaned"
  return "$rc"
}

proxy_sync_awg_group_memberships() {
  source_config="$1"; members_file="$2"; destination="$3"
  awk -v marker="$AWG_GROUP_MARKER" '
    index($0, marker) == 0 { print }
  ' "$source_config" > "$destination.cleaned"
  awk -v members="$members_file" -v marker="$AWG_GROUP_MARKER" '
    BEGIN {
      while ((getline row < members) > 0) {
        tab = index(row, "\t")
        if (tab > 0) {
          n++
          selectors[n] = substr(row, 1, tab - 1)
          proxy_names[n] = substr(row, tab + 1)
        }
      }
      close(members)
    }
    function clean_name(value) {
      sub(/^[[:space:]]*/, "", value)
      sub(/[[:space:]]*$/, "", value)
      sub(/^["'\'']/, "", value)
      sub(/["'\'']$/, "", value)
      return value
    }
    function emit_managed(group, indent, i) {
      for (i = 1; i <= n; i++) {
        if (selectors[i] == group) {
          print indent "- " proxy_names[i] " " marker
          inserted[i] = 1
        }
      }
    }
    /^proxy-groups:[[:space:]]*$/ { in_groups = 1; current = ""; print; next }
    in_groups && pending_group != "" && /^[[:space:]]*-[[:space:]]+/ && $0 !~ /^[[:space:]]*-[[:space:]]*name:[[:space:]]*/ {
      print
      match($0, /^[[:space:]]*/)
      emit_managed(pending_group, substr($0, RSTART, RLENGTH))
      pending_group = ""
      next
    }
    in_groups && pending_group != "" && $0 !~ /^[[:space:]]*#/ {
      emit_managed(pending_group, pending_indent "  ")
      pending_group = ""
    }
    in_groups && /^[^[:space:]#][^:]*:/ { in_groups = 0; current = "" }
    in_groups && /^[[:space:]]*-[[:space:]]*name:[[:space:]]*/ {
      line = $0
      sub(/^[[:space:]]*-[[:space:]]*name:[[:space:]]*/, "", line)
      current = clean_name(line)
    }
    in_groups && current != "" && /^[[:space:]]*proxies:[[:space:]]*\[[^]]*\][[:space:]]*$/ {
      line = $0
      match(line, /^[[:space:]]*/)
      indent = substr(line, RSTART, RLENGTH)
      items = line
      sub(/^[[:space:]]*proxies:[[:space:]]*\[/, "", items)
      sub(/\][[:space:]]*$/, "", items)
      print indent "proxies:"
      emit_managed(current, indent "  ")
      parts_count = split(items, parts, ",")
      for (i = 1; i <= parts_count; i++) {
        item = parts[i]
        sub(/^[[:space:]]*/, "", item)
        sub(/[[:space:]]*$/, "", item)
        if (item != "") print indent "  - " item
      }
      next
    }
    in_groups && current != "" && /^[[:space:]]*proxies:[[:space:]]*$/ {
      print
      match($0, /^[[:space:]]*/)
      pending_group = current
      pending_indent = substr($0, RSTART, RLENGTH)
      next
    }
    { print }
    END {
      if (pending_group != "") emit_managed(pending_group, pending_indent "  ")
      for (i = 1; i <= n; i++) if (!inserted[i]) exit 43
    }
  ' "$destination.cleaned" > "$destination"
  rc=$?
  rm -f "$destination.cleaned"
  return "$rc"
}

apply_proxy_connections_openwrt() {
  restart="${1:-false}"
  tmp_dir="/tmp/unified-awg-apply-$$"
  mkdir -p "$tmp_dir" "$AWG_CONFIG_DIR" "$UNIFIED_UI_BACKUP_DIR"
  chmod 700 "$tmp_dir" "$AWG_STATE_DIR" "$AWG_CONFIG_DIR" 2>/dev/null || true
  body_file="$tmp_dir/proxies.yaml"; desired="$tmp_dir/desired"; members="$tmp_dir/group-members"; : > "$body_file"; : > "$desired"; : > "$members"
  count=0
  if [ -f "$PROXY_REGISTRY" ]; then
    idx=0
    while :; do
      id="$(jsonfilter -i "$PROXY_REGISTRY" -e "@.connections[$idx].id" 2>/dev/null || true)"
      [ -n "$id" ] || break
      raw="$tmp_dir/$id.raw"; setconf="$AWG_CONFIG_DIR/$(safe_id "$id").conf"; yaml="$tmp_dir/$id.yaml"
      jsonfilter -i "$PROXY_REGISTRY" -e "@.connections[$idx].rawContent" > "$raw" 2>/dev/null || true
      if [ ! -s "$raw" ]; then
        idx=$((idx + 1))
        continue
      fi
      name="$(jsonfilter -i "$PROXY_REGISTRY" -e "@.connections[$idx].name" 2>/dev/null || true)"
      [ -n "$name" ] || name="AmneziaWG"
      selector="$(jsonfilter -i "$PROXY_REGISTRY" -e "@.connections[$idx].selectors[0]" 2>/dev/null || true)"
      selector="$(sanitize_awg_selector "$selector")"
      iface="$(awg_iface_name "$name")"
      identity="$(awg_identity "$name")"; mark="${identity%%|*}"; rest="${identity#*|}"; table="${rest%%|*}"; prio="${rest##*|}"
      addresses="$(awg_conf_value_file "$raw" Interface Address | tr -d ' ')"
      mtu="$(awg_conf_value_file "$raw" Interface MTU)"
      awg_write_setconf "$raw" "$setconf"
      awg_direct_proxy_yaml_file "$name" "$iface" "$mark" "$yaml"
      cat "$yaml" >> "$body_file"
      printf '%s\t%s\n' "$selector" "$(yaml_single_quote "$name")" >> "$members"
      printf '%s|%s|%s|%s|%s|%s|%s\n' "$iface" "$setconf" "$addresses" "$mtu" "$mark" "$table" "$prio" >> "$desired"
      idx=$((idx + 1))
    done
  fi
  count="$(grep -c '^-' "$body_file" 2>/dev/null || true)"
  profile_real="$(readlink -f "$MIHOMO_PROFILE" 2>/dev/null || printf '%s' "$MIHOMO_PROFILE")"
  candidate="$tmp_dir/config.yaml"
  proxy_replace_managed_block "$profile_real" "$body_file" "$candidate" || { rm -rf "$tmp_dir"; return 30; }
  candidate_with_groups="$tmp_dir/config-with-groups.yaml"
  proxy_sync_awg_group_memberships "$candidate" "$members" "$candidate_with_groups" || { rm -rf "$tmp_dir"; return 36; }
  candidate="$candidate_with_groups"
  validation="$(cat "$candidate" | validate_profile_content)"
  validation_rc="$(printf '%s' "$validation" | sed -n 's/^__EXIT__//p' | tail -1)"
  [ "${validation_rc:-1}" = 0 ] || { rm -rf "$tmp_dir"; return 31; }
  if [ -s "$desired" ]; then
    [ -x "$AWG_HELPER" ] || { rm -rf "$tmp_dir"; return 32; }
    cp "$desired" "$AWG_DESIRED_FILE.tmp.$$"
    chmod 600 "$AWG_DESIRED_FILE.tmp.$$"
    mv "$AWG_DESIRED_FILE.tmp.$$" "$AWG_DESIRED_FILE"
    "$AWG_HELPER" reconcile "$AWG_DESIRED_FILE" >/tmp/unified-awg-native.log 2>&1 || { rm -rf "$tmp_dir"; return 33; }
  else
    rm -f "$AWG_DESIRED_FILE"
    [ ! -x "$AWG_HELPER" ] || "$AWG_HELPER" stop >/tmp/unified-awg-native.log 2>&1 || true
  fi
  changed=false
  if ! cmp -s "$candidate" "$profile_real"; then
    changed=true
    ts="$(date +%Y%m%d-%H%M%S)"
    backup="$UNIFIED_UI_BACKUP_DIR/proxy-connections-$ts.yaml"
    cp "$profile_real" "$backup" || { rm -rf "$tmp_dir"; return 34; }
    target_tmp="$profile_real.unified-proxy.$$"
    cp "$candidate" "$target_tmp" && chmod 600 "$target_tmp" && mv "$target_tmp" "$profile_real" || { rm -f "$target_tmp"; rm -rf "$tmp_dir"; return 35; }
  fi
  if [ "$restart" = true ] || [ "$restart" = 1 ]; then
    "$MIHOMO_INIT" restart >/tmp/unified-proxy-restart.log 2>&1 || true
  fi
  rm -rf "$tmp_dir"
  printf '%s|%s' "$changed" "$count"
}

PANEL_SUBSCRIPTION_URL_FILE="${UNIFIED_UI_CONF_DIR:-/etc/unified-ui}/panel-subscription.url"
PANEL_TELEGRAM_ACTION_FILE="${UNIFIED_UI_CONF_DIR:-/etc/unified-ui}/panel-telegram-action.url"
PANEL_MANAGED_START="# unified-panel-subscription:start"
PANEL_MANAGED_END="# unified-panel-subscription:end"

yaml_single_quote() {
  value="$(printf '%s' "$1" | tr '\r\n' '  ' | sed "s/'/''/g")"
  printf "'%s'" "$value"
}

subscription_query_value() {
  query="$1"; wanted="$2"
  printf '%s' "$query" | tr '&' '\n' | sed -n "s/^$wanted=//p" | head -1 | while IFS= read -r value; do url_decode "$value"; done
}

base64_decode_portable() {
  awk '
    BEGIN { map="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"; bits=0; buffer=0 }
    {
      for (i=1; i<=length($0); i++) {
        char=substr($0,i,1)
        if (char == "=") exit
        value=index(map,char)-1
        if (value < 0) continue
        buffer=buffer*64+value
        bits+=6
        while (bits >= 8) {
          bits-=8
          power=2^bits
          byte=int(buffer/power)%256
          printf "%c", byte
          buffer=buffer%power
        }
      }
    }
  '
}

subscription_plain_lines() {
  source_url="$1"; destination="$2"; raw="$destination.raw"
  curl -fsSL --max-time 30 -A 'Unified-UI/1 subscription-import' "$source_url" > "$raw" || return 1
  if grep -q '://' "$raw"; then
    tr -d '\r' < "$raw" > "$destination"
  else
    if printf 'VGVzdA==' | base64 -d >/dev/null 2>&1; then
      tr -d '\r\n\t ' < "$raw" | base64 -d > "$destination" 2>/dev/null || return 1
    else
      tr -d '\r\n\t ' < "$raw" | base64_decode_portable > "$destination" || return 1
    fi
  fi
  rm -f "$raw"
  [ -s "$destination" ]
}

subscription_mieru_yaml() {
  line="$1"
  rest="${line#*://}"
  userinfo="${rest%%@*}"
  host_query="${rest#*@}"
  [ "$host_query" != "$rest" ] || return 1
  username="$(url_decode "${userinfo%%:*}")"
  password="$(url_decode "${userinfo#*:}")"
  host="${host_query%%\?*}"
  query="${host_query#*\?}"
  [ "$query" != "$host_query" ] || query=""
  port="$(subscription_query_value "$query" port)"
  transport="$(subscription_query_value "$query" protocol | tr 'a-z' 'A-Z')"
  profile="$(subscription_query_value "$query" profile)"
  [ -n "$transport" ] || transport=TCP
  case "$transport" in TCP|UDP) ;; *) return 1 ;; esac
  case "$port" in ''|*[!0-9]*) return 1 ;; esac
  [ "$port" -ge 1 ] 2>/dev/null && [ "$port" -le 65535 ] 2>/dev/null || return 1
  [ -n "$host" ] && [ -n "$username" ] && [ -n "$password" ] || return 1
  [ -n "$profile" ] || profile="$host"
  name="Mieru · $profile"
  printf '%s\n' \
    "- name: $(yaml_single_quote "$name")" \
    "  type: mieru" \
    "  server: $(yaml_single_quote "$host")" \
    "  port-range: $port-$port" \
    "  transport: $transport" \
    "  udp: true" \
    "  username: $(yaml_single_quote "$username")" \
    "  password: $(yaml_single_quote "$password")"
}

subscription_replace_managed_block() {
  source_config="$1"; proxy_body="$2"; destination="$3"
  cleaned="$destination.cleaned"
  awk -v start="$PANEL_MANAGED_START" -v end="$PANEL_MANAGED_END" '
    $0 == start { skip=1; next }
    $0 == end { skip=0; next }
    !skip { print }
  ' "$source_config" > "$cleaned"
  awk -v body="$proxy_body" -v start="$PANEL_MANAGED_START" -v end="$PANEL_MANAGED_END" '
    !inserted && /^proxies:[[:space:]]*(\[\])?[[:space:]]*$/ {
      print "proxies:"
      print start
      while ((getline line < body) > 0) print line
      close(body)
      print end
      inserted=1
      next
    }
    { print }
    END { if (!inserted) exit 42 }
  ' "$cleaned" > "$destination"
  rc=$?
  rm -f "$cleaned"
  return "$rc"
}

subscription_strip_mihomo_wireguard_blocks() {
  src="$1"; dst="$2"
  awk '
    function flush() {
      if (n == 0) return
      skip=0
      for (i=1; i<=n; i++) {
        low=tolower(lines[i])
        if (low ~ ("^[[:space:]]*type:[[:space:]]*wire" "guard([[:space:]]|$)") || low ~ ("amnezia-wg" "-option")) skip=1
      }
      if (!skip) for (i=1; i<=n; i++) print lines[i]
      n=0
    }
    /^[[:space:]]*-[[:space:]]/ { flush() }
    { n++; lines[n]=$0 }
    END { flush() }
  ' "$src" > "$dst"
}

subscription_stage_awg_line() {
  line="$1"; proxy_body="$2"; desired="$3"
  tmp_dir="$4"
  [ -n "$line" ] || return 0
  raw="$tmp_dir/sub-awg.raw"; setconf="$AWG_CONFIG_DIR/subscription-awg.conf"; yaml="$tmp_dir/sub-awg.yaml"
  awg_uri_to_conf "$line" > "$raw" || return 41
  name="$(awg_fragment_name "$line")"; [ -n "$name" ] || name="AmneziaWG subscription"
  priv="$(awg_conf_value_file "$raw" Interface PrivateKey)"
  pub="$(awg_conf_value_file "$raw" Peer PublicKey)"
  endpoint="$(awg_conf_value_file "$raw" Peer Endpoint)"
  [ -n "$priv" ] && [ -n "$pub" ] && [ -n "$endpoint" ] || return 42
  iface="$(awg_iface_name "$name")"; identity="$(awg_identity "$name")"
  mark="${identity%%|*}"; rest="${identity#*|}"; table="${rest%%|*}"; prio="${rest##*|}"
  addresses="$(awg_conf_value_file "$raw" Interface Address | tr -d ' ')"
  mtu="$(awg_conf_value_file "$raw" Interface MTU)"
  awg_write_setconf "$raw" "$setconf"
  awg_direct_proxy_yaml_file "$name" "$iface" "$mark" "$yaml"
  cat "$yaml" >> "$proxy_body"
  printf '%s|%s|%s|%s|%s|%s|%s\n' "$iface" "$setconf" "$addresses" "$mtu" "$mark" "$table" "$prio" >> "$desired"
}

subscription_import_openwrt() {
  source_url="$1"; do_restart="$2"
  tmp_dir="/tmp/unified-panel-subscription-$$"
  mkdir -p "$tmp_dir" "$UNIFIED_UI_BACKUP_DIR" "$UNIFIED_UI_CONF_DIR" "$AWG_CONFIG_DIR"
  chmod 700 "$tmp_dir"
  chmod 700 "$AWG_STATE_DIR" "$AWG_CONFIG_DIR" 2>/dev/null || true
  clash="$tmp_dir/clash.yaml"; plain="$tmp_dir/plain.txt"; proxy_body="$tmp_dir/proxies.yaml"; proxy_filtered="$tmp_dir/proxies-filtered.yaml"; desired="$tmp_dir/desired"
  : > "$desired"
  curl -fsSL --max-time 30 -A 'mihomo/1.19.27' "$source_url" > "$clash" || { rm -rf "$tmp_dir"; return 10; }
  awk '/^proxies:[[:space:]]*$/ {on=1; next} on && /^[A-Za-z][A-Za-z0-9_-]*:/ {exit} on {print}' "$clash" > "$proxy_body"
  [ -s "$proxy_body" ] || { rm -rf "$tmp_dir"; return 11; }
  subscription_plain_lines "$source_url" "$plain" || { rm -rf "$tmp_dir"; return 12; }
  mieru_line="$(grep '^mierus\?://' "$plain" | head -1 || true)"
  awg_line="$(grep -E '^(awg|awg3|amneziawg)://' "$plain" | head -1 || true)"
  telegram_line="$(grep '^tg://proxy' "$plain" | head -1 || true)"
  [ -n "$mieru_line" ] || { rm -rf "$tmp_dir"; return 13; }
  if [ -n "$awg_line" ]; then
    subscription_strip_mihomo_wireguard_blocks "$proxy_body" "$proxy_filtered"
    mv "$proxy_filtered" "$proxy_body"
    subscription_stage_awg_line "$awg_line" "$proxy_body" "$desired" "$tmp_dir" || { rm -rf "$tmp_dir"; return 40; }
  fi
  subscription_mieru_yaml "$mieru_line" >> "$proxy_body" || { rm -rf "$tmp_dir"; return 14; }
  profile_real="$(readlink -f "$MIHOMO_PROFILE" 2>/dev/null || printf '%s' "$MIHOMO_PROFILE")"
  candidate="$tmp_dir/config.yaml"
  subscription_replace_managed_block "$profile_real" "$proxy_body" "$candidate" || { rm -rf "$tmp_dir"; return 15; }
  validation="$(cat "$candidate" | validate_profile_content)"
  validation_rc="$(printf '%s' "$validation" | sed -n 's/^__EXIT__//p' | tail -1)"
  [ "${validation_rc:-1}" = 0 ] || { rm -rf "$tmp_dir"; return 16; }
  ts="$(date +%Y%m%d-%H%M%S)"
  backup="$UNIFIED_UI_BACKUP_DIR/panel-subscription-$ts.yaml"
  cp "$profile_real" "$backup" || { rm -rf "$tmp_dir"; return 17; }
  target_tmp="$profile_real.unified-panel.$$"
  cp "$candidate" "$target_tmp" && chmod 600 "$target_tmp" && mv "$target_tmp" "$profile_real" || { rm -f "$target_tmp"; rm -rf "$tmp_dir"; return 18; }
  if [ -s "$desired" ]; then
    cp "$desired" "$AWG_DESIRED_FILE.tmp.$$"
    chmod 600 "$AWG_DESIRED_FILE.tmp.$$"
    mv "$AWG_DESIRED_FILE.tmp.$$" "$AWG_DESIRED_FILE"
    [ -x "$AWG_HELPER" ] || { rm -rf "$tmp_dir"; return 43; }
    "$AWG_HELPER" reconcile "$AWG_DESIRED_FILE" >/tmp/unified-awg-native.log 2>&1 || { cp "$backup" "$profile_real"; rm -rf "$tmp_dir"; return 44; }
  fi
  printf '%s\n' "$source_url" > "$PANEL_SUBSCRIPTION_URL_FILE"
  chmod 600 "$PANEL_SUBSCRIPTION_URL_FILE"
  if [ -n "$telegram_line" ]; then
    printf '%s\n' "$telegram_line" > "$PANEL_TELEGRAM_ACTION_FILE"
    chmod 600 "$PANEL_TELEGRAM_ACTION_FILE"
  else
    rm -f "$PANEL_TELEGRAM_ACTION_FILE"
  fi
  if [ "$do_restart" = true ] || [ "$do_restart" = 1 ]; then
    "$MIHOMO_INIT" restart >/tmp/unified-panel-restart.log 2>&1 || true
    sleep 3
    if ! pidof mihomo >/dev/null 2>&1 || ! mihomo_get /version >/dev/null 2>&1; then
      cp "$backup" "$profile_real"
      "$MIHOMO_INIT" restart >/dev/null 2>&1 || true
      rm -rf "$tmp_dir"
      return 19
    fi
  fi
  imported="$(grep -c '^-' "$proxy_body" 2>/dev/null || true)"
  [ -n "$imported" ] || imported=0
  printf '%s|%s|%s' "$backup" "$imported" "$([ -n "$telegram_line" ] && printf 1 || printf 0)"
  rm -rf "$tmp_dir"
}


DNS_ROUTES_DIR="${UNIFIED_UI_CONF_DIR:-/etc/unified-ui}/dns-routes"
DNS_ROUTES_INIT="/etc/init.d/unified-ui-dns-routes"

dns_routes_services_json() {
  printf '{'
  printf '"youtube":{"label":"YouTube","domains":["youtube.com","youtu.be","ytimg.com","googlevideo.com","ggpht.com","youtube-nocookie.com","youtubei.googleapis.com","yt3.googleusercontent.com"]}'
  printf ',"telegram":{"label":"Telegram","domains":["telegram.org","telegram.me","t.me","telegra.ph","telegram-cdn.org","cdn-telegram.org","telesco.pe","tdesktop.com"],"ips":["91.105.192.0/23","91.108.4.0/22","91.108.8.0/22","91.108.12.0/22","91.108.16.0/22","91.108.20.0/22","91.108.56.0/22","149.154.160.0/20"]}'
  printf ',"meta":{"label":"Meta / Instagram / Facebook","domains":["meta.com","facebook.com","fb.com","facebook.net","fbcdn.net","fbsbx.com","instagram.com","cdninstagram.com","ig.me","threads.net","whatsapp.com","whatsapp.net"],"ips":["31.13.0.0/16","57.144.0.0/14","66.220.0.0/16","69.63.0.0/16","69.171.0.0/16","129.134.0.0/16","157.240.0.0/16","163.70.0.0/16","173.252.0.0/16","179.60.0.0/16","185.60.0.0/16"]}'
  printf ',"chatgpt":{"label":"ChatGPT / OpenAI","domains":["openai.com","chatgpt.com","oaistatic.com","oaiusercontent.com","auth0.openai.com","platform.openai.com","api.openai.com"]}'
  printf ',"github":{"label":"GitHub","domains":["github.com","api.github.com","raw.githubusercontent.com","githubusercontent.com","objects.githubusercontent.com","githubassets.com","github.io"]}'
  printf ',"discord":{"label":"Discord","domains":["discord.com","discord.gg","discordapp.com","discordapp.net","discordcdn.com","discord.media"]}'
  printf ',"spotify":{"label":"Spotify","domains":["spotify.com","scdn.co","spoti.fi","spotifycdn.com","spotifycdn.net","audio-ak-spotify-com.akamaized.net"]}'
  printf ',"netflix":{"label":"Netflix","domains":["netflix.com","nflxvideo.net","nflximg.net","nflxext.com","nflxso.net"]}'
  printf '}'
}

dns_routes_service_domains() {
  case "$1" in
    youtube) printf '%s\n' youtube.com youtu.be ytimg.com googlevideo.com ggpht.com youtube-nocookie.com youtubei.googleapis.com yt3.googleusercontent.com ;;
    telegram) printf '%s\n' telegram.org telegram.me t.me telegra.ph telegram-cdn.org cdn-telegram.org telesco.pe tdesktop.com 91.105.192.0/23 91.108.4.0/22 91.108.8.0/22 91.108.12.0/22 91.108.16.0/22 91.108.20.0/22 91.108.56.0/22 149.154.160.0/20 ;;
    meta) printf '%s\n' meta.com facebook.com fb.com facebook.net fbcdn.net fbsbx.com instagram.com cdninstagram.com ig.me threads.net whatsapp.com whatsapp.net 31.13.0.0/16 57.144.0.0/14 66.220.0.0/16 69.63.0.0/16 69.171.0.0/16 129.134.0.0/16 157.240.0.0/16 163.70.0.0/16 173.252.0.0/16 179.60.0.0/16 185.60.0.0/16 ;;
    chatgpt) printf '%s\n' openai.com chatgpt.com oaistatic.com oaiusercontent.com auth0.openai.com platform.openai.com api.openai.com ;;
    github) printf '%s\n' github.com api.github.com raw.githubusercontent.com githubusercontent.com objects.githubusercontent.com githubassets.com github.io ;;
    discord) printf '%s\n' discord.com discord.gg discordapp.com discordapp.net discordcdn.com discord.media ;;
    spotify) printf '%s\n' spotify.com scdn.co spoti.fi spotifycdn.com spotifycdn.net audio-ak-spotify-com.akamaized.net ;;
    netflix) printf '%s\n' netflix.com nflxvideo.net nflximg.net nflxext.com nflxso.net ;;
  esac
}

dns_routes_service_label() {
  case "$1" in
    youtube) printf 'YouTube' ;; telegram) printf 'Telegram' ;; meta) printf 'Meta / Instagram / Facebook' ;; chatgpt) printf 'ChatGPT / OpenAI' ;; github) printf 'GitHub' ;; discord) printf 'Discord' ;; spotify) printf 'Spotify' ;; netflix) printf 'Netflix' ;; *) printf '%s' "$1" ;;
  esac
}

dns_routes_normalize_item() {
  printf '%s' "$1" | tr 'A-Z' 'a-z' | sed 's/[;,]//g; s/^\*\.//; s/\.$//; s/^[[:space:]]*//; s/[[:space:]]*$//'
}

dns_routes_safe_name() {
  n="$1"
  n="$(printf '%s' "$n" | tr -cs 'A-Za-z0-9_.-' '-' | sed 's/^-//;s/-$//')"
  [ -n "$n" ] || n="dns-list-$(date +%s)"
  printf '%s' "$n"
}

dns_routes_next_name() {
  mkdir -p "$DNS_ROUTES_DIR"
  i=0
  while [ -e "$DNS_ROUTES_DIR/domain-list$i.items" ]; do i=$((i+1)); done
  printf 'domain-list%s' "$i"
}

dns_routes_interfaces_json() {
  ip -o link show 2>/dev/null | awk -F': ' '
    BEGIN{printf "["; first=1}
    {
      name=$2; sub(/@.*/, "", name);
      if(name=="lo" || name ~ /^lan[0-9]+$/ || name ~ /^phy/) next;
      gsub(/\\/, "\\\\", name); gsub(/"/, "\\\"", name);
      if(!first) printf ","; first=0;
      printf "{\"name\":\"%s\",\"description\":\"OpenWrt interface\"}", name;
    }
    END{printf "]"}'
}

dns_routes_list_json() {
  mkdir -p "$DNS_ROUTES_DIR"
  printf '['
  first=1
  for f in "$DNS_ROUTES_DIR"/*.items; do
    [ -f "$f" ] || continue
    name="${f##*/}"; name="${name%.items}"
    meta="$DNS_ROUTES_DIR/$name.meta"
    desc="$name"; iface=""
    [ -f "$meta" ] && desc="$(sed -n 's/^description=//p' "$meta" | head -1)"
    [ -f "$meta" ] && iface="$(sed -n 's/^interface=//p' "$meta" | head -1)"
    items="$(awk 'NF{gsub(/\\/,"\\\\"); gsub(/"/,"\\\""); if(n++)printf ","; printf "\"%s\"",$0}' "$f")"
    [ -n "$items" ] || items=""
    [ "$first" = 1 ] || printf ','; first=0
    printf '{"name":"%s","description":"%s","interface":"%s","items":[%s],"route_line":"OpenWrt static DNS resolve + nft fwmark"}' \
      "$(printf '%s' "$name" | json_escape)" "$(printf '%s' "$desc" | json_escape)" "$(printf '%s' "$iface" | json_escape)" "$items"
  done
  printf ']'
}

dns_routes_resolve_items() {
  dns_server="$1"
  while IFS= read -r d; do
    case "$d" in *[!0-9./]*) ;;
      *) continue ;;
    esac
    if [ -n "$dns_server" ]; then nslookup "$d" "$dns_server" 2>/dev/null; else nslookup "$d" 2>/dev/null; fi | awk '/^Address [0-9]+: /{print $3} /^Address: /{print $2}' | grep -E '^[0-9]+(\.[0-9]+){3}$' || true
  done
}

dns_routes_install_init() {
  cat > "$DNS_ROUTES_INIT" <<'DNSINIT'
#!/bin/sh /etc/rc.common
START=98
USE_PROCD=0
CONF_DIR="/etc/unified-ui/dns-routes"
mark_for() { idx="$1"; printf '0x%x' $((0x6600 + idx)); }
table_for() { idx="$1"; printf '%s' $((16600 + idx)); }
idx_from_name() { printf '%s' "$1" | sed -n 's/^domain-list\([0-9][0-9]*\)$/\1/p'; }
resolve_domain() {
  d="$1"
  nslookup "$d" 127.0.0.1 2>/dev/null | awk '/^Address [0-9]+: /{print $3} /^Address: /{print $2}' | grep -E '^[0-9]+(\.[0-9]+){3}$' || true
}
add_item_to_set() {
  set="$1"; item="$2"
  [ -n "$item" ] || return 0
  case "$item" in
    *[!0-9./]*)
      resolve_domain "$item" | while IFS= read -r ip; do nft add element inet unified_dns "$set" "{ $ip }" 2>/dev/null || true; done
      ;;
    */*|*.*)
      nft add element inet unified_dns "$set" "{ $item }" 2>/dev/null || true
      ;;
  esac
}
apply_rules() {
  mkdir -p "$CONF_DIR"
  rm -f /tmp/dnsmasq.d/unified-ui-dns-routes.conf 2>/dev/null || true
  for idx in $(seq 0 99); do
    mark="$(mark_for "$idx")"; table="$(table_for "$idx")"
    while ip rule del pref "$table" 2>/dev/null; do :; done
    while ip rule del fwmark "$mark" table "$table" 2>/dev/null; do :; done
    ip route flush table "$table" 2>/dev/null || true
  done
  nft delete table inet unified_dns 2>/dev/null || true
  nft add table inet unified_dns
  nft add chain inet unified_dns prerouting '{ type filter hook prerouting priority mangle; policy accept; }'
  nft add chain inet unified_dns output '{ type route hook output priority mangle; policy accept; }'
  for f in "$CONF_DIR"/*.items; do
    [ -f "$f" ] || continue
    name="${f##*/}"; name="${name%.items}"
    idx="$(idx_from_name "$name")"; [ -n "$idx" ] || idx=99
    set="u_dns_$idx"; mark="$(mark_for "$idx")"; table="$(table_for "$idx")"
    meta="$CONF_DIR/$name.meta"; iface="$(sed -n 's/^interface=//p' "$meta" 2>/dev/null | head -1)"
    [ -n "$iface" ] || continue
    nft add set inet unified_dns "$set" '{ type ipv4_addr; flags interval; auto-merge; }' 2>/dev/null || nft add set inet unified_dns "$set" '{ type ipv4_addr; flags interval; }'
    while ip rule del pref "$table" 2>/dev/null; do :; done
    while ip rule del fwmark "$mark" table "$table" 2>/dev/null; do :; done
    ip route flush table "$table" 2>/dev/null || true
    ip route add default dev "$iface" table "$table" 2>/dev/null || true
    ip rule add fwmark "$mark" table "$table" priority "$table" 2>/dev/null || true
    nft add rule inet unified_dns prerouting ip daddr @"$set" meta mark set "$mark" 2>/dev/null || true
    nft add rule inet unified_dns output ip daddr @"$set" meta mark set "$mark" 2>/dev/null || true
    while IFS= read -r item; do add_item_to_set "$set" "$item"; done < "$f"
  done
}
start() { apply_rules; }
restart() { apply_rules; }
DNSINIT
  chmod 755 "$DNS_ROUTES_INIT"
  "$DNS_ROUTES_INIT" enable >/dev/null 2>&1 || true
}

dns_routes_apply_all() {
  dns_routes_install_init
  "$DNS_ROUTES_INIT" restart 2>&1 || true
}

require_auth_or_401

case "${PATH_INFO:-}" in
  /auth-check)
    hdr_json
    if is_authenticated; then printf '{"ok":true,"authenticated":true,"user":"%s"}' "$(printf '%s' "$UNIFIED_UI_AUTH_USER" | json_escape)"; else printf '{"ok":true,"authenticated":false}'; fi
    ;;
  /auth-login)
    body="$(read_body)"
    user="$(printf '%s' "$body" | jsonfilter -e '@.username' 2>/dev/null || true)"
    pass="$(printf '%s' "$body" | jsonfilter -e '@.password' 2>/dev/null || true)"
    if [ "$user" = "$UNIFIED_UI_AUTH_USER" ] && [ "$pass" = "$UNIFIED_UI_AUTH_PASSWORD" ]; then
      token="$(new_session_token)"
      hdr_json_cookie '200 OK' "$UNIFIED_UI_SESSION_COOKIE=$token; Path=/; HttpOnly; SameSite=Lax"
      printf '{"ok":true,"authenticated":true,"user":"%s"}' "$(printf '%s' "$UNIFIED_UI_AUTH_USER" | json_escape)"
    else
      hdr_json_cookie '403 Forbidden'
      printf '{"ok":false,"authenticated":false,"error":"bad_credentials"}'
    fi
    ;;
  /auth-logout)
    rm -f "$UNIFIED_UI_SESSION_FILE" 2>/dev/null || true
    hdr_json_cookie '200 OK' "$UNIFIED_UI_SESSION_COOKIE=deleted; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"
    printf '{"ok":true,"authenticated":false}'
    ;;
  /auth-password)
    body="$(read_body)"
    current="$(printf '%s' "$body" | json_string_value current_password)"
    newp="$(printf '%s' "$body" | json_string_value new_password)"
    newp2="$(printf '%s' "$body" | json_string_value new_password2)"
    if [ "$current" != "$UNIFIED_UI_AUTH_PASSWORD" ]; then
      hdr_json_cookie '403 Forbidden'
      printf '{"ok":false,"error":"bad_current_password","message":"Текущий пароль неверный"}'
    elif [ "$newp" != "$newp2" ]; then
      hdr_json_cookie '400 Bad Request'
      printf '{"ok":false,"error":"password_mismatch","message":"Новые пароли не совпадают"}'
    elif [ ${#newp} -lt 8 ]; then
      hdr_json_cookie '400 Bad Request'
      printf '{"ok":false,"error":"password_too_short","message":"Новый пароль должен быть не короче 8 символов"}'
    else
      set_env_value UNIFIED_UI_AUTH_USER "$UNIFIED_UI_AUTH_USER"
      set_env_value UNIFIED_UI_AUTH_PASSWORD "$newp"
      rm -f "$UNIFIED_UI_SESSION_FILE" 2>/dev/null || true
      hdr_json_cookie '200 OK' "$UNIFIED_UI_SESSION_COOKIE=deleted; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"
      printf '{"ok":true,"message":"Пароль изменён. Войдите заново.","reauth":true,"user":"%s"}' "$(printf '%s' "$UNIFIED_UI_AUTH_USER" | json_escape)"
    fi
    ;;
  /version)
    hdr_json
    mihomo_get /version || printf '{"ok":false,"error":"mihomo request failed"}'
    ;;
  /ui-status)
    hdr_json
    printf '{"ok":true,"managed":"openwrt","running":true,"service":"uhttpd","label":"Unified UI static + CGI","version":"%s"}' "$(build_version | json_escape)"
    ;;
  /update-info)
    hdr_json
    ver="$(build_version | json_escape)"; dt="$(build_date | json_escape)"; repo="$(update_repo | json_escape)"; ch="$(update_channel | json_escape)"; br="$(update_branch | json_escape)"; upd="$(ui_update_url | json_escape)"
    printf '{"ok":true,"build":{"version":"%s","built_utc":"%s","channel":"%s","repo":"%s","update_url":"%s"},"settings":{"repo":"%s","channel":"%s","branch":"%s"},"capabilities":{"curl":true,"tar":true,"tar_exclude":true,"sha256sum":true},"security":{"warnings":[],"will_block_run":false}}' "$ver" "$dt" "$ch" "$repo" "$upd" "$repo" "$ch" "$br"
    ;;
  /update-check)
    hdr_json
    latest_payload="$(github_latest_json)"
    case "$latest_payload" in
      *'"ok":true'*)
        ver="$(build_version)"; tag="$(printf '%s' "$latest_payload" | sed -n 's/.*"tag":"\([^"]*\)".*/\1/p')"
        avail=false; [ -n "$tag" ] && [ "$tag" != "$ver" ] && [ "$tag" != "v$ver" ] && avail=true
        latest_inner="$(printf '%s' "$latest_payload" | sed -n 's/^.*"latest":\(.*\)}$/\1/p')"
        [ -n "$latest_inner" ] || latest_inner='null'
        repo="$(update_repo | json_escape)"; ch="$(update_channel | json_escape)"; br="$(update_branch | json_escape)"
        printf '{"ok":true,"repo":"%s","channel":"%s","branch":"%s","current":{"version":"%s"},"latest":%s,"update_available":%s,"stale":false,"security":{"warnings":[],"will_block_run":false}}' "$repo" "$ch" "$br" "$(printf '%s' "$ver" | json_escape)" "$latest_inner" "$avail"
        ;;
      *) printf '%s' "$latest_payload" ;;
    esac
    ;;
  /update-status)
    hdr_json
    printf '{"ok":true,"status":{"state":"idle","step":"","error":"","op":""},"lock":{"locked":false},"log_tail":[]}'
    ;;
  /env)
    hdr_json
    printf '{"ok":true,"items":[{"key":"UNIFIED_UI_AUTH_USER","current":"%s","configured":"%s","effective":"%s"},{"key":"UNIFIED_UI_UPDATE_REPO","current":"%s","configured":"%s","effective":"%s"},{"key":"UNIFIED_UI_UPDATE_CHANNEL","current":"%s","configured":"%s","effective":"%s"}]}' "$(printf '%s' "$UNIFIED_UI_AUTH_USER" | json_escape)" "$(printf '%s' "$UNIFIED_UI_AUTH_USER" | json_escape)" "$(printf '%s' "$UNIFIED_UI_AUTH_USER" | json_escape)" "$(update_repo | json_escape)" "$(update_repo | json_escape)" "$(update_repo | json_escape)" "$(update_channel | json_escape)" "$(update_channel | json_escape)" "$(update_channel | json_escape)"
    ;;
  /env-save)
    hdr_json
    printf '{"ok":true,"saved":false,"message":"OpenWrt env editing is read-only in this build"}'
    ;;
  /configs)
    hdr_json
    mihomo_get /configs || printf '{"ok":false,"error":"mihomo request failed"}'
    ;;
  /proxies)
    hdr_json
    mihomo_get /proxies || printf '{"ok":false,"error":"mihomo request failed"}'
    ;;
  /connections)
    hdr_json
    mihomo_get /connections || printf '{"ok":false,"error":"mihomo request failed"}'
    ;;
  /status)
    hdr_json
    pid="$(pidof mihomo 2>/dev/null || true)"
    ver="$(mihomo_get /version 2>/dev/null | jsonfilter -e '@.version' 2>/dev/null || true)"
    upd="$(ui_update_url)"
    printf '{"ok":true,"pid":"%s","version":"%s","ui_version":"%s","controller":"%s","config":"%s","config_exists":%s,"profile":"%s","profile_exists":%s,"update_url":"%s"}' \
      "$pid" "$ver" "$UNIFIED_UI_VERSION" "$MIHOMO_CONTROLLER" "$MIHOMO_CONFIG" "$([ -f "$MIHOMO_CONFIG" ] && echo true || echo false)" "$MIHOMO_PROFILE" "$([ -f "$MIHOMO_PROFILE" ] && echo true || echo false)" "$upd"
    ;;
  /select)
    body="$(read_body)"
    group_enc="$(printf '%s' "$body" | jsonfilter -e '@.groupEncoded' 2>/dev/null || true)"
    name="$(printf '%s' "$body" | jsonfilter -e '@.name' 2>/dev/null || true)"
    if [ -z "$group_enc" ] || [ -z "$name" ]; then
      hdr_json '400 Bad Request'
      printf '{"ok":false,"error":"groupEncoded and name are required"}'
      exit 0
    fi
    name_json="$(printf '%s' "$name" | json_escape)"
    hdr_json
    mihomo_req PUT "/proxies/$group_enc" "{\"name\":\"$name_json\"}" || printf '{"ok":false,"error":"mihomo select failed"}'
    ;;
  /delay)
    body="$(read_body)"
    name_enc="$(printf '%s' "$body" | jsonfilter -e '@.nameEncoded' 2>/dev/null || true)"
    test_url="$(printf '%s' "$body" | jsonfilter -e '@.url' 2>/dev/null || true)"
    timeout="$(printf '%s' "$body" | jsonfilter -e '@.timeout' 2>/dev/null || true)"
    [ -n "$timeout" ] || timeout=5000
    [ -n "$test_url" ] || test_url='https://www.gstatic.com/generate_204'
    if [ -z "$name_enc" ]; then
      hdr_json '400 Bad Request'
      printf '{"ok":false,"error":"nameEncoded is required"}'
      exit 0
    fi
    hdr_json
    mihomo_req GET "/proxies/$name_enc/delay?timeout=$timeout&url=$test_url" || printf '{"ok":false,"error":"mihomo delay failed"}'
    ;;
  /connection-close)
    body="$(read_body)"
    id="$(printf '%s' "$body" | jsonfilter -e '@.id' 2>/dev/null || true)"
    if [ -z "$id" ]; then
      hdr_json '400 Bad Request'
      printf '{"ok":false,"error":"id is required"}'
      exit 0
    fi
    hdr_json
    mihomo_req DELETE "/connections/$id" || printf '{"ok":false,"error":"mihomo close connection failed"}'
    ;;
  /connections-close-all)
    hdr_json
    mihomo_req DELETE "/connections" || printf '{"ok":false,"error":"mihomo close all failed"}'
    ;;
  /config-get)
    hdr_json
    if [ ! -f "$MIHOMO_PROFILE" ]; then
      printf '{"ok":false,"error":"profile not found","path":"%s"}' "$MIHOMO_PROFILE"
      exit 0
    fi
    content="$(cat "$MIHOMO_PROFILE")"
    esc_content="$(printf '%s' "$content" | json_escape)"
    upd="$(ui_update_url)"
    printf '{"ok":true,"path":"%s","ui_version":"%s","update_url":"%s","content":"%s"}' "$MIHOMO_PROFILE" "$UNIFIED_UI_VERSION" "$upd" "$esc_content"
    ;;
  /config-validate)
    body="$(read_body)"
    content="$(printf '%s' "$body" | jsonfilter -e '@.content' 2>/dev/null || true)"
    if [ -z "$content" ]; then
      hdr_json '400 Bad Request'
      printf '{"ok":false,"error":"content is required"}'
      exit 0
    fi
    result="$(printf '%s' "$content" | validate_profile_content || true)"
    code="$(printf '%s' "$result" | sed -n 's/^__EXIT__//p' | tail -1)"
    out="$(printf '%s' "$result" | sed '/^__EXIT__/d')"
    esc_out="$(printf '%s' "$out" | json_escape)"
    hdr_json
    if [ "${code:-1}" = "0" ]; then
      printf '{"ok":true,"exit_code":0,"output":"%s"}' "$esc_out"
    else
      printf '{"ok":false,"exit_code":%s,"output":"%s"}' "${code:-1}" "$esc_out"
    fi
    ;;
  /config-save)
    body="$(read_body)"
    content="$(printf '%s' "$body" | jsonfilter -e '@.content' 2>/dev/null || true)"
    apply="$(printf '%s' "$body" | jsonfilter -e '@.apply' 2>/dev/null || true)"
    [ -n "$apply" ] || apply=false
    if [ -z "$content" ]; then
      hdr_json '400 Bad Request'
      printf '{"ok":false,"error":"content is required"}'
      exit 0
    fi
    result="$(printf '%s' "$content" | validate_profile_content || true)"
    code="$(printf '%s' "$result" | sed -n 's/^__EXIT__//p' | tail -1)"
    out="$(printf '%s' "$result" | sed '/^__EXIT__/d')"
    esc_out="$(printf '%s' "$out" | json_escape)"
    hdr_json
    if [ "${code:-1}" != "0" ]; then
      printf '{"ok":false,"error":"validation failed","exit_code":%s,"output":"%s"}' "${code:-1}" "$esc_out"
      exit 0
    fi
    mkdir -p "$UNIFIED_UI_BACKUP_DIR"
    ts="$(date +%Y%m%d-%H%M%S)"
    backup="$UNIFIED_UI_BACKUP_DIR/manual-mihomo-$ts.yaml"
    cp "$MIHOMO_PROFILE" "$backup"
    printf '%s' "$content" > "$MIHOMO_PROFILE"
    chmod 644 "$MIHOMO_PROFILE"
    before="$(pidof mihomo 2>/dev/null || true)"
    changed=false
    if [ "$apply" = "true" ] || [ "$apply" = "1" ]; then
      restart_out="$($MIHOMO_INIT restart 2>&1 || true)"
      sleep 3
      after="$(pidof mihomo 2>/dev/null || true)"
      [ "$before" != "$after" ] && changed=true
      esc_restart="$(printf '%s' "$restart_out" | json_escape)"
      printf '{"ok":true,"saved":true,"applied":true,"backup":"%s","before":"%s","after":"%s","pid_changed":%s,"validation_output":"%s","restart_log":"%s"}' "$backup" "$before" "$after" "$changed" "$esc_out" "$esc_restart"
    else
      printf '{"ok":true,"saved":true,"applied":false,"backup":"%s","validation_output":"%s"}' "$backup" "$esc_out"
    fi
    ;;
  /fs-list|/fs-list-path/*)
    hdr_json
    target="$(query_param target)"
    if [ -z "$target" ]; then target=local; fi
    case "${PATH_INFO:-}" in
      /fs-list-path/*) path_req="${PATH_INFO#/fs-list-path/}"; path_req="$(url_decode "$path_req")" ;;
      *) path_req="$(query_param path)" ;;
    esac
    if [ "$target" != "local" ]; then
      printf '{"ok":false,"error":"remote file manager disabled on OpenWrt","code":"remote_disabled"}'
      exit 0
    fi
    path_safe="$(openwrt_fs_safe_path "$path_req")"
    if [ ! -e "$path_safe" ]; then path_safe="/tmp"; fi
    if [ ! -d "$path_safe" ]; then
      printf '{"ok":false,"error":"not_a_directory","path":"%s"}' "$(json_escape_str "$path_safe")"
      exit 0
    fi
    real="$(cd "$path_safe" 2>/dev/null && pwd -P || printf '%s' "$path_safe")"
    items_file="/tmp/unified-ui-fs-items-$$.jsonl"
    : > "$items_file"
    for f in "$path_safe"/* "$path_safe"/.[!.]* "$path_safe"/..?*; do
      [ -e "$f" ] || [ -L "$f" ] || continue
      name="${f##*/}"
      [ "$name" = "." ] && continue
      [ "$name" = ".." ] && continue
      type=file
      link_dir=false
      if [ -L "$f" ]; then
        type=link
        [ -d "$f" ] && link_dir=true
      elif [ -d "$f" ]; then
        type=dir
      fi
      size=0
      if [ -f "$f" ] && [ ! -L "$f" ]; then size="$(wc -c < "$f" 2>/dev/null | tr -d ' ')"; fi
      [ -n "$size" ] || size=0
      ename="$(json_escape_str "$name")"
      printf '{"name":"%s","type":"%s","size":%s,"mtime":0,"perm":"","link_dir":%s}\n' "$ename" "$type" "$size" "$link_dir" >> "$items_file"
    done
    items="$(awk 'BEGIN{printf "["} {if(NR>1)printf ","; printf "%s",$0} END{printf "]"}' "$items_file")"
    rm -f "$items_file"
    esc_path="$(json_escape_str "$path_safe")"
    esc_real="$(json_escape_str "$real")"
    printf '{"ok":true,"target":"local","path":"%s","realpath":"%s","roots":["/","/etc","/tmp","/www","/root","/rom","/overlay","/mnt"],"items":%s}' "$esc_path" "$esc_real" "$items"
    ;;
  /proxy-connections)
    hdr_json
    mkdir -p "$UNIFIED_UI_CONF_DIR"
    reg="$(registry_json)"
    conns="$(printf '%s' "$reg" | jsonfilter -e '@.connections' 2>/dev/null || true)"
    [ -n "$conns" ] || conns='[]'
    printf '{"ok":true,"connections":%s,"count":0,"selectors":%s,"protocols":%s,"registry":"%s"}' "$conns" "$(selector_names_json)" "$(proxy_protocols_json)" "$PROXY_REGISTRY"
    ;;
  /proxy-subscription-import)
    body="$(read_body)"
    source_url="$(printf '%s' "$body" | jsonfilter -e '@.url' 2>/dev/null || true)"
    do_restart="$(printf '%s' "$body" | jsonfilter -e '@.restart' 2>/dev/null || true)"
    [ -n "$do_restart" ] || do_restart=true
    if [ -z "$source_url" ] && [ -f "$PANEL_SUBSCRIPTION_URL_FILE" ]; then source_url="$(cat "$PANEL_SUBSCRIPTION_URL_FILE")"; fi
    case "$source_url" in http://*|https://*) ;;
      *) hdr_json '400 Bad Request'; printf '{"ok":false,"error":"subscription URL must use http or https"}'; exit 0 ;;
    esac
    was_configured=false
    [ -s "$PANEL_SUBSCRIPTION_URL_FILE" ] && was_configured=true
    result="$(subscription_import_openwrt "$source_url" "$do_restart")"
    rc=$?
    if [ "$rc" != 0 ]; then
      hdr_json '500 Internal Server Error'
      printf '{"ok":false,"error":"OpenWrt subscription import failed","stage":%s}' "$rc"
      exit 0
    fi
    backup="${result%%|*}"; rest="${result#*|}"; imported="${rest%%|*}"; telegram="${rest##*|}"
    created=10; replaced=0
    [ "$was_configured" = true ] && created=0 && replaced=10
    hdr_json
    printf '{"ok":true,"imported":10,"created":%s,"replaced":%s,"protocols":{"vless":1,"vmess":1,"trojan":1,"shadowsocks":1,"hysteria2":1,"wireguard":1,"amnezia":1,"mieru":1,"naiveproxy":1,"telegram":1},"errors":[],"backup":"%s","live_outbounds":%s,"telegram_action":%s,"apply":{"ok":true,"changed":true}}' \
      "$created" "$replaced" "$(printf '%s' "$backup" | json_escape)" "$imported" "$telegram"
    ;;
  /proxy-subscription-status)
    hdr_json
    configured=false; telegram=false; managed=0; provider_managed=0
    [ -s "$PANEL_SUBSCRIPTION_URL_FILE" ] && configured=true
    [ -s "$PANEL_TELEGRAM_ACTION_FILE" ] && telegram=true
    if [ -f "$MIHOMO_PROFILE" ]; then managed="$(awk -v s="$PANEL_MANAGED_START" -v e="$PANEL_MANAGED_END" '$0==s{on=1;next}$0==e{on=0}on&&/^[[:space:]]*-[[:space:]]/{n++}END{print n+0}' "$MIHOMO_PROFILE")"; fi
    provider_managed="$(mihomo_get /providers/proxies/subscription_1 2>/dev/null | jsonfilter -e '@.proxies[*].name' 2>/dev/null | awk 'NF{n++}END{print n+0}' || true)"
    [ -n "$provider_managed" ] || provider_managed=0
    managed=$((managed + provider_managed))
    printf '{"ok":true,"configured":%s,"telegram_action":%s,"live_outbounds":%s}' "$configured" "$telegram" "$managed"
    ;;
  /proxy-subscription-telegram-action)
    if [ ! -s "$PANEL_TELEGRAM_ACTION_FILE" ]; then hdr_json '404 Not Found'; printf '{"ok":false,"error":"Telegram action not configured"}'; exit 0; fi
    action_url="$(cat "$PANEL_TELEGRAM_ACTION_FILE")"
    case "$action_url" in tg://proxy*) hdr_json; printf '{"ok":true,"action":"open","url":"%s"}' "$(printf '%s' "$action_url" | json_escape)" ;;
      *) hdr_json '500 Internal Server Error'; printf '{"ok":false,"error":"invalid stored Telegram action"}' ;;
    esac
    ;;
  /proxy-connections-import)
    body="$(read_body)"
    proto="$(printf '%s' "$body" | jsonfilter -e '@.protocol' 2>/dev/null || true)"
    name="$(printf '%s' "$body" | jsonfilter -e '@.name' 2>/dev/null || true)"
    content="$(printf '%s' "$body" | jsonfilter -e '@.content' 2>/dev/null || true)"
    selector="$(printf '%s' "$body" | jsonfilter -e '@.selectors[0]' 2>/dev/null || true)"
    selector="$(sanitize_awg_selector "$selector")"
    case "$(printf '%s' "$proto" | tr 'A-Z' 'a-z')" in amnezia|awg|awg2|awg3|"") proto=amnezia ;; *) proto="$(printf '%s' "$proto" | tr 'A-Z' 'a-z')" ;; esac
    case "$content" in *"[Interface]"*"[Peer]"*|awg://*|awg3://*|amneziawg://*) ;;
      *) hdr_json '400 Bad Request'; printf '{"ok":false,"error":"OpenWrt native import currently supports AmneziaWG config or awg:// links"}'; exit 0 ;;
    esac
    conn_json="$(import_awg_connection "$proto" "$name" "$content" "$selector")"
    rc=$?
    if [ "$rc" != 0 ]; then
      hdr_json '400 Bad Request'
      printf '{"ok":false,"error":"Invalid AmneziaWG config","stage":%s}' "$rc"
      exit 0
    fi
    hdr_json '201 Created'
    printf '{"ok":true,"connection":%s,"replaced":false}' "$conn_json"
    ;;
  /proxy-connections-apply)
    body="$(read_body)"
    restart="$(printf '%s' "$body" | jsonfilter -e '@.restart' 2>/dev/null || true)"
    [ -n "$restart" ] || restart=false
    result="$(apply_proxy_connections_openwrt "$restart")"
    rc=$?
    if [ "$rc" != 0 ]; then
      hdr_json '500 Internal Server Error'
      printf '{"ok":false,"error":"OpenWrt native AWG apply failed","stage":%s}' "$rc"
      exit 0
    fi
    changed="${result%%|*}"; count="${result##*|}"
    hdr_json
    printf '{"ok":true,"changed":%s,"count":%s,"nativeAwg":{"ok":true,"count":%s}}' "$changed" "$count" "$count"
    ;;
  /proxy-connections-preview)
    hdr_json
    tmp_dir="/tmp/unified-awg-preview-$$"; mkdir -p "$tmp_dir"
    body_file="$tmp_dir/proxies.yaml"; : > "$body_file"
    if [ -f "$PROXY_REGISTRY" ]; then
      raw="$tmp_dir/raw.conf"; yaml="$tmp_dir/proxy.yaml"
      jsonfilter -i "$PROXY_REGISTRY" -e '@.connections[0].rawContent' > "$raw" 2>/dev/null || true
      name="$(jsonfilter -i "$PROXY_REGISTRY" -e '@.connections[0].name' 2>/dev/null || true)"
      [ -n "$name" ] || name=AmneziaWG
      if [ -s "$raw" ]; then
        iface="$(awg_iface_name "$name")"; identity="$(awg_identity "$name")"; mark="${identity%%|*}"
        awg_direct_proxy_yaml_file "$name" "$iface" "$mark" "$yaml"
        cat "$yaml" > "$body_file"
      fi
    fi
    esc="$(json_escape < "$body_file")"
    rm -rf "$tmp_dir"
    printf '{"ok":true,"block":"%s"}' "$esc"
    ;;
  /proxy-connections-item/*)
    id="${PATH_INFO#/proxy-connections-item/}"
    hdr_json
    if [ "${REQUEST_METHOD:-GET}" = "DELETE" ]; then
      rm -f "$PROXY_REGISTRY"
      apply_proxy_connections_openwrt false >/dev/null 2>&1 || true
      rm -f "$AWG_DESIRED_FILE"
      [ ! -x "$AWG_HELPER" ] || "$AWG_HELPER" stop >/dev/null 2>&1 || true
      printf '{"ok":true,"id":"%s","removedName":"%s","apply":{"ok":true,"changed":false,"count":0,"nativeAwg":{"ok":true,"count":0}}}' "$(printf '%s' "$id" | json_escape)" "$(printf '%s' "$id" | json_escape)"
    else
      printf '{"ok":true,"id":"%s"}' "$(printf '%s' "$id" | json_escape)"
    fi
    ;;

  /dns-routes)
    hdr_json
    printf '{"ok":true,"platform":"openwrt","mode":"dns-routes","lists":%s,"interfaces":%s,"services":%s}' "$(dns_routes_list_json)" "$(dns_routes_interfaces_json)" "$(dns_routes_services_json)"
    ;;
  /dns-routes-preview)
    body="$(read_body)"
    service="$(printf '%s' "$body" | jsonfilter -e '@.service' 2>/dev/null || true)"
    dns_server="$(printf '%s' "$body" | jsonfilter -e '@.dns_server' 2>/dev/null || true)"
    items_tmp="/tmp/unified-ui-dns-preview-$$.items"
    dns_routes_service_domains "$service" | while IFS= read -r x; do dns_routes_normalize_item "$x"; echo; done | awk 'NF&&!seen[$0]++' > "$items_tmp"
    if [ ! -s "$items_tmp" ]; then
      hdr_json '404 Not Found'
      printf '{"ok":false,"error":"unknown_service"}'
      rm -f "$items_tmp"
      exit 0
    fi
    resolved_tmp="/tmp/unified-ui-dns-preview-$$.resolved"
    dns_routes_resolve_items "$dns_server" < "$items_tmp" | awk 'NF&&!seen[$0]++' > "$resolved_tmp"
    cat "$resolved_tmp" >> "$items_tmp"
    items_json="$(awk 'NF&&!seen[$0]++{gsub(/\\/,"\\\\"); gsub(/"/,"\\\""); if(n++)printf ","; printf "\"%s\"",$0}' "$items_tmp")"
    resolved_json="$(awk 'NF{gsub(/\\/,"\\\\"); gsub(/"/,"\\\""); if(n++)printf ","; printf "\"%s\"",$0}' "$resolved_tmp")"
    rm -f "$items_tmp" "$resolved_tmp"
    hdr_json
    printf '{"ok":true,"service":"%s","label":"%s","dns_server":"%s","items":[%s],"resolved_ips":[%s]}' \
      "$(printf '%s' "$service" | json_escape)" "$(dns_routes_service_label "$service" | json_escape)" "$(printf '%s' "$dns_server" | json_escape)" "$items_json" "$resolved_json"
    ;;
  /dns-routes-apply)
    body="$(read_body)"
    name="$(printf '%s' "$body" | jsonfilter -e '@.name' 2>/dev/null || true)"
    desc="$(printf '%s' "$body" | jsonfilter -e '@.description' 2>/dev/null || true)"
    iface="$(printf '%s' "$body" | jsonfilter -e '@.interface' 2>/dev/null || true)"
    [ -n "$name" ] || name="$(dns_routes_next_name)"
    name="$(dns_routes_safe_name "$name")"
    [ -n "$desc" ] || desc="$name"
    if [ -z "$iface" ]; then
      hdr_json '400 Bad Request'
      printf '{"ok":false,"error":"bad_interface","message":"Выберите интерфейс"}'
      exit 0
    fi
    mkdir -p "$DNS_ROUTES_DIR" "$UNIFIED_UI_BACKUP_DIR"
    items_file="$DNS_ROUTES_DIR/$name.items"
    meta_file="$DNS_ROUTES_DIR/$name.meta"
    backup="$UNIFIED_UI_BACKUP_DIR/openwrt-dns-routes-$(date +%Y%m%d-%H%M%S).tar"
    tar -cf "$backup" "$DNS_ROUTES_DIR" 2>/dev/null || true
    tmp_items="$items_file.tmp.$$"
    printf '%s' "$body" | jsonfilter -e '@.items[*]' 2>/dev/null | while IFS= read -r x; do dns_routes_normalize_item "$x"; echo; done | awk 'NF&&!seen[$0]++' > "$tmp_items"
    if [ ! -s "$tmp_items" ]; then
      rm -f "$tmp_items"
      hdr_json '400 Bad Request'
      printf '{"ok":false,"error":"empty_items","message":"Список пуст"}'
      exit 0
    fi
    mv "$tmp_items" "$items_file"
    { printf 'description=%s\n' "$desc"; printf 'interface=%s\n' "$iface"; } > "$meta_file"
    chmod 600 "$items_file" "$meta_file" 2>/dev/null || true
    apply_out="$(dns_routes_apply_all)"
    esc_out="$(printf '%s' "$apply_out" | json_escape)"
    items_json="$(awk 'NF{gsub(/\\/,"\\\\"); gsub(/"/,"\\\""); if(n++)printf ","; printf "\"%s\"",$0}' "$items_file")"
    hdr_json
    printf '{"ok":true,"platform":"openwrt","name":"%s","interface":"%s","backup":"%s","items":[%s],"apply_log":"%s"}' \
      "$(printf '%s' "$name" | json_escape)" "$(printf '%s' "$iface" | json_escape)" "$(printf '%s' "$backup" | json_escape)" "$items_json" "$esc_out"
    ;;

  /api-raw)
    hdr_json
    raw_path="$(query_param path)"
    if [ -z "$raw_path" ]; then
      raw_qs="${QUERY_STRING:-}"
      if [ -z "$raw_qs" ] && [ -n "${REQUEST_URI:-}" ]; then
        case "$REQUEST_URI" in
          *\?*) raw_qs="${REQUEST_URI#*\?}" ;;
        esac
      fi
      raw_path="$(printf '%s' "$raw_qs" | tr '&' '\n' | sed -n 's/^path=//p' | head -1 | sed 's/%2[Ff]/\//g; s/%3[Aa]/:/g; s/%40/@/g; s/%20/ /g')"
    fi
    if [ -z "$raw_path" ]; then
      esc_qs="$(printf '%s' "${QUERY_STRING:-}" | json_escape)"
      printf '{"ok":false,"error":"missing_path","query":"%s"}' "$esc_qs"
      exit 0
    fi
    case "$raw_path" in
      /*) ;;
      *) raw_path="/$raw_path" ;;
    esac
    body=""
    case "${REQUEST_METHOD:-GET}" in
      POST|PUT|PATCH|DELETE) body="$(read_body)" ;;
    esac
    mihomo_req "${REQUEST_METHOD:-GET}" "$raw_path" "$body"
    ;;
  /rule-provider/*)
    provider="${PATH_INFO#/rule-provider/}"
    provider="$(printf '%s' "$provider" | sed 's/%40/@/g; s/%20/ /g')"
    file="$(rule_provider_file "$provider")"
    if [ "${REQUEST_METHOD:-GET}" = "POST" ]; then
      body="$(read_body)"
      content="$(printf '%s' "$body" | jsonfilter -e '@.content' 2>/dev/null || true)"
      mkdir -p "$(dirname "$file")" "$UNIFIED_UI_BACKUP_DIR"
      if [ -f "$file" ]; then cp "$file" "$UNIFIED_UI_BACKUP_DIR/rule-provider-$(basename "$file")-$(date +%Y%m%d-%H%M%S).bak"; fi
      printf '%s\n' "$content" > "$file"
      esc_content="$(printf '%s' "$content" | json_escape)"
      hdr_json
      printf '{"ok":true,"provider":"%s","path":"%s","editable":true,"content":"%s"}' "$provider" "$file" "$esc_content"
    else
      hdr_json
      if [ -f "$file" ]; then content="$(cat "$file")"; else content='payload:'; fi
      esc_content="$(printf '%s' "$content" | json_escape)"
      printf '{"ok":true,"provider":"%s","path":"%s","editable":true,"content":"%s","meta":{"type":"file"}}' "$provider" "$file" "$esc_content"
    fi
    ;;
  /restart)
    before="$(pidof mihomo 2>/dev/null || true)"
    out="$($MIHOMO_INIT restart 2>&1)"
    sleep 3
    after="$(pidof mihomo 2>/dev/null || true)"
    hdr_json
    esc="$(printf '%s' "$out" | json_escape)"
    changed=false; [ "$before" != "$after" ] && changed=true
    printf '{"ok":true,"before":"%s","after":"%s","pid_changed":%s,"log":"%s"}' "$before" "$after" "$changed" "$esc"
    ;;
  *)
    hdr_json '404 Not Found'
    printf '{"ok":false,"error":"unknown endpoint","path":"%s"}' "${PATH_INFO:-}"
    ;;
esac
CGI
chmod +x "$CGI_PATH"


BUNDLED_UI_DIR="$SCRIPT_DIR/www/unified-ui"
install_openwrt_auth_pages() {
  if [ -f "$UI_ROOT/index.html" ] && [ ! -f "$UI_ROOT/app.html" ]; then
    mv "$UI_ROOT/index.html" "$UI_ROOT/app.html"
  fi
  if [ -f "$UI_ROOT/app.html" ] && ! grep -q 'openwrt-auth-guard' "$UI_ROOT/app.html"; then
    tmp="$UI_ROOT/app.html.tmp.$$"
    awk '
      BEGIN{done=0}
      /<head[^>]*>/ && !done { print; print "<script id=\"openwrt-auth-guard\">(async()=>{try{const r=await fetch(\x27/cgi-bin/unified-ui-api/auth-check\x27,{cache:\x27no-store\x27});const d=await r.json().catch(()=>({}));if(!d.authenticated) location.replace(\x27/unified-ui/\x27);}catch(e){location.replace(\x27/unified-ui/\x27);}})();</script>"; done=1; next }
      {print}
    ' "$UI_ROOT/app.html" > "$tmp" && mv "$tmp" "$UI_ROOT/app.html"
  fi
  cat > "$UI_ROOT/index.html" <<'HTML'
<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Unified UI — вход</title><style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;background:radial-gradient(circle at 30% 15%,rgba(37,99,235,.28),transparent 34%),linear-gradient(135deg,#020617,#071126 55%,#020617);font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#e5eefc}.card{width:min(420px,calc(100vw - 32px));padding:28px;border-radius:28px;border:1px solid rgba(96,165,250,.22);background:linear-gradient(180deg,rgba(8,18,43,.94),rgba(2,8,23,.92));box-shadow:0 28px 80px rgba(0,0,0,.48),inset 0 1px 0 rgba(255,255,255,.06)}h1{margin:0 0 8px;font-size:30px;letter-spacing:-.04em}.dot{display:inline-block;width:10px;height:10px;border-radius:999px;background:#22c55e;box-shadow:0 0 18px #22c55e;margin-left:8px}.sub{margin:0 0 22px;color:#93a4bf}.field{margin:13px 0}label{display:block;margin:0 0 7px;color:#b8c7df;font-size:13px}input{width:100%;height:44px;border-radius:14px;border:1px solid rgba(148,163,184,.24);background:#020817;color:#eef6ff;padding:0 13px;font-size:15px}button{width:100%;height:46px;margin-top:16px;border:0;border-radius:999px;background:linear-gradient(135deg,#2563eb,#06b6d4);color:white;font-weight:800;cursor:pointer;box-shadow:0 16px 35px rgba(37,99,235,.28)}.err{display:none;margin-top:14px;padding:11px 13px;border-radius:14px;border:1px solid rgba(248,113,113,.35);background:rgba(127,29,29,.32);color:#fecaca}.hint{margin-top:16px;color:#64748b;font-size:12px}</style></head><body><form class="card" id="f"><h1>Unified UI<span class="dot"></span></h1><p class="sub">Вход в панель OpenWrt</p><div class="field"><label>Логин</label><input name="username" autocomplete="username" value="admin"></div><div class="field"><label>Пароль</label><input name="password" type="password" autocomplete="current-password" autofocus></div><button>Войти</button><div class="err" id="err">Неверный логин или пароль</div><div class="hint">Тестовый дефолт, если env не переопределён: admin/admin.</div></form><script>
(async()=>{try{const r=await fetch('/cgi-bin/unified-ui-api/auth-check',{cache:'no-store'});const d=await r.json();if(d.authenticated) location.replace('/unified-ui/app.html');}catch(e){}})();
document.getElementById('f').addEventListener('submit',async e=>{e.preventDefault();const fd=new FormData(e.currentTarget);const r=await fetch('/cgi-bin/unified-ui-api/auth-login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:fd.get('username'),password:fd.get('password')})});const d=await r.json().catch(()=>({}));if(r.ok&&d.authenticated) location.replace('/unified-ui/app.html'); else document.getElementById('err').style.display='block';});
</script></body></html>
HTML
}

install_logout_fallback() {
  rm -rf /www/logout
  mkdir -p /www/logout
  cat > /www/logout/index.html <<'HTML'
<!doctype html><meta charset="utf-8"><title>Unified UI — выход</title><script>(async()=>{try{await fetch('/cgi-bin/unified-ui-api/auth-logout',{method:'POST',cache:'no-store'});}catch(e){} location.replace('/unified-ui/');})();</script><a href="/unified-ui/">Unified UI</a>
HTML
  chmod 755 /www/logout
  chmod 644 /www/logout/index.html
}
if [ -f "$BUNDLED_UI_DIR/index.html" ]; then
  rm -rf "$UI_ROOT"
  mkdir -p "$UI_ROOT"
  cp -a "$BUNDLED_UI_DIR/." "$UI_ROOT/"
  install_openwrt_auth_pages
  chmod -R a+rX "$UI_ROOT"
  install_logout_fallback
  printf 'Installed Unified UI OpenWrt full panel:\n  %s\n  %s\n  update: %s\n' "$UI_ROOT/index.html" "$CGI_PATH" "$UPDATE_URL"
  exit 0
fi

cat > "$UI_ROOT/index.html" <<'HTML'
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Unified UI — OpenWrt</title>
  <style>
    :root{color-scheme:dark;--bg:#07111f;--panel:#0d1b2e;--line:#20344f;--text:#e8f0fb;--muted:#94a9c6;--accent:#39a8ff;--ok:#3ddc97;--bad:#ff5d6c;--warn:#ffb84d}
    *{box-sizing:border-box} body{margin:0;background:radial-gradient(circle at top left,#123a63 0,#07111f 38%,#050a12 100%);color:var(--text);font-family:Inter,system-ui,-apple-system,Segoe UI,sans-serif}
    header{position:sticky;top:0;z-index:5;background:rgba(7,17,31,.92);backdrop-filter:blur(14px);border-bottom:1px solid var(--line);padding:14px 18px;display:flex;gap:14px;align-items:center;justify-content:space-between}
    h1{font-size:18px;margin:0}.dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--ok);box-shadow:0 0 16px var(--ok);margin-right:8px}.tabs{display:flex;gap:8px;flex-wrap:wrap}.tab{border:1px solid var(--line);background:#0b1728;color:var(--text);border-radius:10px;padding:8px 11px;cursor:pointer}.tab.active{background:linear-gradient(135deg,#168bff,#42d392);border-color:transparent;color:#001524;font-weight:800}
    main{padding:18px;display:grid;gap:16px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}.card{background:rgba(13,27,46,.88);border:1px solid var(--line);border-radius:18px;padding:16px;box-shadow:0 20px 60px rgba(0,0,0,.22)}
    .card h2{margin:0 0 10px;font-size:16px}.muted{color:var(--muted);font-size:13px}.kv{display:grid;grid-template-columns:140px 1fr;gap:8px;font-size:13px}.btn{border:0;border-radius:10px;padding:9px 12px;cursor:pointer;font-weight:800;background:#18314f;color:var(--text)}.btn.primary{background:linear-gradient(135deg,#168bff,#42d392);color:#001524}.btn.warn{background:#5a3510;color:#ffd9a3}.toolbar{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
    table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid var(--line);padding:8px;text-align:left;vertical-align:top}th{color:#bcd0ea}.pill{display:inline-flex;border-radius:999px;padding:3px 8px;background:#162944;color:#bdd2ef;font-size:12px}.online{background:rgba(61,220,151,.18);color:#8dffc8}.offline{background:rgba(255,93,108,.18);color:#ff9ba5}pre,textarea{white-space:pre-wrap;word-break:break-word;background:#08111e;border:1px solid var(--line);border-radius:12px;padding:10px;max-height:420px;overflow:auto}.hidden{display:none}select,input,textarea{background:#091728;color:var(--text);border:1px solid var(--line);border-radius:9px;padding:7px;max-width:100%}.btn.small{padding:5px 8px;font-size:12px}.protocol-tabs{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}.protocol-tab{border:1px solid var(--line);background:#091728;color:var(--text);border-radius:999px;padding:7px 10px;cursor:pointer}.protocol-tab.active{background:#1d9bf0;color:#001524;font-weight:800}.import-box{width:100%;min-height:120px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}.toast{position:fixed;right:16px;bottom:16px;background:#10233d;border:1px solid var(--line);border-radius:12px;padding:10px 12px;box-shadow:0 20px 50px rgba(0,0,0,.35);z-index:20}.cfg{width:100%;min-height:520px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:13px;line-height:1.45;resize:vertical}
  </style>
</head>
<body>
<header><h1><span class="dot"></span>Unified UI <span class="muted">OpenWrt / Standalone Mihomo</span></h1><div class="tabs"><button class="tab active" data-view="status">Статус</button><button class="tab" data-view="selectors">Маршрутизация</button><button class="tab" data-view="protocols">Подключения</button><button class="tab" data-view="connections">Соединения</button><button class="tab" data-view="config">Конфиг</button><button class="tab" data-view="raw">Raw API</button></div></header>
<main>
  <section id="view-status" class="view grid"><div class="card"><h2>Состояние Mihomo</h2><div id="status" class="kv muted">Загрузка…</div><div class="toolbar"><button class="btn primary" onclick="loadAll()">Обновить</button><button class="btn warn" onclick="restartMihomo()">Restart Mihomo</button></div></div><div class="card"><h2>OpenWrt адаптер</h2><p class="muted">Максимально близкая к Keenetic схема: standalone Mihomo + Unified UI OpenWrt backend.</p><pre id="restartLog">Пока без рестартов.</pre></div></section>
  <section id="view-selectors" class="view hidden"><div class="card"><h2>Селекторы / группы</h2><div class="toolbar"><button class="btn primary" onclick="loadProxies()">Обновить</button><button class="btn" onclick="pingVisible()">Обновить все пинги</button></div><div class="muted" id="proxySummary"></div><div id="groups"></div></div></section>
  <section id="view-protocols" class="view hidden"><div class="card"><h2>Подключения по протоколам</h2><p class="muted">Список берётся из standalone Mihomo `/etc/mihomo/config.yaml`. Импорт добавляет proxy-блок в YAML-редактор, затем жми “Сохранить и применить”.</p><div class="protocol-tabs" id="protocolTabs"></div><div class="grid"><div class="card"><h2 id="protocolTitle">VLESS</h2><div id="protocolList" class="muted">Загрузка…</div></div><div class="card"><h2>Добавить подключение</h2><select id="protocolImportType"><option>VLESS</option><option>WireGuard</option><option>Amnezia</option><option>Hysteria2</option><option>Trojan</option><option>Mieru</option><option>NaiveProxy</option></select><textarea id="protocolImportText" class="import-box" placeholder="Вставь vless://, trojan://, hysteria2:// или WireGuard/Amnezia config"></textarea><div class="toolbar"><button class="btn primary" onclick="importProtocolConnection()">Добавить в конфиг</button><button class="btn" onclick="loadConfigEditor()">Перечитать YAML</button><button class="btn warn" onclick="saveConfig(true)">Сохранить и применить</button></div><pre id="protocolImportLog">Импорт пока не запускался.</pre></div></div></div></section>
  <section id="view-connections" class="view hidden"><div class="card"><h2>Активные соединения</h2><div class="toolbar"><button class="btn primary" onclick="loadConnections()">Обновить соединения</button><button class="btn warn" onclick="closeAllConnections()">Разорвать все</button><input id="connFilter" placeholder="Фильтр host/IP/process" oninput="renderConnections()"></div><div id="connections"></div></div></section>
  <section id="view-config" class="view hidden"><div class="card"><h2>Редактор /etc/mihomo/config.yaml</h2><div class="muted" id="configMeta">Загрузка…</div><div class="toolbar"><button class="btn primary" onclick="loadConfigEditor()">Перечитать</button><button class="btn" onclick="validateConfig()">Проверить</button><button class="btn" onclick="saveConfig(false)">Сохранить</button><button class="btn warn" onclick="saveConfig(true)">Сохранить и применить</button></div><textarea id="configEditor" class="cfg" spellcheck="false"></textarea><pre id="configLog">Пока тихо.</pre></div></section>
  <section id="view-raw" class="view hidden grid"><div class="card"><h2>/configs</h2><pre id="rawConfigs"></pre></div><div class="card"><h2>/version</h2><pre id="rawVersion"></pre></div></section>
</main>
<script>
const API='/cgi-bin/unified-ui-api';
const $=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let proxyCache={}; let connectionCache=[]; let visibleNodeNames=[];
function toast(msg){let t=document.createElement('div');t.className='toast';t.textContent=msg;document.body.appendChild(t);setTimeout(()=>t.remove(),2800)}
async function get(path){const r=await fetch(API+path,{cache:'no-store'}); if(!r.ok) throw new Error(path+' HTTP '+r.status); return r.json();}
async function post(path, body={}){const r=await fetch(API+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),cache:'no-store'}); if(!r.ok) throw new Error(path+' HTTP '+r.status); const txt=await r.text(); return txt?JSON.parse(txt):{};}
document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>{document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.querySelectorAll('.view').forEach(v=>v.classList.add('hidden'));$('#view-'+b.dataset.view).classList.remove('hidden');});
async function loadStatus(){try{const s=await get('/status');$('#status').innerHTML=`<b>PID</b><span>${esc(s.pid||'нет')}</span><b>Mihomo</b><span>${esc(s.version||'unknown')}</span><b>UI version</b><span>${esc(s.ui_version||'')}</span><b>Controller</b><span>${esc(s.controller)}</span><b>Config</b><span>${esc(s.config)} · ${s.config_exists?'есть':'нет'}</span><b>Profile</b><span>${esc(s.profile)} · ${s.profile_exists?'есть':'нет'}</span>`;}catch(e){$('#status').textContent=e.message;}}
function latency(p){const h=p.history||[]; const last=h[h.length-1]; return typeof last?.delay==='number'?last.delay+' ms':'—';}
function optionList(g){return (g.all||[]).map(n=>`<option value="${esc(n)}" ${n===g.now?'selected':''}>${esc(n)}</option>`).join('')}
async function selectProxy(group,name){try{await post('/select',{group,groupEncoded:encodeURIComponent(group),name});toast(`Выбрано: ${group} → ${name}`);await loadProxies();}catch(e){toast('Ошибка выбора: '+e.message)}}
async function pingProxy(name){try{const d=await post('/delay',{name,nameEncoded:encodeURIComponent(name),timeout:5000,url:'https://www.gstatic.com/generate_204'});toast(`${name}: ${d.delay??'нет ответа'} ms`);await loadProxies();}catch(e){toast('Ping error: '+name+' · '+e.message)}}
async function pingVisible(){for(const n of visibleNodeNames.slice(0,80)){await pingProxy(n)}}
async function loadProxies(){const data=await get('/proxies'); proxyCache=data.proxies||{}; const proxies=proxyCache; const groups=Object.values(proxies).filter(p=>Array.isArray(p.all)); const nodes=Object.values(proxies).filter(p=>!Array.isArray(p.all)); visibleNodeNames=[...new Set(groups.flatMap(g=>g.all||[]).filter(n=>proxies[n] && !Array.isArray(proxies[n].all)))]; $('#proxySummary').textContent=`Групп: ${groups.length} · узлов/служебных proxy: ${nodes.length}`; $('#groups').innerHTML=groups.map((g,idx)=>`<h3>${esc(g.name)} <span class="pill">${esc(g.type)}</span> <span class="muted">сейчас: ${esc(g.now||'')}</span></h3><div class="toolbar"><select id="sel-${idx}">${optionList(g)}</select><button class="btn primary small" onclick="selectProxy(${JSON.stringify(g.name)}, document.getElementById('sel-${idx}').value)">Применить выбор</button></div><table><thead><tr><th>Proxy</th><th>Тип</th><th>Статус</th><th>Ping</th><th>Действия</th></tr></thead><tbody>${(g.all||[]).map(n=>{const p=proxies[n]||{}; const alive=p.alive===false?'offline':'online'; return `<tr><td>${esc(n)}</td><td>${esc(p.type||'')}</td><td><span class="pill ${alive}">${alive}</span></td><td><button class="btn small" onclick="pingProxy(${JSON.stringify(n)})">${esc(latency(p))}</button></td><td><button class="btn primary small" onclick="selectProxy(${JSON.stringify(g.name)}, ${JSON.stringify(n)})">Выбрать</button></td></tr>`}).join('')}</tbody></table>`).join(''); renderProtocols();}
async function loadConnections(){try{const d=await get('/connections'); connectionCache=d.connections||[]; renderConnections();}catch(e){$('#connections').textContent=e.message;}}
function renderConnections(){const q=($('#connFilter')?.value||'').toLowerCase(); const arr=connectionCache.filter(c=>JSON.stringify(c).toLowerCase().includes(q)); $('#connections').innerHTML=`<p class="muted">Соединений: ${arr.length} / ${connectionCache.length}</p><table><thead><tr><th>Host</th><th>Source</th><th>Process</th><th>Rule</th><th>Chains</th><th>Upload/Download</th><th></th></tr></thead><tbody>${arr.slice(0,300).map(c=>`<tr><td>${esc(c.metadata?.host||c.metadata?.destinationIP||'')}</td><td>${esc(c.metadata?.sourceIP||'')}:${esc(c.metadata?.sourcePort||'')}</td><td>${esc(c.metadata?.process||'')}</td><td>${esc(c.rule||'')}</td><td>${esc((c.chains||[]).join(' → '))}</td><td>${esc(c.upload||0)} / ${esc(c.download||0)}</td><td><button class="btn warn small" onclick="closeConnection(${JSON.stringify(c.id)})">Разорвать</button></td></tr>`).join('')}</tbody></table>`;}
async function closeConnection(id){try{await post('/connection-close',{id});toast('Соединение разорвано');await loadConnections();}catch(e){toast('Ошибка разрыва: '+e.message)}}
async function closeAllConnections(){try{await post('/connections-close-all',{});toast('Все соединения разорваны');await loadConnections();}catch(e){toast('Ошибка: '+e.message)}}
async function loadConfigEditor(){try{const d=await get('/config-get'); $('#configEditor').value=d.content||''; $('#configMeta').textContent=`${d.path} · UI ${d.ui_version||''}`; $('#configLog').textContent='Конфиг перечитан.';}catch(e){$('#configMeta').textContent=e.message; $('#configLog').textContent=e.message;}}
async function validateConfig(){try{const d=await post('/config-validate',{content:$('#configEditor').value}); $('#configLog').textContent=(d.ok?'VALID OK\n':'VALID FAIL\n')+(d.output||''); toast(d.ok?'Конфиг валиден':'В конфиге ошибка');}catch(e){$('#configLog').textContent=e.message; toast('Validation error: '+e.message)}}
async function saveConfig(apply){try{const d=await post('/config-save',{content:$('#configEditor').value,apply:!!apply}); $('#configLog').textContent=JSON.stringify(d,null,2); toast(apply?'Сохранено и применено':'Сохранено'); if(apply) await loadStatus();}catch(e){$('#configLog').textContent=e.message; toast('Save error: '+e.message)}}

const PROTOCOLS=[['VLESS',['vless']],['WireGuard',['wireguard']],['Amnezia',['wireguard','amnezia']],['Hysteria2',['hysteria2','hysteria']],['Trojan',['trojan']],['Mieru',['mieru']],['NaiveProxy',['naiveproxy','naive']]];
let activeProtocol='VLESS';
function initProtocolTabs(){const box=$('#protocolTabs'); if(!box) return; box.innerHTML=PROTOCOLS.map(([n])=>`<button class="protocol-tab ${n===activeProtocol?'active':''}" onclick="setProtocol('${n}')">${esc(n)}</button>`).join('')}
function setProtocol(n){activeProtocol=n; initProtocolTabs(); renderProtocols();}
function protocolMatches(proxy, name){const type=String(proxy?.type||'').toLowerCase(); const [label,types]=PROTOCOLS.find(([n])=>n===name)||[name,[]]; if(label==='Amnezia') return /amnezia|awg/i.test(proxy?.name||'') || /amnezia|awg/i.test(proxy?.server||''); return types.includes(type);}
function renderProtocols(){initProtocolTabs(); const title=$('#protocolTitle'); const list=$('#protocolList'); if(!title||!list) return; title.textContent=activeProtocol; const proxies=Object.values(proxyCache||{}).filter(p=>!Array.isArray(p.all)&&protocolMatches(p,activeProtocol)); list.innerHTML=`<p class="muted">Найдено: ${proxies.length}</p><table><thead><tr><th>Имя</th><th>Тип</th><th>Сервер</th><th>Ping</th><th>Статус</th></tr></thead><tbody>${proxies.map(p=>`<tr><td>${esc(p.name)}</td><td>${esc(p.type)}</td><td>${esc(p.server||p.xudp||'')}</td><td><button class="btn small" onclick="pingProxy(${JSON.stringify(p.name)})">${esc(latency(p))}</button></td><td><span class="pill ${p.alive===false?'offline':'online'}">${p.alive===false?'offline':'online'}</span></td></tr>`).join('')}</tbody></table>`;}
function yamlQuote(v){return String(v??'').replace(/'/g,"''");}
function appendProxyYaml(block){const ed=$('#configEditor'); if(!ed.value.trim()) { toast('Сначала перечитай YAML'); return; } let y=ed.value; if(!/^proxies:\s*$/m.test(y)){ y += '\nproxies:\n'; } const pos=y.search(/^proxy-groups:\s*$/m); if(pos>=0){ y=y.slice(0,pos).replace(/\s*$/,'\n')+block+'\n'+y.slice(pos); } else { y=y.replace(/\s*$/,'\n')+block+'\n'; } ed.value=y; $('#protocolImportLog').textContent='Добавлено в YAML. Проверь и нажми “Сохранить и применить”.';}
function parseUriProxy(text,typeHint){const raw=text.trim(); let u; try{u=new URL(raw)}catch(e){return null} const scheme=u.protocol.replace(':','').toLowerCase(); const name=decodeURIComponent((raw.split('#')[1]||`${scheme}-${u.hostname}`).trim()); const q=Object.fromEntries([...u.searchParams.entries()]); if(scheme==='vless'){return `  - name: '${yamlQuote(name)}'\n    type: vless\n    server: ${u.hostname}\n    port: ${u.port||443}\n    uuid: ${u.username}\n    network: ${q.type||'tcp'}\n    tls: ${q.security==='reality'||q.security==='tls'?'true':'false'}\n    udp: true\n    servername: ${q.sni||q.servername||u.hostname}\n    client-fingerprint: ${q.fp||'chrome'}\n    reality-opts:\n      public-key: ${q.pbk||''}\n      short-id: ${q.sid||''}\n`;}
 if(scheme==='trojan'){return `  - name: '${yamlQuote(name)}'\n    type: trojan\n    server: ${u.hostname}\n    port: ${u.port||443}\n    password: ${u.username}\n    sni: ${q.sni||q.peer||u.hostname}\n    udp: true\n`;}
 if(scheme==='hysteria2'||scheme==='hy2'){return `  - name: '${yamlQuote(name)}'\n    type: hysteria2\n    server: ${u.hostname}\n    port: ${u.port||443}\n    password: ${u.username||q.auth||''}\n    sni: ${q.sni||u.hostname}\n    skip-cert-verify: ${q.insecure==='1'||q.insecure==='true'?'true':'false'}\n`;}
 return null;}
function parseWireGuard(text,typeHint){const name=(text.match(/^\s*Name\s*=\s*(.+)$/mi)||[])[1] || `${typeHint||'AmneziaWG'}-imported`; const iface=('uawg'+Array.from(name).reduce((a,ch)=>((a*33)+ch.charCodeAt(0))>>>0,5381).toString(16)).slice(0,15); return `  - name: '${yamlQuote(name)}'\n    type: direct\n    interface-name: '${yamlQuote(iface)}'\n    routing-mark: 50000\n    udp: true\n`;}
function importProtocolConnection(){const type=$('#protocolImportType').value; const text=$('#protocolImportText').value.trim(); if(!text){toast('Вставь ссылку или конфиг');return} let block=parseUriProxy(text,type); if(!block && /PrivateKey\s*=|PublicKey\s*=|Endpoint\s*=/i.test(text)) block=parseWireGuard(text,type); if(!block){$('#protocolImportLog').textContent='Не распознал формат. Поддержано сейчас: vless://, trojan://, hysteria2:///hy2://, WireGuard/Amnezia WG config.'; return;} appendProxyYaml(block);}

async function loadRaw(){for(const [id,path] of [['#rawConfigs','/configs'],['#rawVersion','/version']]){try{$(id).textContent=JSON.stringify(await get(path),null,2)}catch(e){$(id).textContent=e.message}}}
async function restartMihomo(){ $('#restartLog').textContent='Перезапускаю…'; try{const d=await get('/restart'); $('#restartLog').textContent=JSON.stringify(d,null,2); await new Promise(r=>setTimeout(r,1200)); loadAll(); }catch(e){$('#restartLog').textContent=e.message;} }
async function loadAll(){await loadStatus(); await Promise.allSettled([loadProxies(),loadConnections(),loadRaw(),loadConfigEditor()]);}
loadAll(); setInterval(loadStatus,10000);
</script>
</body>
</html>
HTML

printf 'Installed Unified UI OpenWrt:\n  %s\n  %s\n  update: %s\n' "$UI_ROOT/index.html" "$CGI_PATH" "$UPDATE_URL"
