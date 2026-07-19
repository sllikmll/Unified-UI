package io.unified.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.SystemBarStyle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import io.unified.mobile.app.AppPhase
import io.unified.mobile.app.CompanionApp
import io.unified.mobile.app.CompanionController
import io.unified.mobile.app.CompanionUiState
import io.unified.mobile.app.MainTab
import io.unified.mobile.app.WorkspaceSection
import io.unified.mobile.app.XrayDatFile
import io.unified.mobile.app.XrayDatItem
import io.unified.mobile.app.XrayDatKind
import io.unified.mobile.app.XrayDatState
import io.unified.mobile.app.XrayDatTag

/** Debug-only, network-free visual surface for the compact DAT viewer. */
class XrayDatPreviewActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge(statusBarStyle = SystemBarStyle.dark(android.graphics.Color.TRANSPARENT))
        val showItems = intent.getBooleanExtra("items", false)
        val controller = CompanionController(
            initialState = CompanionUiState(
                phase = AppPhase.Ready,
                mainTab = MainTab.Routing,
                workspaceSection = WorkspaceSection.XrayAssets,
                dashboard = io.unified.mobile.app.demoDashboardState().copy(
                    endpoint = "",
                    availableCores = listOf("Xray", "Mihomo"),
                    activeCore = "Xray",
                ),
                xrayDat = previewDatState(showItems),
            ),
        )
        setContent {
            CompanionApp(controller)
        }
    }
}

private fun previewDatState(showItems: Boolean): XrayDatState {
    val file = XrayDatFile(
        kind = XrayDatKind.GeoSite,
        name = "geosite_v2fly.dat",
        path = "/opt/etc/xray/dat/geosite_v2fly.dat",
        sizeBytes = 2_254_112,
        modifiedAtEpochSeconds = 1_784_286_600,
    )
    return XrayDatState(
        files = listOf(
            file,
            XrayDatFile(XrayDatKind.GeoSite, "zkeen.dat", "/opt/etc/xray/dat/zkeen.dat", 1_410_048),
            XrayDatFile(XrayDatKind.GeoIp, "geoip_v2fly.dat", "/opt/etc/xray/dat/geoip_v2fly.dat", 408_678),
        ),
        selectedFilePath = file.path,
        geodatInstalled = true,
        tags = listOf(
            XrayDatTag("CATEGORY-ADS-ALL", 124),
            XrayDatTag("DISCORD", 40),
            XrayDatTag("GITHUB", 76),
            XrayDatTag("GOOGLE", 211),
            XrayDatTag("INSTAGRAM", 54),
            XrayDatTag("NETFLIX", 82),
            XrayDatTag("TELEGRAM", 38),
            XrayDatTag("YOUTUBE", 93),
        ),
        selectedTag = "DISCORD".takeIf { showItems },
        items = if (showItems) {
            listOf("discord.com", "discord.gg", "discordapp.com", "discordapp.net", "discord.media", "discord.gift", "discord.design", "discord.new")
                .map { XrayDatItem("domain", it) }
        } else emptyList(),
        itemTotal = 40.takeIf { showItems },
        hasLoadedCatalog = true,
    )
}
