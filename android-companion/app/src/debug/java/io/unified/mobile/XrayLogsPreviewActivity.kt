package io.unified.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.SystemBarStyle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import io.unified.mobile.app.AppPhase
import io.unified.mobile.app.CompanionApp
import io.unified.mobile.app.CompanionController
import io.unified.mobile.app.CompanionUiState
import io.unified.mobile.app.LogEntry
import io.unified.mobile.app.LogLevel
import io.unified.mobile.app.LogsConnectionState
import io.unified.mobile.app.LogsState
import io.unified.mobile.app.LogsTransportPort
import io.unified.mobile.app.LogsTransportUpdate
import io.unified.mobile.app.MainTab
import io.unified.mobile.app.RemoteLogStream
import io.unified.mobile.app.WorkspaceSection
import io.unified.mobile.app.defaultCompanionControllerDependencies
import io.unified.mobile.app.demoDashboardState

/** Debug-only, interactive full-shell preview of the native Xray log viewer. */
class XrayLogsPreviewActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge(statusBarStyle = SystemBarStyle.dark(android.graphics.Color.TRANSPARENT))
        val dependencies = defaultCompanionControllerDependencies().copy(
            logsTransport = PreviewLogsTransport,
        )
        val controller = CompanionController(
            initialState = CompanionUiState(
                phase = AppPhase.Ready,
                mainTab = MainTab.Routing,
                workspaceSection = WorkspaceSection.XrayLogs,
                dashboard = demoDashboardState().copy(
                    endpoint = "",
                    availableCores = listOf("Xray", "Mihomo"),
                    activeCore = "Xray",
                ),
                logs = LogsState(
                    entries = previewLogEntries.asReversed(),
                    connection = LogsConnectionState.Connected,
                    statusMessage = "Поток логов подключён и обновляется автоматически.",
                    hasLoadedHistory = true,
                    streamAvailability = mapOf("access" to true, "error" to true),
                ),
            ),
            dependencies = dependencies,
        )
        setContent { CompanionApp(controller) }
    }
}

private object PreviewLogsTransport : LogsTransportPort {
    override suspend fun read(
        baseUrl: String,
        cursors: Map<String, String>,
        limit: Int,
    ): LogsTransportUpdate = LogsTransportUpdate(
        streams = listOf(
            RemoteLogStream(
                source = "error",
                entries = previewLogEntries.filter { it.source == "xray-error" },
                cursor = "preview-error",
                mode = "snapshot",
                available = true,
            ),
            RemoteLogStream(
                source = "access",
                entries = previewLogEntries.filter { it.source == "xray-access" },
                cursor = "preview-access",
                mode = "snapshot",
                available = true,
            ),
        ),
    )
}

private val previewLogEntries = listOf(
    previewLog("access:1", "20:14:01", "xray-access", LogLevel.Info, "accepted tcp:192.168.1.42:53844 -> api.telegram.org:443 [direct]"),
    previewLog("access:2", "20:14:03", "xray-access", LogLevel.Info, "accepted udp:192.168.1.37:59621 -> dns.google:53 [dns-out]"),
    previewLog("error:1", "20:14:05", "xray-error", LogLevel.Warning, "[Warning] transport/internet/grpc: creating connection to cdn.example.net:443"),
    previewLog("access:3", "20:14:07", "xray-access", LogLevel.Info, "accepted tcp:192.168.1.19:51002 -> github.com:443 [proxy]"),
    previewLog("error:2", "20:14:09", "xray-error", LogLevel.Error, "[Error] app/proxyman/outbound: failed to process outbound traffic > connection reset by peer"),
    previewLog("access:4", "20:14:11", "xray-access", LogLevel.Info, "accepted tcp:192.168.1.42:53860 -> youtubei.googleapis.com:443 [proxy]"),
    previewLog("error:3", "20:14:14", "xray-error", LogLevel.Info, "[Info] infra/conf/serial: reading config: /opt/etc/xray/configs/06_bypass.json"),
    previewLog("access:5", "20:14:17", "xray-access", LogLevel.Info, "accepted tcp:192.168.1.11:44920 -> cloudflare-dns.com:443 [direct]"),
    previewLog("error:4", "20:14:19", "xray-error", LogLevel.Warning, "[Warning] common/mux: unexpected EOF while reading response header"),
    previewLog("access:6", "20:14:22", "xray-access", LogLevel.Info, "accepted tcp:192.168.1.55:60218 -> discord.com:443 [proxy]"),
)

private fun previewLog(
    id: String,
    time: String,
    source: String,
    level: LogLevel,
    message: String,
): LogEntry = LogEntry(
    id = id,
    time = time,
    source = source,
    level = level,
    message = "2026/07/17 $time $message",
)
