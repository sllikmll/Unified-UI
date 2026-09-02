"""Official Amnezia Gateway ``vpn://`` subscription-key support.

The key is an URL-safe Base64 container (optionally qCompress/zlib wrapped) with
subscription metadata and an API credential.  It is deliberately *not* written
to Unified UI state: callers must keep it in ``AMNEZIA_VPN_URI`` or supply it
only for a one-shot import.  The persisted connection record contains only a
SHA-256 fingerprint, selected country and public country/protocol catalogue.

Gateway requests follow amnezia-vpn/amnezia-client:
RSA PKCS#1 v1.5 encrypts a per-request AES key payload, then AES-256-CBC
(PKCS#7) encrypts the JSON payload.  The production public key is public
material embedded in the official client.  It can be replaced at runtime with
``AMNEZIA_GATEWAY_PUBLIC_KEY`` when Amnezia rotates it.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import uuid
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import subprocess
import tempfile
from urllib import request as urlrequest
from .mihomo_xray_json import convert_outbound_to_mihomo

GATEWAY_ENDPOINT = os.environ.get("AMNEZIA_GATEWAY_ENDPOINT") or "http://gw.amnezia.org:80/"
KEY_ENV = "AMNEZIA_VPN_URI"
INSTALLATION_UUID_ENV = "AMNEZIA_GATEWAY_INSTALLATION_UUID"
PUBLIC_KEY_ENV = "AMNEZIA_GATEWAY_PUBLIC_KEY"
# Production storage origins extracted from the official AmneziaVPN 5.0.0.5
# release by the NixOS package. They host encrypted official bypass pools.
PROXY_STORAGE_PRIMARY = (
    "https://s3.eu-north-1.amazonaws.com/amnezia/",
    "https://storage.googleapis.com/lambda-list/",
    "https://amnzstrg01.blob.core.windows.net/lambda-list/",
    "https://objectstorage.eu-zurich-1.oraclecloud.com/n/zrhfyaq6qxvh/b/lambda-list/o/",
)
PROXY_STORAGE_FALLBACK = (
    "https://storage.mwsapis.ru/lambda-list/",
    "https://46.8.209.252/lambda-list/",
)

# Public production Gateway encryption key from the official AmneziaVPN client.
DEFAULT_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAj5mxl/4DL3Sk89ntxs5G
X3JawGQWIoq6rvNkOzNGuNgedNS2+pi6hZl3Izl1Io9om4KiUlMT6mgLO1hTr9q+
s7CYhlvroFA7ErucF+9L+7FCt0Igi0kIK/R2/vxd/2HaUrorn/aSvvutkYwbfxqW
SwtzE+RuBeDWGvEt937OW0oqYONPYv9E4T56Dz/EZ6v2t8ejAnKLbGD/GocMmipK
7etFSiSMAB2RmaztqTq4NleBepfO80XpYlW9pCSXuHcE8wxHczkzxsbyMAMsG/K3
vUQY6qPtohqqzSSBwa/8u2ptNHBeor7l7DdYXeR/Nqcc4z92VUkZ5lOVR4evkS5V
/wQqp5tnOJEj3NjUhEhXFoNEapbZd1bh6iQoUk7jC1TdvKJ/nPKGZAsHRpr0rNKz
fx/N/Oo6lr2yh/+ps6VxTkbPmB6E85WOO3UvjImZUY0XQdBjWle/4iJLdEC77Nr0
jXhdgeypucy6jkB6iBHMeVMlrNMEV7UxoBR/cCNx55zu/8sml5ByiDvCDT7sRomN
NgVt5S/FaVjYuzFUifJ12ToChXFgESKFmuso7WluEaWvMIGREdrMrKQKHfYLOzWF
2B5ZJDqw4o03fU4J/6rw61M1b+rjVpXMjPnzc2A+RgcjTvXv955gfZkwe4lt5wk/
3j8zMVo3+zLrMTAaEeIUM0UCAwEAAQ==
-----END PUBLIC KEY-----
"""


@dataclass(frozen=True)
class AmneziaKey:
    fingerprint: str
    name: str
    description: str
    api_config: dict[str, Any]
    auth_data: dict[str, Any]


def _b64url_decode(value: str) -> bytes:
    raw = str(value or "").strip().removeprefix("vpn://")
    if not raw:
        raise ValueError("empty Amnezia vpn key")
    try:
        return base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4))
    except Exception as exc:
        raise ValueError("invalid Amnezia vpn key encoding") from exc


