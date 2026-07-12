package io.xkeen.mobile.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val LightColors = lightColorScheme(
    primary = Sky,
    onPrimary = Snow,
    primaryContainer = SkySoft,
    onPrimaryContainer = Ink,
    secondary = Teal,
    onSecondary = Snow,
    secondaryContainer = TealSoft,
    onSecondaryContainer = Teal,
    tertiary = Amber,
    onTertiary = Snow,
    tertiaryContainer = AmberSoft,
    onTertiaryContainer = AmberDeep,
    error = Danger,
    onError = Snow,
    errorContainer = DangerSoft,
    onErrorContainer = Danger,
    background = Mist,
    onBackground = Ink,
    surface = Snow,
    onSurface = Ink,
    surfaceContainerLowest = Snow,
    surfaceContainerLow = Mist,
    surfaceContainer = Cloud,
    surfaceContainerHighest = SkySoft,
    onSurfaceVariant = Slate,
)

private val DarkColors = darkColorScheme(
    primary = WebPanelPalette.Border,
    onPrimary = WebPanelPalette.Background,
    primaryContainer = WebPanelPalette.Accent,
    onPrimaryContainer = WebPanelPalette.TextStrong,
    secondary = Color(0xFF7DD3FC),
    onSecondary = WebPanelPalette.Background,
    secondaryContainer = Color(0xFF0D2340),
    onSecondaryContainer = WebPanelPalette.TextBlue,
    tertiary = WebPanelPalette.Warning,
    onTertiary = WebPanelPalette.Background,
    tertiaryContainer = Color(0xFF713F12),
    onTertiaryContainer = Color(0xFFFEF3C7),
    error = WebPanelPalette.Error,
    onError = WebPanelPalette.Background,
    errorContainer = Color(0xFF7F1D1D),
    onErrorContainer = Color(0xFFFEE2E2),
    background = WebPanelPalette.Background,
    onBackground = WebPanelPalette.Text,
    surface = WebPanelPalette.Surface,
    onSurface = WebPanelPalette.Text,
    surfaceContainerLowest = WebPanelPalette.BackgroundDeep,
    surfaceContainerLow = WebPanelPalette.Panel,
    surfaceContainer = WebPanelPalette.Surface,
    surfaceContainerHighest = WebPanelPalette.SurfaceRaised,
    onSurfaceVariant = WebPanelPalette.Muted,
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
