package io.xkeen.mobile.app

import java.net.URLEncoder
import java.nio.charset.StandardCharsets
import org.json.JSONArray
import org.json.JSONObject

data class XraySubscriptionRoutingBalancer(
    val tag: String,
    val strategyType: String,
    val selectorCount: Int,
    val autoManaged: Boolean,
)

internal data class XraySubscriptionsSnapshot(
    val subscriptions: List<XraySubscriptionRecord>,
    val routingBalancers: List<XraySubscriptionRoutingBalancer> = emptyList(),
    val existingAutoBalancerTag: String? = null,
    val autoBalancerCandidateTag: String? = null,
)

data class XraySubscriptionRecord(
    val id: String,
    val name: String,
    val tag: String,
    val url: String,
    val enabled: Boolean,
    val pingEnabled: Boolean,
    val routingMode: String,
    val routingAutoRule: Boolean,
    val routingBalancerTags: List<String>,
    val sockoptMark255: Boolean,
    val intervalHours: Int,
    val outputFile: String,
    val nameFilter: String = "",
    val typeFilter: String = "",
    val transportFilter: String = "",
    val excludedNodeKeys: List<String> = emptyList(),
    val lastOk: Boolean? = null,
    val lastError: String? = null,
    val lastUpdateEpochSeconds: Long? = null,
    val nextUpdateEpochSeconds: Long? = null,
    val lastCount: Int = 0,
    val sourceCount: Int = 0,
    val filteredOutCount: Int = 0,
    val warnings: List<String> = emptyList(),
    val errors: List<String> = emptyList(),
    val sourceFormat: String? = null,
    val fetchMode: String? = null,
    val profileUpdateIntervalHours: Int? = null,
    val nodes: List<OutboundNode> = emptyList(),
)

data class XraySubscriptionPreview(
    val nodes: List<OutboundNode>,
    val count: Int,
    val sourceCount: Int,
    val filteredOutCount: Int,
    val warnings: List<String>,
    val errors: List<String>,
    val sourceFormat: String,
    val fetchMode: String,
    val profileUpdateIntervalHours: Int?,
    val tagPrefix: String,
)

internal data class XraySubscriptionSaveRequest(
    val id: String = "",
    val name: String = "",
    val tag: String = "",
    val url: String = "",
    val nameFilter: String = "",
    val typeFilter: String = "",
    val transportFilter: String = "",
    val excludedNodeKeys: List<String> = emptyList(),
    val enabled: Boolean = true,
    val pingEnabled: Boolean = true,
    val routingMode: String = "safe-fallback",
    val routingAutoRule: Boolean = true,
    val routingBalancerTags: List<String> = emptyList(),
    val sockoptMark255: Boolean = false,
    val intervalHours: Int = 24,
)

internal data class XraySubscriptionMutationResult(
    val ok: Boolean,
    val id: String = "",
    val subscription: XraySubscriptionRecord? = null,
    val changed: Boolean = false,
    val generatedChanged: Boolean = false,
    val observatoryChanged: Boolean = false,
    val routingChanged: Boolean = false,
    val outboundsChanged: Boolean = false,
    val restarted: Boolean = false,
    val count: Int = 0,
    val sourceCount: Int = 0,
    val filteredOutCount: Int = 0,
    val outputFile: String? = null,
    val warnings: List<String> = emptyList(),
    val errors: List<String> = emptyList(),
    val nodes: List<OutboundNode> = emptyList(),
    val error: String? = null,
    val nextUpdateEpochSeconds: Long? = null,
)

internal data class XraySubscriptionsDueResult(
    val updated: Int,
    val okCount: Int,
    val results: List<XraySubscriptionMutationResult>,
)

internal interface XraySubscriptionsPort {
    suspend fun list(baseUrl: String): XraySubscriptionsSnapshot

    suspend fun preview(baseUrl: String, request: XraySubscriptionSaveRequest): XraySubscriptionPreview

    suspend fun upsert(baseUrl: String, request: XraySubscriptionSaveRequest): XraySubscriptionMutationResult

    suspend fun refresh(baseUrl: String, id: String, restart: Boolean): XraySubscriptionMutationResult

