from pathlib import Path


def test_happ_helper_env_keys_are_exposed_in_devtools():
    env_py = Path("unified-ui/services/devtools/env.py").read_text(encoding="utf-8")
    env_js = Path("unified-ui/static/js/features/devtools/env.js").read_text(encoding="utf-8")

    for key in (
        "UNIFIED_HAPP_HELPER_CMD",
        "UNIFIED_HAPP_DECRYPTOR_CMD",
        "UNIFIED_HAPP_DECRYPTOR_REMOTE_URL",
        "UNIFIED_HAPP_HELPER_TIMEOUT",
        "UNIFIED_HAPP_DECRYPTOR_TIMEOUT",
        "UNIFIED_HAPP_HELPER_HWID",
        "UNIFIED_SUBSCRIPTION_HAPP_USER_AGENT",
    ):
        assert f'"{key}"' in env_py
        assert f"ENV_HELP.{key}" in env_js
        assert f"ENV_NO_RESTART_KEYS.add('{key}')" in env_js


def test_happ_helper_env_keys_are_grouped_under_mihomo_hwid():
    env_js = Path("unified-ui/static/js/features/devtools/env.js").read_text(encoding="utf-8")

    assert "title: 'Mihomo и HWID'" in env_js
    assert "'UNIFIED_HAPP_HELPER_CMD'" in env_js
    assert "'UNIFIED_HAPP_DECRYPTOR_CMD'" in env_js
    assert "'UNIFIED_HAPP_DECRYPTOR_REMOTE_URL'" in env_js
    assert "'UNIFIED_HAPP_HELPER_TIMEOUT'" in env_js
    assert "'UNIFIED_HAPP_DECRYPTOR_TIMEOUT'" in env_js
    assert "'UNIFIED_HAPP_HELPER_HWID'" in env_js
    assert "'UNIFIED_SUBSCRIPTION_HAPP_USER_AGENT'" in env_js
