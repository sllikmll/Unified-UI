package io.xkeen.mobile.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class RoutingDraftValidatorTest {
    @Test
    fun `valid draft passes validation`() {
        val draft = """
            {
              "routing": {
                "rules": [
                  {
                    "type": "field",
                    "outboundTag": "direct"
                  }
                ]
              }
            }
        """.trimIndent()

        val result = validateRoutingDraft(draft)

        assertEquals(RoutingValidationState.Valid, result.state)
        assertTrue(result.details.contains("routing object found"))
    }

    @Test
    fun `invalid draft reports structural problems`() {
        val draft = """
            {
              "routing": {
                "comment": "TODO_INVALID"
            }
        """.trimIndent()

        val result = validateRoutingDraft(draft)

        assertEquals(RoutingValidationState.Invalid, result.state)
        assertTrue(result.details.contains("No rules block found."))
        assertTrue(result.details.contains("Brace count does not match."))
        assertTrue(result.details.contains("Draft still contains TODO_INVALID marker."))
    }
}