    suspend fun refreshDue(baseUrl: String, restart: Boolean): XraySubscriptionsDueResult

    suspend fun delete(
        baseUrl: String,
        id: String,
        restart: Boolean,
        removeFile: Boolean = true,
    ): XraySubscriptionMutationResult
}

internal class WebPanelXraySubscriptionsPort(
    private val transport: CompanionHttpTransport,
) : XraySubscriptionsPort {
    override suspend fun list(baseUrl: String): XraySubscriptionsSnapshot =
        parseXraySubscriptionsSnapshot(
            transport.get(
                CompanionHttpRequest(baseUrl = baseUrl, endpoint = "/api/xray/subscriptions"),
            ).body,
        )

    override suspend fun preview(
        baseUrl: String,
        request: XraySubscriptionSaveRequest,
    ): XraySubscriptionPreview = parseXraySubscriptionPreview(
        transport.post(
            CompanionHttpRequest(
                baseUrl = baseUrl,
                endpoint = "/api/xray/subscriptions/preview",
                body = request.toSubscriptionJson(includeSettings = false).toString(),
            ),
        ).body,
    )

    override suspend fun upsert(
        baseUrl: String,
        request: XraySubscriptionSaveRequest,
    ): XraySubscriptionMutationResult = parseXraySubscriptionMutation(
        transport.post(
            CompanionHttpRequest(
                baseUrl = baseUrl,
                endpoint = "/api/xray/subscriptions",
                body = request.toSubscriptionJson(includeSettings = true).toString(),
            ),
        ).body,
    )

    override suspend fun refresh(
        baseUrl: String,
        id: String,
        restart: Boolean,
    ): XraySubscriptionMutationResult = parseXraySubscriptionMutation(
        transport.post(
            CompanionHttpRequest(
                baseUrl = baseUrl,
                endpoint = "/api/xray/subscriptions/${id.subscriptionUrlEncoded()}/refresh?restart=${restart.asQueryFlag()}",
                body = "{}",
            ),
        ).body,
    )

    override suspend fun refreshDue(
        baseUrl: String,
        restart: Boolean,
    ): XraySubscriptionsDueResult = parseXraySubscriptionsDueResult(
        transport.post(
            CompanionHttpRequest(
                baseUrl = baseUrl,
                endpoint = "/api/xray/subscriptions/refresh-due?restart=${restart.asQueryFlag()}",
                body = "{}",
            ),
        ).body,
    )

    override suspend fun delete(
        baseUrl: String,
        id: String,
        restart: Boolean,
        removeFile: Boolean,
    ): XraySubscriptionMutationResult = parseXraySubscriptionMutation(
        transport.delete(
            CompanionHttpRequest(
                baseUrl = baseUrl,
                endpoint = "/api/xray/subscriptions/${id.subscriptionUrlEncoded()}" +
                    "?restart=${restart.asQueryFlag()}&remove_file=${removeFile.asQueryFlag()}",
            ),
        ).body,
    )
}

internal class DemoXraySubscriptionsPort : XraySubscriptionsPort {
    private var subscriptions = mutableListOf(demoSubscription())

    override suspend fun list(baseUrl: String): XraySubscriptionsSnapshot =
        XraySubscriptionsSnapshot(subscriptions = subscriptions.toList())

    override suspend fun preview(
        baseUrl: String,
        request: XraySubscriptionSaveRequest,
    ): XraySubscriptionPreview {
        val node = demoSubscriptionNode(request.tag.ifBlank { "demo" })
        return XraySubscriptionPreview(
            nodes = listOf(node),
            count = 1,
            sourceCount = 1,
            filteredOutCount = 0,
            warnings = emptyList(),
            errors = emptyList(),
            sourceFormat = "links",
            fetchMode = "direct",
            profileUpdateIntervalHours = 24,
            tagPrefix = request.tag.ifBlank { "demo" },
        )
    }

