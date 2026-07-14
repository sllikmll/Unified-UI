package io.xkeen.mobile.app

import androidx.compose.foundation.ScrollState
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.selection.LocalTextSelectionColors
import androidx.compose.foundation.text.selection.TextSelectionColors
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.FactCheck
import androidx.compose.material.icons.outlined.DoneAll
import androidx.compose.material.icons.outlined.Edit
import androidx.compose.material.icons.outlined.Save
import androidx.compose.material.icons.outlined.SettingsBackupRestore
import androidx.compose.material3.Icon
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.input.pointer.PointerEventPass
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.OffsetMapping
import androidx.compose.ui.text.input.TransformedText
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import io.xkeen.mobile.ui.theme.WebPanelPalette
import kotlin.math.abs
import kotlinx.coroutines.launch

@Composable
internal fun RoutingWorkspaceScreen(
    state: CompanionUiState,
    controller: CompanionController,
    modifier: Modifier = Modifier,
) {
    val routing = state.routing
    val selectedDocument = routing.documents.firstOrNull {
        it.id == routing.selectedDocumentId
    } ?: return
    val selectedIndex = routing.documents.indexOfFirst { it.id == selectedDocument.id }
        .coerceAtLeast(0)
    val pagerState = rememberPagerState(
        initialPage = selectedIndex,
        pageCount = { routing.documents.size },
    )
    val scope = rememberCoroutineScope()
    val currentRouting = rememberUpdatedState(routing)
    val currentSelectedIndex = rememberUpdatedState(selectedIndex)
    // Keep the gesture handler stable while first-load updates replace document models.
    val onLongSwipe = remember(controller) {
        swipe@{ pageDelta: Int ->
            val targetIndex = currentSelectedIndex.value + pageDelta
            val targetDocument = currentRouting.value.documents.getOrNull(targetIndex)
                ?: return@swipe
            controller.selectRoutingDocument(targetDocument.id)
        }
    }

    LaunchedEffect(state.dashboard.endpoint) {
        controller.refreshRoutingDocuments()
    }
    LaunchedEffect(routing.selectedDocumentId) {
        controller.loadSelectedRoutingDocument()
    }
    LaunchedEffect(selectedIndex, routing.documents.map { it.id }) {
        // Selection is the single pager target; competing scroll jobs can bounce between pages.
        if (
            pagerState.currentPage != selectedIndex ||
            pagerState.currentPageOffsetFraction != 0f
        ) {
            pagerState.animateScrollToPage(selectedIndex)
        }
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(WebPanelPalette.Background)
            .imePadding(),
    ) {
        DocumentToolbar(
            document = selectedDocument,
            documents = routing.documents,
            onSelectDocument = controller::selectRoutingDocument,
            onEdit = controller::enterRoutingEditMode,
            onValidate = controller::validateRouting,
            onRevert = controller::revertRoutingDraft,
            onSave = controller::saveRouting,
            onApply = controller::requestRoutingApply,
        )
        Box(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .longHorizontalSwipe(onSwipe = onLongSwipe),
        ) {
            HorizontalPager(
                state = pagerState,
                modifier = Modifier.fillMaxSize(),
                userScrollEnabled = false,
                key = { page -> routing.documents[page].id },
            ) { page ->
                val document = routing.documents[page]
                RoutingDocumentPage(
                    document = document,
                    onValueChange = { value -> controller.updateRoutingDraft(document.id, value) },
                    onRetry = {
                        if (document.id == routing.selectedDocumentId) {
                            scope.launch { controller.loadSelectedRoutingDocument() }
                        }
                    },
                )
            }
        }
        EditorStatusBar(
            document = selectedDocument,
            validation = routing.validation,
        )
    }
}

@Composable
private fun RoutingDocumentPage(
    document: RoutingDocument,
    onValueChange: (String) -> Unit,
    onRetry: () -> Unit,
) {
    when {
        document.isLoading -> DocumentLoadMessage(
            title = "Загружаем ${document.title}",
            message = "Получаем JSON/JSONC с Xkeen UI…",
            showProgress = true,
        )

        !document.isLoaded -> DocumentLoadMessage(
            title = document.title,
            message = document.loadError ?: "Сделайте длинный свайп ещё раз или повторите загрузку.",
            actionLabel = "Повторить",
            onAction = onRetry,
        )

        else -> JsonEditor(
            value = document.draftContent,
            onValueChange = onValueChange,
            modifier = Modifier.fillMaxSize(),
        )
    }
}

