from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FEATURES_DIR = ROOT / "unified-ui" / "static" / "js" / "features"
INDEX = FEATURES_DIR / "index.js"


def test_feature_api_registry_exists_and_tracks_current_top_level_features():
    assert INDEX.is_file(), "frontend feature API registry should exist"

    text = INDEX.read_text(encoding="utf-8")
    required_fragments = [
        "export const featureApiRegistry = Object.freeze({",
        "backups: backupsApi,",
        "fileManager: fileManagerApi,",
        "mihomoPanel: mihomoPanelApi,",
        "mihomoImport: mihomoImportApi,",
        "mihomoProxyTools: mihomoProxyToolsApi,",
        "mihomoHwidSub: mihomoHwidSubApi,",
        "restartLog: restartLogApi,",
        "routing: routingApi,",
        "serviceStatus: serviceStatusApi,",
        "xrayLogs: xrayLogsApi,",
    ]
    for fragment in required_fragments:
        assert fragment in text, f"missing registry fragment in {INDEX}: {fragment}"


def test_selected_feature_modules_export_named_api_wrappers():
    expectations = {
        "donate.js": [
            "let donateModuleApi = null;",
            "export function getDonateApi()",
            "export const donateApi = Object.freeze({",
        ],
        "branding_prefs.js": [
            "let brandingPrefsModuleApi = null;",
            "export function getBrandingPrefsApi()",
            "export const brandingPrefsApi = Object.freeze({",
        ],
        "devtools.js": [
            "let devtoolsModuleApi = null;",
            "export function getDevtoolsApi()",
            "export const devtoolsApi = Object.freeze({",
        ],
        "layout_prefs.js": [
            "let layoutPrefsModuleApi = null;",
            "export function getLayoutPrefsApi()",
            "export const layoutPrefsApi = Object.freeze({",
        ],
        "typography.js": [
            "let typographyModuleApi = null;",
            "export function getTypographyApi()",
            "export const typographyApi = Object.freeze({",
        ],
        "update_notifier.js": [
            "let updateNotifierModuleApi = null;",
            "export function getUpdateNotifierApi()",
            "export const updateNotifierApi = Object.freeze({",
        ],
        "routing_templates.js": [
            "let routingTemplatesModuleApi = null;",
            "export function getRoutingTemplatesApi()",
            "export const routingTemplatesApi = Object.freeze({",
        ],
        "file_manager.js": [
            "export function getFileManagerApi()",
            "export const fileManagerApi = Object.freeze({",
        ],
        "mihomo_yaml_patch.js": [
            "let mihomoYamlPatchModuleApi = null;",
            "export function getMihomoYamlPatchApi()",
            "export const mihomoYamlPatchApi = Object.freeze({",
        ],
        "mihomo_panel.js": [
            "export function getMihomoPanelApi()",
            "export function initMihomoPanel(...args)",
            "export const mihomoPanelApi = Object.freeze({",
        ],
        "mihomo_import.js": [
            "export function getMihomoImportApi()",
            "export function generateMihomoImportConfig(...args)",
            "export const mihomoImportApi = Object.freeze({",
        ],
        "mihomo_proxy_tools.js": [
            "export function getMihomoProxyToolsApi()",
            "export function initMihomoProxyTools(...args)",
            "export const mihomoProxyToolsApi = Object.freeze({",
        ],
        "mihomo_hwid_sub.js": [
            "export function getMihomoHwidSubApi()",
            "export function initMihomoHwidSub(...args)",
            "export const mihomoHwidSubApi = Object.freeze({",
        ],
        "restart_log.js": [
            "export function getRestartLogApi()",
            "export function appendRestartLog(...args)",
            "export const restartLogApi = Object.freeze({",
        ],
        "xray_logs.js": [
            "let xrayLogsModuleApi = null;",
            "export function getXrayLogsApi()",
            "export const xrayLogsApi = Object.freeze({",
        ],
        "routing_jsonc_preserve.js": [
            "let routingJsoncPreserveModuleApi = null;",
            "export function getRoutingJsoncPreserveApi()",
            "export const routingJsoncPreserveApi = Object.freeze({",
        ],
        "routing_shell.js": [
            "let routingShellModuleApi = null;",
            "export function getRoutingShellApi()",
            "export const routingShellApi = Object.freeze({",
        ],
        "routing_cards_namespace.js": [
            "let routingCardsNamespace = null;",
            "export function getRoutingCardsNamespace()",
            "export const routingCardsNamespaceApi = Object.freeze({",
        ],
    }

    for filename, fragments in expectations.items():
        text = (FEATURES_DIR / filename).read_text(encoding="utf-8")
        for fragment in fragments:
            assert fragment in text, f"missing explicit API fragment in {filename}: {fragment}"


