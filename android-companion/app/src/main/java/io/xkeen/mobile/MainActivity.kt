package io.xkeen.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.SystemBarStyle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import io.xkeen.mobile.app.CompanionApp
import io.xkeen.mobile.app.CompanionViewModel

class MainActivity : ComponentActivity() {
    private val companionViewModel: CompanionViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge(
            statusBarStyle = SystemBarStyle.dark(android.graphics.Color.TRANSPARENT),
        )
        setContent {
            CompanionApp(controller = companionViewModel.controller)
        }
    }
}
