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
import io.unified.mobile.app.DashboardState
import io.unified.mobile.app.MainTab
import io.unified.mobile.app.OutboundLatency
import io.unified.mobile.app.OutboundNode
import io.unified.mobile.app.OutboundsFragment
import io.unified.mobile.app.OutboundsState
import io.unified.mobile.app.ServiceState
import io.unified.mobile.app.WorkspaceSection
import io.unified.mobile.app.unloadedInboundsState
import io.unified.mobile.app.unloadedRoutingState

/** Debug-only visual review entry point. It is excluded from release builds and performs no I/O. */
class OutboundsPreviewActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge(
            statusBarStyle = SystemBarStyle.dark(android.graphics.Color.TRANSPARENT),
        )
        val controller = CompanionController(initialState = outboundsPreviewState())
        setContent { CompanionApp(controller) }
    }
}

internal fun outboundsPreviewState(): CompanionUiState = CompanionUiState(
    phase = AppPhase.Ready,
    mainTab = MainTab.Routing,
    workspaceSection = WorkspaceSection.XrayOutbounds,
    dashboard = DashboardState(
        instanceLabel = "Xkeen Lab",
        endpoint = "",
        statusSummary = "Preview мобильного интерфейса",
        serviceState = ServiceState.Running,
        activeCore = "Xray",
        version = "Xkeen mobile preview",
        lastOperation = "Загружен 04_outbounds.cdn.json",
        lastError = null,
        capabilities = listOf("outbounds", "latency"),
        recentEvents = emptyList(),
        availableCores = listOf("Xray"),
    ),
    routing = unloadedRoutingState(),
    inbounds = unloadedInboundsState(),
    outbounds = OutboundsState(
        fragments = listOf(
            OutboundsFragment("04_outbounds.cdn.json"),
            OutboundsFragment("04_outbounds.reserve.json"),
        ),
        selectedFragment = "04_outbounds.cdn.json",
        activePath = "/opt/etc/xray/configs/04_outbounds.cdn.json",
        nodes = previewOutboundNodes,
        activeNodeKey = "nl-amsterdam",
        activeNodeTag = "my_proxy--nl",
        activeMessage = "Активный outbound подтверждён runtime-логами Xray.",
        hasLoaded = true,
        message = "Пул proxy-узлов: ${previewOutboundNodes.size}.",
    ),
)

private val previewOutboundNodes = listOf(
    previewNode("nl-amsterdam", "my_proxy--nl", "Нидерланды · Амстердам", "nl.edge.example", 47, "xhttp", "reality"),
    previewNode("de-frankfurt", "my_proxy--de", "Германия · Франкфурт", "de.edge.example", 72, "xhttp", "reality"),
    previewNode("se-stockholm", "reserve_proxy--se", "Швеция · Стокгольм", "se.edge.example", 94, "grpc", "tls"),
    previewNode("us-new-york", "reserve_proxy--us", "США · Нью-Йорк", "us.edge.example", 138, "ws", "tls"),
    previewNode("in-mumbai", "white_list--in", "Индия · Мумбаи", "in.edge.example", 271, "xhttp", "reality"),
    previewNode("sg-singapore", "white_list--sg", "Сингапур", "sg.edge.example", 184, "grpc", "tls"),
    previewNode("jp-tokyo", "reserve_proxy--jp", "Япония · Токио", "jp.edge.example", null, "ws", "tls"),
    previewNode("tr-istanbul", "reserve_proxy--tr", "Турция · Стамбул", "tr.edge.example", null, "tcp", "reality"),
)

private fun previewNode(
    key: String,
    tag: String,
    name: String,
    host: String,
    latencyMillis: Long?,
    transport: String,
    security: String,
): OutboundNode = OutboundNode(
    key = key,
    tag = tag,
    name = name,
    protocol = "vless",
    transport = transport,
    security = security,
    host = host,
    port = "443",
    sni = "cdn.example",
    detail = "",
    latency = latencyMillis?.let { OutboundLatency(status = "ok", delayMillis = it) },
)