def test_selected_small_feature_modules_no_longer_use_window_unified_features_as_canonical_api():
    expectations = {
        "donate.js": [
            "window.UnifiedUI.features ? (window.UnifiedUI.features.donate || null) : null",
            "XK.features.donate = Donate;",
        ],
        "branding_prefs.js": [
            "window.UnifiedUI.features ? (window.UnifiedUI.features.brandingPrefs || null) : null",
            "XK.features.brandingPrefs = Feature;",
        ],
        "devtools.js": [
            "XK.features = XK.features || {};",
            "XK.features.devtools",
            "window.UnifiedUI.features ? (window.UnifiedUI.features.devtools || null) : null",
        ],
        "layout_prefs.js": [
            "window.UnifiedUI.features ? (window.UnifiedUI.features.layoutPrefs || null) : null",
            "XK.features.layoutPrefs = XK.features.layoutPrefs || {};",
        ],
        "typography.js": [
            "window.UnifiedUI.features ? (window.UnifiedUI.features.typography || null) : null",
            "XK.features.typography = XK.features.typography || {};",
        ],
        "update_notifier.js": [
            "window.UnifiedUI.features ? (window.UnifiedUI.features.updateNotifier || null) : null",
            "XK.features.updateNotifier = XK.features.updateNotifier || {}",
        ],
        "routing_templates.js": [
            "window.UnifiedUI.features ? (window.UnifiedUI.features.routingTemplates || null) : null",
            "XK.features.routingTemplates = {",
        ],
        "restart_log.js": [
            "window.UnifiedUI.features ? (window.UnifiedUI.features.restartLog || null) : null",
            "UnifiedUI.features = UnifiedUI.features || {};",
        ],
        "commands_list.js": [
            "window.UnifiedUI.features ? (window.UnifiedUI.features.commandsList || null) : null",
            "UnifiedUI.features = UnifiedUI.features || {};",
        ],
        "cores_status.js": [
            "window.UnifiedUI.features ? (window.UnifiedUI.features.coresStatus || null) : null",
            "UnifiedUI.features = UnifiedUI.features || {};",
        ],
        "service_status.js": [
            "window.UnifiedUI.features ? (window.UnifiedUI.features.serviceStatus || null) : null",
            "UnifiedUI.features = UnifiedUI.features || {};",
        ],
        "mihomo_yaml_patch.js": [
            "GLOBAL_UNIFIED.features.mihomoYamlPatch",
            "const api = GLOBAL_UNIFIED && GLOBAL_UNIFIED.features ? GLOBAL_UNIFIED.features.mihomoYamlPatch : null;",
        ],
        "xray_logs.js": [
            "window.UnifiedUI.features ? (window.UnifiedUI.features.xrayLogs || null) : null",
            "UnifiedUI.features = UnifiedUI.features || {};",
        ],
        "routing_jsonc_preserve.js": [
            "window.UnifiedUI.features ? (window.UnifiedUI.features.routingJsoncPreserve || null) : null",
        ],
        "mihomo_panel.js": [
            "UnifiedUI.features = UnifiedUI.features || {};",
            "UnifiedUI.features.mihomoPanel = MP;",
            "window.UnifiedUI.features.mihomoPanel",
        ],
        "mihomo_import.js": [
            "UnifiedUI.features = UnifiedUI.features || {};",
            "UnifiedUI.features.mihomoImport = MI;",
            "window.UnifiedUI.features.mihomoImport",
        ],
        "mihomo_proxy_tools.js": [
            "UnifiedUI.features = UnifiedUI.features || {};",
            "UnifiedUI.features.mihomoProxyTools = PT;",
            "window.UnifiedUI.features.mihomoProxyTools",
        ],
        "mihomo_hwid_sub.js": [
            "UnifiedUI.features = UnifiedUI.features || {};",
            "UnifiedUI.features.mihomoHwidSub = HW;",
            "window.UnifiedUI.features.mihomoHwidSub",
        ],
        "inbounds.js": [
            "UnifiedUI.features = UnifiedUI.features || {};",
            "window.UnifiedUI.features) ? window.UnifiedUI.features.inbounds : null",
        ],
        "outbounds.js": [
            "UnifiedUI.features = UnifiedUI.features || {};",
            "window.UnifiedUI.features) ? window.UnifiedUI.features.outbounds : null",
        ],
        "routing.js": [
            "UnifiedUI.features = UnifiedUI.features || {};",
            "window.UnifiedUI.features ? window.UnifiedUI.features.routing : null",
        ],
        "routing_cards.js": [
            "window.UnifiedUI.features ? window.UnifiedUI.features.routingCards : null",
        ],
        "routing_shell.js": [
            "const shell = XK.features.routingShell = XK.features.routingShell || {};",
            "window.UnifiedUI && window.UnifiedUI.features ? window.UnifiedUI.features.routingShell : null",
        ],
        "routing_cards_namespace.js": [
            "XK.features && XK.features.routingCards",
        ],
        "ui_prefs_io.js": [
            "XK.features = XK.features || {};",
            "XK.features.uiPrefsIO = Feature;",
            "window.UnifiedUI.features ? (window.UnifiedUI.features.uiPrefsIO || null) : null",
            "XK.features.donate",
        ],
        "unified_texts.js": [
            "UnifiedUI.features = UnifiedUI.features || {};",
            "window.UnifiedUI.features ? (window.UnifiedUI.features.unifiedTexts || null) : null",
        ],
        "mihomo_generator.js": [
            "UnifiedUI.features = UnifiedUI.features || {};",
            "window.UnifiedUI.features ? (window.UnifiedUI.features.mihomoGenerator || null) : null",
        ],
    }

    for filename, forbidden_fragments in expectations.items():
        text = (FEATURES_DIR / filename).read_text(encoding="utf-8")
        for fragment in forbidden_fragments:
            assert fragment not in text, f"feature module should no longer use global canonical API in {filename}: {fragment}"


