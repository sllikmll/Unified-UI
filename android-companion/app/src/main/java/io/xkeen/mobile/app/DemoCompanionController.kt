package io.xkeen.mobile.app

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import java.time.LocalTime
import java.time.format.DateTimeFormatter

class DemoCompanionController(
    initialState: CompanionUiState = CompanionUiState(),
) {
    var state by mutableStateOf(initialState)
        private set

    fun finishLaunch() {
        if (state.phase == AppPhase.Launching) {
            state = state.copy(phase = AppPhase.Connections)
        }
    }

    fun updateConnectionDraftName(value: String) {
        state = state.copy(connectionDraft = state.connectionDraft.copy(name = value))
    }

    fun updateConnectionDraftUrl(value: String) {
        state = state.copy(connectionDraft = state.connectionDraft.copy(baseUrl = value))
    }

    fun saveConnectionDraft() {
        val draft = state.connectionDraft
        if (draft.name.isBlank() || draft.baseUrl.isBlank()) {
            return
        }

        val newConnection = Connection(
            id = draft.name.lowercase().replace(" ", "-"),
            name = draft.name.trim(),
            baseUrl = draft.baseUrl.trim(),
            status = ConnectionStatus.SetupRequired,
            lastSeen = "New draft",
        )

        state = state.copy(
            connections = listOf(newConnection) + state.connections,
            connectionDraft = ConnectionDraft(),
        )
    }

    fun selectConnection(connectionId: String) {
        val selected = state.connections.firstOrNull { it.id == connectionId } ?: return
        state = state.copy(
            phase = AppPhase.PairLogin,
            selectedConnectionId = connectionId,
            loginForm = state.loginForm.copy(username = "admin", password = ""),
            dashboard = state.dashboard.copy(
                instanceLabel = selected.name,
                endpoint = selected.baseUrl,
                statusSummary = when (selected.status) {
                    ConnectionStatus.Configured -> "Ready for safe control"
                    ConnectionStatus.NeedsAuth -> "Authentication required"
                    ConnectionStatus.SetupRequired -> "Setup required"
                    ConnectionStatus.Offline -> "Offline"
                },
            ),
        )
    }

    fun backToConnections() {
        state = state.copy(
            phase = AppPhase.Connections,
            selectedConnectionId = null,
            pendingAction = null,
        )
    }

    fun updateUsername(value: String) {
        state = state.copy(loginForm = state.loginForm.copy(username = value))
    }

    fun updatePassword(value: String) {
        state = state.copy(loginForm = state.loginForm.copy(password = value))
    }

    fun pairDemoDevice() {
        completeSession("Pairing")
    }

    fun login() {
        completeSession("Login")
    }

    fun selectTab(tab: MainTab) {
        state = state.copy(mainTab = tab)
    }

    fun requestServiceAction(action: ServiceAction) {
        state = state.copy(pendingAction = PendingAction.Service(action))
    }

    fun requestRoutingApply() {
        val document = selectedRoutingDocument() ?: return
        when {
            state.routing.validation.state != RoutingValidationState.Valid -> validateRouting()
            document.hasUnsavedChanges -> {
                state = state.copy(
                    routing = state.routing.copy(
                        validation = RoutingValidation(
                            state = RoutingValidationState.Dirty,
                            message = "Save the draft before apply.",
                            details = listOf(
                                "Draft is different from the last saved preview.",
                                "Validate again after save if you change the content.",
                            ),
                        ),
                    ),
                )
            }

            else -> state = state.copy(pendingAction = PendingAction.ApplyRouting)
        }
    }

    fun dismissPendingAction() {
        state = state.copy(pendingAction = null)
    }

    fun confirmPendingAction() {
        when (val action = state.pendingAction) {
            is PendingAction.Service -> {
                performServiceAction(action.action)
                state = state.copy(pendingAction = null)
            }

            PendingAction.ApplyRouting -> {
                applyRouting()
                state = state.copy(pendingAction = null)
            }

            null -> Unit
        }
    }

    fun updateRoutingSearchQuery(query: String) {
        state = state.copy(routing = state.routing.copy(searchQuery = query))
    }

    fun selectRoutingDocument(documentId: String) {
        if (state.routing.selectedDocumentId == documentId) {
            return
        }

        state = state.copy(
            routing = state.routing.copy(
                selectedDocumentId = documentId,
                mode = RoutingMode.Read,
                validation = RoutingValidation(),
                preview = null,
            ),
        )
    }

    fun enterRoutingEditMode() {
        state = state.copy(routing = state.routing.copy(mode = RoutingMode.Edit))
    }

    fun updateRoutingDraft(value: String) {
        val document = selectedRoutingDocument() ?: return
        val updatedDocument = document.copy(draftContent = value)
        state = state.copy(
            routing = state.routing.copy(
                documents = state.routing.documents.replaceDocument(updatedDocument),
                mode = RoutingMode.Edit,
                validation = RoutingValidation(
                    state = RoutingValidationState.Dirty,
                    message = "Draft changed. Validate before preview or apply.",
                ),
                preview = null,
            ),
        )
    }

    fun revertRoutingDraft() {
        val document = selectedRoutingDocument() ?: return
        val reverted = document.copy(
            draftContent = document.publishedContent,
            savedDraftContent = document.publishedContent,
        )
        state = state.copy(
            routing = state.routing.copy(
                documents = state.routing.documents.replaceDocument(reverted),
                mode = RoutingMode.Read,
                validation = RoutingValidation(
                    message = "Draft reverted to published revision.",
                ),
                preview = null,
            ),
        )
    }

    fun validateRouting() {
        val document = selectedRoutingDocument() ?: return
        state = state.copy(
            routing = state.routing.copy(
                validation = validateRoutingDraft(document.draftContent),
            ),
        )
    }

    fun previewRouting() {
        val document = selectedRoutingDocument() ?: return
        val validation = validateRoutingDraft(document.draftContent)
        state = state.copy(routing = state.routing.copy(validation = validation))
        if (validation.state != RoutingValidationState.Valid) {
            return
        }

        state = state.copy(
            routing = state.routing.copy(
                preview = buildRoutingPreview(document),
            ),
        )
    }

    fun saveRouting() {
        val document = selectedRoutingDocument() ?: return
        val savedAt = nowShort()
        val updated = document.copy(
            savedDraftContent = document.draftContent,
            lastSavedAt = savedAt,
        )
        state = state.copy(
            routing = state.routing.copy(
                documents = state.routing.documents.replaceDocument(updated),
                validation = RoutingValidation(
                    state = RoutingValidationState.Valid,
                    message = "Draft saved. Preview or apply when ready.",
                    details = listOf(
                        "Saved at $savedAt",
                        "Published revision is unchanged until apply.",
                    ),
                ),
            ),
            dashboard = state.dashboard.copy(lastOperation = "Routing draft saved at $savedAt"),
            logs = state.logs.prepend(
                LogEntry(nowLong(), "routing", LogLevel.Info, "draft saved for ${document.title}"),
            ),
        )
    }

    fun updateLogFilter(filter: LogFilter) {
        state = state.copy(logs = state.logs.copy(filter = filter))
    }

    fun disconnect() {
        val connectionId = state.selectedConnectionId ?: return
        val updatedConnections = state.connections.map { connection ->
            if (connection.id == connectionId) {
                connection.copy(status = ConnectionStatus.NeedsAuth, lastSeen = "Session closed")
            } else {
                connection
            }
        }

        state = state.copy(
            phase = AppPhase.Connections,
            selectedConnectionId = null,
            connections = updatedConnections,
            mainTab = MainTab.Home,
            dashboard = state.dashboard.copy(statusSummary = "Authentication required"),
            logs = state.logs.prepend(
                LogEntry(nowLong(), "auth", LogLevel.Warning, "mobile session closed by user"),
            ),
        )
    }

    private fun completeSession(mode: String) {
        val connectionId = state.selectedConnectionId ?: return
        val updatedConnections = state.connections.map { connection ->
            if (connection.id == connectionId) {
                connection.copy(status = ConnectionStatus.Configured, lastSeen = "Ready now")
            } else {
                connection
            }
        }
        val selected = updatedConnections.first { it.id == connectionId }
        val eventTime = nowShort()
        val authLog = LogEntry(
            time = nowLong(),
            source = "auth",
            level = LogLevel.Info,
            message = "${mode.lowercase()} session opened for ${selected.name}",
        )

        state = state.copy(
            phase = AppPhase.Ready,
            connections = updatedConnections,
            dashboard = state.dashboard.copy(
                instanceLabel = selected.name,
                endpoint = selected.baseUrl,
                statusSummary = "Ready for safe control",
                lastOperation = "$mode session opened",
                recentEvents = listOf(
                    RecentEvent(eventTime, "$mode complete", "Session opened without browser fallback"),
                ) + state.dashboard.recentEvents.take(2),
            ),
            diagnostics = state.diagnostics.replaceDiagnostic(
                label = "Mobile session",
                status = "Ready",
                severity = DiagnosticSeverity.Ok,
            ),
            logs = state.logs.prepend(authLog),
        )
    }

    private fun performServiceAction(action: ServiceAction) {
        val actionTime = nowShort()
        val serviceState = when (action) {
            ServiceAction.Start -> ServiceState.Running
            ServiceAction.Stop -> ServiceState.Stopped
            ServiceAction.Restart -> ServiceState.Restarting
        }
        val finalState = if (action == ServiceAction.Restart) ServiceState.Running else serviceState
        val summary = when (action) {
            ServiceAction.Start -> "Service start requested"
            ServiceAction.Stop -> "Service stopped safely"
            ServiceAction.Restart -> "Runtime recycled successfully"
        }

        state = state.copy(
            dashboard = state.dashboard.copy(
                serviceState = finalState,
                statusSummary = if (finalState == ServiceState.Running) {
                    "Ready for safe control"
                } else {
                    "Service stopped"
                },
                lastOperation = summary,
                recentEvents = listOf(
                    RecentEvent(actionTime, action.label, summary),
                ) + state.dashboard.recentEvents.take(2),
            ),
            logs = state.logs.prepend(
                LogEntry(nowLong(), "service", LogLevel.Info, "${action.label.lowercase()} action confirmed"),
            ),
        )
    }

    private fun applyRouting() {
        val document = selectedRoutingDocument() ?: return
        val appliedAt = nowShort()
        val updated = document.copy(
            revision = document.revision + 1,
            publishedContent = document.savedDraftContent,
            draftContent = document.savedDraftContent,
            lastAppliedAt = appliedAt,
        )
        state = state.copy(
            routing = state.routing.copy(
                documents = state.routing.documents.replaceDocument(updated),
                mode = RoutingMode.Read,
                validation = RoutingValidation(
                    state = RoutingValidationState.Valid,
                    message = "Apply complete. Published revision is now live.",
                    details = listOf(
                        "Revision r${updated.revision} published at $appliedAt",
                        "No conflict detected in demo shell.",
                    ),
                ),
                preview = buildRoutingPreview(updated).copy(
                    headline = "Applied to ${updated.title}",
                ),
            ),
            dashboard = state.dashboard.copy(
                lastOperation = "Routing applied at $appliedAt",
                recentEvents = listOf(
                    RecentEvent(appliedAt, "Routing apply", "${updated.title} moved to revision r${updated.revision}"),
                ) + state.dashboard.recentEvents.take(2),
            ),
            logs = state.logs.prepend(
                LogEntry(nowLong(), "routing", LogLevel.Info, "applied revision r${updated.revision} for ${updated.title}"),
            ),
        )
    }

    private fun selectedRoutingDocument(): RoutingDocument? =
        state.routing.documents.firstOrNull { it.id == state.routing.selectedDocumentId }

    private fun nowShort(): String =
        LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm"))

    private fun nowLong(): String =
        LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss"))
}