@Composable
private fun DocumentLoadMessage(
    title: String,
    message: String,
    showProgress: Boolean = false,
    actionLabel: String? = null,
    onAction: () -> Unit = {},
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(WebPanelPalette.Background)
            .padding(28.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        if (showProgress) {
            CircularProgressIndicator(
                modifier = Modifier.size(28.dp),
                color = WebPanelPalette.Border,
                strokeWidth = 2.dp,
            )
            Spacer(Modifier.height(14.dp))
        }
        Text(
            text = title,
            color = WebPanelPalette.TextStrong,
            style = MaterialTheme.typography.titleMedium,
            textAlign = TextAlign.Center,
        )
        Spacer(Modifier.height(6.dp))
        Text(
            text = message,
            color = WebPanelPalette.Muted,
            style = MaterialTheme.typography.bodyMedium,
            textAlign = TextAlign.Center,
        )
        if (actionLabel != null) {
            Spacer(Modifier.height(14.dp))
            Text(
                text = actionLabel,
                modifier = Modifier
                    .background(WebPanelPalette.SurfaceRaised, RoundedCornerShape(12.dp))
                    .border(1.dp, WebPanelPalette.Border.copy(alpha = 0.32f), RoundedCornerShape(12.dp))
                    .clickable(onClick = onAction)
                    .padding(horizontal = 16.dp, vertical = 9.dp),
                color = WebPanelPalette.TextBlue,
                fontWeight = FontWeight.Bold,
            )
        }
    }
}

private fun Modifier.longHorizontalSwipe(onSwipe: (pageDelta: Int) -> Unit): Modifier =
    pointerInput(onSwipe) {
        awaitEachGesture {
            val down = awaitFirstDown(requireUnconsumed = false)
            var lastPosition = down.position
            var pointerIsDown = true
            while (pointerIsDown) {
                val event = awaitPointerEvent(PointerEventPass.Final)
                val tracked = event.changes.firstOrNull { it.id == down.id }
                if (tracked != null) {
                    lastPosition = tracked.position
                    pointerIsDown = tracked.pressed
                } else {
                    pointerIsDown = event.changes.any { it.pressed }
                }
            }

            val delta = lastPosition - down.position
            val horizontalDistance = abs(delta.x)
            val isLongSwipe = horizontalDistance >= size.width * 0.38f
            val isClearlyHorizontal = horizontalDistance > abs(delta.y) * 1.35f
            if (isLongSwipe && isClearlyHorizontal) {
                onSwipe(if (delta.x < 0f) 1 else -1)
            }
        }
    }

@Composable
private fun DocumentToolbar(
    document: RoutingDocument,
    documents: List<RoutingDocument>,
    onSelectDocument: (String) -> Unit,
    onEdit: () -> Unit,
    onValidate: () -> Unit,
    onRevert: () -> Unit,
    onSave: () -> Unit,
    onApply: () -> Unit,
) {
    val currentIndex = documents.indexOfFirst { it.id == document.id }.coerceAtLeast(0)
    val nextDocument = documents.getOrNull((currentIndex + 1) % documents.size)

    Surface(color = Color.Transparent, shadowElevation = 5.dp) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .height(48.dp)
                .background(
                    Brush.verticalGradient(
                        listOf(WebPanelPalette.Surface, WebPanelPalette.BackgroundDeep),
                    ),
                )
                .padding(horizontal = 6.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Row(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxHeight()
                    .clickable { nextDocument?.let { onSelectDocument(it.id) } }
                    .padding(start = 9.dp, end = 5.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = document.title,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Medium,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                if (documents.size > 1) {
                    Text(
                        text = "  ${currentIndex + 1}/${documents.size}  ↔",
                        style = MaterialTheme.typography.labelMedium,
                        color = WebPanelPalette.Muted,
                    )
                }
            }
            EditorToolbarButton(Icons.Outlined.Edit, "Редактировать", onEdit)
            EditorToolbarButton(Icons.AutoMirrored.Outlined.FactCheck, "Проверить", onValidate)
            EditorToolbarButton(Icons.Outlined.SettingsBackupRestore, "Откатить", onRevert)
            EditorToolbarButton(
                icon = Icons.Outlined.Save,
                description = "Сохранить",
                onClick = onSave,
                accent = document.hasUnsavedChanges,
            )
            EditorToolbarButton(
                icon = Icons.Outlined.DoneAll,
                description = "Применить",
                onClick = onApply,
                accent = document.hasDraftChanges,
            )
        }
    }
}

