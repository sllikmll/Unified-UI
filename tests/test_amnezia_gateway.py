import base64
import importlib
import json
import zlib


def _vpn_key() -> str:
    payload = {
        "name": "Amnezia Premium",
        "api_config": {"service_type": "amnezia-premium", "service_protocol": "awg", "user_country_code": "ru"},
        "auth_data": {"api_key": "test-only-api-key"},
    }
    # Matches Premium export framing: qCompress length marker + raw zlib stream.
    blob = b"\x00\x00\x00\xff" + zlib.compress(json.dumps(payload).encode())
    return "vpn://" + base64.urlsafe_b64encode(blob).decode().rstrip("=")


AWG = """[Interface]
PrivateKey = client-private-key
Address = 10.8.1.2/32
Jc = 4
Jmin = 10
Jmax = 50
S1 = 12
S2 = 12
S3 = 12
S4 = 12
H1 = 101
H2 = 202
H3 = 303
H4 = 404

[Peer]
PublicKey = server-public-key
Endpoint = france.example.test:443
AllowedIPs = 0.0.0.0/0
"""


def test_decode_amnezia_vpn_key_never_exposes_auth_data():
    gateway = importlib.import_module("services.amnezia_gateway")
    parsed = gateway.decode_vpn_key(_vpn_key())

    assert parsed.api_config["service_protocol"] == "awg"
    assert parsed.fingerprint
    assert parsed.auth_data["api_key"] == "test-only-api-key"


def test_gateway_import_persists_safe_catalog_not_vpn_key(monkeypatch):
    routes = importlib.import_module("routes.proxy_connections")
    source = _vpn_key()
    profile = {
        "fingerprint": "f" * 64,
        "country": "fr",
        "countries": [
            {"code": "fr", "name": "Франция", "protocols": ["awg", "vless"]},
            {"code": "se", "name": "Швеция", "protocols": ["awg", "vless"]},
        ],
        "config": AWG,
    }
    monkeypatch.setattr(routes, "fetch_awg_profile", lambda key: profile)

    conn = routes._parse_connection("amnezia-gateway", source)
    rendered = json.dumps(conn)

    assert conn["protocol"] == "amnezia"
    assert conn["sourceType"] == "amnezia-gateway"
    assert conn["gateway"]["country"] == "fr"
    assert conn["gateway"]["countries"][1]["code"] == "se"
    assert conn["nativeRuntime"]["engine"] == "amneziawg-go"
    assert source not in rendered
    assert "test-only-api-key" not in rendered