    override suspend fun upsert(
        baseUrl: String,
        request: XraySubscriptionSaveRequest,
    ): XraySubscriptionMutationResult {
        val id = request.id.ifBlank { request.tag.ifBlank { "demo-subscription" } }
        val old = subscriptions.firstOrNull { it.id == id }
        val record = XraySubscriptionRecord(
            id = id,
            name = request.name.ifBlank { request.tag.ifBlank { id } },
            tag = request.tag.ifBlank { id },
            url = request.url,
            enabled = request.enabled,
            pingEnabled = request.pingEnabled,
            routingMode = request.routingMode,
            routingAutoRule = request.routingAutoRule,
            routingBalancerTags = request.routingBalancerTags,
            sockoptMark255 = request.sockoptMark255,
            intervalHours = request.intervalHours.coerceIn(1, 168),
            outputFile = old?.outputFile ?: "04_outbounds.$id.json",
            nameFilter = request.nameFilter,
            typeFilter = request.typeFilter,
            transportFilter = request.transportFilter,
            excludedNodeKeys = request.excludedNodeKeys,
            nodes = old?.nodes.orEmpty(),
        )
        subscriptions.removeAll { it.id == id }
        subscriptions.add(record)
        return XraySubscriptionMutationResult(ok = true, id = id, subscription = record)
    }

    override suspend fun refresh(
        baseUrl: String,
        id: String,
        restart: Boolean,
    ): XraySubscriptionMutationResult {
        val index = subscriptions.indexOfFirst { it.id == id }
        if (index < 0) return XraySubscriptionMutationResult(ok = false, id = id, error = "subscription not found")
        val old = subscriptions[index]
        val node = demoSubscriptionNode(old.tag)
        val refreshed = old.copy(
            lastOk = true,
            lastError = null,
            lastCount = 1,
            sourceCount = 1,
            nodes = listOf(node),
        )
        subscriptions[index] = refreshed
        return XraySubscriptionMutationResult(
            ok = true,
            id = id,
            subscription = refreshed,
            changed = true,
            generatedChanged = true,
            restarted = restart,
            count = 1,
            sourceCount = 1,
            outputFile = refreshed.outputFile,
            nodes = refreshed.nodes,
        )
    }

    override suspend fun refreshDue(baseUrl: String, restart: Boolean): XraySubscriptionsDueResult {
        val results = subscriptions.filter { it.enabled }.map { refresh(baseUrl, it.id, restart) }
        return XraySubscriptionsDueResult(results.size, results.count { it.ok }, results)
    }

    override suspend fun delete(
        baseUrl: String,
        id: String,
        restart: Boolean,
        removeFile: Boolean,
    ): XraySubscriptionMutationResult {
        val removed = subscriptions.firstOrNull { it.id == id }
            ?: return XraySubscriptionMutationResult(ok = false, id = id, error = "subscription not found")
        subscriptions.removeAll { it.id == id }
        return XraySubscriptionMutationResult(
            ok = true,
            id = id,
            subscription = removed,
            changed = removeFile,
            generatedChanged = removeFile,
            restarted = restart && removeFile,
            outputFile = removed.outputFile,
        )
    }
}

internal class XraySubscriptionsException(message: String, cause: Throwable? = null) : Exception(message, cause)

internal fun parseXraySubscriptionsSnapshot(body: String): XraySubscriptionsSnapshot {
    val payload = body.subscriptionJsonObject()
    payload.requireSubscriptionOk("Сервер не вернул список подписок Xray.")
    val records = payload.optJSONArray("subscriptions").subscriptionObjects().map(::parseXraySubscriptionRecord)
    val balancers = payload.optJSONArray("routing_balancers").subscriptionObjects().map { item ->
        XraySubscriptionRoutingBalancer(
            tag = item.optString("tag").trim(),
            strategyType = item.optString("strategy_type").trim(),
            selectorCount = item.optInt("selector_count", 0),
            autoManaged = item.optBoolean("auto_managed", false),
        )
    }.filter { it.tag.isNotBlank() }
    val meta = payload.optJSONObject("routing_meta")
    return XraySubscriptionsSnapshot(
        subscriptions = records,
        routingBalancers = balancers,
        existingAutoBalancerTag = meta?.optString("existing_auto_balancer_tag")?.trim()?.takeIf(String::isNotBlank),
        autoBalancerCandidateTag = meta?.optString("auto_balancer_candidate_tag")?.trim()?.takeIf(String::isNotBlank),
    )
}

