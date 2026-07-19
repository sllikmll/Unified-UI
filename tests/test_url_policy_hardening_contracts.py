from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_devtools_env_exposes_url_policy_knobs_for_dat_and_geodat():
    env_py = (ROOT / "unified-ui" / "services" / "devtools" / "env.py").read_text(encoding="utf-8")
    env_js = (ROOT / "unified-ui" / "static" / "js" / "features" / "devtools" / "env.js").read_text(encoding="utf-8")

    for key in (
        "UNIFIED_DAT_ALLOW_HOSTS",
        "UNIFIED_DAT_ALLOW_HTTP",
        "UNIFIED_DAT_ALLOW_CUSTOM_URLS",
        "UNIFIED_DAT_ALLOW_PRIVATE_HOSTS",
        "UNIFIED_GEODAT_ALLOW_HOSTS",
        "UNIFIED_GEODAT_ALLOW_HTTP",
        "UNIFIED_GEODAT_ALLOW_CUSTOM_URLS",
        "UNIFIED_GEODAT_ALLOW_PRIVATE_HOSTS",
    ):
        assert f'"{key}"' in env_py
        assert f"ENV_HELP.{key}" in env_js
        assert f"ENV_NO_RESTART_KEYS.add('{key}')" in env_js


def test_geodat_and_dat_routes_use_shared_url_policy_and_safe_downloads():
    geodat_py = (ROOT / "unified-ui" / "routes" / "routing" / "geodat.py").read_text(encoding="utf-8")
    dat_py = (ROOT / "unified-ui" / "routes" / "routing" / "dat.py").read_text(encoding="utf-8")
    policy_py = (ROOT / "unified-ui" / "services" / "url_policy.py").read_text(encoding="utf-8")

    assert "get_policy_from_env(\"UNIFIED_GEODAT\")" in geodat_py
    assert "download_to_file_with_policy(" in geodat_py
    assert "UNIFIED_GEODAT_URL" not in geodat_py

    assert "get_policy_from_env(\"UNIFIED_DAT\")" in dat_py
    assert "download_to_file_with_policy(" in dat_py
    assert "_dat_url_block_response" in dat_py

    assert "class SafeRedirect" in policy_py
    assert "url_blocked:" in policy_py
    assert "release-assets.githubusercontent.com" in policy_py
