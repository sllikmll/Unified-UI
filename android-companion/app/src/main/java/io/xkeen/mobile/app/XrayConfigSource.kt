package io.xkeen.mobile.app

import java.net.HttpURLConnection
import java.net.URI
import java.net.URLEncoder
import java.nio.charset.StandardCharsets
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject

internal data class XrayFragmentInfo(
    val name: String,
    val sizeBytes: Long?,
    val modifiedAtEpochSeconds: Long?,
    val sensitive: Boolean,
)

internal data class XrayFragmentIndex(
    val directory: String,
    val currentName: String,
    val items: List<XrayFragmentInfo>,
)

internal data class XrayFragmentContent(
    val text: String,
    val hasJsoncSidecar: Boolean,
    val usesJsoncSidecar: Boolean,
)

internal interface XrayConfigSource {
    suspend fun listFragments(baseUrl: String): XrayFragmentIndex

    suspend fun loadFragment(baseUrl: String, filename: String): XrayFragmentContent
}

internal class WebPanelXrayConfigSource : XrayConfigSource {
    override suspend fun listFragments(baseUrl: String): XrayFragmentIndex = withContext(Dispatchers.IO) {
        val response = get(baseUrl, "/api/routing/fragments")
        val payload = try {
            JSONObject(response.body)
        } catch (error: Exception) {
            throw XrayConfigException(
                "Xkeen UI вернул неожиданный ответ. Возможно, требуется авторизация.",
                error,
            )
        }
        if (!payload.optBoolean("ok", false)) {
            throw XrayConfigException("Сервер не вернул список конфигураций Xray.")
        }

        val itemsJson = payload.optJSONArray("items")
        val items = buildList {
            if (itemsJson != null) {
                for (index in 0 until itemsJson.length()) {
                    val item = itemsJson.optJSONObject(index) ?: continue
                    val name = item.optString("name").trim()
                    if (!name.isXrayConfigFilename()) continue
                    add(
                        XrayFragmentInfo(
                            name = name,
                            sizeBytes = item.optLongOrNull("size"),
                            modifiedAtEpochSeconds = item.optLongOrNull("mtime"),
                            sensitive = item.optBoolean("sensitive", false),
                        ),
                    )
                }
            }
        }.sortedBy { it.name.lowercase() }

        XrayFragmentIndex(
            directory = payload.optString("dir"),
            currentName = payload.optString("current"),
            items = items,
        )
    }

    override suspend fun loadFragment(baseUrl: String, filename: String): XrayFragmentContent =
        withContext(Dispatchers.IO) {
            require(filename.isXrayConfigFilename()) { "Unsupported Xray config filename" }
            val encoded = URLEncoder.encode(filename, StandardCharsets.UTF_8.name())
            val response = get(baseUrl, "/api/routing?file=$encoded")
            XrayFragmentContent(
                text = response.body,
                hasJsoncSidecar = response.headers["x-xkeen-jsonc"] == "1",
                usesJsoncSidecar = response.headers["x-xkeen-jsonc-using"] == "1",
            )
        }

    private fun get(baseUrl: String, endpoint: String): HttpResponse {
        val url = resolveEndpoint(baseUrl, endpoint)
        val connection = url.toURL().openConnection() as HttpURLConnection
        return try {
            connection.requestMethod = "GET"
            connection.connectTimeout = 5_000
            connection.readTimeout = 10_000
            connection.useCaches = false
            connection.setRequestProperty("Accept", "application/json, text/plain;q=0.9")
            connection.setRequestProperty("Cache-Control", "no-cache")

            val status = connection.responseCode
            val stream = if (status in 200..299) connection.inputStream else connection.errorStream
            val body = stream?.bufferedReader(StandardCharsets.UTF_8)?.use { it.readText() }.orEmpty()
            if (status !in 200..299) {
                throw XrayConfigException("HTTP $status при загрузке конфигураций Xray.")
            }
            if (connection.contentType.orEmpty().contains("text/html", ignoreCase = true)) {
                throw XrayConfigException(
                    "Xkeen UI вернул страницу входа. Подключите авторизованную сессию.",
                )
            }
            HttpResponse(
                body = body,
                headers = connection.headerFields
                    .filterKeys { it != null }
                    .mapKeys { (name, _) -> name.orEmpty().lowercase() }
                    .mapValues { (_, values) -> values?.firstOrNull().orEmpty() },
            )
        } finally {
            connection.disconnect()
        }
    }
}

internal class XrayConfigException(message: String, cause: Throwable? = null) :
    Exception(message, cause)

private data class HttpResponse(
    val body: String,
    val headers: Map<String, String>,
)

private fun resolveEndpoint(baseUrl: String, endpoint: String): URI {
    val normalizedBase = baseUrl.trim().trimEnd('/')
    if (normalizedBase.isBlank()) {
        throw XrayConfigException("Не указан адрес Xkeen UI.")
    }
    return try {
        URI.create("$normalizedBase/${endpoint.trimStart('/')}")
    } catch (error: IllegalArgumentException) {
        throw XrayConfigException("Некорректный адрес Xkeen UI.", error)
    }
}

private fun String.isXrayConfigFilename(): Boolean {
    val normalized = trim().lowercase()
    return normalized.endsWith(".json") || normalized.endsWith(".jsonc")
}

private fun JSONObject.optLongOrNull(name: String): Long? =
    if (has(name) && !isNull(name)) optLong(name) else null