internal fun parseXraySubscriptionPreview(body: String): XraySubscriptionPreview {
    val payload = body.subscriptionJsonObject()
    payload.requireSubscriptionOk("Сервер не вернул предпросмотр подписки Xray.")
    return XraySubscriptionPreview(
        nodes = parseSubscriptionNodes(payload.optJSONArray("nodes"), payload.optJSONObject("node_latency")),
        count = payload.optInt("count", 0),
        sourceCount = payload.optInt("source_count", 0),
        filteredOutCount = payload.optInt("filtered_out_count", 0),
        warnings = payload.optJSONArray("warnings").subscriptionStrings(),
        errors = payload.optJSONArray("errors").subscriptionErrors(),
        sourceFormat = payload.optString("source_format").trim(),
        fetchMode = payload.optString("fetch_mode").trim(),
        profileUpdateIntervalHours = payload.subscriptionOptInt("profile_update_interval_hours"),
        tagPrefix = payload.optString("tag_prefix").trim(),
    )
}

internal fun parseXraySubscriptionMutation(body: String): XraySubscriptionMutationResult {
    val payload = body.subscriptionJsonObject()
    payload.requireSubscriptionOk("Xkeen UI не выполнил операцию с подпиской.")
    val recordObject = payload.optJSONObject("subscription") ?: payload.optJSONObject("deleted")
    val record = recordObject?.let(::parseXraySubscriptionRecord)
    val generatedChanged = payload.optBoolean("changed", false) || payload.optBoolean("output_removed", false)
    val observatoryChanged = payload.optBoolean("observatory_changed", false)
    val routingChanged = payload.optBoolean("routing_changed", false)
    val outboundsChanged = payload.optBoolean("outbounds_changed", false)
    return XraySubscriptionMutationResult(
        ok = true,
        id = payload.optString("id").trim().ifBlank { record?.id.orEmpty() },
        subscription = record,
        changed = generatedChanged || observatoryChanged || routingChanged || outboundsChanged,
        generatedChanged = generatedChanged,
        observatoryChanged = observatoryChanged,
        routingChanged = routingChanged,
        outboundsChanged = outboundsChanged,
        restarted = payload.optBoolean("restarted", false),
        count = payload.optInt("count", record?.lastCount ?: 0),
        sourceCount = payload.optInt("source_count", record?.sourceCount ?: 0),
        filteredOutCount = payload.optInt("filtered_out_count", record?.filteredOutCount ?: 0),
        outputFile = payload.optString("output_file").trim().takeIf(String::isNotBlank) ?: record?.outputFile,
        warnings = payload.optJSONArray("warnings").subscriptionStrings(),
        errors = payload.optJSONArray("errors").subscriptionErrors(),
        nodes = parseSubscriptionNodes(payload.optJSONArray("last_nodes"), payload.optJSONObject("node_latency")),
        error = payload.optString("error").trim().takeIf(String::isNotBlank),
        nextUpdateEpochSeconds = payload.subscriptionOptLong("next_update_ts"),
    )
}

internal fun parseXraySubscriptionsDueResult(body: String): XraySubscriptionsDueResult {
    val payload = body.subscriptionJsonObject()
    payload.requireSubscriptionOk("Сервер не обновил due-подписки Xray.")
    val results = payload.optJSONArray("results").subscriptionObjects().map { item ->
        if (item.optBoolean("ok", false)) {
            parseXraySubscriptionMutation(item.toString())
        } else {
            XraySubscriptionMutationResult(
                ok = false,
                id = item.optString("id").trim(),
                error = item.optString("error").trim().takeIf(String::isNotBlank),
                nextUpdateEpochSeconds = item.subscriptionOptLong("next_update_ts"),
            )
        }
    }
    return XraySubscriptionsDueResult(
        updated = payload.optInt("updated", results.size),
        okCount = payload.optInt("ok_count", results.count { it.ok }),
        results = results,
    )
}

