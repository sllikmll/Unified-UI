from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES_DIR = ROOT / "unified-ui" / "static" / "js" / "pages"
RUNTIME_DIR = ROOT / "unified-ui" / "static" / "js" / "runtime"
DOCS_DIR = ROOT / "docs"


def test_source_entrypoints_bootstrap_pages_without_legacy_loader():
    expectations = {
        "panel.entry.js": [
            "import { bootTopLevelShell } from './top_level_shell.shared.js';",
            "import { registerPanelMihomoTopLevelScreens } from './top_level_panel_mihomo.shared.js';",
            "import { bootPanelScreen } from './panel.screen.bootstrap.js';",
            "initialScreen: 'panel'",
        ],
        "backups.entry.js": [
            "import { bootTopLevelShell } from './top_level_shell.shared.js';",
            "import { registerPanelMihomoTopLevelScreens } from './top_level_panel_mihomo.shared.js';",
            "import { bootBackupsScreen } from './backups.screen.bootstrap.js';",
            "initialScreen: 'backups'",
        ],
        "devtools.entry.js": [
            "import { bootTopLevelShell } from './top_level_shell.shared.js';",
            "import { registerPanelMihomoTopLevelScreens } from './top_level_panel_mihomo.shared.js';",
            "import { bootDevtoolsScreen } from './devtools.screen.bootstrap.js';",
            "initialScreen: 'devtools'",
        ],
        "unified.entry.js": [
            "import { bootTopLevelShell } from './top_level_shell.shared.js';",
            "import { registerPanelMihomoTopLevelScreens } from './top_level_panel_mihomo.shared.js';",
            "import { bootXkeenScreen } from './unified.screen.bootstrap.js';",
            "initialScreen: 'unified'",
        ],
        "mihomo_generator.entry.js": [
            "import { bootTopLevelShell } from './top_level_shell.shared.js';",
            "import { bootMihomoGeneratorScreen } from './mihomo_generator.screen.bootstrap.js';",
            "import { registerPanelMihomoTopLevelScreens } from './top_level_panel_mihomo.shared.js';",
            "initialScreen: 'mihomo_generator'",
        ],
    }
    forbidden_fragments = {
        "panel.entry.js": [],
        "backups.entry.js": [
            "../features/update_notifier.js?v=",
        ],
        "devtools.entry.js": [
            "../features/update_notifier.js?v=",
            "../features/typography.js?v=",
            "../features/layout_prefs.js?v=",
            "../features/branding_prefs.js?v=",
        ],
        "unified.entry.js": [
            "../features/update_notifier.js?v=",
        ],
        "mihomo_generator.entry.js": [
            "../features/update_notifier.js?v=",
        ],
    }

    for filename, fragments in expectations.items():
        text = (PAGES_DIR / filename).read_text(encoding="utf-8")
        assert "legacy_script_loader.js" not in text
        assert "bootLegacyEntry(" not in text
        for fragment in fragments:
            assert fragment in text, f"missing source-bootstrap fragment in {filename}: {fragment}"
        for fragment in forbidden_fragments.get(filename, []):
            assert fragment not in text, f"source entrypoint should use canonical feature import URLs in {filename}: {fragment}"


def test_top_level_source_entrypoints_stay_thin_wrappers_over_shared_shell_bootstrap():
    expectations = {
        "panel.entry.js": [
            "void bootTopLevelShell({",
            "initialScreen: 'panel'",
            "await bootPanelScreen();",
            "registerPanelMihomoTopLevelScreens();",
        ],
        "devtools.entry.js": [
            "void bootTopLevelShell({",
            "initialScreen: 'devtools'",
            "return bootDevtoolsScreen();",
            "registerPanelMihomoTopLevelScreens();",
        ],
        "mihomo_generator.entry.js": [
            "void bootTopLevelShell({",
            "initialScreen: 'mihomo_generator'",
            "return bootMihomoGeneratorScreen();",
            "registerPanelMihomoTopLevelScreens();",
        ],
    }
    forbidden_fragments = [
        "window.",
        "document.",
        "fetch(",
        "querySelector",
        "addEventListener(",
        "localStorage",
        "sessionStorage",
        "new URL(",
        "../features/",
    ]

    for filename, fragments in expectations.items():
        text = (PAGES_DIR / filename).read_text(encoding="utf-8")
        for fragment in fragments:
            assert fragment in text, f"missing thin-shell wrapper fragment in {filename}: {fragment}"
        assert text.count("bootTopLevelShell({") == 1, f"{filename} should stay a single shell-bootstrap wrapper"
        for fragment in forbidden_fragments:
            assert fragment not in text, f"{filename} should stay thin and not own runtime logic: {fragment}"


def test_top_level_bridge_assets_stay_import_only_over_canonical_source_entrypoints():
    bridge_dir = ROOT / "unified-ui" / "static" / "frontend-build" / "assets"
    expectations = {
        "panel-bridge.js": "../../js/pages/panel.entry.js",
        "devtools-bridge.js": "../../js/pages/devtools.entry.js",
        "mihomo_generator-bridge.js": "../../js/pages/mihomo_generator.entry.js",
    }

    for filename, import_target in expectations.items():
        text = (bridge_dir / filename).read_text(encoding="utf-8")
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        assert lines[-1] == f"import '{import_target}';", (
            f"{filename} should remain an import-only bridge to {import_target}"
        )
        assert sum(1 for line in lines if line.startswith("import ")) == 1, (
            f"{filename} should not grow extra runtime logic or secondary imports"
        )
        assert "bootTopLevelShell" not in text
        assert "window." not in text
        assert "document." not in text
        assert "fetch(" not in text


def test_legacy_script_loader_artifact_is_removed():
    assert not (PAGES_DIR / 'legacy_script_loader.js').exists(), (
        'final compat cleanup should remove legacy_script_loader.js from the repository'
    )


def test_panel_runtime_bundle_files_exist_for_current_architecture():
    required_files = [
        "panel.bootstrap_tail.bundle.js",
        "panel.core_ui_watch.runtime.js",
        "panel.lazy_bindings.runtime.js",
        "panel.mihomo.bundle.js",
        "panel.routing.bundle.js",
        "panel.screen.bootstrap.js",
        "panel.shared_compat.bundle.js",
        "panel.view_runtime.js",
        "devtools.screen.bootstrap.js",
        "mihomo_generator.screen.bootstrap.js",
        "top_level_shell.shared.js",
        "top_level_router.js",
        "top_level_screen_registry.js",
        "top_level_screen_host.shared.js",
        "top_level_panel_screen.js",
        "top_level_mihomo_generator_screen.js",
        "top_level_devtools_screen.js",
        "top_level_panel_mihomo.shared.js",
    ]

    for filename in required_files:
        assert (PAGES_DIR / filename).is_file(), f"missing current panel runtime file: {filename}"


def test_frontend_migration_docs_exist_for_current_contract():
    required_docs = [
        DOCS_DIR / "README.md",
        DOCS_DIR / "README_frontend_migration_plan.md",
        DOCS_DIR / "frontend-target-architecture.md",
        DOCS_DIR / "frontend-feature-api.md",
        DOCS_DIR / "frontend-page-inventory.md",
        DOCS_DIR / "frontend-build-workflow.md",
        DOCS_DIR / "adr" / "0001-frontend-esm-bootstrap.md",
    ]

    for path in required_docs:
        assert path.is_file(), f"missing frontend migration doc: {path.relative_to(ROOT).as_posix()}"
    assert not (DOCS_DIR / "frontend-stage6-implementation-plan.md").exists(), (
        "historical stage-specific implementation plan should be removed from docs/"
    )