def test_file_manager_namespace_module_is_the_canonical_api_root():
    namespace_src = (FEATURES_DIR / "file_manager_namespace.js").read_text(encoding="utf-8")
    module_src = (FEATURES_DIR / "file_manager.js").read_text(encoding="utf-8")

    assert "let fileManagerApiRoot = null;" in namespace_src
    assert "export function getFileManagerApiRoot()" in namespace_src
    assert "return getFileManagerApiRoot();" in namespace_src
    assert "return getFileManagerApiRoot();" in module_src


def test_file_manager_common_module_exposes_runtime_adapter_helpers():
    common_src = (FEATURES_DIR / "file_manager" / "common.js").read_text(encoding="utf-8")

    required_fragments = [
        "C.getUiApi = function getUiApi()",
        "C.getModalApi = function getModalApi()",
        "C.getLayoutApi = function getLayoutApi()",
        "C.getCoreHttp = function getCoreHttp()",
        "C.getEditorEngine = function getEditorEngine()",
        "C.getLazyRuntime = function getLazyRuntime()",
        "C.getTerminal = function getTerminal()",
        "C.syncBodyScrollLock = function syncBodyScrollLock(locked)",
        "C.confirm = async function confirm(opts, fallbackText)",
    ]
    for fragment in required_fragments:
        assert fragment in common_src, f"missing file_manager common runtime helper: {fragment}"


