Внешний Happ decryptor
======================

Кладите сюда сторонний decryptor, если нужна поддержка raw-ссылок
`happ://crypt...`.

Имена файлов, которые панель ищет автоматически:
- happ_decryptor.py
- happ-decryptor.py
- happ_decrypt_universal.py
- happ-decrypt-universal.py
- happwner.py
- Happwner.py
- happ_decryptor
- happ-decryptor
- happ_decrypt_universal
- happ-decrypt-universal
- happwner

Контракт команды:
- XKeen передаёт входящую ссылку последним аргументом или заменяет `%LINK%`.
- Decryptor должен вывести один из вариантов:
  - прямой URL подписки
  - расшифрованный текст или тело подписки
  - JSON с полем `url`, `text`, `result`, `output`, `body` или `decrypted`

Автоопределение всегда можно переопределить переменной:
- XKEEN_HAPP_DECRYPTOR_CMD

Встроенный `scripts/happ_transport_helper.py` по-прежнему отвечает за HTTP(S)
landing page подписки Happ.

Локальная сборка для aarch64 роутеров
=====================================

Репозиторий XKeen не хранит бинарники Happ decryptor и ключевой материал. Для
локальных тестов можно собрать drop-in бинарник Linux/arm64 из локального
checkout `LeeeeT/happ-decryptor` и включить его в локальный архив
`xkeen-ui-routing.tar.gz`, не коммитя сам бинарник или сгенерированный исходник
с ключевым материалом в GitHub.

Ожидаемый локальный checkout:
- `.tmp/leeeet-happ-decryptor`

Builder читает:
- `src/decrypt.js`
- `public/data/expanded_rsa_keys.json`

Команда сборки из корня репозитория:

```sh
python scripts/build_happ_decryptor_aarch64.py
```

Выходной файл по умолчанию:

```text
xkeen-ui/bin/happ-decrypt-universal
```

Целевая платформа по умолчанию:

```text
GOOS=linux GOARCH=arm64 CGO_ENABLED=0
```

Команда для роутера по умолчанию:

```sh
XKEEN_HAPP_DECRYPTOR_CMD='/opt/etc/xkeen-ui/bin/happ-decrypt-universal %LINK%'
```

Если бинарник сохраняет auto-detect имя `happ-decrypt-universal`, задавать
`XKEEN_HAPP_DECRYPTOR_CMD` необязательно. Панель найдёт его автоматически.

Чтобы передать локальный бинарник тестировщикам, пересоберите пользовательский
архив после появления бинарника:

```sh
python scripts/build_user_archive.py --skip-frontend-build
```

Ручная установка у тестировщика
===============================

Тестировщикам можно передавать только локальный бинарный файл:

```text
happ-decrypt-universal
```

Этот бинарник предназначен для Linux/aarch64 роутеров. На MIPS, ARMv7 и x86
роутерах он не запустится.

Рекомендуемый путь на роутере:

```sh
/opt/etc/xkeen-ui/bin/happ-decrypt-universal
```

Пример загрузки с ПК:

```sh
scp happ-decrypt-universal root@192.168.1.1:/tmp/happ-decrypt-universal
```

Затем выполните на роутере по SSH:

```sh
mkdir -p /opt/etc/xkeen-ui/bin
mv /tmp/happ-decrypt-universal /opt/etc/xkeen-ui/bin/happ-decrypt-universal
chmod 755 /opt/etc/xkeen-ui/bin/happ-decrypt-universal
```

Быстрая проверка на роутере:

```sh
/opt/etc/xkeen-ui/bin/happ-decrypt-universal
```

Ожидаемый вывод без аргументов:

```text
usage: happ-decrypt-universal <happ://crypt...>
```

Если файл лежит по указанному пути и сохранил auto-detect имя, XKeen должен
найти его автоматически. Для явной настройки через DevTools -> ENV укажите:

```sh
XKEEN_HAPP_DECRYPTOR_CMD=/opt/etc/xkeen-ui/bin/happ-decrypt-universal %LINK%
```

Значение применяется к следующей попытке импорта или обновления и не требует
Restart UI.