def test_stage0_to_stage3_docs_are_frozen_and_non_reopenable():
    readme_src = (DOCS_DIR / "README_frontend_migration_plan.md").read_text(encoding="utf-8")
    feature_api_src = (DOCS_DIR / "frontend-feature-api.md").read_text(encoding="utf-8")

    readme_required = [
        "Этапы 0-3 считаются закрытыми и замороженными.",
        "## Freeze для stages 0-3",
        "**Stage 0. Архитектурный контракт**",
        "**Stage 1. Page inventory**",
        "**Stage 2. Secondary-page bootstrap**",
        "**Stage 3. Panel bootstrap и manifest bridge**",
        "wrapper-файлы не должны содержать runtime-логики кроме import canonical source entrypoint",
    ]
    feature_api_required = [
        "## Freeze-ограничение для stages 0-3",
        "не возвращать страницы к `legacy_script_loader.js` или `bootLegacyEntry(...)`",
        "не превращать build wrapper assets в место для runtime-логики",
        "не расходиться с canonical source entrypoints как источником истины для page graph",
    ]

    for fragment in readme_required:
        assert fragment in readme_src, f"missing stage 0-3 freeze fragment in README_frontend_migration_plan.md: {fragment}"
    for fragment in feature_api_required:
        assert fragment in feature_api_src, f"missing stage 0-3 freeze fragment in frontend-feature-api.md: {fragment}"


def test_frontend_status_docs_focus_on_closed_current_state():
    docs_index_src = (DOCS_DIR / "README.md").read_text(encoding="utf-8")
    readme_src = (DOCS_DIR / "README_frontend_migration_plan.md").read_text(encoding="utf-8")
    inventory_src = (DOCS_DIR / "frontend-page-inventory.md").read_text(encoding="utf-8")
    feature_api_src = (DOCS_DIR / "frontend-feature-api.md").read_text(encoding="utf-8")

    docs_index_required = [
        "Исторические пошаговые rollout-планы в `docs/` больше не поддерживаются.",
        "`README_frontend_migration_plan.md`",
        "`frontend-target-architecture.md`",
        "`frontend-feature-api.md`",
        "`frontend-page-inventory.md`",
        "`frontend-build-workflow.md`",
    ]
    readme_required = [
        "Frontend migration закрыта: **stages 0-9 fully closed**.",
        "Этот файл больше не является пошаговым rollout-планом.",
        "Исторические stage-by-stage implementation plans удалены из `docs/`",
        "Этапы 4-6 уже закрыты и подтверждены кодом, guardrails и статусной документацией.",
        "- `panel`/`devtools` публикуют только canonical `window.UnifiedUI.pageConfig`;",
        "Stages 7-9 тоже закрыты и теперь считаются частью обычного repository contract.",
        "`UNIFIED_UI_FRONTEND_SOURCE_FALLBACK=1`",
        "`legacy_script_loader.js` удалён",
        "`lazy_runtime.js` остаётся только узким runtime adapter-слоем",
        "`.github/workflows/ci.yml`",
        "`.github/workflows/build-user-archive.yml`",
    ]
    readme_forbidden = [
        "Что осталось до честного финала migration scope",
        "## Этап 6.",
        "## Этап 7.",
        "## Этап 8.",
        "## Этап 9.",
        "## Рекомендуемый порядок выполнения",
        "python-ui-ci.yml",
        "template dual-write",
        "PR-A...PR-F",
    ]
    inventory_required = [
        "template публикует только canonical `window.UnifiedUI.pageConfig`",
        "Для stages 0-9 migration contract считается закрытым",
    ]

    for fragment in docs_index_required:
        assert fragment in docs_index_src, f"missing docs index fragment in docs/README.md: {fragment}"
    for fragment in readme_required:
        assert fragment in readme_src, f"missing current-state fragment in README_frontend_migration_plan.md: {fragment}"
    for fragment in readme_forbidden:
        assert fragment not in readme_src, f"status doc should not keep stale rollout wording in README_frontend_migration_plan.md: {fragment}"
    for fragment in inventory_required:
        assert fragment in inventory_src, f"missing final pageConfig contract note in frontend-page-inventory.md: {fragment}"

    feature_api_required = [
        "migration stages 0-6 считаются закрытыми",
        "## Официальный статус для stages 4-6",
        "`window.UnifiedUI.features.*` не является canonical read-path",
        "`window.UnifiedUI.pageConfig` остаётся единственным server-owned runtime contract.",
    ]
    feature_api_forbidden = [
        "проект всё ещё находится в переходной фазе",
        "Приоритетные зоны для дальнейшей чистки:",
        "После PR-A...PR-F canonical path уже считается закрытым:",
        "`mihomo_panel`",
        "`mihomo_import`",
        "`mihomo_proxy_tools`",
        "`mihomo_hwid_sub`",
    ]
    for fragment in feature_api_required:
        assert fragment in feature_api_src, f"missing final closure fragment in frontend-feature-api.md: {fragment}"
    for fragment in feature_api_forbidden:
        assert fragment not in feature_api_src, f"frontend-feature-api.md should no longer describe stage 4-6 canonical path as open: {fragment}"


def test_terminal_lazy_path_forbids_dom_script_injection_and_uses_vendor_adapter():
    entry_text = (PAGES_DIR / "terminal.lazy.entry.js").read_text(encoding="utf-8")
    adapter_text = (ROOT / "unified-ui" / "static" / "js" / "terminal" / "vendors" / "xterm_import_adapter.js").read_text(encoding="utf-8")

    required_entry_fragments = [
        "from '../terminal/vendors/xterm_import_adapter.js';",
        "await ensureXtermVendorReady();",
        "requiredVendorCount: REQUIRED_XTERM_VENDOR_SPECS.length",
        "optionalVendorCount: OPTIONAL_XTERM_VENDOR_SPECS.length",
    ]
    forbidden_fragments = [
        "document.createElement('script')",
        "appendChild(script)",
        "document.head.appendChild(script)",
        "querySelector('script[data-xk-term-src=",
    ]
    required_adapter_fragments = [
        "export async function ensureXtermVendorReady()",
        "await import(/* @vite-ignore */ url);",
        "appendTerminalDebug('lazy:vendor:amd-shield'",
        "restoreAmdGlobals(scope, amdStash)",
    ]

    for fragment in required_entry_fragments:
        assert fragment in entry_text, f"missing terminal lazy import-first fragment: {fragment}"
    for fragment in forbidden_fragments:
        assert fragment not in entry_text, f"terminal lazy entry must not perform DOM script injection: {fragment}"
        assert fragment not in adapter_text, f"terminal vendor adapter must not perform DOM script injection: {fragment}"
    for fragment in required_adapter_fragments:
        assert fragment in adapter_text, f"missing terminal vendor adapter fragment: {fragment}"


def test_lazy_runtime_keeps_only_generic_compat_feature_paths():
    text = (RUNTIME_DIR / "lazy_runtime.js").read_text(encoding="utf-8")

    required_fragments = [
        "const featureLoaders = {",
        "backups: () => import('../features/backups.js'),",
        "jsonEditor: () => import('../ui/json_editor_modal.js'),",
        "datContents: () => import('../ui/dat_contents_modal.js'),",
        "const featureModules = Object.create(null);",
        "function loadFeatureModule(name) {",
        "case 'backups': {",
        "const managed = getBuildManagedFeatureLoader(key);",
    ]
    forbidden_fragments = [
        "routingTemplates: () => import('../features/routing_templates.js'),",
        "github: () => import('../features/github.js').then(",
        "serviceStatus: () => import('../features/service_status.js'),",
        "restartLog: () => import('../features/restart_log.js'),",
        "donate: () => import('../features/donate.js'),",
        "unifiedTexts: () => import('../features/unified_texts.js'),",
        "commandsList: () => import('../features/commands_list.js'),",
        "coresStatus: () => import('../features/cores_status.js'),",
        "formatters: () => import('../ui/prettier_loader.js').then(() => import('../ui/formatters.js')),",
        "xrayPreflight: () => import('../ui/xray_preflight_modal.js'),",
        "uiSettingsPanel: () => import('../ui/settings_panel.js'),",
        "mihomoImport: () => import('../features/mihomo_import.js').then(",
        "mihomoProxyTools: () => import('../features/mihomo_import.js')",
        "mihomoHwidSub: () => import('../features/mihomo_hwid_sub.js').then(",
        "const featureModuleApiGetters = Object.freeze({",
        "function getFeatureApiFromModule(name) {",
    ]

    for fragment in required_fragments:
        assert fragment in text, f"missing generic lazy runtime fragment in lazy_runtime.js: {fragment}"
    for fragment in forbidden_fragments:
        assert fragment not in text, f"lazy runtime should not own panel-specific feature path: {fragment}"


