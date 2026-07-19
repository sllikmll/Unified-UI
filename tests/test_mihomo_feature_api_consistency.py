from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_panel_mihomo_bundle_uses_canonical_feature_urls():
    src = _read("unified-ui/static/js/pages/panel.mihomo.bundle.js")

    assert "../features/mihomo_panel.js?v=" not in src
    assert "../features/mihomo_yaml_patch.js?v=" not in src
    assert "import '../features/mihomo_panel.js';" in src
    assert "import '../features/compat/mihomo_panel.js';" in src
    assert "import '../features/mihomo_yaml_patch.js';" in src


def test_mihomo_legacy_global_publish_is_handled_only_by_compat_modules():
    expectations = {
        "unified-ui/static/js/features/compat/mihomo_panel.js": "UnifiedUI.features.mihomoPanel = legacyMihomoPanelApi;",
        "unified-ui/static/js/features/compat/mihomo_import.js": "UnifiedUI.features.mihomoImport = legacyMihomoImportApi;",
        "unified-ui/static/js/features/compat/mihomo_proxy_tools.js": "UnifiedUI.features.mihomoProxyTools = legacyMihomoProxyToolsApi;",
        "unified-ui/static/js/features/compat/mihomo_hwid_sub.js": "UnifiedUI.features.mihomoHwidSub = legacyMihomoHwidSubApi;",
    }

    for rel_path, marker in expectations.items():
        src = _read(rel_path)
        assert marker in src, f"expected legacy global API marker in {rel_path}"

    forbidden = {
        "unified-ui/static/js/features/mihomo_panel.js": [
            "UnifiedUI.features = UnifiedUI.features || {};",
            "UnifiedUI.features.mihomoPanel = MP;",
            "window.UnifiedUI.features.mihomoPanel",
        ],
        "unified-ui/static/js/features/mihomo_import.js": [
            "UnifiedUI.features = UnifiedUI.features || {};",
            "UnifiedUI.features.mihomoImport = MI;",
            "window.UnifiedUI.features.mihomoImport",
        ],
        "unified-ui/static/js/features/mihomo_proxy_tools.js": [
            "UnifiedUI.features = UnifiedUI.features || {};",
            "UnifiedUI.features.mihomoProxyTools = PT;",
            "window.UnifiedUI.features.mihomoProxyTools",
        ],
        "unified-ui/static/js/features/mihomo_hwid_sub.js": [
            "UnifiedUI.features = UnifiedUI.features || {};",
            "UnifiedUI.features.mihomoHwidSub = HW;",
            "window.UnifiedUI.features.mihomoHwidSub",
        ],
    }

    for rel_path, markers in forbidden.items():
        src = _read(rel_path)
        for marker in markers:
            assert marker not in src, f"canonical Mihomo module should not self-publish global API in {rel_path}: {marker}"


def test_panel_lazy_bindings_load_mihomo_compat_bridges_for_legacy_consumers():
    src = _read("unified-ui/static/js/pages/panel.lazy_bindings.runtime.js")

    required_fragments = [
        "mihomoImport: {",
        "load: () => import('../features/mihomo_import.js').then(",
        "import('../features/compat/mihomo_import.js')",
        "import('../features/mihomo_proxy_tools.js'))",
        "import('../features/compat/mihomo_proxy_tools.js').then(() => mod)",
        "mihomoHwidSub: {",
        "load: () => import('../features/mihomo_hwid_sub.js').then(",
        "import('../features/compat/mihomo_hwid_sub.js').then(() => mod)",
    ]

    for fragment in required_fragments:
        assert fragment in src, f"missing Mihomo compat panel-lazy fragment: {fragment}"


