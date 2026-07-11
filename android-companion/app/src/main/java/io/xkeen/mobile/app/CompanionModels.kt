package io.xkeen.mobile.app

enum class AppPhase {
    Launching,
    Connections,
    PairLogin,
    Ready,
}

enum class MainTab {
    Home,
    Routing,
    Logs,
    More,
}

enum class ConnectionStatus {
    Offline,
    NeedsAuth,
    Configured,
    SetupRequired,
}

enum class ServiceState {
    Running,
    Stopped,
    Restarting,
}

enum class LogLevel {
    Info,
    Warning,
    Error,
}

enum class LogFilter {
    All,
    Service,
    Routing,
    Errors,
}

enum class RoutingMode {
    Read,
    Edit,
}

enum class RoutingValidationState {
    Idle,
    Dirty,
    Valid,
    Invalid,
}

enum class DiagnosticSeverity {
    Ok,
    Warning,
    Error,
}

enum class ServiceAction(val label: String) {
    Start("Start"),
    Stop("Stop"),
    Restart("Restart"),
}

data class Connection(
    val id: String,
    val name: String,
    val baseUrl: String,
    val status: ConnectionStatus,
    val lastSeen: String,
)

data class ConnectionDraft(
    val name: String = "",
    val baseUrl: String = "http://",
)

data class LoginForm(
    val username: String = "admin",
    val password: String = "",
)

data class DashboardState(
    val instanceLabel: String,
    val endpoint: String,
    val statusSummary: String,
    val serviceState: ServiceState,
    val activeCore: String,
    val version: String,
    val lastOperation: String,
    val lastError: String?,
    val capabilities: List<String>,
    val recentEvents: List<RecentEvent>,
)

data class RecentEvent(
    val time: String,
    val title: String,
    val subtitle: String,
)

data class RoutingDocument(
    val id: String,
    val title: String,
    val path: String,
    val summary: String,
    val revision: Int,
    val publishedContent: String,
    val draftContent: String,
    val savedDraftContent: String,
    val lastSavedAt: String,
    val lastAppliedAt: String?,
) {
    val hasDraftChanges: Boolean
        get() = draftContent != publishedContent

    val hasUnsavedChanges: Boolean
        get() = draftContent != savedDraftContent

    val hasSavedPreview: Boolean
        get() = savedDraftContent != publishedContent
}

data class RoutingValidation(
    val state: RoutingValidationState = RoutingValidationState.Idle,
    val message: String = "Open a document and validate before apply.",
    val details: List<String> = emptyList(),
)

data class RoutingPreview(
    val headline: String,
    val details: List<String>,
)

data class RoutingState(
    val searchQuery: String = "",
    val documents: List<RoutingDocument>,
    val selectedDocumentId: String,
    val mode: RoutingMode = RoutingMode.Read,
    val validation: RoutingValidation = RoutingValidation(),
    val preview: RoutingPreview? = null,
)

data class LogEntry(
    val time: String,
    val source: String,
    val level: LogLevel,
    val message: String,
)

data class LogsState(
    val filter: LogFilter = LogFilter.All,
    val entries: List<LogEntry>,
)

data class DiagnosticItem(
    val label: String,
    val status: String,
    val severity: DiagnosticSeverity,
)

sealed interface PendingAction {
    data class Service(val action: ServiceAction) : PendingAction
    data object ApplyRouting : PendingAction
}

data class CompanionUiState(
    val phase: AppPhase = AppPhase.Launching,
    val connections: List<Connection> = demoConnections(),
    val connectionDraft: ConnectionDraft = ConnectionDraft(),
    val selectedConnectionId: String? = null,
    val loginForm: LoginForm = LoginForm(),
    val mainTab: MainTab = MainTab.Home,
    val dashboard: DashboardState = demoDashboardState(),
    val routing: RoutingState = demoRoutingState(),
    val logs: LogsState = demoLogsState(),
    val diagnostics: List<DiagnosticItem> = demoDiagnostics(),
    val pendingAction: PendingAction? = null,
)

