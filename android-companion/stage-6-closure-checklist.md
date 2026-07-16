# Закрытие этапа 6: backend-backed service actions и core switch

Status: completed 2026-07-16
Updated: 2026-07-16

Этот документ фиксирует приемку этапа 6 из [next-practical-step-plan.md](next-practical-step-plan.md). Production Android flow больше не использует локальное предположение об успехе service/core action: POST и последующий server snapshot являются одной операцией.

## Граница этапа

Этап переиспользует существующие browser-compatible service endpoint'ы Xkeen UI и cookie+CSRF сессию этапа 5. Отдельный агрегированный `/api/mobile/v1` ready/actions envelope и `operation_id` для долгих операций остаются будущим backend-hardening; Android изолирует текущую совместимость внутри `WebPanelServiceActionsPort`.

| Действие | Write endpoint | Обязательное подтверждение |
| --- | --- | --- |
| Start | `POST /api/xkeen/start` | `GET /api/xkeen/status` возвращает `running` |
| Stop | `POST /api/xkeen/stop` | `GET /api/xkeen/status` возвращает `stopped` |
| Restart | `POST /api/restart` | POST принят и последующий status возвращает `running` |
| Core switch | `POST /api/xkeen/core` с `{ "core": ... }` | status возвращает `running`, а runtime/config core reread совпадает с выбранным ядром |

После каждого принятого write также читается `GET /api/xkeen/core`, поэтому `activeCore` и `availableCores` не вычисляются из нажатой кнопки. На write failure controller по возможности перечитывает тот же snapshot для актуализации dashboard, но исходная операция остаётся `Failure`.

## Action lifecycle

```text
confirm / core apply
  -> Pending + repeat guard
  -> authenticated POST
  -> GET /api/xkeen/status
  -> GET /api/xkeen/core
       ├─ ожидаемое состояние совпало -> Success + dashboard/core/events/log
       ├─ состояние не совпало ------> Failure + явная диагностика
       └─ 401 -----------------------> clear session material -> Pair/Login
```

- `ServiceOperationState` хранит `Idle`, `Pending`, `Success`, `Failure`, action/target и user-facing message.
- Header actions, dashboard actions, core selector и повторный confirm не запускают вторую операцию, пока первая находится в `Pending`.
- Confirm dialog вызывает suspend-operation из Compose coroutine; core dialog остаётся открытым на pending/failure и закрывается только после подтверждённого success.
- Глобальная result surface показывает progress, success или failure независимо от текущего workspace section; failure также попадает в dashboard `lastError`, diagnostics и `LogsPort`.
- Для долгого synchronous core switch production composition использует отдельный action transport с `readTimeoutMillis = 90_000`; timeout обычных read/session запросов не увеличен.

## Checklist закрытия

- [x] Production dependency composition использует `WebPanelServiceActionsPort`, а не `DemoServiceActionsPort`.
- [x] `start`, `stop`, `restart` и core switch отправляют реальные authenticated/CSRF-protected POST-запросы.
- [x] POST response с `ok != true`, malformed payload, HTTP/transport failure и mismatch подтверждённого runtime state не превращаются в success.
- [x] Dashboard service state, active core и available cores после операции приходят из server reread.
- [x] Есть явные `Pending`, `Success`, `Failure` и защита от повторных действий во всех service/core entry points.
- [x] `401` сохраняет общий этапу 5 contract: выбранная сессия очищается, приложение возвращается в `Pair/Login`.
- [x] Unit tests покрывают endpoint/payload mapping, status parsing, mismatch, pending/repeat guard, success/failure и server-backed state refresh.
- [x] Обязательная Android verification `testDebugUnitTest assembleDebug` проходит.
- [x] Релевантные backend service-control tests проходят без регрессий.

## Команды проверки

```powershell
python -m pytest -q tests/test_xkeen_service_control_fallback.py tests/test_exception_detail_sanitization.py
cd android-companion
.\gradlew.bat testDebugUnitTest assembleDebug
```

## Минимальная ручная приемка на реальном узле

1. Нажать `Start`, `Stop` и `Restart`, подтвердить dialog и убедиться, что до server reread показывается progress, а повторные кнопки недоступны.
2. Для каждой операции сверить итоговый chip/status с `/api/xkeen/status`; success не должен появляться при отклонённом POST или несовпавшем runtime state.
3. Переключить Xray/Mihomo: core dialog должен ждать backend и закрыться только после того, как reread подтвердил выбранное работающее ядро.
4. Имитировать backend failure/offline и проверить глобальную error surface, dashboard `lastError`, diagnostic и log entry.
5. Удалить/просрочить server session перед действием: `401` должен вернуть приложение в `Pair/Login` и очистить material только выбранного connection.

Ручная проверка зависит от доступного Xkeen-узла и не подменяется unit/build verification; список выше является device acceptance для релизного прогона.
