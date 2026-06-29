"""Helpers for Happ deep-link/landing-page resolution via external decryptor."""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from typing import Any, Dict, List
from urllib.parse import urlparse
from pathlib import Path


HAPP_HELPER_CMD_ENV = "XKEEN_HAPP_HELPER_CMD"
HAPP_DECRYPTOR_CMD_ENV = "XKEEN_HAPP_DECRYPTOR_CMD"
HAPP_HELPER_TIMEOUT_ENV = "XKEEN_HAPP_HELPER_TIMEOUT"
HAPP_RESOLVED_HEADER = "x-xkeen-happ-resolved"
HAPP_LINK_HEADER = "x-xkeen-happ-link"
HAPP_ERROR_HEADER = "x-xkeen-happ-error"

_DEFAULT_TIMEOUT_SECONDS = 15.0
_MAX_TIMEOUT_SECONDS = 120.0
_HTML_LANDING_RE = re.compile(r"(?is)^\s*(?:<!doctype html|<html\b)")
_HAPP_LINK_RE = re.compile(r"(?i)\bhapp://crypt[0-9]*/[^\s\"'<>]+")
_INCY_IMPORT_RE = re.compile(r"(?i)\bincy://import/([^\s\"'<>]+)")
_RESULT_HEADER_RE = re.compile(r"(?i)^result\s*:?\s*$")
_SUPPORTED_TEXT_SCHEMES = (
    "http://",
    "https://",
    "vless://",
    "vmess://",
    "trojan://",
    "ss://",
    "shadowsocks://",
    "hy2://",
    "hysteria2://",
    "hysteria://",
    "tuic://",
    "wireguard://",
)
_DECRYPTOR_DROPIN_NAMES = (
    "happ_decryptor.py",
    "happ-decryptor.py",
    "happ_decrypt_universal.py",
    "happ-decrypt-universal.py",
    "happwner.py",
    "Happwner.py",
    "happ_decryptor",
    "happ-decryptor",
    "happ_decrypt_universal",
    "happ-decrypt-universal",
    "happwner",
)


def _is_http_url(value: Any) -> bool:
    scheme = urlparse(str(value or "").strip()).scheme.lower()
    return scheme in {"http", "https"}


def _bundled_helper_script_path() -> str:
    try:
        here = Path(__file__).resolve()
        candidates = (
            here.parents[1] / "scripts" / "happ_transport_helper.py",
            here.parents[2] / "scripts" / "happ_transport_helper.py",
        )
        for script in candidates:
            if script.is_file():
                return str(script)
    except Exception:
        pass
    return ""


def _command_parts_from_path(path: str) -> List[str]:
    script = str(path or "").strip()
    if not script:
        return []
    exe = str(sys.executable or "").strip()
    suffix = Path(script).suffix.lower()
    if suffix == ".py":
        if not exe:
            exe = str(shutil.which("python3") or shutil.which("python") or "").strip()
        if not exe:
            return []
        return [exe, script]
    return [script]


def _bundled_helper_command_parts() -> List[str]:
    return _command_parts_from_path(_bundled_helper_script_path())


def _bundled_decryptor_command_parts() -> List[str]:
    try:
        here = Path(__file__).resolve()
        roots = (
            here.parents[1],
            here.parents[2],
        )
        for root in roots:
            for relative_dir in ("bin", "scripts"):
                base = root / relative_dir
                if not base.is_dir():
                    continue
                for name in _DECRYPTOR_DROPIN_NAMES:
                    candidate = base / name
                    if candidate.is_file():
                        parts = _command_parts_from_path(str(candidate))
                        if parts:
                            return parts
    except Exception:
        pass
    return []


def helper_env_configured() -> bool:
    return bool(str(os.environ.get(HAPP_HELPER_CMD_ENV) or "").strip())


def helper_command_parts() -> List[str]:
    raw = str(os.environ.get(HAPP_HELPER_CMD_ENV) or "").strip()
    if raw:
        return _parse_command(raw)
    return _bundled_helper_command_parts()


def decryptor_command_parts() -> List[str]:
    raw = str(os.environ.get(HAPP_DECRYPTOR_CMD_ENV) or "").strip()
    if raw:
        return _parse_command(raw)
    return _bundled_decryptor_command_parts()


def _format_command_parts(parts: List[str], *, include_placeholder: bool = False) -> str:
    out = list(parts or [])
    if not out:
        return ""
    if include_placeholder:
        out.append("%LINK%")
    if os.name == "nt":
        return subprocess.list2cmdline(out)
    try:
        return shlex.join(out)
    except Exception:
        return " ".join(out)


