package io.xkeen.mobile.app

import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.navigationBars
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBars
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.automirrored.outlined.FactCheck
import androidx.compose.material.icons.automirrored.outlined.Subject
import androidx.compose.material.icons.outlined.AccountTree
import androidx.compose.material.icons.outlined.Bolt
import androidx.compose.material.icons.outlined.DoneAll
import androidx.compose.material.icons.outlined.Edit
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.Http
import androidx.compose.material.icons.outlined.Key
import androidx.compose.material.icons.outlined.Lan
import androidx.compose.material.icons.outlined.MoreHoriz
import androidx.compose.material.icons.outlined.Password
import androidx.compose.material.icons.outlined.PlayArrow
import androidx.compose.material.icons.outlined.Preview
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material.icons.outlined.ReportProblem
import androidx.compose.material.icons.outlined.Save
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material.icons.outlined.SettingsBackupRestore
import androidx.compose.material.icons.outlined.Stop
import androidx.compose.material.icons.outlined.Verified
import androidx.compose.material.icons.outlined.VpnKey
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.AssistChip
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import io.xkeen.mobile.ui.theme.XkeenMobileTheme
import kotlinx.coroutines.delay

@Composable
fun CompanionApp() {
    val controller = remember { DemoCompanionController() }
    val state = controller.state

    XkeenMobileTheme {
        Surface(
            modifier = Modifier.fillMaxSize(),
            color = MaterialTheme.colorScheme.background,
        ) {
            when (state.phase) {
                AppPhase.Launching -> LaunchRoute(controller)
                AppPhase.Connections -> ConnectionsRoute(state, controller)
                AppPhase.PairLogin -> PairLoginRoute(state, controller)
                AppPhase.Ready -> ReadyRoute(state, controller)
            }
        }
    }
}

@Composable
private fun LaunchRoute(controller: DemoCompanionController) {
    LaunchedEffect(Unit) {
        delay(1100)
        controller.finishLaunch()
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.surfaceContainerLowest)
            .windowInsetsPadding(WindowInsets.safeDrawing),
        contentAlignment = Alignment.Center,
    ) {
        Card(
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.surface,
            ),
            shape = RoundedCornerShape(28.dp),
        ) {
            Column(
                modifier = Modifier.padding(horizontal = 28.dp, vertical = 24.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
                horizontalAlignment = Alignment.Start,
            ) {
                Surface(
                    shape = CircleShape,
                    color = MaterialTheme.colorScheme.secondaryContainer,
                ) {
                    Icon(
                        imageVector = Icons.Outlined.Bolt,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.onSecondaryContainer,
                        modifier = Modifier.padding(12.dp),
                    )
                }
                Text(
                    text = "Xkeen Mobile",
                    style = MaterialTheme.typography.headlineSmall,
                )
                Text(
                    text = "Restoring the last trusted shell and preparing compact controls for phone-sized workflows.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Row(
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    CircularProgressIndicator(modifier = Modifier.size(20.dp), strokeWidth = 2.dp)
                    Text(
                        text = "Checking saved connections, auth state, and routing drafts",
                        style = MaterialTheme.typography.labelLarge,
                    )
                }
            }
        }
    }
}

@Composable
private fun ConnectionsRoute(
    state: CompanionUiState,
    controller: DemoCompanionController,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .windowInsetsPadding(WindowInsets.safeDrawing)
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        TitleBlock(
            eyebrow = "Connections",
            title = "Trusted instances",
            subtitle = "Manual host entry first, then pairing or login. No browser-sized layout, no stretched controls.",
        )

        SectionCard(
            title = "Add instance",
            supporting = "Draft a connection now. In the real app this will feed secure storage and mobile bootstrap.",
        ) {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                CompactField(
                    modifier = Modifier.weight(1f),
                    value = state.connectionDraft.name,
                    onValueChange = controller::updateConnectionDraftName,
                    label = "Label",
                    leadingIcon = { Icon(Icons.Outlined.Lan, contentDescription = null) },
                )
                CompactField(
                    modifier = Modifier.weight(1f),
                    value = state.connectionDraft.baseUrl,
                    onValueChange = controller::updateConnectionDraftUrl,
                    label = "Base URL",
                    leadingIcon = { Icon(Icons.Outlined.Http, contentDescription = null) },
                    keyboardType = KeyboardType.Uri,
                )
            }
            CompactActionRow {
                FilledTonalButton(onClick = controller::saveConnectionDraft) {
                    Icon(Icons.Outlined.Save, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("Save draft")
                }
            }
        }

        SectionCard(
            title = "Saved connections",
            supporting = "Tap any card to continue into pairing or login.",
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                state.connections.forEach { connection ->
                    ConnectionCard(
                        connection = connection,
                        onOpen = { controller.selectConnection(connection.id) },
                    )
                }
            }
        }
    }
}

