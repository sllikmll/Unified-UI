import base64
import importlib
import json
import sys


def _reload(name: str):
    if name in sys.modules:
        return importlib.reload(sys.modules[name])
    return importlib.import_module(name)


def test_wireguard_uri_becomes_live_mihomo_wireguard():
    mod = _reload("routes.proxy_connections")
    link = (
        "wireguard://private-key@example.net:31005"
        "?publickey=server-public-key&address=10.10.0.2%2F32"
        "&keepalive=25&mtu=1420#WG-panel"
    )
    conn = mod._parse_connection("", link)
    assert conn["protocol"] == "wireguard"
    assert conn["mihomoSupported"] is True
    assert "type: wireguard" in conn["proxyYaml"]
    assert "server: example.net" in conn["proxyYaml"]
    assert "port: 31005" in conn["proxyYaml"]
    assert "private-key: private-key" in conn["proxyYaml"]
    assert "public-key: server-public-key" in conn["proxyYaml"]


def test_awg_data_uri_uses_native_amnezia_runtime():
    mod = _reload("routes.proxy_connections")
    config = """[Interface]
PrivateKey = private-key
Address = 10.20.0.2/32
Jc = 5
Jmin = 50
Jmax = 1000
S1 = 100
S2 = 200
H1 = 123456
H2 = 234567
H3 = 345678
H4 = 456789
[Peer]
PublicKey = server-public-key
Endpoint = vpn.example.net:32001
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""
    payload = base64.urlsafe_b64encode(config.encode()).decode().rstrip("=")
    conn = mod._parse_connection("", f"awg://{payload}#AWG-panel")
    assert conn["protocol"] == "amnezia"
    assert conn["mihomoSupported"] is True
    assert "type: direct" in conn["proxyYaml"]
    assert "interface-name:" in conn["proxyYaml"]
    assert "amnezia-wg-option:" not in conn["proxyYaml"]
    assert conn["nativeRuntime"]["engine"] == "amneziawg-go"


def test_awg3_data_uri_uses_native_amnezia_runtime():
    mod = _reload("routes.proxy_connections")
    config = """[Interface]
PrivateKey = private-key
Address = 10.203.183.2/32
Jc = 4
HeaderProtectionKey = awg3-header-key
ContentPaddingAddition = 10-100
RekeyAfterTime = 100-120
RekeyTimeout = 3-7
RejectAfterTime = 150-180
KeepaliveTimeout = 5-15
MaxHandshakeAttempts = 15-20
[Peer]
PublicKey = server-public-key
Endpoint = almaty.example.net:9731
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""
    payload = base64.urlsafe_b64encode(config.encode()).decode().rstrip("=")
    conn = mod._parse_connection("", f"awg3://{payload}#AWG3-panel")
    assert conn["protocol"] == "amnezia"
    assert conn["mihomoSupported"] is True
    assert "type: direct" in conn["proxyYaml"]
    assert "interface-name:" in conn["proxyYaml"]
    assert "amnezia-wg-option:" not in conn["proxyYaml"]
    assert conn["nativeRuntime"]["engine"] == "amneziawg-go"


def test_mierus_uri_becomes_native_mihomo_mieru():
    mod = _reload("routes.proxy_connections")
    conn = mod._parse_connection(
        "",
        "mierus://user:password@vpn.example.net?port=32002&protocol=TCP&mtu=1400&profile=panel",
    )
    assert conn["protocol"] == "mieru"
    assert conn["mihomoSupported"] is True
    assert "type: mieru" in conn["proxyYaml"]
    assert "server: vpn.example.net" in conn["proxyYaml"]
    assert "port-range: 32002-32002" in conn["proxyYaml"]
    assert "transport: TCP" in conn["proxyYaml"]
    assert "username: user" in conn["proxyYaml"]
    assert "password: password" in conn["proxyYaml"]


def test_naive_and_standard_subscription_schemes_are_detected():
    mod = _reload("routes.proxy_connections")
    assert mod._detect_protocol("naive+https://u:p@example.net:443") == "naiveproxy"
    assert mod._detect_protocol("vmess://payload") == "vmess"
    assert mod._detect_protocol("ss://payload") == "shadowsocks"
    assert mod._detect_protocol("tg://proxy?server=example.net&port=443&secret=secret") == "telegram"


def test_telegram_is_explicit_action_not_fake_mihomo_proxy():
    mod = _reload("routes.proxy_connections")
    conn = mod._parse_connection("", "tg://proxy?server=example.net&port=443&secret=secret")
    assert conn["protocol"] == "telegram"
    assert conn["mihomoSupported"] is False
    assert not conn["proxyYaml"].lstrip().startswith("- name:")
    public = mod._connection_public(conn)
    assert "raw" not in public
    assert public["actionAvailable"] is True


