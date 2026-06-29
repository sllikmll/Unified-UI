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
