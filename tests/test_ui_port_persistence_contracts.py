from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_devtools_env_exposes_ui_port_as_restart_bound_setting():
    env_py = (ROOT / "unified-ui" / "services" / "devtools" / "env.py").read_text(encoding="utf-8")
    env_js = (ROOT / "unified-ui" / "static" / "js" / "features" / "devtools" / "env.js").read_text(encoding="utf-8")

    assert '"UNIFIED_UI_PORT"' in env_py
    assert 'if k == "UNIFIED_UI_PORT":' in env_py
    assert 'return "8088"' in env_py
    assert "UNIFIED_UI_PORT': 'Порт веб-панели Unified UI." in env_js
    assert "const ENV_RESTART_KEYS = new Set([" in env_js
    assert "    'UNIFIED_UI_PORT'," in env_js


def test_install_script_preserves_and_persists_panel_port_via_env_file():
    text = (ROOT / "unified-ui" / "install.sh").read_text(encoding="utf-8")

    assert 'EXISTING_ENV_FILE="$UI_DIR/devtools.env"' in text
    assert 'extract_env_numeric_field() {' in text
    assert 'extract_run_server_port() {' in text
    assert 'EXISTING_PORT="$(extract_env_numeric_field "UNIFIED_UI_PORT" "$EXISTING_ENV_FILE")"' in text
    assert 'EXISTING_PORT="$(extract_run_server_port "$EXISTING_RUN")"' in text
    assert 'write_env_numeric_field "$EXISTING_ENV_FILE" "UNIFIED_UI_PORT" "$PANEL_PORT"' in text
    assert 'export UNIFIED_UI_PORT="${UNIFIED_UI_PORT:-$PANEL_PORT}"' in text
    assert 'PANEL_PORT="__UNIFIED_UI_PORT__"' in text
    assert 'sed -i -E "s/__UNIFIED_UI_PORT__/${PANEL_PORT}/g" "$INIT_SCRIPT" || true' in text
