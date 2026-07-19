import importlib
import json
import sys
from pathlib import Path


def _reload(name: str):
    if name in sys.modules:
        return importlib.reload(sys.modules[name])
    return importlib.import_module(name)


def test_auth_setup_migrates_legacy_auth_and_secret_to_persistent_state(tmp_path, monkeypatch):
    legacy = tmp_path / "legacy-ui-dir"
    persistent = tmp_path / "persistent-auth"
    legacy.mkdir()
    legacy_auth = {
        "version": 1,
        "created_at": 123,
        "username": "pavel",
        "password_hash": "hash-value",
    }
    (legacy / "auth.json").write_text(json.dumps(legacy_auth) + "\n", encoding="utf-8")
    (legacy / "secret.key").write_text("legacy-secret\n", encoding="utf-8")

    monkeypatch.setenv("XKEEN_UI_STATE_DIR", str(legacy))
    monkeypatch.setenv("XKEEN_AUTH_STATE_DIR", str(persistent))
    monkeypatch.delenv("XKEEN_UI_SECRET_KEY", raising=False)

    _reload("core.paths")
    auth_setup = _reload("services.auth_setup")

    assert auth_setup.AUTH_FILE == str(persistent / "auth.json")
    assert auth_setup.SECRET_KEY_FILE == str(persistent / "secret.key")
    assert auth_setup.auth_is_configured() is True
    assert auth_setup._load_or_create_secret_key() == "legacy-secret"
    assert json.loads((persistent / "auth.json").read_text(encoding="utf-8"))["username"] == "pavel"
    assert (persistent / "secret.key").read_text(encoding="utf-8").strip() == "legacy-secret"