def helper_command() -> str:
    raw = str(os.environ.get(HAPP_HELPER_CMD_ENV) or "").strip()
    if raw:
        return raw
    return _format_command_parts(_bundled_helper_command_parts(), include_placeholder=True)


def decryptor_command() -> str:
    raw = str(os.environ.get(HAPP_DECRYPTOR_CMD_ENV) or "").strip()
    if raw:
        return raw
    return _format_command_parts(_bundled_decryptor_command_parts(), include_placeholder=True)


def helper_configured() -> bool:
    return bool(helper_command_parts())


def decryptor_configured() -> bool:
    return bool(decryptor_command_parts())


def helper_timeout_seconds() -> float:
    raw = str(os.environ.get(HAPP_HELPER_TIMEOUT_ENV) or "").strip()
    if not raw:
        return _DEFAULT_TIMEOUT_SECONDS
    try:
        timeout = float(raw)
    except Exception:
        timeout = _DEFAULT_TIMEOUT_SECONDS
    return max(1.0, min(_MAX_TIMEOUT_SECONDS, timeout))


def is_happ_deep_link(value: Any) -> bool:
    return str(value or "").strip().lower().startswith("happ://crypt")


def looks_like_html_landing(text: Any, *, content_type: Any = None) -> bool:
    body = str(text or "")
    ctype = str(content_type or "").strip().lower()
    return "text/html" in ctype or bool(_HTML_LANDING_RE.match(body.lstrip("\ufeff\r\n\t ")))


def extract_happ_links(text: Any) -> List[str]:
    body = str(text or "")
    out: List[str] = []
    seen: set[str] = set()
    for match in _HAPP_LINK_RE.finditer(body):
        link = str(match.group(0) or "").strip()
        if link and link not in seen:
            seen.add(link)
            out.append(link)
    return out


def extract_incy_import_urls(text: Any) -> List[str]:
    body = str(text or "")
    out: List[str] = []
    seen: set[str] = set()
    for match in _INCY_IMPORT_RE.finditer(body):
        value = str(match.group(1) or "").strip()
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def _parse_command(cmd: str) -> List[str]:
    raw = str(cmd or "").strip()
    if not raw:
        return []
    try:
        return shlex.split(raw, posix=(os.name != "nt"))
    except Exception:
        return [raw]


def _command_with_link(parts: List[str], link: str) -> List[str]:
    out: List[str] = []
    replaced = False
    for part in parts:
        next_part = str(part or "")
        if next_part in {"%LINK%", "{link}", "{input}"}:
            out.append(link)
            replaced = True
            continue
        patched = next_part
        for token in ("%LINK%", "{link}", "{input}"):
            if token in patched:
                patched = patched.replace(token, link)
                replaced = True
        out.append(patched)
    if not replaced:
        out.append(link)
    return out


def _json_helper_value(obj: Any) -> Dict[str, Any] | None:
    if isinstance(obj, dict):
        headers = obj.get("headers") if isinstance(obj.get("headers"), dict) else {}
        for key in ("url", "uri", "link"):
            value = str(obj.get(key) or "").strip()
            if value:
                return {"kind": "url", "value": value, "headers": headers}
        for key in ("text", "body", "payload", "result", "output", "decrypted"):
            value = obj.get(key)
            if value is None:
                continue
            value_text = str(value).strip()
            if value_text:
                nested = _normalize_helper_output(value_text)
                if nested:
                    if headers and not nested.get("headers"):
                        nested["headers"] = headers
                    return nested
    elif isinstance(obj, str) and obj.strip():
        return _normalize_helper_output(obj)
    return None


