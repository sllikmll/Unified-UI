import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "unified-ui"))

from services.mihomo_proxy_parsers import parse_proxy_uri


def test_parse_mieru_uri_to_mihomo_yaml():
    res = parse_proxy_uri("mierus://user:pass@example.com:32002?protocol=tcp#Mieru")
    assert res.name == "Mieru"
    assert "type: mieru" in res.yaml
    assert "server: example.com" in res.yaml
    assert "port-range: '32002-32002'" in res.yaml or "port-range: 32002-32002" in res.yaml
    assert "transport: TCP" in res.yaml
    assert "username: user" in res.yaml
    assert "password: pass" in res.yaml


def test_parse_naiveproxy_uri_to_http_tls_yaml():
    res = parse_proxy_uri("naive+https://user:pass@example.com:32003?sni=yandex.ru#Naive")
    assert res.name == "Naive"
    assert "type: http" in res.yaml
    assert "server: example.com" in res.yaml
    assert "port: 32003" in res.yaml
    assert "tls: true" in res.yaml
    assert "sni: yandex.ru" in res.yaml
    assert "username: user" in res.yaml
    assert "password: pass" in res.yaml
