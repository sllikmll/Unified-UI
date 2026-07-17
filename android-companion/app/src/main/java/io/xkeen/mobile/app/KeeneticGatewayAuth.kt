package io.xkeen.mobile.app

import java.net.URI
import java.nio.charset.StandardCharsets
import java.security.MessageDigest
import java.security.SecureRandom
import java.util.Locale
import java.util.concurrent.ConcurrentHashMap

/**
 * Credentials for the Keenetic HTTP proxy that protects remote KeenDNS applications.
 *
 * They deliberately stay in process memory. The router password is never written to the
 * connection store or to [SessionMaterialStore].
 */
internal data class KeeneticGatewayCredentials(
    val username: String,
    val password: String,
)

internal interface KeeneticGatewayAuthStore {
    fun credentialsFor(normalizedBaseUrl: String): KeeneticGatewayCredentials?

    fun save(baseUrl: String, credentials: KeeneticGatewayCredentials)

    fun clear(baseUrl: String)
}

internal object NoOpKeeneticGatewayAuthStore : KeeneticGatewayAuthStore {
    override fun credentialsFor(normalizedBaseUrl: String): KeeneticGatewayCredentials? = null

    override fun save(baseUrl: String, credentials: KeeneticGatewayCredentials) = Unit

    override fun clear(baseUrl: String) = Unit
}

internal class InMemoryKeeneticGatewayAuthStore : KeeneticGatewayAuthStore {
    private val credentials = ConcurrentHashMap<String, KeeneticGatewayCredentials>()

    override fun credentialsFor(normalizedBaseUrl: String): KeeneticGatewayCredentials? =
        credentials[normalizedBaseUrl]

    override fun save(baseUrl: String, credentials: KeeneticGatewayCredentials) {
        this.credentials[normalizeCompanionBaseUrl(baseUrl).toString()] = credentials.copy(
            username = credentials.username.trim(),
        )
    }

    override fun clear(baseUrl: String) {
        credentials.remove(normalizeCompanionBaseUrl(baseUrl).toString())
    }
}

internal data class KeeneticDigestChallenge(
    val realm: String,
    val nonce: String,
    val opaque: String? = null,
    val algorithm: String = "MD5",
    val qop: Set<String> = emptySet(),
    val stale: Boolean = false,
)

/** Parses the RFC Digest challenge emitted by the Keenetic KeenDNS HTTP proxy. */
internal fun parseKeeneticDigestChallenge(header: String?): KeeneticDigestChallenge? {
    val value = header?.trim().orEmpty()
    val digestMatch = Regex("""(?:^|,)\s*Digest\s+""", RegexOption.IGNORE_CASE).find(value)
        ?: return null
    val parameters = value.substring(digestMatch.range.last + 1)
    val values = buildMap<String, String> {
        val parameterPattern = Regex("""([A-Za-z][A-Za-z0-9_-]*)\s*=\s*(?:"((?:\\.|[^"])*)"|([^,\s]+))""")
        parameterPattern.findAll(parameters).forEach { match ->
            val name = match.groupValues[1].lowercase(Locale.ROOT)
            val raw = match.groupValues[2].ifEmpty { match.groupValues[3] }
            put(name, raw.replace("\\\"", "\"").replace("\\\\", "\\"))
        }
    }
    val realm = values["realm"]?.takeIf(String::isNotBlank) ?: return null
    val nonce = values["nonce"]?.takeIf(String::isNotBlank) ?: return null
    val algorithm = values["algorithm"]?.uppercase(Locale.ROOT) ?: "MD5"
    if (algorithm !in setOf("MD5", "MD5-SESS", "SHA-256", "SHA-256-SESS")) return null
    val qop = values["qop"].orEmpty()
        .split(',')
        .map { it.trim().lowercase(Locale.ROOT) }
        .filter(String::isNotBlank)
        .toSet()
    if (qop.isNotEmpty() && "auth" !in qop) return null
    return KeeneticDigestChallenge(
        realm = realm,
        nonce = nonce,
        opaque = values["opaque"]?.takeIf(String::isNotBlank),
        algorithm = algorithm,
        qop = qop,
        stale = values["stale"].equals("true", ignoreCase = true),
    )
}

internal fun createKeeneticDigestAuthorization(
    challenge: KeeneticDigestChallenge,
    credentials: KeeneticGatewayCredentials,
    method: String,
    uri: URI,
    nonceCount: Int,
    cnonce: String = randomDigestCnonce(),
): String {
    val requestTarget = buildString {
        append(uri.rawPath.ifEmpty { "/" })
        uri.rawQuery?.let { append('?').append(it) }
    }
    val digestName = if (challenge.algorithm.startsWith("SHA-256")) "SHA-256" else "MD5"
    val username = credentials.username.trim()
    val initialHa1 = digestHex(
        digestName,
        "$username:${challenge.realm}:${credentials.password}",
    )
    val ha1 = if (challenge.algorithm.endsWith("-SESS")) {
        digestHex(digestName, "$initialHa1:${challenge.nonce}:$cnonce")
    } else {
        initialHa1
    }
    val ha2 = digestHex(digestName, "${method.uppercase(Locale.ROOT)}:$requestTarget")
    val nc = nonceCount.coerceAtLeast(1).toString(16).padStart(8, '0')
    val response = if (challenge.qop.isEmpty()) {
        digestHex(digestName, "$ha1:${challenge.nonce}:$ha2")
    } else {
        digestHex(digestName, "$ha1:${challenge.nonce}:$nc:$cnonce:auth:$ha2")
    }
    return buildString {
        append("Digest username=\"").append(username.escapeDigestValue()).append('"')
        append(", realm=\"").append(challenge.realm.escapeDigestValue()).append('"')
        append(", nonce=\"").append(challenge.nonce.escapeDigestValue()).append('"')
        append(", uri=\"").append(requestTarget.escapeDigestValue()).append('"')
        append(", algorithm=").append(challenge.algorithm)
        append(", response=\"").append(response).append('"')
        challenge.opaque?.let {
            append(", opaque=\"").append(it.escapeDigestValue()).append('"')
        }
        if (challenge.qop.isNotEmpty()) {
            append(", qop=auth, nc=").append(nc)
            append(", cnonce=\"").append(cnonce.escapeDigestValue()).append('"')
        }
    }
}

private fun digestHex(algorithm: String, value: String): String =
    MessageDigest.getInstance(algorithm)
        .digest(value.toByteArray(StandardCharsets.UTF_8))
        .joinToString(separator = "") { byte -> "%02x".format(byte.toInt() and 0xff) }

private fun String.escapeDigestValue(): String = replace("\\", "\\\\").replace("\"", "\\\"")

private fun randomDigestCnonce(): String {
    val bytes = ByteArray(16)
    SecureRandom().nextBytes(bytes)
    return bytes.joinToString(separator = "") { byte -> "%02x".format(byte.toInt() and 0xff) }
}