fun validateRoutingDraft(draft: String): RoutingValidation {
    val details = mutableListOf<String>()

    if (!draft.contains("\"routing\"")) {
        details += "Missing top-level routing object."
    }
    if (!draft.contains("\"rules\"")) {
        details += "No rules block found."
    }
    if (draft.count { it == '{' } != draft.count { it == '}' }) {
        details += "Brace count does not match."
    }
    if (draft.contains("TODO_INVALID")) {
        details += "Draft still contains TODO_INVALID marker."
    }

    return if (details.isEmpty()) {
        RoutingValidation(
            state = RoutingValidationState.Valid,
            message = "Validation passed. Safe to preview and save.",
            details = listOf(
                "routing object found",
                "rules block detected",
                "basic JSON shape looks consistent",
            ),
        )
    } else {
        RoutingValidation(
            state = RoutingValidationState.Invalid,
            message = "Fix ${details.size} issue(s) before apply.",
            details = details,
        )
    }
}

private fun buildRoutingPreview(document: RoutingDocument): RoutingPreview {
    val outboundMentions = Regex("\"outboundTag\"").findAll(document.draftContent).count()
    val ruleMentions = Regex("\"type\"\\s*:\\s*\"field\"").findAll(document.draftContent).count()

    return RoutingPreview(
        headline = "Preview ready for ${document.title}",
        details = listOf(
            "rule blocks touched: $ruleMentions",
            "outbound tags referenced: $outboundMentions",
            "published revision: r${document.revision}",
            "saved preview is ready for apply",
        ),
    )
}

private fun List<RoutingDocument>.replaceDocument(updated: RoutingDocument): List<RoutingDocument> =
    map { document -> if (document.id == updated.id) updated else document }

private fun LogsState.prepend(entry: LogEntry): LogsState =
    copy(entries = listOf(entry) + entries.take(19))

private fun List<DiagnosticItem>.replaceDiagnostic(
    label: String,
    status: String,
    severity: DiagnosticSeverity,
): List<DiagnosticItem> = map { item ->
    if (item.label == label) {
        item.copy(status = status, severity = severity)
    } else {
        item
    }
}