def test_mihomo_menu_feature_flows_keep_editor_patch_integrations_and_single_save_config():
    panel_src = _read("unified-ui/static/js/features/mihomo_panel.js")
    assert panel_src.count("MP.saveConfig = async function saveConfig() {") == 1
    template_src = _read("unified-ui/templates/panel.html")
    assert 'id="mihomo-import-parse-static-btn"' in template_src

    expectations = {
        "unified-ui/static/js/features/mihomo_import.js": [
            "txt = await applyInsertProxy(txt, o, groups);",
            "setEditorText(txt);",
            "refreshEditor();",
            "const api = getMihomoPanelApi();",
            "await post('/api/mihomo/provider/probe', {",
            "return `http://127.0.0.1:${port}/mihomo/provider.yaml?${params.toString()}`;",
            "const out = await buildSubscriptionProviderConfig(line, tmp, {",
            "providerStaticBulk: true,",
            "provider_proxies",
            "staticProviderProxies: true",
            "refresh_parser: group.refreshParser",
            "mihomo-provider",
            "Распознана HWID-подписка:",
            "providerHeaders",
            "if (headers) provider.header = headers;",
            "MI.open = function open(options = {}) {",
            "MI.openWithInput = async function openWithInput(input, options = {}) {",
            "openWithInput: openMihomoImportWithInput,",
        ],
        "unified-ui/static/js/features/mihomo_proxy_tools.js": [
            "const mi = getMihomoImportApi();",
            "const data = await apiPost('/api/mihomo/patch/rename_proxy', {",
            "const data = await apiPost('/api/mihomo/patch/replace_proxy', {",
            "setEditorText(patched);",
            "refreshEditor();",
        ],
        "unified-ui/static/js/features/mihomo_hwid_sub.js": [
            "const patch = getMihomoYamlPatchApi();",
            "const next = patch.insertIntoSection(existing, 'proxy-providers', snippet, { avoidDuplicates: true });",
            "setEditorText(next);",
            "refreshEditor();",
            "function hwidSourceLabel(source)",
            "function hwidProviderHeaderTips(headers)",
            "function payloadSummaryTips(res)",
            "function payloadSummaryMeta(res)",
            "res.hwid_response_headers",
            "res.provider_payload",
            "const r = await postJSONAllowError('/api/mihomo/hwid/apply', {",
            "getMihomoEditorEngineApi,",
            "async function ensurePreviewEditor()",
            "async function activatePreviewEngine(engine)",
            "mode: 'yaml'",
            "language: 'yaml'",
            "wordWrap: 'on'",
            "readOnly: 'nocursor'",
            "getXkeenLazyRuntimeApi",
            "import { getMihomoImportApi } from './mihomo_import.js';",
            "async function resolveMihomoImportApi()",
            "await lazy.ensureFeature('mihomoImport');",
            "const api = lazy.getFeatureApi('mihomoImport');",
            "const api = getMihomoImportApi();",
            "function getLegacyMihomoImportApi()",
            "return features.mihomoImport || null;",
            "await api.openWithInput(value, { mode: 'auto' });",
        ],
    }

    for rel_path, markers in expectations.items():
        src = _read(rel_path)
        for marker in markers:
            assert marker in src, f"expected '{marker}' in {rel_path}"


def test_mihomo_hwid_preview_uses_shared_editor_host_contract():
    panel_src = _read("unified-ui/templates/panel.html")
    feature_src = _read("unified-ui/static/js/features/mihomo_hwid_sub.js")
    css_src = _read("unified-ui/static/styles.css")

    required_panel_fragments = [
        'id="mihomo-hwid-engine-select"',
        'id="mihomo-hwid-preview-monaco"',
        'class="xk-monaco-editor xk-monaco-editor--modal xk-hw-preview-monaco hidden"',
    ]
    for fragment in required_panel_fragments:
        assert fragment in panel_src, f"missing HWID preview DOM contract: {fragment}"

    required_feature_fragments = [
        "previewMonaco: 'mihomo-hwid-preview-monaco'",
        "engineSelect: 'mihomo-hwid-engine-select'",
        "setEngineSelectValue(engine)",
        "resolvePreferredEngine()",
        "runtime.create(host, {",
    ]
    for fragment in required_feature_fragments:
        assert fragment in feature_src, f"missing HWID preview editor integration: {fragment}"

    required_css_fragments = [
        "#mihomo-hwid-preview-monaco",
        ".xk-hw-preview-wrap .xk-hw-preview-cm .cm-scroller",
        ".xk-hw-preview-wrap .xk-hw-preview-cm .cm-foldGutter",
    ]
    for fragment in required_css_fragments:
        assert fragment in css_src, f"missing HWID preview layout CSS: {fragment}"