def test_selected_file_manager_modules_use_common_runtime_helpers_instead_of_raw_window_unified_globals():
    expectations = {
        "file_manager/api.js": [
            "window.UnifiedUI.core.http",
        ],
        "file_manager/actions.js": [
            "UnifiedUI.ui.confirm",
        ],
        "file_manager.js": [
            "UnifiedUI.ui.layout",
            "window.UnifiedUI && UnifiedUI.ui && UnifiedUI.ui.layout",
        ],
        "file_manager/actions_modals.js": [
            "UnifiedUI.ui.confirm",
        ],
        "file_manager/bookmarks.js": [
            "window.toast",
            "UnifiedUI.ui.toast",
        ],
        "file_manager/chrome.js": [
            "UnifiedUI.ui.modal.syncBodyScrollLock",
        ],
        "file_manager/dragdrop.js": [
            "UnifiedUI.ui.modal.syncBodyScrollLock",
        ],
        "file_manager/editor.js": [
            "UnifiedUI.ui.modal.syncBodyScrollLock",
            "UnifiedUI.ui.editorEngine",
            "window.toast",
            "UnifiedUI.ui.confirm",
        ],
        "file_manager/errors.js": [
            "window.toast",
        ],
        "file_manager/ops.js": [
            "UnifiedUI.ui.confirm",
        ],
        "file_manager/remote.js": [
            "UnifiedUI.ui.confirm",
        ],
        "file_manager/storage.js": [
            "UnifiedUI.ui.confirm",
            "UnifiedUI.ui.toast",
        ],
        "file_manager/terminal.js": [
            "UnifiedUI.runtime.lazy",
            "window.UnifiedUI.terminal",
            "UnifiedUI.ui.toast",
        ],
        "file_manager/transfers.js": [
            "UnifiedUI.ui.confirm",
        ],
    }

    for relative_path, forbidden_fragments in expectations.items():
        text = (FEATURES_DIR / relative_path).read_text(encoding="utf-8")
        for fragment in forbidden_fragments:
            assert fragment not in text, (
                f"file_manager module should use shared common runtime helpers instead of raw globals in {relative_path}: {fragment}"
            )


def test_routing_cards_subtree_uses_canonical_namespace_root():
    namespace_src = (FEATURES_DIR / "routing_cards_namespace.js").read_text(encoding="utf-8")
    facade_src = (FEATURES_DIR / "routing_cards.js").read_text(encoding="utf-8")
    compat_src = (FEATURES_DIR / "compat" / "routing_cards.js").read_text(encoding="utf-8")

    assert "const RC = {};" in namespace_src
    assert "import { getRoutingCardsNamespace } from './routing_cards_namespace.js';" in facade_src
    assert "import { getRoutingCardsNamespace } from '../routing_cards_namespace.js';" in compat_src
    assert "const legacyRoutingCardsApi = routingCardsNamespace;" in compat_src

    for path in sorted((FEATURES_DIR / "routing_cards").rglob("*.js")):
        text = path.read_text(encoding="utf-8")
        assert "XK.features.routingCards = XK.features.routingCards || {}" not in text, (
            f"routing_cards subtree should not use window.UnifiedUI.features.routingCards as canonical root: {path.name}"
        )
        assert "XK.features = XK.features || {};" not in text, (
            f"routing_cards subtree should not create a canonical features root: {path.name}"
        )
        if path.name == "ns.js":
            assert "initRoutingCardsNamespace" in text
        else:
            assert "getRoutingCardsNamespace" in text, (
                f"routing_cards subtree should use canonical namespace helper in {path.name}"
            )