def test_panel_lazy_bindings_own_panel_specific_feature_loaders():
    text = (PAGES_DIR / "panel.lazy_bindings.runtime.js").read_text(encoding="utf-8")

    required_fragments = [
        "const panelFeatureSpecs = Object.freeze({",
        "const panelFeatureModulePromises = Object.create(null);",
        "const panelFeatureEnsurePromises = Object.create(null);",
        "function loadPanelFeatureModule(name) {",
        "function initPanelFeature(name, api) {",
        "const localApi = getPanelFeatureApiFromModule(key);",
        "restartLog: {",
        "serviceStatus: {",
        "routingTemplates: {",
        "github: {",
        "donate: {",
        "uiSettingsPanel: {",
        "mihomoImport: {",
        "mihomoProxyTools: {",
        "mihomoHwidSub: {",
        "unifiedTexts: {",
        "commandsList: {",
        "coresStatus: {",
        "import('../features/restart_log.js')",
        "import('../features/service_status.js')",
        "import('../features/routing_templates.js')",
        "import('../features/github.js').then(",
        "import('../features/compat/github.js').then(() => mod)",
        "import('../ui/settings_panel.js')",
        "import('../features/compat/mihomo_import.js').then(() => mod)",
        "import('../features/compat/mihomo_proxy_tools.js').then(() => mod)",
        "import('../features/compat/mihomo_hwid_sub.js').then(() => mod)",
    ]

    for fragment in required_fragments:
        assert fragment in text, (
            f"missing panel-local lazy binding fragment in panel.lazy_bindings.runtime.js: {fragment}"
        )


def test_panel_view_runtime_uses_panel_lazy_bindings_for_unified_and_commands_views():
    text = (PAGES_DIR / "panel.view_runtime.js").read_text(encoding="utf-8")

    required_fragments = [
        "import { ensurePanelLazyFeature, getPanelLazyRuntimeApi } from './panel.lazy_bindings.runtime.js';",
        "const ready = await ensurePanelLazyFeature('unifiedTexts');",
        "ensurePanelLazyFeature('commandsList'),",
        "ensurePanelLazyFeature('coresStatus'),",
    ]
    forbidden_fragments = [
        "function ensureLazyFeature(name) {",
        "ensureLazyFeature('unifiedTexts')",
        "ensureLazyFeature('commandsList')",
        "ensureLazyFeature('coresStatus')",
    ]

    for fragment in required_fragments:
        assert fragment in text, f"panel view runtime should use panel lazy bindings: {fragment}"
    for fragment in forbidden_fragments:
        assert fragment not in text, f"legacy panel view lazy helper should be removed: {fragment}"


def test_formatters_and_xray_preflight_use_direct_imports_in_consumers():
    expectations = {
        ROOT / "unified-ui" / "static" / "js" / "features" / "mihomo_panel.js": [
            "await import('../ui/prettier_loader.js');",
            "await import('../ui/formatters.js');",
        ],
        ROOT / "unified-ui" / "static" / "js" / "features" / "routing.js": [
            "await import('../ui/prettier_loader.js');",
            "await import('../ui/formatters.js');",
            "return import('../ui/xray_preflight_modal.js');",
        ],
        ROOT / "unified-ui" / "static" / "js" / "ui" / "json_editor_modal.js": [
            "await import('./prettier_loader.js');",
            "await import('./formatters.js');",
        ],
        ROOT / "unified-ui" / "static" / "js" / "ui" / "spinner_fetch.js": [
            "return import('./xray_preflight_modal.js');",
        ],
    }
    forbidden_fragments = [
        "ensureFeature('formatters')",
        "ensureFeature('xrayPreflight')",
    ]

    for path, fragments in expectations.items():
        text = path.read_text(encoding="utf-8")
        for fragment in fragments:
            assert fragment in text, f"missing direct-import fragment in {path.relative_to(ROOT).as_posix()}: {fragment}"
        for fragment in forbidden_fragments:
            assert fragment not in text, (
                f"consumer should not use lazy_runtime feature bridge in {path.relative_to(ROOT).as_posix()}: {fragment}"
            )


def test_routing_jsonc_preserve_uses_canonical_import_urls():
    files = [
        PAGES_DIR / "panel.routing.bundle.js",
        ROOT / "unified-ui" / "static" / "js" / "features" / "routing_cards" / "rules" / "apply.js",
        ROOT / "unified-ui" / "static" / "js" / "features" / "routing_cards" / "rules" / "model.js",
    ]

    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "routing_jsonc_preserve.js?v=" not in text, (
            f"routing jsonc preserve should be imported via canonical URL in {path.relative_to(ROOT).as_posix()}"
        )


def test_routing_compat_bridges_use_canonical_import_urls_and_explicit_shell_bridge():
    expectations = {
        PAGES_DIR / "panel.routing.bundle.js": [
            "import '../features/routing.js';",
            "import '../features/compat/routing.js';",
            "import '../features/compat/routing_shell.js';",
            "import { initRoutingCards } from '../features/routing_cards.js';",
            "import '../features/compat/routing_cards.js';",
            "initRoutingCards();",
        ],
        ROOT / "unified-ui" / "static" / "js" / "features" / "compat" / "routing.js": [
            "import { getRoutingApi } from '../routing.js';",
        ],
        ROOT / "unified-ui" / "static" / "js" / "features" / "compat" / "routing_cards.js": [
            "import { getRoutingCardsApi } from '../routing_cards.js';",
            "import { getRoutingCardsNamespace } from '../routing_cards_namespace.js';",
        ],
        ROOT / "unified-ui" / "static" / "js" / "features" / "routing_cards" / "ns.js": [
            "import { initRoutingCardsNamespace } from '../routing_cards_namespace.js';",
        ],
        ROOT / "unified-ui" / "static" / "js" / "features" / "routing_cards_namespace.js": [
            "let routingCardsNamespace = null;",
            "const RC = {};",
        ],
        ROOT / "unified-ui" / "static" / "js" / "features" / "compat" / "routing_shell.js": [
            "import { getRoutingShellApi } from '../routing_shell.js';",
            "UnifiedUI.features.routingShell = legacyRoutingShellApi;",
        ],
    }
    forbidden = {
        PAGES_DIR / "panel.routing.bundle.js": [
            "../features/routing.js?v=",
            "../features/routing_cards.js?v=",
        ],
        ROOT / "unified-ui" / "static" / "js" / "features" / "compat" / "routing.js": [
            "../routing.js?v=",
        ],
        ROOT / "unified-ui" / "static" / "js" / "features" / "compat" / "routing_cards.js": [
            "../routing_cards.js?v=",
        ],
        ROOT / "unified-ui" / "static" / "js" / "features" / "routing_cards_namespace.js": [
            "XK.features && XK.features.routingCards",
        ],
    }

    for path, fragments in expectations.items():
        text = path.read_text(encoding="utf-8")
        for fragment in fragments:
            assert fragment in text, f"missing routing compat fragment in {path.relative_to(ROOT).as_posix()}: {fragment}"

    for path, fragments in forbidden.items():
        text = path.read_text(encoding="utf-8")
        for fragment in fragments:
            assert fragment not in text, (
                f"routing compat should use canonical import URLs in {path.relative_to(ROOT).as_posix()}: {fragment}"
            )


