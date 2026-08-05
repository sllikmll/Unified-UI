import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "unified-ui"))

from services.mihomo_generator_providers import filter_proxy_group_uses


def test_filter_proxy_group_uses_inserts_use_when_group_lacks_it():
    cfg = """
proxy-providers:
  proxy-sub:
    type: http
    url: "https://example.test/sub"
proxy-groups:
  - name: AI
    type: select
    proxies: [DIRECT]
  - name: Fastest
    type: url-test
    url: https://www.gstatic.com/generate_204
    proxies: [DIRECT]
rules:
  - MATCH,AI
""".strip()

    out = filter_proxy_group_uses(cfg, ["https://example.test/sub"])

    assert "  - name: AI\n    type: select\n    proxies: [DIRECT]\n    use:\n      - proxy-sub" in out
    assert "  - name: Fastest" in out
    assert "    type: url-test" in out
    assert out.count("    use:\n      - proxy-sub") == 2


def test_filter_proxy_group_uses_removes_use_when_no_subscriptions():
    cfg = """
proxy-groups:
  - name: AI
    type: select
    proxies: [DIRECT]
    use:
      - proxy-sub
""".strip()

    out = filter_proxy_group_uses(cfg, [])

    assert "use:" not in out
    assert "proxy-sub" not in out