private fun parseXraySubscriptionRecord(payload: JSONObject): XraySubscriptionRecord {
    val latency = payload.optJSONObject("node_latency")
    return XraySubscriptionRecord(
        id = payload.optString("id").trim(),
        name = payload.optString("name").trim(),
        tag = payload.optString("tag").trim(),
        url = payload.optString("url").trim(),
        enabled = payload.optBoolean("enabled", true),
        pingEnabled = payload.optBoolean("ping_enabled", true),
        routingMode = payload.optString("routing_mode", "safe-fallback").trim().ifBlank { "safe-fallback" },
        routingAutoRule = payload.optBoolean("routing_auto_rule", true),
        routingBalancerTags = payload.optJSONArray("routing_balancer_tags").subscriptionStrings(),
        sockoptMark255 = payload.optBoolean("sockopt_mark_255", false),
        intervalHours = payload.optInt("interval_hours", 24),
        outputFile = payload.optString("output_file").trim(),
        nameFilter = payload.optString("name_filter").trim(),
        typeFilter = payload.optString("type_filter").trim(),
        transportFilter = payload.optString("transport_filter").trim(),
        excludedNodeKeys = payload.optJSONArray("excluded_node_keys").subscriptionStrings(),
        lastOk = payload.subscriptionOptBoolean("last_ok"),
        lastError = payload.optString("last_error").trim().takeIf(String::isNotBlank),
        lastUpdateEpochSeconds = payload.subscriptionOptLong("last_update_ts"),
        nextUpdateEpochSeconds = payload.subscriptionOptLong("next_update_ts"),
        lastCount = payload.optInt("last_count", 0),
        sourceCount = payload.optInt("last_source_count", 0),
        filteredOutCount = payload.optInt("last_filtered_out_count", 0),
        warnings = payload.optJSONArray("last_warnings").subscriptionStrings(),
        errors = payload.optJSONArray("last_errors").subscriptionErrors(),
        sourceFormat = payload.optString("last_source_format").trim().takeIf(String::isNotBlank),
        fetchMode = payload.optString("last_fetch_mode").trim().takeIf(String::isNotBlank),
        profileUpdateIntervalHours = payload.subscriptionOptInt("profile_update_interval_hours"),
        nodes = parseSubscriptionNodes(payload.optJSONArray("last_nodes"), latency),
    )
}

private fun parseSubscriptionNodes(nodes: JSONArray?, latency: JSONObject?): List<OutboundNode> = buildList {
    if (nodes == null) return@buildList
    for (index in 0 until nodes.length()) {
        val item = nodes.optJSONObject(index) ?: continue
        val key = item.optString("key").trim()
        if (key.isBlank()) continue
        add(
            OutboundNode(
                key = key,
                tag = item.optString("tag").trim(),
                name = item.optString("name").trim(),
                protocol = item.optString("protocol").trim(),
                transport = item.optString("transport").trim(),
                security = item.optString("security").trim(),
                host = item.optString("host").trim(),
                port = item.opt("port")?.takeUnless { it == JSONObject.NULL }?.toString()?.trim().orEmpty(),
                sni = item.optString("sni").trim(),
                detail = item.optString("detail").trim(),
                subscriptionName = item.optString("name").trim().takeIf(String::isNotBlank),
                latency = latency?.optJSONObject(key)?.let(::parseSubscriptionLatency),
            ),
        )
    }
}

private fun parseSubscriptionLatency(payload: JSONObject): OutboundLatency = OutboundLatency(
    status = payload.optString("status").trim().ifBlank {
        if (payload.has("delay_ms") && !payload.isNull("delay_ms")) "ok" else "unknown"
    },
    delayMillis = payload.subscriptionOptLong("delay_ms"),
    message = payload.optString("error").trim().takeIf(String::isNotBlank),
)

private fun XraySubscriptionSaveRequest.toSubscriptionJson(includeSettings: Boolean): JSONObject =
    JSONObject()
        .put("id", id.trim())
        .put("name", name.trim())
        .put("tag", tag.trim())
        .put("url", url.trim())
        .put("name_filter", nameFilter.trim())
        .put("type_filter", typeFilter.trim())
        .put("transport_filter", transportFilter.trim())
        .put("excluded_node_keys", JSONArray(excludedNodeKeys.map(String::trim).filter(String::isNotBlank)))
        .apply {
            if (includeSettings) {
                put("enabled", enabled)
                put("ping_enabled", pingEnabled)
                put("routing_mode", routingMode.trim().ifBlank { "safe-fallback" })
                put("routing_auto_rule", routingAutoRule)
                put("routing_balancer_tags", JSONArray(routingBalancerTags.map(String::trim).filter(String::isNotBlank)))
                put("sockopt_mark_255", sockoptMark255)
                put("interval_hours", intervalHours.coerceIn(1, 168))
            }
        }