@Composable
private fun EditorToolbarButton(
    icon: ImageVector,
    description: String,
    onClick: () -> Unit,
    accent: Boolean = false,
) {
    val shape = RoundedCornerShape(10.dp)
    val accentColor = WebPanelPalette.Border
    Box(
        modifier = Modifier
            .size(34.dp)
            .padding(2.dp)
            .shadow(if (accent) 4.dp else 2.dp, shape)
            .background(
                brush = Brush.verticalGradient(
                    if (accent) {
                        listOf(Color(0xFF102C5E), Color(0xFF081436))
                    } else {
                        listOf(WebPanelPalette.SurfaceRaised, WebPanelPalette.Surface)
                    },
                ),
                shape = shape,
            )
            .border(
                width = 1.dp,
                brush = Brush.linearGradient(
                    if (accent) {
                        listOf(
                            Color.White.copy(alpha = 0.12f),
                            WebPanelPalette.Border.copy(alpha = 0.56f),
                            WebPanelPalette.Border.copy(alpha = 0.20f),
                        )
                    } else {
                        listOf(
                            Color.White.copy(alpha = 0.08f),
                            WebPanelPalette.Border.copy(alpha = 0.20f),
                        )
                    },
                ),
                shape = shape,
            )
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        Icon(
            imageVector = icon,
            contentDescription = description,
            tint = if (accent) accentColor else WebPanelPalette.TextBlue,
            modifier = Modifier.size(19.dp),
        )
    }
}

@Composable
private fun JsonEditor(
    value: String,
    onValueChange: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val lineCount = value.count { it == '\n' } + 1
    val verticalScrollState = rememberScrollState()

    Row(
        modifier = modifier
            .fillMaxWidth()
            .background(JsonEditorPalette.Background)
            .editorVerticalScroll(verticalScrollState)
            .verticalScroll(verticalScrollState)
            .padding(top = 8.dp, bottom = 24.dp),
        verticalAlignment = Alignment.Top,
    ) {
        Text(
            text = (1..lineCount).joinToString("\n"),
            modifier = Modifier
                .width(45.dp)
                .padding(end = 7.dp),
            color = JsonEditorPalette.LineNumber,
            fontFamily = FontFamily.Monospace,
            fontSize = 15.sp,
            lineHeight = 23.sp,
            textAlign = TextAlign.End,
        )
        Box(
            modifier = Modifier
                .width(1.dp)
                .heightIn(min = 640.dp)
                .background(JsonEditorPalette.IndentGuide),
        )
        Box(
            modifier = Modifier
                .weight(1f)
                .horizontalScroll(rememberScrollState()),
        ) {
            CompositionLocalProvider(
                LocalTextSelectionColors provides JsonEditorPalette.Selection,
            ) {
                BasicTextField(
                    value = value,
                    onValueChange = onValueChange,
                    modifier = Modifier
                        .widthIn(min = 600.dp)
                        .heightIn(min = 640.dp)
                        .padding(start = 10.dp, end = 12.dp),
                    textStyle = MaterialTheme.typography.bodyMedium.copy(
                        color = JsonEditorPalette.Foreground,
                        fontFamily = FontFamily.Monospace,
                        fontSize = 15.sp,
                        lineHeight = 23.sp,
                    ),
                    cursorBrush = SolidColor(JsonEditorPalette.Cursor),
                    visualTransformation = JsonVisualTransformation,
                )
            }
        }
    }
}

private fun Modifier.editorVerticalScroll(scrollState: ScrollState): Modifier =
    pointerInput(scrollState) {
        awaitEachGesture {
            val down = awaitFirstDown(
                requireUnconsumed = false,
                pass = PointerEventPass.Initial,
            )
            var lastPosition = down.position
            var accumulatedX = 0f
            var accumulatedY = 0f
            var isVerticalScroll = false

            while (true) {
                val event = awaitPointerEvent(PointerEventPass.Initial)
                val change = event.changes.firstOrNull { it.id == down.id } ?: break
                val delta = change.position - lastPosition
                lastPosition = change.position

                if (isVerticalScroll) {
                    change.consume()
                    scrollState.dispatchRawDelta(-delta.y)
                } else {
                    accumulatedX += delta.x
                    accumulatedY += delta.y
                    val verticalDistance = abs(accumulatedY)
                    val horizontalDistance = abs(accumulatedX)

                    if (
                        verticalDistance > viewConfiguration.touchSlop &&
                        verticalDistance > horizontalDistance * 1.15f
                    ) {
                        isVerticalScroll = true
                        change.consume()
                        scrollState.dispatchRawDelta(-accumulatedY)
                    } else if (
                        horizontalDistance > viewConfiguration.touchSlop &&
                        horizontalDistance > verticalDistance
                    ) {
                        break
                    }
                }

                if (!change.pressed) break
            }
        }
    }

