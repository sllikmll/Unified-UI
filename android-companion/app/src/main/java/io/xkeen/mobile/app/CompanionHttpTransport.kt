package io.xkeen.mobile.app

import java.net.HttpURLConnection
import java.net.URI
import java.nio.charset.StandardCharsets
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

internal data class CompanionHttpRequest(
    val baseUrl: String,
    val endpoint: String,
    val headers: Map<String, String> = emptyMap(),
)

internal data class CompanionHttpResponse(
    val statusCode: Int,
    val body: String,
    val headers: Map<String, String>,
    val contentType: String,
)

internal interface CompanionHttpTransport {
    suspend fun get(request: CompanionHttpRequest): CompanionHttpResponse
}

internal class HttpUrlConnectionCompanionTransport : CompanionHttpTransport {
    override suspend fun get(request: CompanionHttpRequest): CompanionHttpResponse =
        withContext(Dispatchers.IO) {
            val url = resolveCompanionEndpoint(request.baseUrl, request.endpoint)
            val connection = url.toURL().openConnection() as HttpURLConnection
            try {
                connection.requestMethod = "GET"
                connection.connectTimeout = 5_000
                connection.readTimeout = 10_000
                connection.useCaches = false
                request.headers.forEach(connection::setRequestProperty)

                val status = connection.responseCode
                val stream = if (status in 200..299) connection.inputStream else connection.errorStream
                val body = stream?.bufferedReader(StandardCharsets.UTF_8)?.use { it.readText() }.orEmpty()

                CompanionHttpResponse(
                    statusCode = status,
                    body = body,
                    headers = connection.headerFields
                        .filterKeys { it != null }
                        .mapKeys { (name, _) -> name.orEmpty().lowercase() }
                        .mapValues { (_, values) -> values?.firstOrNull().orEmpty() },
                    contentType = connection.contentType.orEmpty(),
                )
            } catch (error: Exception) {
                throw CompanionTransportException("Не удалось выполнить запрос к Xkeen UI.", error)
            } finally {
                connection.disconnect()
            }
        }
}

internal class CompanionTransportException(message: String, cause: Throwable? = null) :
    Exception(message, cause)

internal fun resolveCompanionEndpoint(baseUrl: String, endpoint: String): URI {
    val normalizedBase = baseUrl.trim().trimEnd('/')
    if (normalizedBase.isBlank()) {
        throw CompanionTransportException("Не указан адрес Xkeen UI.")
    }
    return try {
        URI.create("$normalizedBase/${endpoint.trimStart('/')}")
    } catch (error: IllegalArgumentException) {
        throw CompanionTransportException("Некорректный адрес Xkeen UI.", error)
    }
}