def decode_vpn_key(value: str) -> AmneziaKey:
    original = str(value or "").strip()
    blob = _b64url_decode(original)
    # Premium V2 export prefixes raw qCompress stream with 00 00 00 ff.
    if blob.startswith(b"\x00\x00\x00\xff"):
        blob = blob[4:]
    decoded = b""
    for candidate in (blob, blob[4:] if len(blob) > 4 else b""):
        try:
            decoded = zlib.decompress(candidate)
            if decoded:
                break
        except zlib.error:
            continue
    if not decoded:
        decoded = blob
    try:
        item = json.loads(decoded)
    except Exception as exc:
        raise ValueError("Amnezia vpn key does not contain JSON") from exc
    if not isinstance(item, dict):
        raise ValueError("Amnezia vpn key has invalid JSON root")
    api = item.get("api_config")
    auth = item.get("auth_data")
    if not isinstance(api, dict) or not isinstance(auth, dict) or not str(auth.get("api_key") or ""):
        raise ValueError("Amnezia vpn key has no Gateway subscription data")
    return AmneziaKey(
        fingerprint=hashlib.sha256(original.encode("utf-8")).hexdigest(),
        name=str(item.get("name") or "Amnezia"),
        description=str(item.get("description") or ""),
        api_config=dict(api),
        auth_data=dict(auth),
    )


def _openssl() -> str:
    return os.environ.get("AMNEZIA_OPENSSL_BIN") or "openssl"


