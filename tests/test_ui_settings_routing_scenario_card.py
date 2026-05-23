from services import ui_settings


def test_ui_settings_default_routing_scenario_card_is_visible(tmp_path):
    loaded = ui_settings.load_settings(ui_state_dir=str(tmp_path))
    assert loaded["routing"]["showScenarioCard"] is True


def test_ui_settings_persists_routing_scenario_card_toggle(tmp_path):
    saved = ui_settings.save_settings(
        {"routing": {"showScenarioCard": False}},
        ui_state_dir=str(tmp_path),
    )

    assert saved["routing"]["showScenarioCard"] is False

    loaded = ui_settings.load_settings(ui_state_dir=str(tmp_path))
    assert loaded["routing"]["showScenarioCard"] is False

    patched, report = ui_settings.patch_settings(
        {"routing": {"showScenarioCard": True}},
        ui_state_dir=str(tmp_path),
    )

    assert report["errors"] == []
    assert patched["routing"]["showScenarioCard"] is True


def test_ui_settings_rejects_invalid_routing_scenario_card_toggle(tmp_path):
    saved = ui_settings.save_settings(
        {"routing": {"showScenarioCard": False}},
        ui_state_dir=str(tmp_path),
    )
    assert saved["routing"]["showScenarioCard"] is False

    try:
        ui_settings.patch_settings(
            {"routing": {"showScenarioCard": "nope"}},
            ui_state_dir=str(tmp_path),
        )
    except ui_settings.UISettingsValidationError as exc:
        assert exc.errors == [{"path": "routing.showScenarioCard", "error": "must be boolean"}]
    else:
        raise AssertionError("invalid showScenarioCard patch should be rejected")

    loaded = ui_settings.load_settings(ui_state_dir=str(tmp_path))
    assert loaded["routing"]["showScenarioCard"] is False
