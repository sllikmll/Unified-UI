"""Versioned session contract for the native mobile companion.

The browser UI keeps its existing auth routes and Flask session model.  This
module gives native clients a small, explicit envelope around that model so
they do not need to parse HTML login/setup pages or emulate browser forms.
"""

from __future__ import annotations

from flask import Flask, jsonify, request, session
from werkzeug.security import check_password_hash

from services.auth_rate_limit import (
    clear_login_rate_limit,
    format_lockout_wait,
    get_login_rate_limit_status,
    register_login_failure,
)
from services.auth_setup import (
    _auth_load,
    _ensure_csrf_token,
    _is_logged_in,
    auth_is_configured,
)


MOBILE_API_PREFIX = "/api/mobile/v1"


def register_mobile_routes(app: Flask) -> None:
    """Register the stable mobile session bootstrap/login/logout endpoints."""

    def response(data: dict, status: int = 200):
        result = jsonify({"ok": True, "data": data})
        result.status_code = status
        result.headers["Cache-Control"] = "no-store"
        return result

    def error(code: str, message: str, status: int, **details):
        result = jsonify(
            {
                "ok": False,
                "error": {
                    "code": code,
                    "message": message,
                    **details,
                },
            }
        )
        result.status_code = status
        result.headers["Cache-Control"] = "no-store"
        return result

    def rate_limit_view(remote_addr: str | None) -> dict:
        current = get_login_rate_limit_status(remote_addr)
        return {
            "enabled": bool(current.get("enabled")),
            "window_seconds": int(current.get("window_seconds") or 0),
            "max_attempts": int(current.get("max_attempts") or 0),
            "failures": int(current.get("failures") or 0),
            "attempts_left": int(current.get("attempts_left") or 0),
            "locked": bool(current.get("locked")),
            "retry_after": int(current.get("retry_after") or 0),
        }

    def invalid_credentials_message(rate: dict) -> str:
        attempts_left = int(rate.get("attempts_left") or 0)
        if attempts_left > 0:
            return f"Неверный логин или пароль. Осталось попыток: {attempts_left}."
        return "Неверный логин или пароль."

    def locked_message(rate: dict) -> str:
        return "Слишком много неудачных попыток входа. Повторите через " + format_lockout_wait(
            rate.get("retry_after") or 0
        ) + "."

    @app.get(f"{MOBILE_API_PREFIX}/bootstrap")
    def mobile_bootstrap():
        configured = auth_is_configured()
        authenticated = configured and _is_logged_in()
        return response(
            {
                "contract_version": 1,
                "auth": {
                    "configured": configured,
                    "authenticated": authenticated,
                    "user": session.get("user") if authenticated else None,
                },
            }
        )

    @app.post(f"{MOBILE_API_PREFIX}/session")
    def mobile_session_login():
        if not auth_is_configured():
            return error(
                "not_configured",
                "На Xkeen UI нужно завершить начальную настройку.",
                428,
            )

        data = request.get_json(silent=True) or {}
        username = str(data.get("username") or "").strip()
        password = str(data.get("password") or "")
        if not username or not password:
            return error("invalid_credentials", "Введите логин и пароль.", 400)

        rate = rate_limit_view(request.remote_addr)
        if rate["locked"]:
            retry_after = rate["retry_after"]
            result = error(
                "login_locked",
                locked_message(rate),
                429,
                rate_limit=rate,
                retry_after=retry_after,
            )
            if retry_after > 0:
                result.headers["Retry-After"] = str(retry_after)
            return result

        record = _auth_load() or {}
        authenticated = False
        try:
            authenticated = username == (record.get("username") or "") and check_password_hash(
                record.get("password_hash") or "",
                password,
            )
        except Exception:
            authenticated = False

        if not authenticated:
            rate = register_login_failure(request.remote_addr)
            if rate.get("locked"):
                retry_after = int(rate.get("retry_after") or 0)
                result = error(
                    "login_locked",
                    locked_message(rate),
                    429,
                    rate_limit=rate_limit_view(request.remote_addr),
                    retry_after=retry_after,
                )
                if retry_after > 0:
                    result.headers["Retry-After"] = str(retry_after)
                return result
            return error(
                "invalid_credentials",
                invalid_credentials_message(rate),
                401,
                rate_limit=rate_limit_view(request.remote_addr),
            )

        clear_login_rate_limit(request.remote_addr)
        session.clear()
        csrf_token = _ensure_csrf_token()
        session["auth"] = True
        session["user"] = username
        return response(
            {
                "session": {
                    "user": username,
                    "csrf_token": csrf_token,
                },
            }
        )

    @app.delete(f"{MOBILE_API_PREFIX}/session")
    def mobile_session_logout():
        # Authentication and CSRF have already been enforced by _auth_guard.
        session.clear()
        return response({"session": {"closed": True}})
