package io.unified.mobile.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class JsonSyntaxHighlighterTest {
    @Test
    fun stringValuesAreNotRecoloredAsNumbers() {
        val source = """{"port":"443","enabled":true,"value":443}"""
        val highlighted = highlightJsonc(source)
        val styledTokens = highlighted.spanStyles.map { range ->
            source.substring(range.start, range.end)
        }

        assertEquals(1, styledTokens.count { it == "\"443\"" })
        assertEquals(1, styledTokens.count { it == "443" })
        assertTrue(styledTokens.contains("true"))
    }

    @Test
    fun jsoncCommentsRemainSingleTokens() {
        val source = "// \"port\": 443\n{\"enabled\": false} /* true 12 */"
        val highlighted = highlightJsonc(source)
        val styledTokens = highlighted.spanStyles.map { range ->
            source.substring(range.start, range.end)
        }

        assertTrue(styledTokens.contains("// \"port\": 443"))
        assertTrue(styledTokens.contains("/* true 12 */"))
        assertFalse(styledTokens.contains("\"port\""))
    }
}