def _extract_result_block(text: str) -> str:
    lines = str(text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if not _RESULT_HEADER_RE.match(stripped):
            continue
        collected: List[str] = []
        for candidate in lines[idx + 1 :]:
            if not candidate.strip():
                if collected:
                    break
                continue
            if not candidate.startswith((" ", "\t")) and collected:
                break
            collected.append(candidate.strip())
        if collected:
            return "\n".join(collected).strip()
    return ""


def _normalize_helper_output(text: Any) -> Dict[str, Any] | None:
    raw = str(text or "").strip()
    if not raw:
        return None

    try:
        data = json.loads(raw)
    except Exception:
        data = None
    parsed = _json_helper_value(data)
    if parsed:
        return parsed

    result_block = _extract_result_block(raw)
    if result_block and result_block != raw:
        parsed = _normalize_helper_output(result_block)
        if parsed:
            return parsed

    lines = [line.strip() for line in raw.replace("\r", "\n").split("\n") if line.strip()]
    if len(lines) == 1:
        line = lines[0]
        lowered = line.lower()
        if lowered.startswith("incy://import/"):
            return {"kind": "url", "value": line[len("incy://import/") :].strip(), "headers": {}}
        if any(lowered.startswith(prefix) for prefix in _SUPPORTED_TEXT_SCHEMES):
            return {"kind": "url", "value": line, "headers": {}}
    return {"kind": "text", "value": raw, "headers": {}}


def _run_command(parts: List[str], link: str, *, error_prefix: str) -> Dict[str, Any]:
    if not str(link or "").strip():
        raise RuntimeError(f"{error_prefix}invalid_input")
    if not parts:
        raise RuntimeError(f"{error_prefix}not_configured")

    command = _command_with_link(parts, str(link).strip())
    timeout = helper_timeout_seconds()
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"{error_prefix}missing:" + str(exc)) from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"{error_prefix}timeout") from exc
    except Exception as exc:
        raise RuntimeError(f"{error_prefix}failed:" + str(exc)) from exc

    stdout = str(completed.stdout or "").strip()
    stderr = str(completed.stderr or "").strip()
    if completed.returncode != 0:
        detail = stderr or stdout or f"exit_{completed.returncode}"
        raise RuntimeError(f"{error_prefix}failed:" + detail[:240])
    if not stdout:
        raise RuntimeError(f"{error_prefix}empty")

    parsed = _normalize_helper_output(stdout)
    if not parsed:
        raise RuntimeError(f"{error_prefix}unparsed_output")
    parsed["helper_stdout"] = stdout
    return parsed


def run_helper(link: str) -> Dict[str, Any]:
    return _run_command(helper_command_parts(), link, error_prefix="happ_helper_")


def run_decryptor(link: str) -> Dict[str, Any]:
    return _run_command(decryptor_command_parts(), link, error_prefix="happ_decryptor_")


def _resolve_candidates(
    candidates: List[str],
    runner,
    *,
    via: str,
) -> tuple[Dict[str, Any] | None, RuntimeError | None]:
    seen: set[str] = set()
    last_error: RuntimeError | None = None
    for candidate in candidates:
        candidate_s = str(candidate or "").strip()
        if not candidate_s or candidate_s in seen:
            continue
        seen.add(candidate_s)
        try:
            parsed = runner(candidate_s)
        except RuntimeError as exc:
            last_error = exc
            continue
        parsed["via"] = via
        parsed["candidate"] = candidate_s
        return parsed, None
    return None, last_error


def resolve_source(url: str, *, body: Any = None, content_type: Any = None) -> Dict[str, Any] | None:
    raw_url = str(url or "").strip()
    if not raw_url and body is None:
        return None

    candidates: List[str] = []
    helper_inputs: List[str] = []
    incy_targets: List[str] = []
    if is_happ_deep_link(raw_url):
        candidates.append(raw_url)
    else:
        links = extract_happ_links(body)
        incy_targets = extract_incy_import_urls(body)
        if _is_http_url(raw_url):
            helper_inputs.append(raw_url)
        for target in incy_targets:
            if _is_http_url(target):
                helper_inputs.append(target.strip())
        if links:
            candidates.extend(links)
        elif incy_targets:
            for target in incy_targets:
                if _is_http_url(target) and target.strip() != raw_url:
                    return {
                        "kind": "url",
                        "value": target.strip(),
                        "headers": {},
                        "via": "incy-import",
                        "candidate": target.strip(),
                    }

    last_error: RuntimeError | None = None

    if helper_inputs and helper_configured():
        parsed, last_error = _resolve_candidates(helper_inputs, run_helper, via="helper")
        if parsed:
            return parsed

    if candidates and decryptor_configured():
        parsed, last_error = _resolve_candidates(candidates, run_decryptor, via="decryptor")
        if parsed:
            return parsed

    if candidates and helper_env_configured():
        parsed, last_error = _resolve_candidates(candidates, run_helper, via="helper")
        if parsed:
            return parsed

    if last_error is not None and candidates:
        raise last_error

    if not candidates:
        return None

    if is_happ_deep_link(candidates[0]):
        if decryptor_configured():
            parsed = run_decryptor(candidates[0])
            parsed["via"] = "decryptor"
            parsed["candidate"] = candidates[0]
            return parsed
        if helper_env_configured():
            parsed = run_helper(candidates[0])
            parsed["via"] = "helper"
            parsed["candidate"] = candidates[0]
            return parsed
        raise RuntimeError("happ_decryptor_not_configured")

    if helper_configured():
        parsed = run_helper(candidates[0])
        parsed["via"] = "helper"
        parsed["candidate"] = candidates[0]
        return parsed

    return None