def test_selected_page_runtime_modules_use_shared_runtime_adapters_instead_of_raw_window_unified_reads():
    expectations = {
        PAGES_DIR / "panel.lazy_bindings.runtime.js": [
            "from '../features/unified_runtime.js';",
        ],
        PAGES_DIR / "panel.core_ui_watch.runtime.js": [
            "from '../features/unified_runtime.js';",
        ],
        RUNTIME_DIR / "lazy_runtime.js": [
            "from '../features/unified_runtime.js';",
        ],
    }
    forbidden = {
        PAGES_DIR / "panel.lazy_bindings.runtime.js": [
            "window.UnifiedUI.runtime",
            "window.UnifiedUI.core",
            "window.openTerminal(",
        ],
        PAGES_DIR / "panel.core_ui_watch.runtime.js": [
            "window.UnifiedUI && UnifiedUI.core && UnifiedUI.core.http",
            "window.UnifiedUI && UnifiedUI.ui",
            "window.toast(",
            "UnifiedUI.jsonEditor",
            "window.confirm(",
        ],
        RUNTIME_DIR / "lazy_runtime.js": [
            "window.UnifiedUI && UnifiedUI.ui && UnifiedUI.ui.cm6Runtime",
            "window.UnifiedUI && UnifiedUI.ui && UnifiedUI.ui.editorActions",
            "XK.pages ? XK.pages.logsShell : null",
            "XK.pages ? XK.pages.configShell : null",
        ],
    }

    for path, fragments in expectations.items():
        text = path.read_text(encoding="utf-8")
        for fragment in fragments:
            assert fragment in text, f"missing runtime adapter import in {path.relative_to(ROOT).as_posix()}: {fragment}"

    for path, fragments in forbidden.items():
        text = path.read_text(encoding="utf-8")
        for fragment in fragments:
            assert fragment not in text, (
                f"page/runtime module should use shared runtime adapters instead of raw globals in {path.relative_to(ROOT).as_posix()}: {fragment}"
            )


def test_page_shell_helper_modules_use_unified_runtime_adapters_for_page_api_and_shell_access():
    expectations = {
        PAGES_DIR / "panel.view_runtime.js": [
            "from '../features/unified_runtime.js';",
            "getXkeenStateValue(",
            "hasXkeenXrayCore()",
            "syncXkeenBodyScrollLock()",
        ],
        PAGES_DIR / "panel_shell.shared.js": [
            "from '../features/unified_runtime.js';",
            "getXkeenCoreHttpApi()",
            "getXkeenUiShellApi()",
            "ensureXkeenUiBucket('tabs')",
            "publishXkeenPageApi('panelShell', api);",
            "getXkeenPageApi('panelShell')",
        ],
        PAGES_DIR / "config_shell.shared.js": [
            "from '../features/unified_runtime.js';",
            "getXkeenUiConfigShellApi()",
            "publishXkeenPageApi('configShell', {",
            "getXkeenPageApi('configShell')",
        ],
        PAGES_DIR / "logs_shell.shared.js": [
            "from '../features/unified_runtime.js';",
            "publishXkeenPageApi('logsShell', {",
            "getXkeenPageApi('logsShell')",
        ],
    }
    forbidden = {
        PAGES_DIR / "panel.view_runtime.js": [
            "window.UnifiedUI && UnifiedUI.state",
            "UnifiedUI.ui.modal.syncBodyScrollLock",
        ],
        PAGES_DIR / "panel_shell.shared.js": [
            "window.UnifiedUI && UnifiedUI.core && UnifiedUI.core.http",
            "window.UnifiedUI && UnifiedUI.core && UnifiedUI.core.uiShell",
            "XK.pages.panelShell = api;",
            "window.UnifiedUI && window.UnifiedUI.pages ? window.UnifiedUI.pages.panelShell : null",
        ],
        PAGES_DIR / "config_shell.shared.js": [
            "const api = XK.ui ? XK.ui.configShell : null;",
            "XK.pages.configShell = {",
            "window.UnifiedUI && window.UnifiedUI.pages ? window.UnifiedUI.pages.configShell : null",
        ],
        PAGES_DIR / "logs_shell.shared.js": [
            "XK.pages.logsShell = {",
            "window.UnifiedUI && window.UnifiedUI.pages ? window.UnifiedUI.pages.logsShell : null",
        ],
    }

    for path, fragments in expectations.items():
        text = path.read_text(encoding="utf-8")
        for fragment in fragments:
            assert fragment in text, (
                f"missing page helper runtime adapter fragment in {path.relative_to(ROOT).as_posix()}: {fragment}"
            )

    for path, fragments in forbidden.items():
        text = path.read_text(encoding="utf-8")
        for fragment in fragments:
            assert fragment not in text, (
                f"page helper should use unified runtime adapters instead of raw globals in {path.relative_to(ROOT).as_posix()}: {fragment}"
            )


