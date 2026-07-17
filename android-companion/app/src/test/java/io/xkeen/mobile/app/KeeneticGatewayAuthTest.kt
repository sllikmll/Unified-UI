package io.xkeen.mobile.app

import java.net.InetAddress
import java.net.ServerSocket
import java.net.SocketException
import java.net.URI
import java.nio.charset.StandardCharsets
import java.util.Collections
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

class KeeneticGatewayAuthTest {
    @Test
    fun parsesKeeneticDigestChallenge() {
        val challenge = parseKeeneticDigestChallenge(
            """Digest realm="Keenetic Giga", nonce="nonce-value", qop="auth,auth-int", opaque="proxy", algorithm=MD5""",
        )

        assertNotNull(challenge)
        assertEquals("Keenetic Giga", challenge?.realm)
        assertEquals("nonce-value", challenge?.nonce)
        assertEquals(setOf("auth", "auth-int"), challenge?.qop)
        assertEquals("proxy", challenge?.opaque)
    }

    @Test
    fun createsRfcCompatibleDigestResponse() {
        val authorization = createKeeneticDigestAuthorization(
            challenge = KeeneticDigestChallenge(
                realm = "testrealm@host.com",
                nonce = "dcd98b7102dd2f0e8b11d0f600bfb0c093",
                qop = setOf("auth"),
            ),
            credentials = KeeneticGatewayCredentials(
                username = "Mufasa",
                password = "Circle Of Life",
            ),
            method = "GET",
            uri = URI.create("http://www.example.com/dir/index.html"),
            nonceCount = 1,
            cnonce = "0a4f113b",
        )

        assertTrue(authorization.startsWith("Digest username=\"Mufasa\""))
        assertTrue(authorization.contains("uri=\"/dir/index.html\""))
        assertTrue(authorization.contains("nc=00000001"))
        assertTrue(authorization.contains("response=\"6629fae49393a05397450978507c4ef1\""))
    }

    @Test
    fun transportAnswersChallengeAndThenUsesCachedDigestState() = runTest {
        val server = DigestTestServer(expectedRequests = 3)
        try {
            val baseUrl = server.baseUrl
            val credentials = InMemoryKeeneticGatewayAuthStore().also { store ->
                store.save(
                    baseUrl,
                    KeeneticGatewayCredentials(username = "admin", password = "router-secret"),
                )
            }
            val transport = HttpUrlConnectionCompanionTransport(keeneticGatewayAuth = credentials)
            val request = CompanionHttpRequest(baseUrl, "/api/mobile/v1/bootstrap")

            transport.get(request)
            transport.get(request)

            assertEquals(3, server.authorizationHeaders.size)
            assertEquals(null, server.authorizationHeaders[0])
            assertTrue(server.authorizationHeaders[1]?.startsWith("Digest ") == true)
            assertTrue(server.authorizationHeaders[2]?.startsWith("Digest ") == true)
            assertTrue(server.authorizationHeaders[1]?.contains("nc=00000001") == true)
            assertTrue(server.authorizationHeaders[2]?.contains("nc=00000002") == true)
        } finally {
            server.close()
        }
    }

    @Test
    fun transportDistinguishesKeeneticChallengeFromXkeenLogin() = runTest {
        val server = DigestTestServer(expectedRequests = 1, alwaysChallenge = true)
        try {
            val error = runCatching {
                HttpUrlConnectionCompanionTransport().get(
                    CompanionHttpRequest(
                        baseUrl = server.baseUrl,
                        endpoint = "/api/mobile/v1/bootstrap",
                    ),
                )
            }.exceptionOrNull() as? CompanionTransportException

            assertNotNull(error)
            assertEquals(
                CompanionTransportFailureKind.KeeneticAuthenticationRequired,
                error?.failure?.kind,
            )
            assertEquals("keenetic_auth_required", error?.failure?.serverCode)
        } finally {
            server.close()
        }
    }
}

private class DigestTestServer(
    private val expectedRequests: Int,
    private val alwaysChallenge: Boolean = false,
) : AutoCloseable {
    private val server = ServerSocket(0, 10, InetAddress.getLoopbackAddress())
    val authorizationHeaders = Collections.synchronizedList(mutableListOf<String?>())
    val baseUrl = "http://127.0.0.1:${server.localPort}"

    private val worker = Thread {
        try {
            repeat(expectedRequests) {
                server.accept().use { socket ->
                    val reader = socket.getInputStream().bufferedReader(StandardCharsets.US_ASCII)
                    var authorization: String? = null
                    while (true) {
                        val line = reader.readLine() ?: break
                        if (line.isEmpty()) break
                        if (line.startsWith("Authorization:", ignoreCase = true)) {
                            authorization = line.substringAfter(':').trim()
                        }
                    }
                    authorizationHeaders += authorization
                    val challenge = alwaysChallenge || authorization == null
                    val body = if (challenge) {
                        ByteArray(0)
                    } else {
                        """{"ok":true,"data":{"auth":{"configured":true,"authenticated":false}}}"""
                            .toByteArray(StandardCharsets.UTF_8)
                    }
                    val headers = buildString {
                        append(if (challenge) "HTTP/1.1 401 Unauthorized\r\n" else "HTTP/1.1 200 OK\r\n")
                        if (challenge) {
                            append("WWW-Authenticate: Digest realm=\"Keenetic Test\", nonce=\"test-nonce\", qop=\"auth\", algorithm=MD5\r\n")
                        }
                        append("Content-Type: application/json\r\n")
                        append("Content-Length: ${body.size}\r\n")
                        append("Connection: close\r\n\r\n")
                    }.toByteArray(StandardCharsets.US_ASCII)
                    socket.getOutputStream().use { output ->
                        output.write(headers)
                        output.write(body)
                        output.flush()
                    }
                }
            }
        } catch (_: SocketException) {
            // Closing the fixture is the normal way to stop a failed/short test.
        }
    }.apply {
        isDaemon = true
        name = "keenetic-digest-test-server"
        start()
    }

    override fun close() {
        server.close()
        worker.join(1_000)
    }
}