def test_full_panel_subscription_parses_all_ten_schemes():
    mod = _reload("routes.proxy_connections")
    vmess_payload = base64.urlsafe_b64encode(
        json.dumps(
            {
                "v": "2",
                "ps": "VMess-panel",
                "add": "vpn.example.net",
                "port": "443",
                "id": "11111111-1111-1111-1111-111111111111",
                "aid": "0",
                "net": "ws",
                "host": "vpn.example.net",
                "path": "/ws",
                "tls": "tls",
            }
        ).encode()
    ).decode().rstrip("=")
    ss_user = base64.urlsafe_b64encode(b"aes-256-gcm:password").decode().rstrip("=")
    awg_config = """[Interface]
PrivateKey = private-key
Address = 10.20.0.2/32
Jc = 5
Jmin = 50
Jmax = 1000
S1 = 100
S2 = 200
H1 = 123456
H2 = 234567
H3 = 345678
H4 = 456789
[Peer]
PublicKey = server-public-key
Endpoint = vpn.example.net:32001
AllowedIPs = 0.0.0.0/0
"""
    awg_payload = base64.urlsafe_b64encode(awg_config.encode()).decode().rstrip("=")
    lines = [
        "vless://11111111-1111-1111-1111-111111111111@vpn.example.net:443?security=tls&type=tcp#VLESS-panel",
        f"vmess://{vmess_payload}",
        "trojan://password@vpn.example.net:443?security=tls#Trojan-panel",
        f"ss://{ss_user}@vpn.example.net:8388#SS-panel",
        "hysteria2://password@vpn.example.net:443?sni=vpn.example.net#HY2-panel",
        "wireguard://private-key@vpn.example.net:31005?publickey=server-public-key&address=10.10.0.2%2F32#WG-panel",
        f"awg://{awg_payload}#AWG-panel",
        "mierus://user:password@vpn.example.net?port=32002&protocol=TCP&mtu=1400&profile=Mieru-panel",
        "naive+https://user:password@vpn.example.net:32003",
        "tg://proxy?server=vpn.example.net&port=443&secret=secret",
    ]
    parsed, errors = mod._parse_subscription(lines)
    assert errors == []
    assert len(parsed) == 10
    assert {item["protocol"] for item in parsed} == {
        "vless",
        "vmess",
        "trojan",
        "shadowsocks",
        "hysteria2",
        "wireguard",
        "amnezia",
        "mieru",
        "naiveproxy",
        "telegram",
    }
    assert len([item for item in parsed if item["mihomoSupported"]]) == 9


def test_subscription_decoder_accepts_plain_and_base64():
    mod = _reload("routes.proxy_connections")
    text = "vless://one\ntrojan://two\n"
    encoded = base64.urlsafe_b64encode(text.encode()).decode().rstrip("=")
    assert mod._decode_subscription_content(text) == ["vless://one", "trojan://two"]
    assert mod._decode_subscription_content(encoded) == ["vless://one", "trojan://two"]


def test_shadowsocks_2022_identity_chain_is_url_decoded():
    parser = _reload("services.mihomo_proxy_parsers")
    key1 = "A" * 43 + "="
    key2 = "B" * 43 + "="
    link = f"ss://2022-blake3-aes-256-gcm:{key1}%3A{key2}@vpn.example.net:31004#SS2022"
    result = parser.parse_shadowsocks(link)
    assert "cipher: 2022-blake3-aes-256-gcm" in result.yaml
    assert f"password: '{key1}:{key2}'" in result.yaml
    assert "%3A" not in result.yaml


def test_subscription_duplicate_names_are_protocol_qualified():
    mod = _reload("routes.proxy_connections")
    lines = [
        "trojan://password@vpn.example.net:443",
        "naive+https://user:password@vpn.example.net:8443",
    ]
    parsed, errors = mod._parse_subscription(lines)
    assert errors == []
    names = [item["name"] for item in parsed]
    assert names == ["Trojan · vpn.example.net", "NaiveProxy · vpn.example.net"]
    assert len(set(names)) == 2
    for item in parsed:
        assert f"name: '{item['name']}'" in item["proxyYaml"]


def test_subscription_records_are_read_only_and_provider_nodes_are_not_duplicated():
    mod = _reload("routes.proxy_connections")
    local = {
        "id": "local-vless",
        "protocol": "vless",
        "name": "Local VLESS",
        "sourceType": "import",
        "mihomoSupported": True,
        "enabled": True,
        "proxyYaml": "- name: 'Local VLESS'\n  type: vless\n",
    }
    incoming = [
        {
            "id": "sub-vless",
            "protocol": "vless",
            "name": "Panel VLESS",
            "sourceType": "import",
            "mihomoSupported": True,
            "enabled": True,
            "proxyYaml": "- name: 'Panel VLESS'\n  type: vless\n",
        },
        {
            "id": "sub-mieru",
            "protocol": "mieru",
            "name": "Panel Mieru",
            "sourceType": "import",
            "mihomoSupported": True,
            "enabled": True,
            "proxyYaml": "- name: 'Panel Mieru'\n  type: mieru\n",
        },
        {
            "id": "sub-telegram",
            "protocol": "telegram",
            "name": "Panel Telegram",
            "sourceType": "import",
            "mihomoSupported": False,
            "enabled": True,
            "proxyYaml": "# external Telegram action\n",
        },
    ]
    data = {"version": 1, "connections": [local]}
    conns, _, _ = mod._upsert_connections(data, incoming, default_selectors=["AI"])
    assert len(conns) == 4
    assert next(item for item in conns if item["id"] == "local-vless")["sourceType"] == "import"
    assert next(item for item in conns if item["id"] == "sub-vless")["sourceType"] == "subscription-provider"
    assert next(item for item in conns if item["id"] == "sub-mieru")["sourceType"] == "subscription-static"
    assert next(item for item in conns if item["id"] == "sub-telegram")["sourceType"] == "subscription-action"
    assert all(mod._connection_public(item)["readOnly"] for item in conns if item["id"].startswith("sub-"))
    block = mod._format_managed_block(conns)
    assert "Panel VLESS" not in block
    assert "Panel Mieru" in block
    assert "Panel Telegram" not in block

    # Reimport replaces the subscription-owned set without duplicating it.
    conns2, _, _ = mod._upsert_connections(data, incoming, default_selectors=["AI"])
    assert len(conns2) == 4
    assert len({item["id"] for item in conns2}) == 4