@Composable
private fun PairLoginRoute(
    state: CompanionUiState,
    controller: DemoCompanionController,
) {
    val connection = state.connections.firstOrNull { it.id == state.selectedConnectionId }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .windowInsetsPadding(WindowInsets.safeDrawing)
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = controller::backToConnections) {
                Icon(Icons.AutoMirrored.Outlined.ArrowBack, contentDescription = "Back")
            }
            Spacer(Modifier.width(4.dp))
            Column {
                Text(
                    text = connection?.name ?: "Selected instance",
                    style = MaterialTheme.typography.titleLarge,
                )
                Text(
                    text = connection?.baseUrl ?: "",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }

        SectionCard(
            title = "Auth gate",
            supporting = "This shell keeps pairing and login separate from the main navigation, so the bottom nav only appears after a trusted session exists.",
        ) {
            CompactStatusRow(
                items = listOf(
                    connectionStatusChip(connection?.status ?: ConnectionStatus.NeedsAuth),
                    StatusChipModel("Phone-safe flow", MaterialTheme.colorScheme.tertiaryContainer, MaterialTheme.colorScheme.onTertiaryContainer),
                ),
            )
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                CompactField(
                    modifier = Modifier.weight(1f),
                    value = state.loginForm.username,
                    onValueChange = controller::updateUsername,
                    label = "User",
                    leadingIcon = { Icon(Icons.Outlined.Key, contentDescription = null) },
                )
                CompactField(
                    modifier = Modifier.weight(1f),
                    value = state.loginForm.password,
                    onValueChange = controller::updatePassword,
                    label = "Password",
                    leadingIcon = { Icon(Icons.Outlined.Password, contentDescription = null) },
                    visualTransformation = PasswordVisualTransformation(),
                )
            }
            CompactActionRow {
                FilledTonalButton(onClick = controller::pairDemoDevice) {
                    Icon(Icons.Outlined.VpnKey, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("Pair demo")
                }
                OutlinedButton(onClick = controller::login) {
                    Icon(Icons.Outlined.Verified, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("Login")
                }
            }
        }

        SectionCard(
            title = "What opens next",
            supporting = "The first ready shell is intentionally compact and useful before any backend integration lands.",
        ) {
            CompactStatusRow(
                items = listOf(
                    statusChip("Dashboard"),
                    statusChip("Routing Xray"),
                    statusChip("Logs"),
                    statusChip("More"),
                ),
            )
        }
    }
}

