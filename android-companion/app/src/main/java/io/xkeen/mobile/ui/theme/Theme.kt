package io.xkeen.mobile.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val LightColors = lightColorScheme(
    primary = Olive,
    onPrimary = Paper,
    primaryContainer = OliveSoft,
    onPrimaryContainer = Ink,
    secondary = Copper,
    onSecondary = Paper,
    secondaryContainer = CopperSoft,
    onSecondaryContainer = Ink,
    tertiary = Slate,
    onTertiary = Paper,
    tertiaryContainer = SlateSoft,
    onTertiaryContainer = Ink,
    error = Alert,
    onError = Paper,
    errorContainer = AlertSoft,
    onErrorContainer = Ink,
    background = Sand,
    onBackground = Ink,
    surface = Paper,
    onSurface = Ink,
    surfaceContainerLowest = Paper,
    surfaceContainerLow = Sand,
    surfaceContainer = SlateSoft,
    surfaceContainerHighest = OliveSoft,
    onSurfaceVariant = Slate,
)

private val DarkColors = darkColorScheme(
    primary = OliveSoft,
    onPrimary = Ink,
    primaryContainer = Olive,
    onPrimaryContainer = Paper,
    secondary = CopperSoft,
    onSecondary = Ink,
    secondaryContainer = Copper,
    onSecondaryContainer = Paper,
    tertiary = SlateSoft,
    onTertiary = Ink,
    tertiaryContainer = Slate,
    onTertiaryContainer = Paper,
    error = AlertSoft,
    onError = Ink,
    errorContainer = Alert,
    onErrorContainer = Paper,
    background = Ink,
    onBackground = Paper,
    surface = Slate,
    onSurface = Paper,
    surfaceContainerLowest = Ink,
    surfaceContainerLow = Slate,
    surfaceContainer = Olive,
    surfaceContainerHighest = Copper,
    onSurfaceVariant = Sand,
)

@Composable
fun XkeenMobileTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkColors else LightColors,
        typography = XkeenTypography,
        content = content,
    )
}