def _run(command: list[str], data: bytes, *, what: str) -> bytes:
    try:
        result = subprocess.run(command, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
    except OSError as exc:
        raise RuntimeError(f"Amnezia Gateway {what} tool is unavailable") from exc
    if result.returncode != 0:
        raise RuntimeError(f"Amnezia Gateway {what} failed")
    return result.stdout


def _public_key_pem() -> str:
    return os.environ.get(PUBLIC_KEY_ENV) or DEFAULT_PUBLIC_KEY


def _encrypt_aes(data: bytes, key: bytes, iv: bytes) -> bytes:
    return _run([_openssl(), "enc", "-aes-256-cbc", "-K", key.hex(), "-iv", iv[:16].hex()], data, what="AES encryption")


def _decrypt_aes(data: bytes, key: bytes, iv: bytes) -> bytes:
    return _run([_openssl(), "enc", "-d", "-aes-256-cbc", "-K", key.hex(), "-iv", iv[:16].hex()], data, what="AES decryption")


def _rsa_encrypt(data: bytes) -> bytes:
    handle = tempfile.NamedTemporaryFile(mode="w", prefix="amnezia-gateway-", suffix=".pem", delete=False)
    try:
        handle.write(_public_key_pem())
        handle.close()
        return _run([_openssl(), "pkeyutl", "-encrypt", "-pubin", "-inkey", handle.name, "-pkeyopt", "rsa_padding_mode:pkcs1"], data, what="RSA encryption")
    finally:
        try:
            os.unlink(handle.name)
        except OSError:
            pass


def _installation_uuid() -> str:
    current = str(os.environ.get(INSTALLATION_UUID_ENV) or "").strip()
    if current:
        return current
    # This fallback is intentionally ephemeral. Production importers must set the
    # env var so a router stays one Amnezia device across refreshes/reboots.
    return str(uuid.uuid4())


def _request_payload(key: AmneziaKey, client_public_key: str, *, country: str | None = None) -> dict[str, Any]:
    api = key.api_config
    payload: dict[str, Any] = {
        "os_version": "linux",
        "app_version": os.environ.get("AMNEZIA_GATEWAY_APP_VERSION") or "5.0.1.5",
        "cli_name": "Unified UI",
        "distribution": "github",
        "app_language": "ru",
        "installation_uuid": _installation_uuid(),
        "user_country_code": api.get("user_country_code"),
        "service_type": api.get("service_type"),
        "service_protocol": "awg",
        "public_key": client_public_key,
        "auth_data": key.auth_data,
    }
    if country:
        payload["server_country_code"] = str(country).lower()
    return {name: value for name, value in payload.items() if value not in (None, "", {}, [])}


def _official_bypass_urls(payload: dict[str, Any]) -> list[str]:
    """Resolve Amnezia's encrypted bypass pool exactly like GatewayController."""
    service = str(payload.get("service_type") or "")
    user_country = str(payload.get("user_country_code") or "")
    paths = []
    if service:
        import base64 as _b64
        suffix = _b64.urlsafe_b64encode(f"endpoints-{service}-{user_country}".encode()).decode().rstrip("=") + ".json"
        paths.append(suffix)
    paths.append("endpoints.json")
    # Upstream hashes the PEM macro without its file-terminal newline.
    digest = hashlib.sha512(_public_key_pem().rstrip("\n").encode()).digest()
    urls: list[str] = []
    for base in (*PROXY_STORAGE_PRIMARY, *PROXY_STORAGE_FALLBACK):
        for path in paths:
            try:
                with urlrequest.urlopen(base.rstrip("/") + "/" + path, timeout=3) as response:
                    wire = response.read(1024 * 1024)
                decoded = _decrypt_aes(base64.b64decode(wire), digest[:32], digest[32:48])
                candidates = json.loads(decoded)
                if isinstance(candidates, list):
                    urls.extend(str(x).rstrip("/") + "/" for x in candidates if isinstance(x, str) and x.startswith(("http://", "https://")))
                    if urls:
                        return urls
            except Exception:
                continue
    return urls


def _gateway_wire(url: str, body: bytes, timeout: int) -> bytes:
    req = urlrequest.Request(url, data=body, headers={"Content-Type": "application/json", "X-Client-Request-ID": str(uuid.uuid4())})
    with urlrequest.urlopen(req, timeout=timeout) as response:
        return response.read(2 * 1024 * 1024 + 1)


def _gateway_health(url: str) -> None:
    with urlrequest.urlopen(url, timeout=1) as response:
        response.read(1024)


def _post(path: str, payload: dict[str, Any], *, timeout: int = 35) -> dict[str, Any]:
    aes_key, aes_iv, aes_salt = os.urandom(32), os.urandom(32), os.urandom(8)
    key_payload = json.dumps(
        {"aes_key": base64.b64encode(aes_key).decode(), "aes_iv": base64.b64encode(aes_iv).decode(), "aes_salt": base64.b64encode(aes_salt).decode()},
        separators=(",", ":"),
    ).encode()
    encrypted_key = _rsa_encrypt(key_payload)
    encrypted_payload = _encrypt_aes(json.dumps(payload, separators=(",", ":")).encode(), aes_key, aes_iv)
    body = json.dumps({"key_payload": base64.b64encode(encrypted_key).decode(), "api_payload": base64.b64encode(encrypted_payload).decode()}).encode()
    direct = (os.environ.get("AMNEZIA_GATEWAY_ENDPOINT") or GATEWAY_ENDPOINT).rstrip("/") + "/"
    candidates = [direct]
    last_error: Exception | None = None
    for base in candidates + _official_bypass_urls(payload):
        try:
            if base != direct:
                # Official client probes this exact health path before retrying.
                _gateway_health(base.rstrip("/") + "/lmbd-health")
            wire = _gateway_wire(base.rstrip("/") + "/" + path.lstrip("/"), body, timeout)
            break
        except Exception as exc:
            last_error = exc
    else:
        raise RuntimeError("Amnezia Gateway is unavailable directly and via official bypass endpoints") from last_error
    if len(wire) > 2 * 1024 * 1024:
        raise RuntimeError("Amnezia Gateway response is too large")
    try:
        answer = json.loads(_decrypt_aes(wire, aes_key, aes_iv))
    except Exception as exc:
        raise RuntimeError("Amnezia Gateway returned an unreadable response") from exc
    if not isinstance(answer, dict):
        raise RuntimeError("Amnezia Gateway returned invalid JSON")
    if answer.get("message") and not answer.get("config"):
        raise RuntimeError("Amnezia Gateway: " + str(answer["message"])[:200])
    return answer


def _decode_config(value: str) -> dict[str, Any]:
    blob = _b64url_decode(value)
    if blob.startswith(b"\x00\x00\x00\xff"):
        blob = blob[4:]
    for candidate in (blob, blob[4:] if len(blob) > 4 else b""):
        try:
            decoded = zlib.decompress(candidate)
            item = json.loads(decoded)
            if isinstance(item, dict):
                return item
        except Exception:
            continue
    raise RuntimeError("Amnezia Gateway returned an invalid config")


def _awg_text(server_config: dict[str, Any], private_key: str) -> str:
    containers = server_config.get("containers")
    if not isinstance(containers, list):
        raise RuntimeError("Amnezia config has no containers")
    for container in containers:
        if not isinstance(container, dict):
            continue
        awg = container.get("awg")
        if not isinstance(awg, dict):
            continue
        raw = awg.get("last_config")
        if not isinstance(raw, str):
            continue
        try:
            parsed = json.loads(raw)
            text = str(parsed.get("config") or "")
        except Exception:
            text = raw
        if "[Interface]" in text and "[Peer]" in text:
            return text.replace("$WIREGUARD_CLIENT_PRIVATE_KEY", private_key)
    raise RuntimeError("Amnezia config has no AWG profile")


def _awg_keypair() -> tuple[str, str]:
    awg = os.environ.get("AMNEZIA_AWG_BIN") or "awg"
    private = _run([awg, "genkey"], b"", what="AWG key generation").decode().strip()
    if not private:
        raise RuntimeError("Amnezia Gateway generated an empty AWG private key")
    public = _run([awg, "pubkey"], (private + "\n").encode(), what="AWG public-key generation").decode().strip()
    if not public:
        raise RuntimeError("Amnezia Gateway generated an empty AWG public key")
    return private, public


def fetch_gateway_profile(vpn_key: str, *, country: str | None = None, protocol: str = "awg") -> dict[str, Any]:
    """Resolve one official Gateway country/protocol into its local runtime form."""
    protocol = str(protocol or "").lower()
    if protocol not in {"awg", "vless"}:
        raise ValueError("unsupported Amnezia Gateway protocol")
    key = decode_vpn_key(vpn_key)
    private_b64 = ""
    if protocol == "awg":
        private_b64, public_key = _awg_keypair()
    else:
        public_key = str(uuid.uuid4())
    payload = _request_payload(key, public_key, country=country)
    payload["service_protocol"] = protocol
    answer = _post("v1/config", payload)
    encoded = str(answer.get("config") or "")
    if not encoded:
        raise RuntimeError("Amnezia Gateway did not return a config")
    server = _decode_config(encoded)
    api = server.get("api_config") if isinstance(server.get("api_config"), dict) else {}
    countries = api.get("available_countries") if isinstance(api.get("available_countries"), list) else []
    selected = str(api.get("server_country_code") or country or "").lower()
    result = {
        "fingerprint": key.fingerprint, "name": key.name, "description": key.description,
        "country": selected, "protocol": protocol,
        "countries": [{"code": str(item.get("server_country_code") or "").lower(), "name": str(item.get("server_country_name") or item.get("server_country_code") or ""), "protocols": [str(p) for p in (item.get("available_protocols") or []) if str(p)]} for item in countries if isinstance(item, dict)],
    }
    if protocol == "awg":
        result["config"] = _awg_text(server, private_b64)
        return result
    containers = server.get("containers") if isinstance(server.get("containers"), list) else []
    for container in containers:
        xray = container.get("xray") if isinstance(container, dict) else None
        try:
            cfg = json.loads(str(xray.get("last_config") or "")) if isinstance(xray, dict) else {}
        except Exception:
            cfg = {}
        for outbound in cfg.get("outbounds", []) if isinstance(cfg, dict) else []:
            converted = convert_outbound_to_mihomo(outbound, f"Amnezia · {selected.upper()} · VLESS")
            if converted:
                result["proxyYaml"] = converted.yaml
                return result
    raise RuntimeError("Amnezia Gateway VLESS config has no compatible Xray outbound")


def fetch_awg_profile(vpn_key: str, *, country: str | None = None) -> dict[str, Any]:
    """Resolve one country into a native AWG profile plus public catalogue.

    Returned mapping is safe to persist except ``config`` (contains the client
    private key and must be written only to the 0600 native runtime state).
    """
    key = decode_vpn_key(vpn_key)
    private_b64, public_b64 = _awg_keypair()
    answer = _post("v1/config", _request_payload(key, public_b64, country=country))
    encoded = str(answer.get("config") or "")
    if not encoded:
        raise RuntimeError("Amnezia Gateway did not return a config")
    server = _decode_config(encoded)
    api = server.get("api_config") if isinstance(server.get("api_config"), dict) else {}
    countries = api.get("available_countries") if isinstance(api.get("available_countries"), list) else []
    selected = str(api.get("server_country_code") or country or "").lower()
    return {
        "fingerprint": key.fingerprint,
        "name": key.name,
        "description": key.description,
        "country": selected,
        "countries": [
            {
                "code": str(item.get("server_country_code") or "").lower(),
                "name": str(item.get("server_country_name") or item.get("server_country_code") or ""),
                "protocols": [str(p) for p in (item.get("available_protocols") or []) if str(p)],
            }
            for item in countries
            if isinstance(item, dict)
        ],
        "config": _awg_text(server, private_b64),
    }
