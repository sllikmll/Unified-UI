from __future__ import annotations

import services.xray as xray_svc


def _install(monkeypatch, *, running, control_result):
    """Patch services.xray so restart_xray_core runs against fakes.

    Returns a state dict recording the control action(s) requested.
    """
    state = {"control_calls": []}

    monkeypatch.setattr(xray_svc, "_pidof", lambda name: [111] if running else [])

    def fake_control(action, **kwargs):
        state["control_calls"].append((action, kwargs))
        return control_result

    monkeypatch.setattr(xray_svc, "control_xkeen_action", fake_control)
    return state


def test_restart_running_core_delegates_to_verified_control(monkeypatch):
    state = _install(monkeypatch, running=True, control_result=True)

    ok, detail = xray_svc.restart_xray_core()

    assert ok is True
    assert detail == "restarted"
    # Must go through the verified stop+start path, not a raw kill.
    assert len(state["control_calls"]) == 1
    action, kwargs = state["control_calls"][0]
    assert action == "restart"
    assert kwargs.get("prefer_init") is True


def test_stopped_core_is_refused_by_default(monkeypatch):
    state = _install(monkeypatch, running=False, control_result=True)

    ok, detail = xray_svc.restart_xray_core()

    assert ok is False
    assert detail == "xray not running"
    # A core stopped on purpose must not be touched.
    assert state["control_calls"] == []


def test_stopped_core_is_started_when_requested(monkeypatch):
    state = _install(monkeypatch, running=False, control_result=True)

    ok, detail = xray_svc.restart_xray_core(start_if_stopped=True)

    assert ok is True
    assert detail == "started"
    assert len(state["control_calls"]) == 1
    assert state["control_calls"][0][0] == "restart"


def test_restart_reports_failure_when_core_does_not_come_back(monkeypatch):
    _install(monkeypatch, running=True, control_result=False)

    ok, detail = xray_svc.restart_xray_core()

    assert ok is False
    assert detail == "xray did not start"


def test_enable_logs_forwards_start_if_stopped(monkeypatch):
    from services import xray_log_api

    calls = []

    def spy_restart(**kwargs):
        calls.append(kwargs)
        return True, "started"

    ok, detail = xray_log_api._call_restart(spy_restart, start_if_stopped=True)

    assert ok is True
    assert calls == [{"start_if_stopped": True}]


def test_call_restart_falls_back_for_zero_arg_callable():
    from services import xray_log_api

    # Older wrappers / test stubs may expose a zero-arg callable.
    ok, detail = xray_log_api._call_restart(lambda: (True, "restarted"), start_if_stopped=True)

    assert ok is True
    assert detail == "restarted"
