# Stage 10 closure checklist — final hardening and acceptance

Status: repository implementation and automated acceptance completed 2026-07-16. The remaining real-device rollout is intentionally recorded as an external operational check, not claimed as a local test result.

## Final product boundary

- [x] `Launching -> Connections -> Pair/Login -> Ready` uses persisted connections, encrypted trusted session material and server validation.
- [x] Fresh `Ready` starts with neutral `Unknown` runtime state. It obtains service/core state from `GET /api/xkeen/status` and `GET /api/xkeen/core` through the service port before presenting it as confirmed.
- [x] Reopening or switching a connection clears previous routing metadata. Xray documents load only after the new node confirms Xray availability.
- [x] Missing or failed routing directory reads have a visible loading/retry surface; stale or sample documents are not shown as the new node's configuration.
- [x] Service actions, routing validation/save/apply/conflict and Xray logs/reconnect remain server-backed as specified in stages 5–9.

## Automated acceptance matrix

| Scenario | Android coverage | Backend coverage |
| --- | --- | --- |
| HTTP parsing and typed failure semantics | `CompanionHttpTransportTest`, source/port tests | mobile session/routing contract tests |
| Cold start and trusted restore | `CompanionControllerTest`, `MobileSessionPortTest` | `test_mobile_session_contract.py` |
| Persisted connections and encrypted material | `PersistedConnectionsPortTest`, `SecureSessionMaterialStoreTest` | — |
| Confirmed service/core actions and failure | `WebPanelServiceActionsPortTest`, `CompanionControllerTest` | service-control regression tests |
| Routing validate/save/apply and conflicts | validation/write port and controller tests | mobile routing validate/write contracts |
| Xray log history, reconnect and auth expiry | `LogsTransportTest` | `test_mobile_logs_contract.py` |

## Verification completed 2026-07-16

- [x] `python -m pytest -q` over mobile session/routing/logs contracts, request-size/preflight and service regressions — `58 passed`.
- [x] `python -m ruff check` passes for mobile backend paths and the contract/regression tests.
- [x] `cd android-companion; .\gradlew.bat testDebugUnitTest assembleDebug` — `81` unit tests, `0` failures; debug APK assembled.

## Operational acceptance still required

These steps need a reachable Xkeen node, a backend archive containing stages 7–9 endpoints and the matching APK; they cannot be truthfully completed from the repository alone.

- [ ] Cold start with trusted restore, then server-side session expiry.
- [ ] Offline node and failed service action from a real network/device.
- [ ] Routing `load -> edit -> validate -> save -> apply`, followed by an external revision conflict.
- [ ] Logs history, appended line, temporary offline, `background -> foreground` and reconnect.

Detailed device procedures remain in [stage-5-closure-checklist.md](stage-5-closure-checklist.md), [stage-6-closure-checklist.md](stage-6-closure-checklist.md), [stage-7-closure-checklist.md](stage-7-closure-checklist.md), [stage-8-closure-checklist.md](stage-8-closure-checklist.md) and [stage-9-closure-checklist.md](stage-9-closure-checklist.md).
