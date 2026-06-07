from __future__ import annotations

import pytest
from flask import Flask

from routes import mihomo


@pytest.fixture()
def client(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("proxy-providers: {}\n", encoding="utf-8")
    bp = mihomo.create_mihomo_blueprint(
        MIHOMO_CONFIG_FILE=str(cfg),
        MIHOMO_TEMPLATES_DIR=str(tmp_path),
        MIHOMO_DEFAULT_TEMPLATE=str(tmp_path / "default.yaml"),
        restart_xkeen=lambda: None,
    )
    app = Flask(__name__)
    app.register_blueprint(bp)
    return app.test_client()


def test_hwid_probe_route_blocks_private_url_before_probe(monkeypatch, client):
    monkeypatch.delenv("XKEEN_MIHOMO_HWID_ALLOW_PRIVATE_HOSTS", raising=False)
    calls = []

    def fake_probe(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("probe should not be called for blocked URL")

    monkeypatch.setattr(mihomo, "_mh_hwid_probe_subscription_safe", fake_probe)

    response = client.post(
        "/api/mihomo/hwid/probe",
        json={"url": "https://127.0.0.1/sub"},
    )

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["ok"] is False
    assert payload["error"]["code"] == "URL_BLOCKED"
    assert payload["error"]["reason"] == "private_host_not_allowed:127.0.0.1"
    assert calls == []


def test_hwid_apply_route_blocks_http_url_before_probe(monkeypatch, client):
    monkeypatch.delenv("XKEEN_MIHOMO_HWID_ALLOW_HTTP", raising=False)
    calls = []

    def fake_probe(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("probe should not be called for blocked URL")

    monkeypatch.setattr(mihomo, "_mh_hwid_probe_subscription_safe", fake_probe)

    response = client.post(
        "/api/mihomo/hwid/apply",
        json={"url": "http://example.com/sub", "name": "sub", "restart": True},
    )

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["ok"] is False
    assert payload["stage"] == "probe"
    assert payload["probe"]["error"]["code"] == "URL_BLOCKED"
    assert payload["probe"]["error"]["reason"] == "http_not_allowed"
    assert calls == []


def test_hwid_probe_route_allows_private_url_when_enabled(monkeypatch, client):
    monkeypatch.setenv("XKEEN_MIHOMO_HWID_ALLOW_PRIVATE_HOSTS", "1")
    calls = []

    monkeypatch.setattr(
        mihomo,
        "_mh_hwid_get_device_info",
        lambda: {"headers": {"x-hwid": "AABBCCDDEEFF"}},
    )

    def fake_probe(url, *, headers, insecure, timeout, prefer, policy):
        calls.append(
            {
                "url": url,
                "headers": headers,
                "allow_private_hosts": policy.allow_private_hosts,
            }
        )
        return {
            "ok": True,
            "probe": {
                "url": url,
                "resolved_url": url,
                "method": "HEAD",
                "http_status": 200,
                "content_type": "text/plain",
                "content_length": 0,
                "timing_ms": 1,
            },
            "profile": {
                "profile_title": "Local",
                "profile_title_raw": "Local",
                "profile_title_encoding": None,
                "suggested_name": "Local",
            },
            "headers_used": headers or {},
            "warnings": [],
            "error": None,
        }

    monkeypatch.setattr(mihomo, "_mh_hwid_probe_subscription_safe", fake_probe)

    response = client.post(
        "/api/mihomo/hwid/probe",
        json={"url": "https://127.0.0.1/sub"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert calls[0]["allow_private_hosts"] is True
    assert calls[0]["headers"]["x-hwid"] == "AABBCCDDEEFF"
    assert "no_headers_ok" not in payload
    assert len(calls) == 1


def test_hwid_probe_route_maps_tls_handshake_timeout_to_504(monkeypatch, client):
    monkeypatch.setattr(
        mihomo,
        "_mh_hwid_get_device_info",
        lambda: {"headers": {"x-hwid": "AABBCCDDEEFF"}},
    )

    def fake_probe(url, *, headers, insecure, timeout, prefer, policy):
        return {
            "ok": False,
            "probe": {
                "url": url,
                "resolved_url": None,
                "method": "HEAD",
                "http_status": None,
                "content_type": None,
                "content_length": None,
                "timing_ms": int(timeout * 1000),
            },
            "profile": {
                "profile_title": None,
                "profile_title_raw": None,
                "profile_title_encoding": None,
                "suggested_name": None,
            },
            "headers_used": headers or {},
            "warnings": [],
            "error": {
                "code": "TLS_HANDSHAKE_TIMEOUT",
                "message": "TLS handshake с сервером подписки не завершился вовремя.",
                "hint": "Попробуйте другой VPN/exit-IP.",
                "retryable": True,
            },
        }

    monkeypatch.setattr(mihomo, "_mh_hwid_probe_subscription_safe", fake_probe)

    response = client.post(
        "/api/mihomo/hwid/probe",
        json={"url": "https://provider.example/sub"},
    )

    assert response.status_code == 504
    payload = response.get_json()
    assert payload["error"]["code"] == "TLS_HANDSHAKE_TIMEOUT"


def test_hwid_provider_adapter_route_is_loopback_only(monkeypatch, client):
    monkeypatch.setattr(
        mihomo,
        "_mh_hwid_get_device_info",
        lambda: {"headers": {"x-hwid": "AABBCCDDEEFF"}},
    )

    calls = []

    def fake_fetch(url, *, headers, insecure, timeout, policy):
        calls.append(
            {
                "url": url,
                "headers": headers,
                "insecure": insecure,
                "allow_custom_urls": policy.allow_custom_urls,
            }
        )
        return "proxies:\n  - name: node-1\n    type: direct\n", {"converted": True}

    monkeypatch.setattr(mihomo, "_mh_hwid_fetch_provider_payload", fake_fetch)

    response = client.get(
        "/mihomo/hwid/provider.yaml?url=https%3A%2F%2Fprovider.example%2Fsub&insecure=1"
    )

    assert response.status_code == 200
    assert response.get_data(as_text=True).startswith("proxies:\n")
    assert calls[0]["url"] == "https://provider.example/sub"
    assert calls[0]["headers"]["x-hwid"] == "AABBCCDDEEFF"
    assert calls[0]["insecure"] is True
    assert calls[0]["allow_custom_urls"] is True

    denied = client.get(
        "/mihomo/hwid/provider.yaml?url=https%3A%2F%2Fprovider.example%2Fsub",
        environ_base={"REMOTE_ADDR": "192.168.1.50"},
    )
    assert denied.status_code == 403


def test_regular_provider_adapter_route_fetches_without_hwid_headers(monkeypatch, client):
    calls = []

    def fake_fetch(url, *, headers, insecure, timeout, policy):
        calls.append(
            {
                "url": url,
                "headers": headers,
                "insecure": insecure,
                "allow_custom_urls": policy.allow_custom_urls,
            }
        )
        return "dmxlc3M6Ly9leGFtcGxl\n", {"format": "raw"}

    monkeypatch.setattr(mihomo, "_mh_hwid_fetch_provider_payload", fake_fetch)

    response = client.get(
        "/mihomo/provider.yaml?url=http%3A%2F%2Fprovider.example%2Fsub&insecure=1"
    )

    assert response.status_code == 200
    assert response.get_data(as_text=True).startswith("dmxlc3M6")
    assert calls[0]["url"] == "http://provider.example/sub"
    assert calls[0]["headers"] == {}
    assert calls[0]["insecure"] is True
    assert calls[0]["allow_custom_urls"] is True

    denied = client.get(
        "/mihomo/provider.yaml?url=https%3A%2F%2Fprovider.example%2Fsub",
        environ_base={"REMOTE_ADDR": "192.168.1.50"},
    )
    assert denied.status_code == 403


def test_regular_provider_probe_fetches_without_hwid_headers(monkeypatch, client):
    calls = []

    def fake_probe(url, *, headers, insecure, timeout, prefer, policy):
        calls.append(
            {
                "url": url,
                "headers": headers,
                "insecure": insecure,
                "prefer": prefer,
                "allow_http": policy.allow_http,
                "allow_custom_urls": policy.allow_custom_urls,
            }
        )
        return {
            "ok": True,
            "probe": {"url": url, "http_status": 200},
            "profile": {
                "profile_title": "Remnawave",
                "profile_title_raw": "base64:UmVtbmF3YXZl",
                "profile_title_encoding": "base64",
                "suggested_name": "Remnawave",
            },
            "headers_used": {},
            "warnings": [],
        }

    monkeypatch.setattr(mihomo, "_mh_hwid_probe_subscription_safe", fake_probe)

    response = client.post(
        "/api/mihomo/provider/probe",
        json={"url": "http://provider.example/sub", "insecure": True},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["profile"]["suggested_name"] == "Remnawave"
    assert payload["provider_url"].startswith("http://127.0.0.1:")
    assert "/mihomo/provider.yaml?" in payload["provider_url"]
    assert calls[0]["url"] == "http://provider.example/sub"
    assert calls[0]["headers"] == {}
    assert calls[0]["insecure"] is True
    assert calls[0]["prefer"] == "head_then_range_get"
    assert calls[0]["allow_http"] is True
    assert calls[0]["allow_custom_urls"] is True
