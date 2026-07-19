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
import io.unified.mobile.app.OutboundNode
import io.unified.mobile.app.WorkspaceSection
import io.unified.mobile.app.XraySubscriptionDraft
import io.unified.mobile.app.XraySubscriptionEditorState
import io.unified.mobile.app.XraySubscriptionPreview
import io.unified.mobile.app.XraySubscriptionRecord
import io.unified.mobile.app.XraySubscriptionsState

/** Debug-only visual review surface. It is excluded from release builds and performs no I/O. */
class XraySubscriptionsPreviewActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge(statusBarStyle = SystemBarStyle.dark(android.graphics.Color.TRANSPARENT))
        val editor = intent.getBooleanExtra("editor", false)
        val base = CompanionUiState(
            phase = AppPhase.Ready,
            workspaceSection = WorkspaceSection.XraySubscriptions,
            xraySubscriptions = previewSubscriptionsState(editor),
        )
        setContent { CompanionApp(CompanionController(initialState = base)) }
    }
}

private fun previewSubscriptionsState(editorOpen: Boolean): XraySubscriptionsState {
    val draft = XraySubscriptionDraft(
        name = "Cloud provider",
        tag = "cloud",
        url = "https://provider.example/api/v1/client/subscribe?token=private",
        intervalHours = "24",
    )
    val preview = XraySubscriptionPreview(
        nodes = previewSubscriptionNodes,
        count = 4,
        sourceCount = 5,
        filteredOutCount = 1,
        warnings = listOf("Один узел не поддерживается Xray."),
        errors = emptyList(),
        sourceFormat = "links",
        fetchMode = "direct",
        profileUpdateIntervalHours = 12,
        tagPrefix = "cloud",
    )
    return XraySubscriptionsState(
        items = previewSubscriptionRecords,
        hasLoaded = true,
        message = "Подписок: 3 · узлов: 29.",
        editor = if (editorOpen) {
            XraySubscriptionEditorState(
                isOpen = true,
                draft = draft,
                savedDraft = XraySubscriptionDraft(),
                preview = preview,
                previewSignature = draft.previewSignature(),
                message = "Preview: 4 из 5 узлов.",
            )
        } else {
            XraySubscriptionEditorState()
        },
    )
}

private val previewSubscriptionRecords = listOf(
    previewSubscriptionRecord("cloud-eu", "Cloud Europe", "cloud", 18, true, 1784289600),
    previewSubscriptionRecord("backup", "Резервный провайдер", "backup", 7, true, 1784275200),
    previewSubscriptionRecord("lab", "Лабораторные узлы", "lab", 4, false, null),
)

private fun previewSubscriptionRecord(
    id: String,
    name: String,
    tag: String,
    count: Int,
    enabled: Boolean,
    nextUpdate: Long?,
): XraySubscriptionRecord = XraySubscriptionRecord(
    id = id,
    name = name,
    tag = tag,
    url = "https://provider.example/$id?token=private",
    enabled = enabled,
    pingEnabled = true,
    routingMode = "safe-fallback",
    routingAutoRule = true,
    routingBalancerTags = emptyList(),
    sockoptMark255 = false,
    intervalHours = 24,
    outputFile = "04_outbounds.$id.json",
    lastOk = true,
    lastUpdateEpochSeconds = 1784246400,
    nextUpdateEpochSeconds = nextUpdate,
    lastCount = count,
    sourceCount = count,
)

private val previewSubscriptionNodes = listOf(
    previewSubscriptionNode("nl", "Нидерланды · Амстердам", "nl.example.net"),
    previewSubscriptionNode("de", "Германия · Франкфурт", "de.example.net"),
    previewSubscriptionNode("fi", "Финляндия · Хельсинки", "fi.example.net"),
    previewSubscriptionNode("pl", "Польша · Варшава", "pl.example.net"),
)

private fun previewSubscriptionNode(key: String, name: String, host: String): OutboundNode = OutboundNode(
    key = key,
    tag = "cloud--$key",
    name = name,
    protocol = "vless",
    transport = "xhttp",
    security = "reality",
    host = host,
    port = "443",
    sni = "cdn.example.net",
    detail = "",
)
