from __future__ import annotations

import yaml

from services.mihomo_proxy_config import insert_proxy_into_groups


def test_insert_proxy_supports_pyyaml_indentless_group_sequences():
    source = """\
proxies: []
proxy-groups:
- name: Остальное
  type: select
  proxies:
  - DIRECT
  - Маршрутизация
rules:
- MATCH,Остальное
"""

    patched = insert_proxy_into_groups(source, "MikroTik-AWG-Test", ["Остальное"])
    parsed = yaml.safe_load(patched)

    group = parsed["proxy-groups"][0]
    assert group["proxies"] == ["DIRECT", "Маршрутизация", "MikroTik-AWG-Test"]
    assert patched.count("MikroTik-AWG-Test") == 1

    repeated = insert_proxy_into_groups(patched, "MikroTik-AWG-Test", ["Остальное"])
    assert yaml.safe_load(repeated)["proxy-groups"][0]["proxies"] == group["proxies"]
    assert repeated.count("MikroTik-AWG-Test") == 1