fun demoConnections(): List<Connection> = listOf(
    Connection(
        id = "home-lab",
        name = "Home Lab",
        baseUrl = "https://lab.lan:8443",
        status = ConnectionStatus.Configured,
        lastSeen = "Seen 20 sec ago",
    ),
    Connection(
        id = "edge-node",
        name = "Edge Node",
        baseUrl = "https://edge.lan:8443",
        status = ConnectionStatus.NeedsAuth,
        lastSeen = "Auth expired",
    ),
    Connection(
        id = "travel-box",
        name = "Travel Box",
        baseUrl = "http://192.168.31.20:8080",
        status = ConnectionStatus.Offline,
        lastSeen = "Offline",
    ),
)

fun demoDashboardState(): DashboardState = DashboardState(
    instanceLabel = "Home Lab",
    endpoint = "https://lab.lan:8443",
    statusSummary = "Ready for safe control",
    serviceState = ServiceState.Running,
    activeCore = "Xray",
    version = "Xkeen 0.8.0-alpha",
    lastOperation = "Routing preview prepared",
    lastError = null,
    capabilities = listOf("routingEditor", "logs", "restart", "diagnostics"),
    recentEvents = listOf(
        RecentEvent("17:48", "Service healthy", "xray runtime is accepting traffic"),
        RecentEvent("17:42", "Routing draft saved", "main-routing.json is ready to apply"),
        RecentEvent("17:35", "Session restored", "mobile token reused without browser fallback"),
    ),
)

private fun mainRoutingContent(): String = """
    {
      "routing": {
        "domainStrategy": "AsIs",
        "rules": [
          {
            "type": "field",
            "domain": ["geosite:private"],
            "outboundTag": "direct"
          },
          {
            "type": "field",
            "ip": ["geoip:private"],
            "outboundTag": "direct"
          },
          {
            "type": "field",
            "port": "53",
            "outboundTag": "dns-out"
          }
        ]
      }
    }
""".trimIndent()

private fun bypassRoutingContent(): String = """
    {
      "routing": {
        "rules": [
          {
            "type": "field",
            "domain": ["geosite:category-ads-all"],
            "outboundTag": "block"
          }
        ]
      }
    }
""".trimIndent()

fun demoRoutingState(): RoutingState {
    val main = mainRoutingContent()
    val bypass = bypassRoutingContent()

    return RoutingState(
        documents = listOf(
            RoutingDocument(
                id = "main-routing",
                title = "Main Routing",
                path = "/etc/xkeen/xray/main-routing.json",
                summary = "Active Xray policy set for LAN and DNS rules",
                revision = 14,
                publishedContent = main,
                draftContent = main,
                savedDraftContent = main,
                lastSavedAt = "17:42",
                lastAppliedAt = "17:20",
            ),
            RoutingDocument(
                id = "bypass-routing",
                title = "Ad Bypass",
                path = "/etc/xkeen/xray/ad-bypass.json",
                summary = "Secondary rules for block and bypass entries",
                revision = 6,
                publishedContent = bypass,
                draftContent = bypass,
                savedDraftContent = bypass,
                lastSavedAt = "16:58",
                lastAppliedAt = "16:40",
            ),
        ),
        selectedDocumentId = "main-routing",
    )
}

fun demoLogsState(): LogsState = LogsState(
    entries = listOf(
        LogEntry("17:49:11", "service", LogLevel.Info, "runtime heartbeat looks healthy"),
        LogEntry("17:48:02", "routing", LogLevel.Info, "preview generated for main-routing.json"),
        LogEntry("17:46:55", "service", LogLevel.Warning, "restart window opened for 8 seconds"),
        LogEntry("17:41:13", "auth", LogLevel.Info, "mobile session restored from secure storage"),
        LogEntry("17:35:28", "routing", LogLevel.Error, "draft 13 failed validate on missing rules"),
    ),
)

fun demoDiagnostics(): List<DiagnosticItem> = listOf(
    DiagnosticItem("Mobile session", "Warm and restored", DiagnosticSeverity.Ok),
    DiagnosticItem("Streaming", "Reconnect window 30 sec", DiagnosticSeverity.Ok),
    DiagnosticItem("Secure storage", "Not wired yet", DiagnosticSeverity.Warning),
    DiagnosticItem("Backend mobile API", "Still mocked in shell", DiagnosticSeverity.Warning),
)