def test_devtools_subtree_uses_canonical_namespace_root():
    namespace_src = (FEATURES_DIR / "devtools_namespace.js").read_text(encoding="utf-8")
    main_src = (FEATURES_DIR / "devtools.js").read_text(encoding="utf-8")
    compat_src = (FEATURES_DIR / "compat" / "devtools.js").read_text(encoding="utf-8")

    assert "let devtoolsNamespace = null;" in namespace_src
    assert "export function getDevtoolsNamespace()" in namespace_src
    assert "export function setDevtoolsNamespaceApi(name, api)" in namespace_src
    assert "import { getDevtoolsNamespace, getDevtoolsSharedApi, setDevtoolsNamespaceApi } from './devtools_namespace.js';" in main_src
    assert "setDevtoolsNamespaceApi('devtools', devtoolsModuleApi);" in main_src
    assert "import { getDevtoolsApi } from '../devtools.js" in compat_src
    assert "UnifiedUI.features[key] = legacyApi;" in compat_src

    for path in sorted((FEATURES_DIR / "devtools").rglob("*.js")):
        text = path.read_text(encoding="utf-8")
        assert "XK.features = XK.features || {};" not in text, (
            f"devtools subtree should not recreate window.UnifiedUI.features in {path.name}"
        )
        assert "XK.features.devtools" not in text, (
            f"devtools subtree should not use window.UnifiedUI.features.* as canonical API in {path.name}"
        )
        assert "window.UnifiedUI.features" not in text, (
            f"devtools subtree should not read canonical API from window.UnifiedUI.features in {path.name}"
        )


def test_unified_runtime_module_exposes_shared_runtime_adapter_helpers():
    runtime_src = (FEATURES_DIR / "unified_runtime.js").read_text(encoding="utf-8")

    required_fragments = [
        "export function getXkeenPageConfig()",
        "export function getXkeenPageConfigValue(path, fallbackValue = undefined)",
        "export function getXkeenPageName()",
        "export function getXkeenPageSectionsConfig()",
        "export function getXkeenPageFilesConfig()",
        "export function getXkeenPageFlagsConfig()",
        "export function getXkeenPageCoresConfig()",
        "export function getXkeenFileManagerDefaults()",
        "export function getXkeenGithubConfig()",
        "export function getXkeenStaticConfig()",
        "export function getXkeenRuntimeConfig()",
        "export function getXkeenTerminalConfig()",
        "export function supportsXkeenTerminalPty()",
        "export function shouldEnableXkeenTerminalOptionalAddons()",
        "export function shouldEnableXkeenTerminalLigatures()",
        "export function shouldEnableXkeenTerminalWebgl()",
        "export function getXkeenStateApi()",
        "export function getXkeenConfigDirtyApi()",
        "export function getXkeenFormattersApi()",
        "export function getXkeenCm6RuntimeApi()",
        "export function getXkeenJsonEditorApi()",
        "export function getXkeenPanelShellApi()",
        "export function getXkeenCoreHttpApi()",
        "export function getXkeenCoreStorageApi()",
        "export function getXkeenCommandJobApi()",
        "export function getXkeenShowXrayPreflightErrorApi()",
        "export function openXkeenJsonEditor(target, options)",
        "export function ansiToXkeenHtml(text)",
        "export const unifiedRuntimeApi = Object.freeze({",
        "getPageConfig: getXkeenPageConfig,",
        "getPageConfigValue: getXkeenPageConfigValue,",
        "getPageName: getXkeenPageName,",
        "getPageSectionsConfig: getXkeenPageSectionsConfig,",
        "getPageFilesConfig: getXkeenPageFilesConfig,",
        "getPageFlagsConfig: getXkeenPageFlagsConfig,",
        "getPageCoresConfig: getXkeenPageCoresConfig,",
        "getFileManagerDefaults: getXkeenFileManagerDefaults,",
        "getGithubConfig: getXkeenGithubConfig,",
        "getStaticConfig: getXkeenStaticConfig,",
        "getRuntimeConfig: getXkeenRuntimeConfig,",
        "getTerminalConfig: getXkeenTerminalConfig,",
        "getStateApi: getXkeenStateApi,",
        "getConfigDirtyApi: getXkeenConfigDirtyApi,",
        "getFormattersApi: getXkeenFormattersApi,",
        "getCm6RuntimeApi: getXkeenCm6RuntimeApi,",
        "getJsonEditorApi: getXkeenJsonEditorApi,",
        "getPanelShellApi: getXkeenPanelShellApi,",
        "getCoreHttpApi: getXkeenCoreHttpApi,",
        "getCoreStorageApi: getXkeenCoreStorageApi,",
        "getCommandJobApi: getXkeenCommandJobApi,",
        "getShowXrayPreflightErrorApi: getXkeenShowXrayPreflightErrorApi,",
        "hasMihomoCore: hasXkeenMihomoCore,",
        "getStaticBase: getXkeenStaticBase,",
        "getStaticVersion: getXkeenStaticVersion,",
        "getFilePath: getXkeenFilePath,",
        "getCoreAvailability: getXkeenCoreAvailability,",
        "supportsTerminalPty: supportsXkeenTerminalPty,",
        "shouldEnableTerminalOptionalAddons: shouldEnableXkeenTerminalOptionalAddons,",
        "shouldEnableTerminalLigatures: shouldEnableXkeenTerminalLigatures,",
        "shouldEnableTerminalWebgl: shouldEnableXkeenTerminalWebgl,",
        "openJsonEditor: openXkeenJsonEditor,",
        "ansiToHtml: ansiToXkeenHtml,",
    ]

    for fragment in required_fragments:
        assert fragment in runtime_src, f"missing shared runtime adapter fragment in unified_runtime.js: {fragment}"


