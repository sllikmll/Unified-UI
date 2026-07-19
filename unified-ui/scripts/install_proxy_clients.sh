#!/bin/sh
set -eu

# Optional proxy runtime installer for unified Unified UI.
# Mihomo-native protocols do not need separate binaries. This script installs
# optional external runtimes from bundled files or this fork's GitHub Release
# assets when they exist.

OWNER="${UNIFIED_PROXY_CLIENTS_OWNER:-sllikmll}"
REPO="${UNIFIED_PROXY_CLIENTS_REPO:-Unified-UI}"
TAG="${UNIFIED_PROXY_CLIENTS_TAG:-${UNIFIED_UI_UPDATE_TAG:-latest}}"
DEST_DIR="${UNIFIED_PROXY_CLIENTS_DEST:-/opt/sbin}"
STATUS_DIR="${UNIFIED_PROXY_CLIENTS_STATUS_DIR:-/opt/var/lib/unified-ui}"
BUNDLED_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/../third_party/proxy-clients" 2>/dev/null && pwd || true)"
STATUS_FILE="$STATUS_DIR/proxy-clients-status.json"
TMP_DIR="${TMPDIR:-/tmp}/unified-proxy-clients-$$"

mkdir -p "$DEST_DIR" "$STATUS_DIR" "$TMP_DIR"

arch="$(uname -m 2>/dev/null || echo unknown)"
case "$arch" in
  aarch64|arm64) platform="linux-arm64" ;;
  *) platform="linux-$arch" ;;
esac

asset_url() {
  asset="$1"
  if [ "$TAG" = "latest" ]; then
    echo "https://github.com/$OWNER/$REPO/releases/latest/download/$asset"
  else
    echo "https://github.com/$OWNER/$REPO/releases/download/$TAG/$asset"
  fi
}

write_status() {
  # args: tool status message path
  tool="$1"; status="$2"; message="$3"; path="$4"
  printf '{"tool":"%s","status":"%s","message":"%s","path":"%s","platform":"%s","source":"%s"}\n' \
    "$tool" "$status" "$(printf '%s' "$message" | sed 's/"/\\"/g')" "$path" "$platform" "$TAG" >> "$STATUS_FILE.tmp"
}

install_archive() {
  tool="$1"; asset="$2"; bin="$3"; install_as="$4"
  archive="$TMP_DIR/$asset"
  bundled="$BUNDLED_DIR/$asset"
  if [ -f "$bundled" ]; then
    cp -f "$bundled" "$archive"
  else
    url="$(asset_url "$asset")"
    if command -v curl >/dev/null 2>&1; then
      if ! curl -fsSL --connect-timeout 8 --max-time 60 "$url" -o "$archive"; then
        write_status "$tool" "unavailable" "asset not found or download failed: $url" "$install_as"
        return 0
      fi
    elif command -v wget >/dev/null 2>&1; then
      if ! wget -q -T 60 -O "$archive" "$url"; then
        write_status "$tool" "unavailable" "asset not found or download failed: $url" "$install_as"
        return 0
      fi
    else
      write_status "$tool" "unavailable" "curl/wget missing" "$install_as"
      return 0
    fi
  fi
  work="$TMP_DIR/$tool"
  mkdir -p "$work"
  if ! tar -xzf "$archive" -C "$work" >/dev/null 2>&1; then
    write_status "$tool" "error" "cannot extract $asset" "$install_as"
    return 0
  fi
  found="$(find "$work" -type f -name "$bin" -perm -u+x 2>/dev/null | head -n 1 || true)"
  if [ -z "$found" ]; then
    found="$(find "$work" -type f -name "$bin" 2>/dev/null | head -n 1 || true)"
  fi
  if [ -z "$found" ]; then
    write_status "$tool" "error" "binary $bin not found in $asset" "$install_as"
    return 0
  fi
  cp -f "$found" "$install_as"
  chmod +x "$install_as" || true
  write_status "$tool" "installed" "installed from $asset" "$install_as"
}

: > "$STATUS_FILE.tmp"
# Current known optional external clients. Keep non-fatal: Mihomo-native paths
# remain fully usable without these binaries.
install_archive "amneziawg-go" "amneziawg-go-linux-arm64.tar.gz" "amneziawg-go" "$DEST_DIR/amneziawg-go"
install_archive "mieru" "mieru-client-linux-arm64.tar.gz" "mieru" "$DEST_DIR/mieru"
install_archive "naiveproxy" "naiveproxy-linux-arm64.tar.gz" "naive" "$DEST_DIR/naive"
install_archive "hysteria" "hysteria-linux-arm64.tar.gz" "hysteria" "$DEST_DIR/hysteria"

{
  echo '{'
  echo '  "ok": true,'
  echo "  \"platform\": \"$platform\","
  echo '  "items": ['
  awk 'NF{ if (n++) print ","; printf "    %s", $0 } END{print ""}' "$STATUS_FILE.tmp"
  echo '  ]'
  echo '}'
} > "$STATUS_FILE"
rm -rf "$TMP_DIR" "$STATUS_FILE.tmp" 2>/dev/null || true
cat "$STATUS_FILE"