private object JsonEditorPalette {
    // Mirrors the xkeen-dark Monaco theme from web ui/monaco_shared.js.
    val Background = Color(0xFF01030A)
    val Foreground = Color(0xFFD4D4D4)
    val LineNumber = Color(0xFF64748B)
    val Cursor = Color(0xFF60A5FA)
    val IndentGuide = Color(0xFF172033)
    val Comment = Color(0xFF6A9955)
    val Keyword = Color(0xFF569CD6)
    val String = Color(0xFFCE9178)
    val Number = Color(0xFFB5CEA8)
    val Property = Color(0xFF9CDCFE)
    val Punctuation = Color(0xFFD4D4D4)
    val BracketDepth = listOf(
        Color(0xFFFFD700),
        Color(0xFFC586C0),
        Color(0xFF4FC1FF),
    )
    val Selection = TextSelectionColors(
        handleColor = Cursor,
        backgroundColor = Color(0x501D4ED8),
    )
}

private object JsonVisualTransformation : VisualTransformation {
    override fun filter(text: AnnotatedString): TransformedText {
        return TransformedText(highlightJsonc(text.text), OffsetMapping.Identity)
    }
}

internal fun highlightJsonc(source: String): AnnotatedString = buildAnnotatedString {
    append(source)
    var index = 0
    var bracketDepth = 0

    while (index < source.length) {
        val keyword = source.jsonKeywordAt(index)
        when {
            source.startsWith("//", index) -> {
                val end = source.indexOf('\n', index).takeIf { it >= 0 } ?: source.length
                addJsonStyle(JsonEditorPalette.Comment, index, end)
                index = end
            }

            source.startsWith("/*", index) -> {
                val closing = source.indexOf("*/", index + 2)
                val end = if (closing >= 0) closing + 2 else source.length
                addJsonStyle(JsonEditorPalette.Comment, index, end)
                index = end
            }

            source[index] == '"' -> {
                val end = source.jsonStringEnd(index)
                val nextToken = source.indexOfFirstNonWhitespace(end)
                val color = if (nextToken < source.length && source[nextToken] == ':') {
                    JsonEditorPalette.Property
                } else {
                    JsonEditorPalette.String
                }
                addJsonStyle(color, index, end)
                index = end
            }

            source[index] == '-' || source[index].isDigit() -> {
                val end = source.jsonNumberEnd(index)
                val startsNumber = source[index].isDigit() ||
                    (index + 1 < source.length && source[index] == '-' && source[index + 1].isDigit())
                if (startsNumber) {
                    addJsonStyle(JsonEditorPalette.Number, index, end)
                    index = end
                } else {
                    index += 1
                }
            }

            keyword != null -> {
                addJsonStyle(JsonEditorPalette.Keyword, index, index + keyword.length)
                index += keyword.length
            }

            source[index] == '{' || source[index] == '[' -> {
                val color = JsonEditorPalette.BracketDepth[bracketDepth % JsonEditorPalette.BracketDepth.size]
                addJsonStyle(color, index, index + 1)
                bracketDepth += 1
                index += 1
            }

            source[index] == '}' || source[index] == ']' -> {
                bracketDepth = (bracketDepth - 1).coerceAtLeast(0)
                val color = JsonEditorPalette.BracketDepth[bracketDepth % JsonEditorPalette.BracketDepth.size]
                addJsonStyle(color, index, index + 1)
                index += 1
            }

            source[index] == ':' || source[index] == ',' -> {
                addJsonStyle(JsonEditorPalette.Punctuation, index, index + 1)
                index += 1
            }

            else -> index += 1
        }
    }
}

private fun AnnotatedString.Builder.addJsonStyle(color: Color, start: Int, end: Int) {
    addStyle(SpanStyle(color = color), start, end)
}

private fun String.jsonStringEnd(start: Int): Int {
    var index = start + 1
    var escaped = false
    while (index < length) {
        val char = this[index]
        if (!escaped && char == '"') return index + 1
        escaped = !escaped && char == '\\'
        if (char != '\\') escaped = false
        index += 1
    }
    return length
}