@Composable
private fun ReadyRoute(
    state: CompanionUiState,
    controller: DemoCompanionController,
) {
    Scaffold(
        modifier = Modifier.fillMaxSize(),
        topBar = {
            ReadyTopBar(state)
        },
        bottomBar = {
            ReadyBottomBar(
                selected = state.mainTab,
                onSelected = controller::selectTab,
            )
        },
        contentWindowInsets = WindowInsets.statusBars,
    ) { innerPadding ->
        val contentModifier = Modifier
            .padding(innerPadding)
            .padding(horizontal = 16.dp)
            .windowInsetsPadding(WindowInsets.navigationBars)

        when (state.mainTab) {
            MainTab.Home -> DashboardScreen(state, controller, contentModifier)
            MainTab.Routing -> RoutingScreen(state, controller, contentModifier)
            MainTab.Logs -> LogsScreen(state, controller, contentModifier)
            MainTab.More -> MoreScreen(state, controller, contentModifier)
        }

        PendingActionDialog(
            pendingAction = state.pendingAction,
            onDismiss = controller::dismissPendingAction,
            onConfirm = controller::confirmPendingAction,
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ReadyTopBar(state: CompanionUiState) {
    TopAppBar(
        title = {
            Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text(
                    text = state.dashboard.instanceLabel,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                Text(
                    text = "${state.dashboard.statusSummary}  •  ${state.dashboard.activeCore}",
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
        },
        actions = {
            AssistChip(
                onClick = {},
                label = {
                    Text(serviceStateLabel(state.dashboard.serviceState))
                },
                leadingIcon = {
                    Icon(Icons.Outlined.Bolt, contentDescription = null, modifier = Modifier.size(18.dp))
                },
            )
            Spacer(Modifier.width(8.dp))
        },
    )
}

@Composable
private fun ReadyBottomBar(
    selected: MainTab,
    onSelected: (MainTab) -> Unit,
) {
    NavigationBar {
        BottomBarItem(MainTab.Home, selected, onSelected, Icons.Outlined.Home, "Home")
        BottomBarItem(MainTab.Routing, selected, onSelected, Icons.Outlined.AccountTree, "Routing")
        BottomBarItem(MainTab.Logs, selected, onSelected, Icons.AutoMirrored.Outlined.Subject, "Logs")
        BottomBarItem(MainTab.More, selected, onSelected, Icons.Outlined.MoreHoriz, "More")
    }
}

@Composable
private fun DashboardScreen(
    state: CompanionUiState,
    controller: DemoCompanionController,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        SectionCard(
            title = "Instance summary",
            supporting = state.dashboard.endpoint,
        ) {
            CompactStatusRow(
                items = buildList {
                    add(serviceStateChip(state.dashboard.serviceState))
                    add(statusChip(state.dashboard.activeCore))
                    state.dashboard.capabilities.forEach { add(statusChip(it)) }
                },
            )
            Spacer(Modifier.height(12.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                MetricCard("Version", state.dashboard.version, Modifier.weight(1f))
                MetricCard("Last action", state.dashboard.lastOperation, Modifier.weight(1f))
            }
            state.dashboard.lastError?.let { error ->
                Spacer(Modifier.height(12.dp))
                WarningBanner(error)
            }
        }

        SectionCard(
            title = "Safe actions",
            supporting = "Small buttons and explicit confirms instead of a full-width control bar.",
        ) {
            CompactActionRow {
                SmallActionButton("Start", Icons.Outlined.PlayArrow) {
                    controller.requestServiceAction(ServiceAction.Start)
                }
                SmallActionButton("Stop", Icons.Outlined.Stop) {
                    controller.requestServiceAction(ServiceAction.Stop)
                }
                SmallActionButton("Restart", Icons.Outlined.Refresh) {
                    controller.requestServiceAction(ServiceAction.Restart)
                }
            }
        }

        SectionCard(
            title = "Recent events",
            supporting = "Compact status blocks keep the home screen dense but still readable on a phone.",
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                state.dashboard.recentEvents.forEach { event ->
                    EventRow(event)
                }
            }
        }
    }
}

@Composable
private fun RoutingScreen(
    state: CompanionUiState,
    controller: DemoCompanionController,
    modifier: Modifier = Modifier,
) {
    val routing = state.routing
    val selectedDocument = routing.documents.firstOrNull { it.id == routing.selectedDocumentId } ?: return
    val filteredDocuments = routing.documents.filter { document ->
        routing.searchQuery.isBlank() ||
            document.title.contains(routing.searchQuery, ignoreCase = true) ||
            document.path.contains(routing.searchQuery, ignoreCase = true)
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        SectionCard(
            title = "Routing Xray",
            supporting = "Read-first shell with save, validate, preview, and apply. No desktop split panes.",
        ) {
            CompactField(
                value = routing.searchQuery,
                onValueChange = controller::updateRoutingSearchQuery,
                label = "Search docs",
                leadingIcon = { Icon(Icons.Outlined.Search, contentDescription = null) },
                modifier = Modifier.fillMaxWidth(),
            )
            Spacer(Modifier.height(12.dp))
            Row(
                modifier = Modifier.horizontalScroll(rememberScrollState()),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                filteredDocuments.forEach { document ->
                    FilterChip(
                        selected = document.id == selectedDocument.id,
                        onClick = { controller.selectRoutingDocument(document.id) },
                        label = { Text(document.title) },
                    )
                }
            }
        }

        SectionCard(
            title = selectedDocument.title,
            supporting = selectedDocument.path,
        ) {
            CompactStatusRow(
                items = listOf(
                    statusChip("r${selectedDocument.revision}"),
                    statusChip(if (selectedDocument.hasDraftChanges) "draft changed" else "published clean"),
                    statusChip(if (selectedDocument.hasUnsavedChanges) "not saved" else "saved"),
                    statusChip(if (routing.mode == RoutingMode.Read) "read mode" else "edit mode"),
                ),
            )
            Spacer(Modifier.height(12.dp))
            Text(
                text = selectedDocument.summary,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.height(12.dp))
            CompactActionRow {
                SmallActionButton("Edit", Icons.Outlined.Edit, onClick = controller::enterRoutingEditMode)
                SmallActionButton("Validate", Icons.AutoMirrored.Outlined.FactCheck, onClick = controller::validateRouting)
                SmallActionButton("Preview", Icons.Outlined.Preview, onClick = controller::previewRouting)
                SmallActionButton("Save", Icons.Outlined.Save, onClick = controller::saveRouting)
                SmallActionButton("Apply", Icons.Outlined.DoneAll, onClick = controller::requestRoutingApply)
                SmallActionButton("Undo", Icons.Outlined.SettingsBackupRestore, onClick = controller::revertRoutingDraft)
            }
            Spacer(Modifier.height(12.dp))
            OutlinedTextField(
                value = selectedDocument.draftContent,
                onValueChange = controller::updateRoutingDraft,
                readOnly = routing.mode == RoutingMode.Read,
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = 220.dp),
                textStyle = MaterialTheme.typography.bodyMedium.copy(fontFamily = FontFamily.Monospace),
                label = {
                    Text(if (routing.mode == RoutingMode.Read) "Published or saved draft" else "Draft editor")
                },
            )
        }

        SectionCard(
            title = "Validation",
            supporting = routing.validation.message,
        ) {
            CompactStatusRow(
                items = listOf(validationChip(routing.validation.state)),
            )
            if (routing.validation.details.isNotEmpty()) {
                Spacer(Modifier.height(10.dp))
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    routing.validation.details.forEach { detail ->
                        Text(
                            text = "• $detail",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            }
        }

        routing.preview?.let { preview ->
            SectionCard(
                title = "Preview",
                supporting = preview.headline,
            ) {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    preview.details.forEach { detail ->
                        Text(
                            text = "• $detail",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun LogsScreen(
    state: CompanionUiState,
    controller: DemoCompanionController,
    modifier: Modifier = Modifier,
) {
    val filteredEntries = state.logs.entries.filter { entry ->
        when (state.logs.filter) {
            LogFilter.All -> true
            LogFilter.Service -> entry.source == "service"
            LogFilter.Routing -> entry.source == "routing"
            LogFilter.Errors -> entry.level == LogLevel.Error
        }
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        SectionCard(
            title = "Live logs",
            supporting = "This shell keeps recent history and live-tail concerns together, with reconnect kept visible in the diagnostics screen.",
        ) {
            CompactStatusRow(
                items = listOf(
                    statusChip("history + tail"),
                    statusChip("reconnect ready"),
                    statusChip("source filters"),
                ),
            )
            Spacer(Modifier.height(12.dp))
            Row(
                modifier = Modifier.horizontalScroll(rememberScrollState()),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                LogFilter.entries.forEach { filter ->
                    FilterChip(
                        selected = filter == state.logs.filter,
                        onClick = { controller.updateLogFilter(filter) },
                        label = { Text(filter.name) },
                    )
                }
            }
        }

        SectionCard(
            title = "Recent entries",
            supporting = "${filteredEntries.size} visible in the current filter",
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                filteredEntries.forEach { entry ->
                    LogRow(entry)
                }
            }
        }
    }
}

@Composable
private fun MoreScreen(
    state: CompanionUiState,
    controller: DemoCompanionController,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        SectionCard(
            title = "Diagnostics",
            supporting = "The app shell keeps operational clarity close at hand instead of hiding it in a web-style settings maze.",
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                state.diagnostics.forEach { item ->
                    DiagnosticRow(item)
                }
            }
        }

        SectionCard(
            title = "Connections",
            supporting = "The current instance can be disconnected without touching destructive admin surfaces.",
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                state.connections.forEach { connection ->
                    ConnectionMiniRow(connection)
                }
            }
            Spacer(Modifier.height(12.dp))
            CompactActionRow {
                OutlinedButton(onClick = controller::disconnect) {
                    Icon(Icons.AutoMirrored.Outlined.ArrowBack, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("Disconnect")
                }
            }
        }

        SectionCard(
            title = "Build info",
            supporting = "Initial Android skeleton",
        ) {
            CompactStatusRow(
                items = listOf(
                    statusChip("Compose shell"),
                    statusChip("Demo state"),
                    statusChip("Backend mock"),
                ),
            )
        }
    }
}

@Composable
private fun PendingActionDialog(
    pendingAction: PendingAction?,
    onDismiss: () -> Unit,
    onConfirm: () -> Unit,
) {
    val dialog = when (pendingAction) {
        is PendingAction.Service -> when (pendingAction.action) {
            ServiceAction.Start -> DialogModel("Start service?", "This confirms a start request from the mobile shell.")
            ServiceAction.Stop -> DialogModel("Stop service?", "This confirms a stop request from the mobile shell.")
            ServiceAction.Restart -> DialogModel("Restart runtime?", "This confirms a restart request from the mobile shell.")
        }

        PendingAction.ApplyRouting -> DialogModel(
            title = "Apply routing draft?",
            body = "The draft was validated and saved. Apply now to publish the current routing revision.",
        )

        null -> null
    }

    dialog ?: return

    AlertDialog(
        onDismissRequest = onDismiss,
        confirmButton = {
            TextButton(onClick = onConfirm) {
                Text("Confirm")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        },
        title = {
            Text(dialog.title)
        },
        text = {
            Text(dialog.body)
        },
    )
}

@Composable
private fun ConnectionCard(
    connection: Connection,
    onOpen: () -> Unit,
) {
    Card(
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceContainerLow,
        ),
        shape = RoundedCornerShape(22.dp),
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(connection.name, style = MaterialTheme.typography.titleMedium)
                    Text(
                        text = connection.baseUrl,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
                FilledTonalButton(
                    onClick = onOpen,
                    contentPadding = PaddingValues(horizontal = 14.dp, vertical = 10.dp),
                ) {
                    Text("Open")
                }
            }
            CompactStatusRow(
                items = listOf(
                    connectionStatusChip(connection.status),
                    statusChip(connection.lastSeen),
                ),
            )
        }
    }
}

@Composable
private fun ConnectionMiniRow(connection: Connection) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(connection.name, style = MaterialTheme.typography.titleSmall)
            Text(
                text = connection.baseUrl,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        StatusChip(connectionStatusChip(connection.status))
    }
}

@Composable
private fun EventRow(event: RecentEvent) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
        verticalAlignment = Alignment.Top,
    ) {
        Surface(
            shape = RoundedCornerShape(14.dp),
            color = MaterialTheme.colorScheme.secondaryContainer,
        ) {
            Text(
                text = event.time,
                modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSecondaryContainer,
            )
        }
        Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text(event.title, style = MaterialTheme.typography.titleSmall)
            Text(
                text = event.subtitle,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun MetricCard(
    label: String,
    value: String,
    modifier: Modifier = Modifier,
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(20.dp),
        tonalElevation = 1.dp,
        color = MaterialTheme.colorScheme.surfaceContainerLow,
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Text(
                text = label,
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Text(text = value, style = MaterialTheme.typography.titleSmall)
        }
    }
}

@Composable
private fun LogRow(entry: LogEntry) {
    Surface(
        shape = RoundedCornerShape(18.dp),
        color = MaterialTheme.colorScheme.surfaceContainerLow,
    ) {
        Column(
            modifier = Modifier.padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                StatusChip(
                    when (entry.level) {
                        LogLevel.Info -> StatusChipModel("INFO", MaterialTheme.colorScheme.secondaryContainer, MaterialTheme.colorScheme.onSecondaryContainer)
                        LogLevel.Warning -> StatusChipModel("WARN", MaterialTheme.colorScheme.tertiaryContainer, MaterialTheme.colorScheme.onTertiaryContainer)
                        LogLevel.Error -> StatusChipModel("ERROR", MaterialTheme.colorScheme.errorContainer, MaterialTheme.colorScheme.onErrorContainer)
                    },
                )
                Text(entry.source, style = MaterialTheme.typography.labelMedium)
                Text(
                    entry.time,
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Text(entry.message, style = MaterialTheme.typography.bodySmall)
        }
    }
}

@Composable
private fun DiagnosticRow(item: DiagnosticItem) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(item.label, style = MaterialTheme.typography.titleSmall)
            Text(
                text = item.status,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        StatusChip(
            when (item.severity) {
                DiagnosticSeverity.Ok -> StatusChipModel("OK", MaterialTheme.colorScheme.secondaryContainer, MaterialTheme.colorScheme.onSecondaryContainer)
                DiagnosticSeverity.Warning -> StatusChipModel("WARN", MaterialTheme.colorScheme.tertiaryContainer, MaterialTheme.colorScheme.onTertiaryContainer)
                DiagnosticSeverity.Error -> StatusChipModel("ERROR", MaterialTheme.colorScheme.errorContainer, MaterialTheme.colorScheme.onErrorContainer)
            },
        )
    }
}

@Composable
private fun WarningBanner(message: String) {
    Surface(
        shape = RoundedCornerShape(18.dp),
        color = MaterialTheme.colorScheme.errorContainer,
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(
                imageVector = Icons.Outlined.ReportProblem,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onErrorContainer,
            )
            Text(
                text = message,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onErrorContainer,
            )
        }
    }
}

@Composable
private fun SectionCard(
    title: String,
    supporting: String? = null,
    content: @Composable ColumnScope.() -> Unit,
) {
    Card(
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface,
        ),
        shape = RoundedCornerShape(26.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier.padding(18.dp),
        ) {
            Text(text = title, style = MaterialTheme.typography.titleLarge)
            if (!supporting.isNullOrBlank()) {
                Spacer(Modifier.height(4.dp))
                Text(
                    text = supporting,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Spacer(Modifier.height(14.dp))
            content()
        }
    }
}

@Composable
private fun TitleBlock(
    eyebrow: String,
    title: String,
    subtitle: String,
) {
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text(
            text = eyebrow.uppercase(),
            style = MaterialTheme.typography.labelLarge,
            color = MaterialTheme.colorScheme.primary,
        )
        Text(
            text = title,
            style = MaterialTheme.typography.headlineSmall,
        )
        Text(
            text = subtitle,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
private fun CompactField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
    modifier: Modifier = Modifier,
    leadingIcon: @Composable (() -> Unit)? = null,
    keyboardType: KeyboardType = KeyboardType.Text,
    visualTransformation: androidx.compose.ui.text.input.VisualTransformation = androidx.compose.ui.text.input.VisualTransformation.None,
) {
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        modifier = modifier,
        label = { Text(label) },
        leadingIcon = leadingIcon,
        shape = RoundedCornerShape(18.dp),
        keyboardOptions = KeyboardOptions(keyboardType = keyboardType),
        visualTransformation = visualTransformation,
        singleLine = true,
    )
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun CompactActionRow(
    content: @Composable () -> Unit,
) {
    FlowRow(
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        content()
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun CompactStatusRow(
    items: List<StatusChipModel>,
) {
    FlowRow(
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        items.forEach { item ->
            StatusChip(item)
        }
    }
}

@Composable
private fun SmallActionButton(
    label: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    onClick: () -> Unit,
) {
    FilledTonalButton(
        onClick = onClick,
        contentPadding = PaddingValues(horizontal = 12.dp, vertical = 10.dp),
        colors = ButtonDefaults.filledTonalButtonColors(
            containerColor = MaterialTheme.colorScheme.secondaryContainer,
            contentColor = MaterialTheme.colorScheme.onSecondaryContainer,
        ),
    ) {
        Icon(icon, contentDescription = null, modifier = Modifier.size(18.dp))
        Spacer(Modifier.width(8.dp))
        Text(label)
    }
}

@Composable
private fun StatusChip(model: StatusChipModel) {
    Surface(
        shape = RoundedCornerShape(999.dp),
        color = model.containerColor,
    ) {
        Text(
            text = model.label,
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
            style = MaterialTheme.typography.labelMedium,
            color = model.contentColor,
        )
    }
}

private data class StatusChipModel(
    val label: String,
    val containerColor: Color,
    val contentColor: Color,
)

private data class DialogModel(
    val title: String,
    val body: String,
)

@Composable
private fun statusChip(label: String): StatusChipModel = StatusChipModel(
    label = label,
    containerColor = MaterialTheme.colorScheme.surfaceContainerHighest,
    contentColor = MaterialTheme.colorScheme.onSurfaceVariant,
)

@Composable
private fun connectionStatusChip(status: ConnectionStatus): StatusChipModel =
    when (status) {
        ConnectionStatus.Configured -> StatusChipModel(
            "configured",
            MaterialTheme.colorScheme.secondaryContainer,
            MaterialTheme.colorScheme.onSecondaryContainer,
        )

        ConnectionStatus.NeedsAuth -> StatusChipModel(
            "needs auth",
            MaterialTheme.colorScheme.tertiaryContainer,
            MaterialTheme.colorScheme.onTertiaryContainer,
        )

        ConnectionStatus.SetupRequired -> StatusChipModel(
            "setup required",
            MaterialTheme.colorScheme.primaryContainer,
            MaterialTheme.colorScheme.onPrimaryContainer,
        )

        ConnectionStatus.Offline -> StatusChipModel(
            "offline",
            MaterialTheme.colorScheme.errorContainer,
            MaterialTheme.colorScheme.onErrorContainer,
        )
    }

@Composable
private fun serviceStateChip(state: ServiceState): StatusChipModel =
    when (state) {
        ServiceState.Running -> StatusChipModel(
            "running",
            MaterialTheme.colorScheme.secondaryContainer,
            MaterialTheme.colorScheme.onSecondaryContainer,
        )

        ServiceState.Stopped -> StatusChipModel(
            "stopped",
            MaterialTheme.colorScheme.errorContainer,
            MaterialTheme.colorScheme.onErrorContainer,
        )

        ServiceState.Restarting -> StatusChipModel(
            "restarting",
            MaterialTheme.colorScheme.tertiaryContainer,
            MaterialTheme.colorScheme.onTertiaryContainer,
        )
    }

@Composable
private fun validationChip(state: RoutingValidationState): StatusChipModel =
    when (state) {
        RoutingValidationState.Idle -> statusChip("idle")
        RoutingValidationState.Dirty -> StatusChipModel(
            "dirty",
            MaterialTheme.colorScheme.tertiaryContainer,
            MaterialTheme.colorScheme.onTertiaryContainer,
        )

        RoutingValidationState.Valid -> StatusChipModel(
            "valid",
            MaterialTheme.colorScheme.secondaryContainer,
            MaterialTheme.colorScheme.onSecondaryContainer,
        )

        RoutingValidationState.Invalid -> StatusChipModel(
            "invalid",
            MaterialTheme.colorScheme.errorContainer,
            MaterialTheme.colorScheme.onErrorContainer,
        )
    }

private fun serviceStateLabel(state: ServiceState): String =
    when (state) {
        ServiceState.Running -> "Running"
        ServiceState.Stopped -> "Stopped"
        ServiceState.Restarting -> "Restarting"
    }

@Composable
private fun RowScope.BottomBarItem(
    tab: MainTab,
    selected: MainTab,
    onSelected: (MainTab) -> Unit,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    label: String,
) {
    NavigationBarItem(
        selected = tab == selected,
        onClick = { onSelected(tab) },
        icon = { Icon(icon, contentDescription = null) },
        label = { Text(label) },
    )
}

@Preview(showBackground = true)
@Composable
private fun ReadyPreview() {
    XkeenMobileTheme {
        ReadyRoute(
            state = CompanionUiState(phase = AppPhase.Ready),
            controller = DemoCompanionController(CompanionUiState(phase = AppPhase.Ready)),
        )
    }
}
