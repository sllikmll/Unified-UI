package io.xkeen.mobile.app

import org.json.JSONArray
import org.json.JSONObject
import java.net.URLEncoder
import java.nio.charset.StandardCharsets

internal const val MOBILE_LOGS_PATH = "/api/mobile/v1/logs"

/** A page from one server-side log file.  The cursor is opaque to the client. */
internal data class RemoteLogStream(
    val source: String,
    val entries: List<LogEntry>,
    val cursor: String,
    val mode: String,
    val available: Boolean,
)

internal data class LogsTransportUpdate(
    val streams: List<RemoteLogStream>,
)

/**
 * Cursor polling is intentionally used instead of a second WebSocket stack.  It works through
 * the same authenticated HTTP seam as the rest of the companion and makes reconnect/rotation
 * explicit: a server can return a full snapshot whenever an old cursor is no longer valid.
 */
internal interface LogsTransportPort {
    suspend fun read(
        baseUrl: String,
        cursors: Map<String, String>,
        limit: Int = 200,
    ): LogsTransportUpdate
}

internal class WebPanelLogsTransport(
    private val transport: CompanionHttpTransport,
) : LogsTransportPort {
    override suspend fun read(
        baseUrl: String,
        cursors: Map<String, String>,
        limit: Int,
    ): LogsTransportUpdate {
        val cursorQuery = cursors
            .filterKeys { it in mobileLogSources }
            .mapNotNull { (source, cursor) ->
                cursor.takeIf { it.isNotBlank() }?.let {
                    "$source-cursor=${URLEncoder.encode(it, StandardCharsets.UTF_8.name())}"
                }
            }
        val query = buildList {
            if (limit != 200) add("limit=${limit.coerceIn(50, 500)}")
            addAll(cursorQuery)
        }.joinToString("&")
        val response = transport.get(
            CompanionHttpRequest(
                baseUrl = baseUrl,
                endpoint = if (query.isBlank()) MOBILE_LOGS_PATH else "$MOBILE_LOGS_PATH?$query",
            ),
        )
        return parseLogsTransportEnvelope(response.body)
    }
}

internal val mobileLogSources: Set<String> = setOf("error", "access")

internal fun parseLogsTransportEnvelope(body: String): LogsTransportUpdate {
    val root = JSONObject(body)
    if (!root.optBoolean("ok", false)) {
        val error = root.optJSONObject("error")
        throw IllegalStateException(
            error?.optString("message")?.takeIf(String::isNotBlank)
                ?: "Xkeen UI вернул некорректный ответ логов.",
        )
    }
    val data = root.optJSONObject("data")
        ?: throw IllegalStateException("В ответе Xkeen UI отсутствуют данные логов.")
    val contractVersion = data.optInt("contract_version", 1)
    if (contractVersion != 1) {
        throw IllegalStateException("Версия контракта логов $contractVersion пока не поддерживается.")
    }
    val streams = data.optJSONArray("streams")
        ?: throw IllegalStateException("В ответе Xkeen UI отсутствуют потоки логов.")
    return LogsTransportUpdate(
        streams = buildList {
            for (index in 0 until streams.length()) {
                val item = streams.optJSONObject(index) ?: continue
                val source = item.optString("source").trim()
                if (source !in mobileLogSources) continue
                add(
                    RemoteLogStream(
                        source = source,
                        entries = item.optJSONArray("entries").toLogEntries(),
                        cursor = item.optString("cursor").trim(),
                        mode = item.optString("mode", "append").trim().ifBlank { "append" },
                        available = item.optBoolean("available", false),
                    ),
                )
            }
        },
    )
}

private fun JSONArray?.toLogEntries(): List<LogEntry> {
    if (this == null) return emptyList()
    return buildList {
        for (index in 0 until length()) {
            val item = optJSONObject(index) ?: continue
            val message = item.optString("message").trimEnd()
            if (message.isBlank()) continue
            add(
                LogEntry(
                    id = item.optString("id").trim(),
                    time = item.optString("time").trim().ifBlank { "—" },
                    source = item.optString("source").trim().ifBlank { "xray" },
                    level = item.optString("level").toLogLevel(),
                    message = message,
                ),
            )
        }
    }
}

private fun String?.toLogLevel(): LogLevel =
    when (this?.trim()?.lowercase()) {
        "error" -> LogLevel.Error
        "warning", "warn" -> LogLevel.Warning
        else -> LogLevel.Info
    }
