from __future__ import annotations

from pathlib import Path

from flask import Flask


def test_extract_device_entries_from_keenetic_device_list():
    from services.xray_device_names import extract_device_entries_from_device_list

    entries = extract_device_entries_from_device_list(
        {
            "host": [
                {"ip": "192.168.1.83", "name": "umar-pc", "mac": "0c:9d:92:85:d6:9d"},
                {"ip": "192.168.1.35", "hostname": "Galaxy-A15 Uma"},
                {"ip": "999.999.999.999", "name": "bad"},
                {"ip6": ["fd00::1"], "name": "v6-device"},
            ]
        }
    )

    assert entries["192.168.1.83"]["name"] == "umar-pc"
    assert entries["192.168.1.83"]["source"] == "router"
    assert entries["192.168.1.35"]["name"] == "Galaxy-A15 Uma"
    assert entries["fd00::1"]["name"] == "v6-device"
    assert "999.999.999.999" not in entries


def test_manual_device_name_overrides_router_name(tmp_path: Path):
    from services.xray_device_names import get_xray_device_names_state, set_manual_device_name

    set_manual_device_name(str(tmp_path), "192.168.1.83:56519", "desktop")
    state = get_xray_device_names_state(
        str(tmp_path),
        router_fetcher=lambda: {"host": [{"ip": "192.168.1.83", "name": "router-name"}]},
    )

    entry = state["device_map"]["192.168.1.83"]
    assert entry["name"] == "desktop"
    assert entry["source"] == "manual"
    assert entry["router_name"] == "router-name"


def test_xray_logs_devices_routes_manage_manual_names(tmp_path: Path, monkeypatch):
    from routes.xray_logs import create_xray_logs_blueprint

    monkeypatch.setattr(
        "services.xray_device_names._fetch_router_device_list",
        lambda timeout=2.0: {"host": [{"ip": "192.168.1.83", "name": "router-name"}]},
    )

    app = Flask(__name__)
    app.register_blueprint(
        create_xray_logs_blueprint(
            ws_debug=lambda *args, **kwargs: None,
            restart_xray_core=lambda: None,
            ui_state_dir=str(tmp_path),
        )
    )
    client = app.test_client()

    res = client.get("/api/xray-logs/devices")
    assert res.status_code == 200
    assert res.get_json()["device_map"]["192.168.1.83"]["name"] == "router-name"

    res = client.post("/api/xray-logs/devices", json={"ip": "192.168.1.83", "name": "manual-name"})
    assert res.status_code == 200
    assert res.get_json()["device_map"]["192.168.1.83"]["name"] == "manual-name"

    res = client.delete("/api/xray-logs/devices/192.168.1.83")
    assert res.status_code == 200
    assert res.get_json()["device_map"]["192.168.1.83"]["name"] == "router-name"