def test_selected_runtime_adapter_feature_modules_no_longer_read_raw_window_unified_or_window_toast_globals():
    expectations = {
        "commands_list.js": [
            "from './unified_runtime.js';",
        ],
        "cores_status.js": [
            "from './unified_runtime.js';",
        ],
        "service_status.js": [
            "from './unified_runtime.js';",
        ],
        "update_notifier.js": [
            "from './unified_runtime.js';",
        ],
        "xray_logs.js": [
            "from './unified_runtime.js';",
        ],
        "backups.js": [
            "from './unified_runtime.js';",
        ],
        "github.js": [
            "from './unified_runtime.js';",
        ],
        "local_io.js": [
            "from './unified_runtime.js';",
        ],
        "inbounds.js": [
            "from './unified_runtime.js';",
        ],
        "outbounds.js": [
            "from './unified_runtime.js';",
        ],
        "restart_log.js": [
            "from './unified_runtime.js';",
        ],
        "routing.js": [
            "from './unified_runtime.js';",
        ],
        "routing_cards.js": [
            "from './unified_runtime.js';",
        ],
        "routing_templates.js": [
            "from './unified_runtime.js';",
        ],
        "unified_texts.js": [
            "from './unified_runtime.js';",
        ],
    }
    forbidden_fragments = [
        "window.UnifiedUI.",
        "UnifiedUI.ui.",
        "UnifiedUI.core.",
        "UnifiedUI.pages.",
        "UnifiedUI.util.",
        "UnifiedUI.runtime.",
        "UnifiedUI.terminal.",
        "UnifiedUI.jsonEditor",
        "UnifiedUI.state.",
        "window.toast(",
        "window.showToast(",
        "window.openTerminal(",
    ]

    for filename, required_fragments in expectations.items():
        text = (FEATURES_DIR / filename).read_text(encoding="utf-8")
        for fragment in required_fragments:
            assert fragment in text, f"missing shared runtime adapter import in {filename}: {fragment}"
        for fragment in forbidden_fragments:
            assert fragment not in text, (
                f"feature module should use unified_runtime/shared adapter helpers instead of raw globals in {filename}: {fragment}"
            )


def test_routing_shell_keeps_editor_state_module_local_instead_of_window_unified_state():
    shell_src = (FEATURES_DIR / "routing_shell.js").read_text(encoding="utf-8")

    assert "const state = shell.state = shell.state || {};" in shell_src
    assert "XK.state.routingEditor" not in shell_src
    assert "XK.state.routingEditorFacade" not in shell_src
    assert "window.UnifiedUI" not in shell_src


