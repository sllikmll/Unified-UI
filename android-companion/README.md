# Xkeen Mobile Companion

Стартовый Android skeleton для companion-приложения Xkeen-UI. Базовый проект уже собирается через Gradle wrapper и служит рабочей площадкой для дальнейшего подключения mobile backend contract.

## Что уже есть

- Jetpack Compose shell с состояниями `launch`, `Connections`, `Pair/Login`, `Home`, `Routing`, `Logs`, `More`.
- Demo coordinator в памяти без реального backend, чтобы можно было открыть приложение и пройти весь основной поток на устройстве.
- Экран подключений с ручным добавлением инстанса, проверкой доступности и переходом в pair/login flow.
- Dashboard со статусной сводкой, capability badges и безопасными действиями `start`, `stop`, `restart` через confirm state.
- Первый `Routing Xray` flow в виде skeleton-сценария `read`, `validate`, `preview`, `save`, `apply`, `revert`.
- Logs screen с live/recent переключением и компактными фильтрами.
- Компактный mobile-first UI: плотные карточки, короткие статусы, icon/actions вместо web-like wide layout.
- Базовая структура под дальнейшее подключение mobile API contract и замены demo state на реальные data layers.

## Как открыть

1. Открой каталог `android-companion/` в Android Studio.
2. Дождись Gradle sync.
3. Запусти конфигурацию `app` на эмуляторе или устройстве.

## Локальная сборка

```powershell
cd android-companion
.\gradlew.bat testDebugUnitTest assembleDebug
```

Команда выше уже проходила успешно в текущем репозитории, включая unit test для базовой валидации draft-потока.

## Текущие ограничения

- Нет реального backend transport, auth/session и secure storage.
- Данные подключения, dashboard state, logs и routing draft пока полностью demo-only.
- Нет offline persistence и reconnect behavior поверх настоящего network layer.

## Ближайшие следующие шаги

- Подключить реальный mobile bootstrap/dashboard contract вместо demo coordinator.
- Добавить storage для подключений и секретов, затем вынести auth/session/network в отдельные repositories и use cases.
- Заменить demo `Routing Xray` flow на backend-backed draft/validate/preview/apply contract.
- Подключить реальный logs transport с lifecycle-safe reconnect behavior.