def test_terminal_runtime_helper_and_core_modules_use_terminal_runtime_adapters():
    runtime_src = (ROOT / "unified-ui" / "static" / "js" / "terminal" / "runtime.js").read_text(encoding="utf-8")
    required_runtime_fragments = [
        "export function ensureTerminalRoot()",
        "export function ensureTerminalCompatState(defaults)",
        "export function ensureTerminalNamespaceBucket(name)",
        "export function getTerminalContext()",
        "export function publishTerminalCompatApi(name, api)",
        "export function publishWindowCompatFunction(name, fn)",
        "export function computeTerminalTabId()",
        "export function getTerminalCoreApi()",
        "export function getTerminalMode(ctx)",
        "export function getTerminalUiActionsApi()",
        "export function getTerminalExecCommand()",
        "export function focusTerminalView()",
        "export function isTerminalPtyConnected()",
        "export function openTerminalCompat(options)",
        "export function escapeTerminalHtml(text)",
        "export function openTerminalModal(modal, source, fallbackLocked)",
        "export function closeTerminalModal(modal, source, fallbackLocked)",
    ]
    for fragment in required_runtime_fragments:
        assert fragment in runtime_src, f"missing terminal runtime helper fragment: {fragment}"

    expectations = {
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "_core.js": [
            "from './runtime.js';",
            "publishTerminalCompatApi('_core', terminalCoreApi);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "capabilities.js": [
            "from './runtime.js';",
            "publishTerminalCompatApi('capabilities', {",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "history.js": [
            "from './runtime.js';",
            "publishTerminalCompatApi('history', {",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "lite_runner.js": [
            "from './runtime.js';",
            "publishTerminalCompatApi('lite_runner', terminalLiteRunnerApi);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "terminal.js": [
            "from './runtime.js';",
            "publishWindowCompatFunction('terminalOpen', (a, b) => {",
            "publishWindowCompatFunction('openTerminal', (cmd, mode) => uiActions.openTerminal(cmd, mode || 'shell'));",
        ],
    }
    forbidden = {
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "_core.js": [
            "window.UnifiedUI.terminal",
            "window.UnifiedUI.state",
            "UnifiedUI.util.getTabId",
            "UnifiedUI.ui.modal",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "capabilities.js": [
            "window.UnifiedUI.terminal",
            "window.UnifiedUI.state",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "history.js": [
            "window.UnifiedUI.terminal",
            "UnifiedUI.ui.modal",
            "window.showToast(",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "lite_runner.js": [
            "(window.UnifiedUI && UnifiedUI.util && UnifiedUI.util.commandJob)",
            "window.UnifiedUI.terminal",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "terminal.js": [
            "window.UnifiedUI.terminal",
            "window.UnifiedUI.state",
        ],
    }

    for path, fragments in expectations.items():
        text = path.read_text(encoding="utf-8")
        for fragment in fragments:
            assert fragment in text, f"missing terminal runtime adapter fragment in {path.relative_to(ROOT).as_posix()}: {fragment}"

    for path, fragments in forbidden.items():
        text = path.read_text(encoding="utf-8")
        for fragment in fragments:
            assert fragment not in text, (
                f"terminal core module should use terminal runtime adapters instead of raw globals in {path.relative_to(ROOT).as_posix()}: {fragment}"
            )


def test_terminal_side_modules_use_terminal_runtime_adapters_instead_of_raw_window_unified_reads():
    expectations = {
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "chrome.js": [
            "from './runtime.js';",
            "publishTerminalCompatApi('chrome', terminalChromeApi);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "pty.js": [
            "from './runtime.js';",
            "getTerminalContext()",
            "getTerminalMode()",
            "toastTerminal('PTY не подключён', 'info');",
            "publishTerminalCompatApi('pty', terminalPtyApi);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "quick_commands.js": [
            "from './runtime.js';",
            "escapeTerminalHtml(",
            "getTerminalExecCommand()",
            "isTerminalPtyConnected()",
            "publishTerminalCompatApi('quick_commands', terminalQuickCommandsApi);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "search.js": [
            "from './runtime.js';",
            "focusTerminalView()",
            "toastTerminal(",
            "publishTerminalCompatApi('search', terminalSearchApi);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "xray_tail.js": [
            "from './runtime.js';",
            "openTerminalCompat({ mode: 'pty', cmd: '' });",
            "isTerminalPtyConnected()",
            "publishTerminalCompatApi('xray_tail', terminalXrayTailApi);",
            "publishTerminalCompatApi('xrayTail', terminalXrayTailApi);",
        ],
    }
    forbidden = {
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "chrome.js": [
            "window.UnifiedUI.terminal",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "pty.js": [
            "window.UnifiedUI.terminal",
            "typeof showToast === 'function'",
            "window.UnifiedUI && window.UnifiedUI.state",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "quick_commands.js": [
            "window.UnifiedUI.terminal",
            "window.showToast(",
            "window.escapeHtml",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "search.js": [
            "window.UnifiedUI.terminal",
            "window.showToast(",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "xray_tail.js": [
            "window.UnifiedUI.terminal",
            "window.UnifiedUI = window.UnifiedUI || {};",
        ],
    }

    for path, fragments in expectations.items():
        text = path.read_text(encoding="utf-8")
        for fragment in fragments:
            assert fragment in text, (
                f"missing terminal side-module runtime adapter fragment in {path.relative_to(ROOT).as_posix()}: {fragment}"
            )

    for path, fragments in forbidden.items():
        text = path.read_text(encoding="utf-8")
        for fragment in fragments:
            assert fragment not in text, (
                f"terminal side module should use runtime adapters instead of raw globals in {path.relative_to(ROOT).as_posix()}: {fragment}"
            )


def test_deeper_terminal_core_transport_and_command_modules_use_runtime_adapter_publishers():
    runtime_src = (ROOT / "unified-ui" / "static" / "js" / "terminal" / "runtime.js").read_text(encoding="utf-8")
    required_runtime_fragments = [
        "export function ensureTerminalCoreRoot()",
        "export function ensureTerminalTransportRoot()",
        "export function ensureTerminalCommandsRoot()",
        "export function ensureTerminalCommandBuiltinsRoot()",
        "export function publishTerminalCoreCompatApi(name, api)",
        "export function publishTerminalTransportCompatApi(name, api)",
        "export function publishTerminalCommandsCompatApi(name, api)",
        "export function publishTerminalBuiltinCommandCompatApi(name, api)",
    ]
    for fragment in required_runtime_fragments:
        assert fragment in runtime_src, f"missing deeper terminal runtime helper fragment: {fragment}"

    expectations = {
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "api.js": [
            "from '../runtime.js';",
            "getTerminalCommandJobApi()",
            "publishTerminalCoreCompatApi('createApi', createApi);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "config.js": [
            "from '../runtime.js';",
            "publishTerminalCoreCompatApi('createConfig', createConfig);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "events.js": [
            "from '../runtime.js';",
            "publishTerminalCoreCompatApi('createEventBus', createEventBus);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "logger.js": [
            "from '../runtime.js';",
            "publishTerminalCoreCompatApi('createLogger', createLogger);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "registry.js": [
            "from '../runtime.js';",
            "publishTerminalCoreCompatApi('createRegistry', createRegistry);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "state.js": [
            "from '../runtime.js';",
            "publishTerminalCoreCompatApi('defaultState', defaultState);",
            "publishTerminalCoreCompatApi('createStateStore', createStateStore);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "ui.js": [
            "from '../runtime.js';",
            "getTerminalById(",
            "toastTerminal(",
            "publishTerminalCoreCompatApi('createUiAdapter', createUiAdapter);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "context.js": [
            "from '../runtime.js';",
            "getTerminalCoreCompatApi('createEventBus')",
            "getTerminalTransportCompatApi('createTransportManager')",
            "getTerminalCompatApi('lite_runner')",
            "publishTerminalCoreCompatApi('createTerminalContext', createTerminalContext);",
            "publishTerminalCoreCompatApi('getCtx', getCtx);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "transport" / "index.js": [
            "from '../runtime.js';",
            "getTerminalTransportCompatApi('createPtyTransport')",
            "getTerminalTransportCompatApi('createLiteTransport')",
            "publishTerminalTransportCompatApi('createTransportManager', createTransportManager);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "transport" / "lite_transport.js": [
            "from '../runtime.js';",
            "getTerminalCommandJobApi()",
            "getTerminalMode(ctx)",
            "publishTerminalTransportCompatApi('createLiteTransport', createLiteTransport);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "transport" / "pty_transport.js": [
            "from '../runtime.js';",
            "getTerminalPtyApi()",
            "publishTerminalTransportCompatApi('createPtyTransport', createPtyTransport);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "commands" / "registry.js": [
            "from '../runtime.js';",
            "publishTerminalCommandsCompatApi('createCommandRegistry', createCommandRegistry);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "commands" / "router.js": [
            "from '../runtime.js';",
            "publishTerminalCommandsCompatApi('createCommandRouter', createCommandRouter);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "commands" / "builtins" / "sysmon.js": [
            "from '../../runtime.js';",
            "getTerminalCommandJobApi()",
            "publishTerminalBuiltinCommandCompatApi('sysmon', commandDef);",
            "publishTerminalBuiltinCommandCompatApi('registerSysmon', register);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "commands" / "builtins" / "unified_restart.js": [
            "from '../../runtime.js';",
            "publishTerminalBuiltinCommandCompatApi('unified_restart', commandDef);",
            "publishTerminalBuiltinCommandCompatApi('registerXkeenRestart', register);",
        ],
    }
    forbidden = {
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "api.js": [
            "window.UnifiedUI.terminal.core",
            "UnifiedUI.util.commandJob",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "config.js": [
            "window.UnifiedUI.terminal.core",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "events.js": [
            "window.UnifiedUI.terminal.core",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "logger.js": [
            "window.UnifiedUI.terminal.core",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "registry.js": [
            "window.UnifiedUI.terminal.core",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "state.js": [
            "window.UnifiedUI.terminal.core",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "ui.js": [
            "window.UnifiedUI.terminal.core",
            "window.showToast(",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "context.js": [
            "window.UnifiedUI.terminal.core.createEventBus",
            "window.UnifiedUI.terminal.transport",
            "window.UnifiedUI.terminal.ctx",
            "window.UnifiedUI.terminal._core",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "transport" / "index.js": [
            "window.UnifiedUI.terminal.transport",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "transport" / "lite_transport.js": [
            "window.UnifiedUI.util.commandJob",
            "window.UnifiedUI.terminal.transport",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "transport" / "pty_transport.js": [
            "window.UnifiedUI.terminal.pty",
            "window.UnifiedUI.terminal.transport",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "commands" / "registry.js": [
            "window.UnifiedUI.terminal.commands",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "commands" / "router.js": [
            "window.UnifiedUI.terminal.commands",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "commands" / "builtins" / "sysmon.js": [
            "window.UnifiedUI.terminal.commands",
            "window.UnifiedUI.util",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "commands" / "builtins" / "unified_restart.js": [
            "window.UnifiedUI.terminal.commands",
        ],
    }

    for path, fragments in expectations.items():
        text = path.read_text(encoding="utf-8")
        for fragment in fragments:
            assert fragment in text, (
                f"missing deeper terminal adapter fragment in {path.relative_to(ROOT).as_posix()}: {fragment}"
            )

    for path, fragments in forbidden.items():
        text = path.read_text(encoding="utf-8")
        for fragment in fragments:
            assert fragment not in text, (
                f"deeper terminal compat module should use runtime adapters instead of raw globals in {path.relative_to(ROOT).as_posix()}: {fragment}"
            )


def test_terminal_remaining_core_controllers_and_modules_use_runtime_adapters():
    expectations = {
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "input_controller.js": [
            "from '../runtime.js';",
            "getTerminalHistoryApi()",
            "publishTerminalCoreCompatApi('createInputController', createInputController);",
            "publishTerminalCompatApi('input_controller', {",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "output_controller.js": [
            "from '../runtime.js';",
            "getTerminalHistoryApi()",
            "publishTerminalCoreCompatApi('createOutputController', createOutputController);",
            "publishTerminalCompatApi('output_controller', {",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "public_api.js": [
            "from '../runtime.js';",
            "getTerminalContext()",
            "publishTerminalCompatApi('api', createPublicApi());",
            "publishTerminalCoreCompatApi('createPublicApi', createPublicApi);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "session_controller.js": [
            "from '../runtime.js';",
            "getTerminalPtyApi()",
            "publishTerminalCoreCompatApi('createSessionController', createSessionController);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "xterm_manager.js": [
            "from '../runtime.js';",
            "toastTerminal(String(msg || ''), kind || 'info');",
            "getTerminalCoreApi()",
            "publishTerminalCoreCompatApi('xterm_manager', terminalXtermManagerApi);",
            "publishTerminalCompatApi('xterm_manager', terminalXtermManagerApi);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "modules" / "confirm_prompt.js": [
            "from '../runtime.js';",
            "getTerminalMode(ctx)",
            "getTerminalPublicApi()",
            "publishTerminalCompatApi('confirmPrompt', mod);",
            "publishTerminalCompatApi('confirm_prompt', terminalConfirmPromptCompat);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "modules" / "output_prefs.js": [
            "from '../runtime.js';",
            "toastTerminal(m, k);",
            "publishTerminalCompatApi('outputPrefs', prefs);",
            "publishTerminalCompatApi('output_prefs', terminalOutputPrefsCompat);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "modules" / "overlay_controller.js": [
            "from '../runtime.js';",
            "getTerminalModalApi()",
            "publishTerminalCompatApi('overlay', api);",
            "publishTerminalCompatApi('overlay_controller', terminalOverlayControllerCompat);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "modules" / "reconnect_controller.js": [
            "from '../runtime.js';",
            "getTerminalCoreApi()",
            "getTerminalOverlayApi()",
            "publishTerminalCompatApi('reconnect', controller);",
            "publishTerminalCompatApi('reconnect_controller', terminalReconnectControllerCompat);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "modules" / "status_controller.js": [
            "from '../runtime.js';",
            "getTerminalCoreApi()",
            "publishTerminalCompatApi('status', api);",
            "publishTerminalCompatApi('status_controller', terminalStatusControllerCompat);",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "modules" / "ssh_profiles.js": [
            "from '../runtime.js';",
            "toastTerminal(String(msg || ''), kind || 'info');",
            "publishTerminalCompatApi('ssh_profiles', { createModule });",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "modules" / "terminal_controller.js": [
            "from '../runtime.js';",
            "getTerminalContext()",
            "getTerminalChromeApi()",
            "getTerminalPtyApi()",
            "getTerminalSearchApi()",
            "publishTerminalCompatApi('terminalCtrl', api);",
            "publishTerminalCompatApi('terminal_controller', {",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "modules" / "ui_controller.js": [
            "from '../runtime.js';",
            "getTerminalUiActionsApi() || {};",
            "getTerminalPtyApi()",
            "getTerminalPublicApi()",
            "getTerminalReconnectApi()",
            "publishTerminalCompatApi('ui_controller', { createModule });",
        ],
    }
    forbidden = {
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "input_controller.js": [
            "window.UnifiedUI.terminal.history",
            "window.showToast(",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "output_controller.js": [
            "window.UnifiedUI.terminal.history",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "public_api.js": [
            "window.UnifiedUI.terminal.api",
            "window.UnifiedUI.terminal._legacy",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "session_controller.js": [
            "window.UnifiedUI.terminal.pty",
            "window.UnifiedUI.terminal._core",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "xterm_manager.js": [
            "window.UnifiedUI.terminal",
            "window.showToast(",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "modules" / "confirm_prompt.js": [
            "window.UnifiedUI.terminal.api",
            "window.UnifiedUI = window.UnifiedUI || {};",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "modules" / "output_prefs.js": [
            "window.showToast(",
            "window.UnifiedUI.terminal.output_prefs",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "modules" / "overlay_controller.js": [
            "window.UnifiedUI.ui.modal",
            "window.UnifiedUI.terminal.overlay_controller",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "modules" / "reconnect_controller.js": [
            "window.UnifiedUI.terminal.overlay",
            "window.UnifiedUI.terminal.reconnect_controller",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "modules" / "status_controller.js": [
            "window.UnifiedUI.terminal.status",
            "window.UnifiedUI.terminal.status_controller",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "modules" / "ssh_profiles.js": [
            "window.showToast(",
            "window.UnifiedUI.terminal.ssh_profiles",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "modules" / "terminal_controller.js": [
            "window.UnifiedUI.terminal.terminalCtrl",
            "window.UnifiedUI.terminal.terminal_controller",
            "window.showToast(",
        ],
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "modules" / "ui_controller.js": [
            "window.UnifiedUI.terminal.ui_actions",
            "window.UnifiedUI.terminal.open",
            "window.UnifiedUI.terminal.close",
            "window.UnifiedUI.terminal.pty",
            "window.UnifiedUI.terminal.ui_controller",
        ],
    }

    for path, fragments in expectations.items():
        text = path.read_text(encoding="utf-8")
        for fragment in fragments:
            assert fragment in text, (
                f"missing terminal controller/module runtime adapter fragment in {path.relative_to(ROOT).as_posix()}: {fragment}"
            )

    for path, fragments in forbidden.items():
        text = path.read_text(encoding="utf-8")
        for fragment in fragments:
            assert fragment not in text, (
                f"terminal controller/module should use runtime adapters instead of raw globals in {path.relative_to(ROOT).as_posix()}: {fragment}"
            )


def test_templates_publish_final_page_config_contract():
    panel_src = (ROOT / "unified-ui" / "templates" / "panel.html").read_text(encoding="utf-8")
    devtools_src = (ROOT / "unified-ui" / "templates" / "devtools.html").read_text(encoding="utf-8")
    mihomo_src = (ROOT / "unified-ui" / "templates" / "mihomo_generator.html").read_text(encoding="utf-8")

    panel_required = [
        "frontend_page_config(",
        "'panel'",
        "window.UnifiedUI.pageConfig = pageConfig;",
        "<script type=\"module\" src=\"{{ frontend_page_entry_url('panel') }}\"></script>",
    ]
    panel_forbidden = [
        "window.UnifiedUI.env = window.UnifiedUI.env || {};",
        "window.UnifiedUI.env.panelSectionsWhitelist",
        "window.UnifiedUI.env.devtoolsSectionsWhitelist",
        "window.UNIFIED_GITHUB_REPO_URL",
        "window.UNIFIED_STATIC_BASE",
        "window.UNIFIED_IS_MIPS",
        "window.UNIFIED_AVAILABLE_CORES",
        "window.UNIFIED_DETECTED_CORES",
        "window.UNIFIED_CORE_UI_FALLBACK",
        "window.UNIFIED_HAS_XRAY",
        "window.UNIFIED_HAS_MIHOMO",
        "window.UNIFIED_MIHOMO_CONFIG_EXISTS",
        "window.UNIFIED_MULTI_CORE",
        "window.UNIFIED_STATIC_VER",
        "window.UNIFIED_FILES",
        "window.UNIFIED_FM_RIGHT_DEFAULT",
    ]

    devtools_required = [
        "frontend_page_config(",
        "'devtools'",
        "window.UnifiedUI.pageConfig = pageConfig;",
        "<script type=\"module\" src=\"{{ frontend_page_entry_url('devtools') }}\"></script>",
    ]
    devtools_forbidden = [
        "window.UnifiedUI.env = window.UnifiedUI.env || {};",
        "window.UnifiedUI.env.panelSectionsWhitelist",
        "window.UnifiedUI.env.devtoolsSectionsWhitelist",
    ]
    mihomo_required = [
        "frontend_page_config(",
        "'mihomo_generator'",
        "window.UnifiedUI.pageConfig = pageConfig;",
        "<script type=\"module\" src=\"{{ frontend_page_entry_url('mihomo_generator') }}\"></script>",
    ]
    mihomo_forbidden = [
        "window.UnifiedUI.env = window.UnifiedUI.env || {};",
        "window.UnifiedUI.env.panelSectionsWhitelist",
        "window.UnifiedUI.env.devtoolsSectionsWhitelist",
    ]

    for fragment in panel_required:
        assert fragment in panel_src, f"missing panel final page-config fragment: {fragment}"
    for fragment in panel_forbidden:
        assert fragment not in panel_src, f"panel template should publish only final pageConfig contract: {fragment}"

    for fragment in devtools_required:
        assert fragment in devtools_src, f"missing devtools final page-config fragment: {fragment}"
    for fragment in devtools_forbidden:
        assert fragment not in devtools_src, f"devtools template should publish only final pageConfig contract: {fragment}"

    for fragment in mihomo_required:
        assert fragment in mihomo_src, f"missing mihomo_generator final page-config fragment: {fragment}"
    for fragment in mihomo_forbidden:
        assert fragment not in mihomo_src, f"mihomo_generator template should publish only final pageConfig contract: {fragment}"


def test_runtime_page_config_contract_no_longer_syncs_legacy_aliases():
    runtime_src = (ROOT / "unified-ui" / "static" / "js" / "features" / "unified_runtime.js").read_text(encoding="utf-8")

    required = [
        "export function getXkeenPageConfigValue(path, fallbackValue = undefined)",
        "export function setXkeenPageConfigValue(path, value)",
        "export function getXkeenRuntimeConfig()",
        "export function getXkeenTerminalConfig()",
        "function coerceXkeenBooleanValue(value, fallbackValue = false) {",
    ]
    forbidden = [
        "syncLegacyPageConfigAlias(",
        "getXkeenLegacyPageConfigValue(",
        "win.UnifiedUI.env.panelSectionsWhitelist",
        "win.UnifiedUI.env.devtoolsSectionsWhitelist",
        "win.UNIFIED_FILES",
        "win.UNIFIED_GITHUB_REPO_URL",
        "win.UNIFIED_STATIC_BASE",
        "win.UNIFIED_IS_MIPS",
        "function getRawWindowFlag(",
        "function getXkeenLegacyEnvValue(",
        "const WINDOW_FLAG_PAGE_CONFIG_PATHS = Object.freeze({",
        "export function getXkeenWindowFlag(",
        "export function getXkeenBooleanFlag(",
    ]

    for fragment in required:
        assert fragment in runtime_src, f"missing runtime final page-config fragment in unified_runtime.js: {fragment}"
    for fragment in forbidden:
        assert fragment not in runtime_src, (
            f"runtime page-config contract should no longer sync legacy aliases in unified_runtime.js: {fragment}"
        )



def test_stage6_consumer_sweep_uses_runtime_page_config_helpers_in_canonical_readers():
    expectations = {
        ROOT / "unified-ui" / "static" / "js" / "ui" / "sections.js": {
            "required": [
                "typeof XK.runtime.getPageSectionsConfig === 'function'",
                "XK.pageConfig",
            ],
            "forbidden": [
                "window.UnifiedUI.env.panelSectionsWhitelist",
                "window.UnifiedUI.env.devtoolsSectionsWhitelist",
                "const env = (XK && XK.env) ? XK.env : {};",
                "panelSectionsWhitelist",
                "devtoolsSectionsWhitelist",
            ],
        },
        PAGES_DIR / "panel.screen.bootstrap.js": {
            "required": [
                "hasXkeenXrayCore()",
                "hasXkeenMihomoCore()",
            ],
            "forbidden": [
                "window.UNIFIED_HAS_XRAY",
                "window.UNIFIED_HAS_MIHOMO",
            ],
        },
        PAGES_DIR / "panel.init.js": {
            "required": [
                "import { hasXkeenXrayCore } from '../features/unified_runtime.js';",
                "return hasXkeenXrayCore();",
            ],
            "forbidden": [
                "window.UNIFIED_HAS_XRAY",
            ],
        },
        PAGES_DIR / "panel.core_ui_watch.runtime.js": {
            "required": [
                "getXkeenPageCoresConfig",
                "const cores = getXkeenPageCoresConfig();",
            ],
            "forbidden": [
                "window.UNIFIED_DETECTED_CORES",
                "window.UNIFIED_AVAILABLE_CORES",
                "window.UNIFIED_CORE_UI_FALLBACK",
            ],
        },
        PAGES_DIR / "panel.lazy_bindings.runtime.js": {
            "required": [
                "getXkeenGithubRepoUrl",
                "api.init({ repoUrl: getXkeenGithubRepoUrl() });",
            ],
            "forbidden": [
                "window.UNIFIED_GITHUB_REPO_URL",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "ui" / "monaco_loader.js": {
            "required": [
                "import { getXkeenStaticBase } from '../features/unified_runtime.js';",
                "const configured = String(getXkeenStaticBase() || '').trim();",
            ],
            "forbidden": [
                "window.UNIFIED_STATIC_BASE",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "ui" / "config_shell.js": {
            "required": [
                "import { setXkeenPageConfigValue } from '../features/unified_runtime.js';",
                "setXkeenPageConfigValue('files.' + name, nextPath);",
            ],
            "forbidden": [
                "window.UNIFIED_FILES = window.UNIFIED_FILES || {};",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "ui" / "last_activity.js": {
            "required": [
                "import { getXkeenFilePath } from '../features/unified_runtime.js';",
                "getXkeenFilePath('mihomo',",
                "getXkeenFilePath('routing', \"/opt/etc/xray/configs/05_routing.json\")",
            ],
            "forbidden": [
                "window.UNIFIED_FILES",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "ui" / "json_editor_modal.js": {
            "required": [
                "getXkeenFilePath",
                "getXkeenPageFilesConfig",
            ],
            "forbidden": [
                "window.UNIFIED_FILES && window.UNIFIED_FILES",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "features" / "routing.js": {
            "required": [
                "getXkeenFilePath",
                "isXkeenMipsRuntime",
            ],
            "forbidden": [
                "window.UNIFIED_IS_MIPS",
                "window.UNIFIED_FILES",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "features" / "inbounds.js": {
            "required": [
                "getXkeenFilePath('inbounds', '')",
            ],
            "forbidden": [
                "window.UNIFIED_FILES",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "features" / "outbounds.js": {
            "required": [
                "getXkeenFilePath('outbounds', '')",
            ],
            "forbidden": [
                "window.UNIFIED_FILES",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "features" / "backups.js": {
            "required": [
                "getXkeenPageFilesConfig",
            ],
            "forbidden": [
                "window.UNIFIED_FILES",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "features" / "github.js": {
            "required": [
                "getXkeenGithubRepoUrl",
                "_repoUrl || getXkeenGithubRepoUrl()",
            ],
            "forbidden": [
                "window.UNIFIED_GITHUB_REPO_URL",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "features" / "mihomo_panel.js": {
            "required": [
                "getXkeenPageFlagsConfig",
                "setXkeenPageConfigValue('flags.mihomoConfigExists', true);",
                "getXkeenFilePath('mihomo',",
            ],
            "forbidden": [
                "window.UNIFIED_MIHOMO_CONFIG_EXISTS",
                "window.UNIFIED_FILES",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "features" / "mihomo_import.js": {
            "required": [
                "getXkeenFilePath('mihomo',",
            ],
            "forbidden": [
                "window.UNIFIED_FILES",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "features" / "mihomo_proxy_tools.js": {
            "required": [
                "getXkeenFilePath('mihomo',",
            ],
            "forbidden": [
                "window.UNIFIED_FILES",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "features" / "mihomo_hwid_sub.js": {
            "required": [
                "getXkeenFilePath('mihomo',",
            ],
            "forbidden": [
                "window.UNIFIED_FILES",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "features" / "file_manager" / "common.js": {
            "required": [
                "import { isXkeenMipsRuntime } from '../unified_runtime.js';",
                "return isXkeenMipsRuntime();",
            ],
            "forbidden": [
                "window.UNIFIED_IS_MIPS",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "features" / "file_manager" / "state.js": {
            "required": [
                "getXkeenFileManagerDefaults",
                "isXkeenMipsRuntime(),",
                "getXkeenFileManagerDefaults().rightDefault || '/tmp/mnt'",
            ],
            "forbidden": [
                "window.UNIFIED_IS_MIPS",
                "window.UNIFIED_FM_RIGHT_DEFAULT",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "features" / "file_manager.js": {
            "required": [
                "import { isXkeenMipsRuntime } from './unified_runtime.js';",
                "return isXkeenMipsRuntime();",
            ],
            "forbidden": [
                "window.UNIFIED_IS_MIPS",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "features" / "xray_logs.js": {
            "required": [
                "isXkeenMipsRuntime",
                "if (isXkeenMipsRuntime()) return true;",
            ],
            "forbidden": [
                "window.UNIFIED_IS_MIPS",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "features" / "routing_cards" / "rules" / "controls.js": {
            "required": [
                "import { isXkeenMipsRuntime } from '../../unified_runtime.js';",
                "return isXkeenMipsRuntime();",
            ],
            "forbidden": [
                "window.UNIFIED_IS_MIPS",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "features" / "routing_cards" / "rules" / "render.js": {
            "required": [
                "import { isXkeenMipsRuntime } from '../../unified_runtime.js';",
                "return isXkeenMipsRuntime();",
            ],
            "forbidden": [
                "window.UNIFIED_IS_MIPS",
            ],
        },
    }

    for path, fragments in expectations.items():
        text = path.read_text(encoding="utf-8")
        for fragment in fragments["required"]:
            assert fragment in text, (
                f"missing stage-6 consumer-sweep helper fragment in {path.relative_to(ROOT).as_posix()}: {fragment}"
            )
        for fragment in fragments["forbidden"]:
            assert fragment not in text, (
                f"consumer should not read legacy template globals directly in {path.relative_to(ROOT).as_posix()}: {fragment}"
            )





def test_editor_json_and_terminal_cluster_use_runtime_adapters_instead_of_raw_globals():
    expectations = {
        ROOT / "unified-ui" / "static" / "js" / "features" / "file_manager" / "editor.js": {
            "required": [
                "attachXkeenEditorToolbar",
                "getXkeenEditorToolbarDefaultItems",
                "getXkeenEditorToolbarIcons",
            ],
            "forbidden": [
                "window.UNIFIED_CM_",
                "window.unifiedAttachCmToolbar",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "ui" / "json_editor_modal.js": {
            "required": [
                "attachXkeenEditorToolbar",
                "getXkeenEditorToolbarMiniItems",
            ],
            "forbidden": [
                "window.UNIFIED_CM_",
                "window.unifiedAttachCmToolbar",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "ui" / "editor_toolbar.js": {
            "required": [
                "icons: UNIFIED_CM_ICONS",
                "defaultItems: UNIFIED_CM_TOOLBAR_DEFAULT",
                "miniItems: UNIFIED_CM_TOOLBAR_MINI",
                "window.UNIFIED_CM_ICONS = window.UNIFIED_CM_ICONS || UNIFIED_CM_ICONS;",
            ],
            "forbidden": [
                "icons: window.UNIFIED_CM_ICONS || UNIFIED_CM_ICONS",
                "defaultItems: window.UNIFIED_CM_TOOLBAR_DEFAULT || UNIFIED_CM_TOOLBAR_DEFAULT",
                "miniItems: window.UNIFIED_CM_TOOLBAR_MINI || UNIFIED_CM_TOOLBAR_MINI",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "terminal" / "core" / "xterm_manager.js": {
            "required": [
                "shouldEnableXkeenTerminalOptionalAddons",
                "shouldEnableXkeenTerminalLigatures",
                "shouldEnableXkeenTerminalWebgl",
                "shouldEnableXkeenTerminalOptionalAddons();",
                "shouldEnableXkeenTerminalLigatures()",
                "shouldEnableXkeenTerminalWebgl()",
            ],
            "forbidden": [
                "window.UNIFIED_ENABLE_XTERM_OPTIONAL_ADDONS",
                "window.UNIFIED_ENABLE_XTERM_LIGATURES",
                "window.UNIFIED_ENABLE_XTERM_WEBGL",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "runtime" / "lazy_runtime.js": {
            "required": [
                "getXkeenEditorToolbarApi",
                "const editorToolbar = getXkeenEditorToolbarApi();",
                "typeof editorToolbar.attach === 'function'",
                "isXkeenDebugRuntime",
                "const isDebug = isXkeenDebugRuntime();",
            ],
            "forbidden": [
                "window.UNIFIED_DEV",
                "window.unifiedAttachCmToolbar",
                "window.buildCmExtraKeysCommon",
                "XK.lazy = XK.lazy || {}",
            ],
        },
    }

    for path, fragments in expectations.items():
        text = path.read_text(encoding="utf-8")
        for fragment in fragments["required"]:
            assert fragment in text, (
                f"missing stage-5/6 runtime-adapter fragment in {path.relative_to(ROOT).as_posix()}: {fragment}"
            )
        for fragment in fragments["forbidden"]:
            assert fragment not in text, (
                f"canonical consumer should not read raw globals directly in {path.relative_to(ROOT).as_posix()}: {fragment}"
            )


def test_routing_and_mihomo_cluster_use_toolbar_runtime_adapters_instead_of_raw_toolbar_globals():
    expectations = {
        ROOT / "unified-ui" / "static" / "js" / "features" / "routing.js": {
            "required": [
                "attachXkeenEditorToolbar",
                "buildXkeenEditorCommonKeys",
                "getXkeenEditorToolbarDefaultItems",
                "getXkeenEditorToolbarIcons",
            ],
            "forbidden": [
                "window.UNIFIED_CM_",
                "window.unifiedAttachCmToolbar",
                "window.buildCmExtraKeysCommon",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "features" / "mihomo_panel.js": {
            "required": [
                "attachXkeenEditorToolbar",
                "buildXkeenEditorCommonKeys",
                "getXkeenEditorToolbarDefaultItems",
                "getXkeenEditorToolbarMiniItems",
                "getXkeenEditorToolbarIcons",
            ],
            "forbidden": [
                "window.UNIFIED_CM_",
                "window.unifiedAttachCmToolbar",
                "window.buildCmExtraKeysCommon",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "features" / "mihomo_generator.js": {
            "required": [
                "attachXkeenEditorToolbar",
                "buildXkeenEditorCommonKeys",
                "getXkeenEditorToolbarDefaultItems",
                "getXkeenEditorToolbarMiniItems",
                "getXkeenEditorToolbarIcons",
            ],
            "forbidden": [
                "window.UNIFIED_CM_",
                "window.unifiedAttachCmToolbar",
                "window.buildCmExtraKeysCommon",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "features" / "routing_cards.js": {
            "required": [
                "isXkeenDebugRuntime",
                "IS_DEBUG = isXkeenDebugRuntime();",
            ],
            "forbidden": [
                "window.UNIFIED_DEV",
            ],
        },
        ROOT / "unified-ui" / "static" / "js" / "features" / "unified_runtime.js": {
            "required": [
                "export function getXkeenEditorToolbarApi()",
                "export function getXkeenEditorToolbarIcons()",
                "export function getXkeenEditorToolbarDefaultItems()",
                "export function getXkeenEditorToolbarMiniItems()",
                "export function attachXkeenEditorToolbar(editor, items, options)",
                "export function getXkeenRuntimeConfig()",
                "export function getXkeenTerminalConfig()",
                "export function isXkeenDebugRuntime()",
                "return !!getXkeenRuntimeConfig().debug;",
            ],
            "forbidden": [
                "window.location.search",
                "debug=1",
                "function getRawWindowFlag(",
                "function getXkeenLegacyEnvValue(",
                "const WINDOW_FLAG_PAGE_CONFIG_PATHS = Object.freeze({",
                "export function getXkeenWindowFlag(",
                "export function getXkeenBooleanFlag(",
            ],
        },
    }

    for path, fragments in expectations.items():
        text = path.read_text(encoding="utf-8")
        for fragment in fragments["required"]:
            assert fragment in text, (
                f"missing toolbar/debug runtime helper fragment in {path.relative_to(ROOT).as_posix()}: {fragment}"
            )
        for fragment in fragments["forbidden"]:
            assert fragment not in text, (
                f"routing/mihomo canonical consumer should not read raw toolbar/debug globals in {path.relative_to(ROOT).as_posix()}: {fragment}"
            )
