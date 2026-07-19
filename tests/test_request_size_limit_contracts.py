from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_devtools_env_exposes_request_size_limit_knobs():
    env_py = (ROOT / "unified-ui" / "services" / "devtools" / "env.py").read_text(encoding="utf-8")
    env_js = (ROOT / "unified-ui" / "static" / "js" / "features" / "devtools" / "env.js").read_text(encoding="utf-8")
    app_factory = (ROOT / "unified-ui" / "app_factory.py").read_text(encoding="utf-8")
    geodat_py = (ROOT / "unified-ui" / "routes" / "routing" / "geodat.py").read_text(encoding="utf-8")

    assert '"UNIFIED_UI_MAX_CONTENT_LENGTH"' in env_py
    assert '"UNIFIED_JSON_BODY_MAX_BYTES"' in env_py
    assert '"UNIFIED_JSON_HEAVY_MAX_BYTES"' in env_py
    assert '"UNIFIED_MIHOMO_JSON_MAX_BYTES"' in env_py
    assert '"UNIFIED_GEODAT_UPLOAD_MAX_BYTES"' in env_py
    assert '"UNIFIED_ROUTING_SAVE_MAX_BYTES"' in env_py
    assert '"UNIFIED_CONFIG_EXCHANGE_MAX_BYTES"' in env_py
    assert "ENV_HELP.UNIFIED_UI_MAX_CONTENT_LENGTH" in env_js
    assert "ENV_HELP.UNIFIED_JSON_BODY_MAX_BYTES" in env_js
    assert "ENV_HELP.UNIFIED_JSON_HEAVY_MAX_BYTES" in env_js
    assert "ENV_HELP.UNIFIED_MIHOMO_JSON_MAX_BYTES" in env_js
    assert "ENV_HELP.UNIFIED_GEODAT_UPLOAD_MAX_BYTES" in env_js
    assert 'if k == "UNIFIED_ROUTING_SAVE_MAX_BYTES":' in env_py
    assert 'if k == "UNIFIED_CONFIG_EXCHANGE_MAX_BYTES":' in env_py
    assert "ENV_HELP.UNIFIED_ROUTING_SAVE_MAX_BYTES" in env_js
    assert "ENV_HELP.UNIFIED_CONFIG_EXCHANGE_MAX_BYTES" in env_js
    assert "install_request_size_guards(app)" in app_factory
    assert "read_uploaded_file_bytes_limited" in geodat_py
    assert "get_geodat_upload_max_bytes" in geodat_py
    assert "ENV_NO_RESTART_KEYS.add('UNIFIED_ROUTING_SAVE_MAX_BYTES')" in env_js
    assert "ENV_NO_RESTART_KEYS.add('UNIFIED_CONFIG_EXCHANGE_MAX_BYTES')" in env_js
    assert "ENV_NO_RESTART_KEYS.add('UNIFIED_UI_MAX_CONTENT_LENGTH')" in env_js
    assert "ENV_NO_RESTART_KEYS.add('UNIFIED_JSON_BODY_MAX_BYTES')" in env_js


def test_routing_and_config_exchange_use_streaming_request_limit_helpers():
    routing_py = (ROOT / "unified-ui" / "routes" / "routing" / "config.py").read_text(encoding="utf-8")
    exchange_py = (ROOT / "unified-ui" / "routes" / "config_exchange.py").read_text(encoding="utf-8")
    limits_py = (ROOT / "unified-ui" / "services" / "request_limits.py").read_text(encoding="utf-8")

    assert "read_request_bytes_limited" in routing_py
    assert '"payload too large", "max_bytes": max_bytes' in routing_py
    assert "read_uploaded_file_bytes_limited" in exchange_py
    assert "read_request_json_limited" in exchange_py
    assert '_api_error("payload too large", 413, ok=False, max_bytes=max_bytes)' in exchange_py
    assert "classify_json_request_max_bytes" in limits_py
    assert "get_filemanager_upload_max_bytes" in limits_py
    assert "_is_filemanager_upload_path" in limits_py
    assert "install_request_size_guards" in limits_py
