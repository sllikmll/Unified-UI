from __future__ import annotations

from services import happ_links


def test_helper_command_uses_bundled_helper_when_env_is_missing(monkeypatch):
    monkeypatch.delenv(happ_links.HAPP_HELPER_CMD_ENV, raising=False)

    command = happ_links.helper_command()

    assert "happ_transport_helper.py" in command
    assert "xkeen-ui" in command
    assert happ_links.helper_configured() is True


def test_decryptor_command_is_empty_without_dropin_or_env(monkeypatch):
    monkeypatch.delenv(happ_links.HAPP_DECRYPTOR_CMD_ENV, raising=False)
    monkeypatch.setattr(happ_links, "_bundled_decryptor_command_parts", lambda: [])

    assert happ_links.decryptor_command() == ""
    assert happ_links.decryptor_configured() is False


def test_resolve_source_uses_decryptor_for_raw_happ_link(monkeypatch):
    calls: list[str] = []

    def fake_run_decryptor(value):
        calls.append(value)
        return {"kind": "text", "value": "vless://demo", "headers": {}}

    monkeypatch.setattr(happ_links, "decryptor_configured", lambda: True)
    monkeypatch.setattr(happ_links, "run_decryptor", fake_run_decryptor)
    monkeypatch.setattr(happ_links, "helper_env_configured", lambda: False)

    resolved = happ_links.resolve_source("happ://crypt5/demo-token")

    assert resolved["kind"] == "text"
    assert resolved["via"] == "decryptor"
    assert resolved["candidate"] == "happ://crypt5/demo-token"
    assert calls == ["happ://crypt5/demo-token"]


def test_resolve_source_tries_http_helper_before_happ_deep_link(monkeypatch):
    calls: list[str] = []

    def fake_run_helper(value):
        calls.append(value)
        if value == "https://example.com/sub":
            return {"kind": "text", "value": "vless://demo", "headers": {}}
        raise RuntimeError("unexpected")

    monkeypatch.setattr(happ_links, "helper_configured", lambda: True)
    monkeypatch.setattr(happ_links, "run_helper", fake_run_helper)

    resolved = happ_links.resolve_source(
        "https://example.com/sub",
        body=(
            '<html><body><a href="happ://crypt5/demo-token">Happ</a>'
            '<a href="incy://import/https://example.com/sub">Incy</a></body></html>'
        ),
        content_type="text/html; charset=utf-8",
    )

    assert resolved["kind"] == "text"
    assert resolved["candidate"] == "https://example.com/sub"
    assert calls == ["https://example.com/sub"]


def test_resolve_source_falls_back_to_happ_link_when_http_helper_input_fails(monkeypatch):
    helper_calls: list[str] = []
    decryptor_calls: list[str] = []

    def fake_run_helper(value):
        helper_calls.append(value)
        if value == "https://example.com/sub":
            raise RuntimeError("unsupported")
        raise RuntimeError("unexpected")

    def fake_run_decryptor(value):
        decryptor_calls.append(value)
        if value == "happ://crypt5/demo-token":
            return {"kind": "text", "value": "vless://demo", "headers": {}}
        raise RuntimeError("unexpected")

    monkeypatch.setattr(happ_links, "helper_configured", lambda: True)
    monkeypatch.setattr(happ_links, "decryptor_configured", lambda: True)
    monkeypatch.setattr(happ_links, "run_helper", fake_run_helper)
    monkeypatch.setattr(happ_links, "run_decryptor", fake_run_decryptor)

    resolved = happ_links.resolve_source(
        "https://example.com/sub",
        body=(
            '<html><body><a href="happ://crypt5/demo-token">Happ</a>'
            '<a href="incy://import/https://example.com/sub">Incy</a></body></html>'
        ),
        content_type="text/html; charset=utf-8",
    )

    assert resolved["kind"] == "text"
    assert resolved["candidate"] == "happ://crypt5/demo-token"
    assert resolved["via"] == "decryptor"
    assert helper_calls == ["https://example.com/sub"]
    assert decryptor_calls == ["happ://crypt5/demo-token"]