def test_unified_runtime_exposes_page_config_mutator_and_window_runtime_bridge():
    text = (FEATURES_DIR / "unified_runtime.js").read_text(encoding="utf-8")

    required_fragments = [
        "export function setXkeenPageConfigValue(path, value) {",
        "setPageConfigValue: setXkeenPageConfigValue,",
        "Object.assign(xk.runtime, unifiedRuntimeApi);",
    ]

    for fragment in required_fragments:
        assert fragment in text, f"missing runtime stage-6 consumer-sweep fragment: {fragment}"


def test_feature_access_module_publishes_runtime_accessor_for_migrated_feature_consumers():
    access_src = (FEATURES_DIR / 'feature_access.js').read_text(encoding='utf-8')
    shell_src = (ROOT / 'unified-ui' / 'static' / 'js' / 'pages' / 'shell.shared.js').read_text(encoding='utf-8')

    required_fragments = [
        "const featureAccessorRegistry = Object.freeze({",
        "devtools: () => getDevtoolsNamespaceApi('devtools'),",
        "updateNotifier: getUpdateNotifierApi,",
        "export function getFeatureApi(name)",
        "export function requireFeatureApi(name)",
        "xk.runtime.getFeatureApi = getFeatureApi;",
        "xk.runtime.requireFeatureApi = requireFeatureApi;",
        "xk.runtime.getFeatureAccessorRegistry = getFeatureAccessorRegistry;",
    ]
    for fragment in required_fragments:
        assert fragment in access_src, f"missing feature access fragment in feature_access.js: {fragment}"

    assert "import '../features/feature_access.js';" in shell_src


def test_selected_canonical_consumers_use_feature_accessors_instead_of_window_unified_features():
    expectations = {
        ROOT / 'unified-ui' / 'static' / 'js' / 'ui' / 'settings_panel.js': [
            "import { getFeatureApi } from '../features/feature_access.js';",
            "const api = getFeatureApi('updateNotifier');",
        ],
        ROOT / 'unified-ui' / 'static' / 'js' / 'ui' / 'sections.js': [
            "typeof XK.runtime.getFeatureApi === 'function'",
            "const devtoolsApi = getFeatureApi('devtools');",
        ],
        ROOT / 'unified-ui' / 'static' / 'js' / 'pages' / 'panel_shell.shared.js': [
            "import { getRoutingCardsNamespace } from '../features/routing_cards_namespace.js';",
            "const backups = getPanelLazyFeatureApi('backups');",
            "ensurePanelLazyFeature('backups').then((ready) => {",
            "const routingCards = getRoutingCardsFeatureApi();",
        ],
    }
    forbidden = {
        ROOT / 'unified-ui' / 'static' / 'js' / 'ui' / 'settings_panel.js': [
            'XK.features && XK.features.updateNotifier',
            'window.UnifiedUI.features',
        ],
        ROOT / 'unified-ui' / 'static' / 'js' / 'ui' / 'sections.js': [
            'XK.features && XK.features.devtools',
            'window.UnifiedUI.features',
        ],
        ROOT / 'unified-ui' / 'static' / 'js' / 'pages' / 'panel_shell.shared.js': [
            'window.UnifiedUI && window.UnifiedUI.features ? window.UnifiedUI.features : null',
            'window.UnifiedUI && window.UnifiedUI.features ? window.UnifiedUI.features.routingCards : null',
            'window.UnifiedUI && window.UnifiedUI.backups ? window.UnifiedUI.backups : null',
        ],
    }

    for path, fragments in expectations.items():
        text = path.read_text(encoding='utf-8')
        for fragment in fragments:
            assert fragment in text, f"missing feature accessor fragment in {path.relative_to(ROOT).as_posix()}: {fragment}"

    for path, fragments in forbidden.items():
        text = path.read_text(encoding='utf-8')
        for fragment in fragments:
            assert fragment not in text, (
                f"canonical consumer should not read compat feature globals in {path.relative_to(ROOT).as_posix()}: {fragment}"
            )