private fun String.indexOfFirstNonWhitespace(start: Int): Int {
    var index = start
    while (index < length && this[index].isWhitespace()) index += 1
    return index
}

private fun String.jsonNumberEnd(start: Int): Int {
    var index = start
    if (index < length && this[index] == '-') index += 1
    while (index < length && this[index].isDigit()) index += 1
    if (index < length && this[index] == '.') {
        index += 1
        while (index < length && this[index].isDigit()) index += 1
    }
    if (index < length && (this[index] == 'e' || this[index] == 'E')) {
        index += 1
        if (index < length && (this[index] == '+' || this[index] == '-')) index += 1
        while (index < length && this[index].isDigit()) index += 1
    }
    return index
}

private val JsonKeywords = listOf("true", "false", "null")

private fun String.jsonKeywordAt(index: Int): String? =
    JsonKeywords.firstOrNull { keyword ->
        startsWith(keyword, index) &&
            (index == 0 || !this[index - 1].isLetterOrDigit()) &&
            (index + keyword.length == length || !this[index + keyword.length].isLetterOrDigit())
    }

@Composable
private fun EditorStatusBar(
    document: RoutingDocument,
    validation: RoutingValidation,
) {
    val statusText = when {
        document.isLoading -> "Загрузка с Xkeen UI…"
        document.loadError != null -> document.loadError
        validation.state == RoutingValidationState.Invalid -> validation.message
        validation.state == RoutingValidationState.Valid -> validation.message
        document.hasUnsavedChanges -> "Изменения не сохранены"
        document.hasDraftChanges -> "Черновик сохранён"
        document.modifiedAtEpochSeconds != null -> if (document.usesJsonc) {
            "server · JSONC"
        } else {
            "server · JSON"
        }
        else -> "r${document.revision} · опубликовано"
    }
    val statusColor = when (validation.state) {
        RoutingValidationState.Invalid -> WebPanelPalette.Error
        RoutingValidationState.Valid -> WebPanelPalette.Success
        RoutingValidationState.Dirty -> WebPanelPalette.Warning
        RoutingValidationState.Idle -> WebPanelPalette.Muted
    }

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .height(28.dp)
            .background(
                Brush.horizontalGradient(
                    listOf(
                        WebPanelPalette.Surface,
                        Color(0xFF081436),
                        WebPanelPalette.Surface,
                    ),
                ),
            )
            .border(1.dp, WebPanelPalette.Border.copy(alpha = 0.16f))
            .padding(horizontal = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(
            modifier = Modifier
                .size(7.dp)
                .background(statusColor, CircleShape),
        )
        Spacer(Modifier.width(6.dp))
        Text(
            text = statusText,
            modifier = Modifier.weight(1f),
            style = MaterialTheme.typography.labelMedium,
            color = WebPanelPalette.Text,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )
        Text(
            text = "Ln ${document.draftContent.lines().size}",
            style = MaterialTheme.typography.labelMedium,
            color = WebPanelPalette.Muted,
        )
    }
}

@Composable
internal fun ModulePlaceholderScreen(
    title: String,
    subtitle: String,
    modifier: Modifier = Modifier,
) {
    Box(
        modifier = modifier
            .fillMaxSize()
            .background(WebPanelPalette.Background)
            .padding(28.dp),
        contentAlignment = Alignment.Center,
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(text = title, style = MaterialTheme.typography.headlineSmall)
            Text(
                text = subtitle,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center,
            )
        }
    }
}

@Composable
internal fun ShellWorkspaceScreen(
    state: CompanionUiState,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(WebPanelPalette.Background)
            .padding(14.dp)
            .verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(7.dp),
    ) {
        Text(
            text = "xkeen@${state.dashboard.instanceLabel.lowercase().replace(' ', '-')}:~$",
            color = WebPanelPalette.Success,
            fontFamily = FontFamily.Monospace,
            fontSize = 13.sp,
        )
        state.logs.entries.forEach { entry ->
            Text(
                text = "${entry.time}  [${entry.source}]  ${entry.message}",
                color = if (entry.level == LogLevel.Error) WebPanelPalette.Error else WebPanelPalette.Text,
                fontFamily = FontFamily.Monospace,
                fontSize = 12.sp,
                lineHeight = 17.sp,
            )
        }
    }
}