private fun JSONObject.requireSubscriptionOk(message: String) {
    if (!optBoolean("ok", false)) {
        throw XraySubscriptionsException(optString("error").trim().takeIf(String::isNotBlank) ?: message)
    }
}

private fun String.subscriptionJsonObject(): JSONObject = try {
    JSONObject(this)
} catch (error: Exception) {
    throw XraySubscriptionsException("Xkeen UI вернул неожиданный ответ для подписок Xray.", error)
}

private fun JSONArray?.subscriptionObjects(): List<JSONObject> = buildList {
    val source = this@subscriptionObjects ?: return@buildList
    for (index in 0 until source.length()) source.optJSONObject(index)?.let(::add)
}

private fun JSONArray?.subscriptionStrings(): List<String> = buildList {
    val source = this@subscriptionStrings ?: return@buildList
    for (index in 0 until source.length()) {
        source.optString(index).trim().takeIf(String::isNotBlank)?.let(::add)
    }
}

private fun JSONArray?.subscriptionErrors(): List<String> = buildList {
    val source = this@subscriptionErrors ?: return@buildList
    for (index in 0 until source.length()) {
        val item = source.opt(index)
        val text = when (item) {
            is JSONObject -> {
                val prefix = listOf(
                    item.subscriptionOptInt("idx")?.let { "#${it + 1}" }.orEmpty(),
                    item.optString("tag").trim(),
                ).filter(String::isNotBlank).joinToString(" · ")
                val message = item.optString("error").trim().ifBlank { item.optString("message").trim() }
                when {
                    prefix.isNotBlank() && message.isNotBlank() -> "$prefix: $message"
                    else -> prefix.ifBlank { message }
                }
            }
            else -> item?.takeUnless { it == JSONObject.NULL }?.toString()?.trim().orEmpty()
        }
        text.takeIf(String::isNotBlank)?.let(::add)
    }
}

private fun JSONObject.subscriptionOptBoolean(name: String): Boolean? =
    if (has(name) && !isNull(name)) optBoolean(name) else null

private fun JSONObject.subscriptionOptInt(name: String): Int? =
    if (has(name) && !isNull(name)) optInt(name) else null

private fun JSONObject.subscriptionOptLong(name: String): Long? =
    if (has(name) && !isNull(name)) optDouble(name).toLong() else null

private fun String.subscriptionUrlEncoded(): String =
    URLEncoder.encode(trim(), StandardCharsets.UTF_8.name())

private fun Boolean.asQueryFlag(): String = if (this) "1" else "0"

private fun demoSubscription(): XraySubscriptionRecord = XraySubscriptionRecord(
    id = "demo-provider",
    name = "Demo provider",
    tag = "demo",
    url = "https://demo.example/subscription",
    enabled = true,
    pingEnabled = true,
    routingMode = "safe-fallback",
    routingAutoRule = true,
    routingBalancerTags = emptyList(),
    sockoptMark255 = false,
    intervalHours = 24,
    outputFile = "04_outbounds.demo-provider.json",
    lastOk = true,
    lastCount = 1,
    sourceCount = 1,
    nodes = listOf(demoSubscriptionNode("demo")),
)

private fun demoSubscriptionNode(prefix: String): OutboundNode = OutboundNode(
    key = "demo-node-nl",
    tag = "${prefix.ifBlank { "demo" }}--Amsterdam",
    name = "Нидерланды · Амстердам",
    protocol = "vless",
    transport = "xhttp",
    security = "reality",
    host = "nl.example.net",
    port = "443",
    sni = "cdn.example.net",
    detail = "",
    subscriptionName = "Нидерланды · Амстердам",
)