def test_mihomo_import_is_compact_and_surfaces_hwid_provider_warnings():
    panel_src = _read("unified-ui/templates/panel.html")
    import_src = _read("unified-ui/static/js/features/mihomo_import.js")
    css_src = _read("unified-ui/static/styles.css")

    assert 'id="mihomo-hwid-sub-btn"' in panel_src
    assert "🧬 HWID" in panel_src
    assert "Mihomo Premium Import" in panel_src
    assert "Быстрый импорт без ручного YAML" not in panel_src
    assert "Сначала проверь превью" not in panel_src
    assert "id=\"mihomo-hwid-mode\"" not in panel_src
    assert "id=\"mihomo-hwid-template-wrap\"" not in panel_src

    assert "function providerHeaderWarnings(headers, explicitLimitInfo, opts)" in import_src
    assert "x-hwid-max-devices-reached" in import_src
    assert "x-hwid-limit" in import_src
    assert "limitInfoFromHeaders" in import_src
    assert "использовано ${data.used} из ${data.limit}" in import_src
    assert "provider_warnings" in import_src
    assert "xk-mi-status.warning" in css_src


def test_mihomo_runtime_helper_exposes_shared_window_unified_adapters():
    src = _read("unified-ui/static/js/features/mihomo_runtime.js")

    required_fragments = [
        "export function getMihomoUiApi()",
        "export function getMihomoModalApi()",
        "export function syncMihomoModalBodyScrollLock()",
        "export function getMihomoEditorEngineApi()",
        "export function getMihomoEditorActionsApi()",
        "export function getMihomoFormattersApi()",
        "export function getMihomoCoreHttpApi()",
        "export function getMihomoCommandJobApi()",
        "export async function confirmMihomoAction(opts, fallbackText)",
        "export function getSharedMihomoEditor()",
        "export function setSharedMihomoEditor(editor)",
        "export function clearSharedMihomoEditor(editor)",
        "export function refreshSharedMihomoEditor()",
    ]

    for fragment in required_fragments:
        assert fragment in src, f"missing Mihomo runtime helper fragment: {fragment}"


def test_mihomo_track2_modules_use_runtime_helper_instead_of_raw_window_unified_globals():
    expectations = {
        "unified-ui/static/js/features/mihomo_panel.js": [
            "window.UnifiedUI && UnifiedUI.util && UnifiedUI.util.commandJob",
            "window.UnifiedUI && UnifiedUI.ui && typeof UnifiedUI.ui.confirm === 'function'",
            "UnifiedUI.state.mihomoEditor",
            "UnifiedUI.ui.formatters.formatYaml",
            "UnifiedUI.ui.editorEngine",
            "UnifiedUI.ui.editorActions",
        ],
        "unified-ui/static/js/features/mihomo_import.js": [
            "window.UnifiedUI = window.UnifiedUI || {};",
            "UnifiedUI.ui.editorEngine",
            "UnifiedUI.state.mihomoEditor",
            "UnifiedUI.ui.modal.syncBodyScrollLock",
            "(window.UnifiedUI && UnifiedUI.core && UnifiedUI.core.http) ? UnifiedUI.core.http : null",
        ],
        "unified-ui/static/js/features/mihomo_proxy_tools.js": [
            "window.UnifiedUI = window.UnifiedUI || {};",
            "UnifiedUI.state.mihomoEditor",
            "(window.UnifiedUI && UnifiedUI.core && UnifiedUI.core.http) ? UnifiedUI.core.http : null",
        ],
        "unified-ui/static/js/features/mihomo_hwid_sub.js": [
            "window.UnifiedUI = window.UnifiedUI || {};",
            "UnifiedUI.util.commandJob",
            "UnifiedUI.ui.modal.syncBodyScrollLock",
            "UnifiedUI.core.http",
            "UnifiedUI.state.mihomoEditor",
        ],
        "unified-ui/static/js/features/mihomo_generator.js": [
            "window.UnifiedUI = window.UnifiedUI || {};",
            "UnifiedUI.ui.editorEngine",
            "UnifiedUI.ui.editorActions",
            "UnifiedUI.util.commandJob",
        ],
    }

    for rel_path, markers in expectations.items():
        src = _read(rel_path)
        assert "from './mihomo_runtime.js'" in src, f"expected runtime helper import in {rel_path}"
        for marker in markers:
            assert marker not in src, f"Track 2 Mihomo module should not use raw window.UnifiedUI.* in {rel_path}: {marker}"
