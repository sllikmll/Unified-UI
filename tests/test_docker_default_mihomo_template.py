from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "unified-ui/opt/etc/mihomo/templates/keenetic-default.yaml"
DOCKER_ENTRYPOINT = ROOT / "docker/entrypoint.sh"
MIKROTIK_ENTRYPOINT = ROOT / "mikrotik/entrypoint.sh"
FORBIDDEN_SUB_HOST = "3xmsk." + "dogonin.ru:2096" + "/sub/"
PLACEHOLDER_SUB = "https://example.com/replace-with-your-subscription.yaml"


def test_keenetic_default_template_is_bundled_and_sanitized():
    text = TEMPLATE.read_text(encoding="utf-8")
    assert FORBIDDEN_SUB_HOST not in text
    assert PLACEHOLDER_SUB in text
    cfg = yaml.safe_load(text)
    assert isinstance(cfg, dict)
    assert cfg["proxy-providers"]["subscription_1"]["url"] == PLACEHOLDER_SUB
    assert cfg["rules"][-1] == "MATCH,GLOBAL"


def test_docker_entrypoints_seed_template_and_subscribe_from_env_only():
    for path in (DOCKER_ENTRYPOINT, MIKROTIK_ENTRYPOINT):
        text = path.read_text(encoding="utf-8")
        assert FORBIDDEN_SUB_HOST not in text
        assert "keenetic-default.yaml" in text
        assert "MIHOMO_SUB_URL" in text
        assert "providers.pop('subscription_1', None)" in text
