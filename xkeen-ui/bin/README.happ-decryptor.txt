Drop-in external Happ decryptor
================================

Place a third-party decryptor here if you need raw `happ://crypt...` support.

Auto-detected filenames:
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

Command contract:
- XKeen passes the incoming link as the last argument, or replaces `%LINK%`.
- The decryptor should print one of:
  - a direct subscription URL
  - decoded subscription text/body
  - JSON with `url`, `text`, `result`, `output`, `body`, or `decrypted`

You can always override auto-detection with:
- XKEEN_HAPP_DECRYPTOR_CMD

The built-in `scripts/happ_transport_helper.py` still handles HTTP(S) Happ landing pages.

Local aarch64 router build
==========================

The XKeen repository does not store Happ decryptor binaries or key material.
For local tests you can build a drop-in Linux/arm64 binary from a local
`LeeeeT/happ-decryptor` checkout and include it into your local
`xkeen-ui-routing.tar.gz` archive without committing the binary or generated
key-bearing source to GitHub.

Expected local source checkout:
- `.tmp/leeeet-happ-decryptor`

The builder reads:
- `src/decrypt.js`
- `public/data/expanded_rsa_keys.json`

Build command from the repository root:

```sh
python scripts/build_happ_decryptor_aarch64.py
```

Default output:

```text
xkeen-ui/bin/happ-decrypt-universal
```

Default target:

```text
GOOS=linux GOARCH=arm64 CGO_ENABLED=0
```

Default router command:

```sh
XKEEN_HAPP_DECRYPTOR_CMD='/opt/etc/xkeen-ui/bin/happ-decrypt-universal %LINK%'
```

If the binary keeps the auto-detected name `happ-decrypt-universal`, setting
`XKEEN_HAPP_DECRYPTOR_CMD` is optional. The panel will discover it automatically.

To ship the local binary to testers, rebuild the user archive after the binary exists:

```sh
python scripts/build_user_archive.py --skip-frontend-build
```
