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
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.MutableState
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.input.pointer.PointerEventPass
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.platform.LocalTextToolbar
import androidx.compose.ui.platform.TextToolbar
import androidx.compose.ui.platform.TextToolbarStatus
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextRange
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.OffsetMapping
import androidx.compose.ui.text.input.TransformedText
import androidx.compose.ui.text.input.TextFieldValue
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.IntRect
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Popup
import androidx.compose.ui.window.PopupPositionProvider
import androidx.compose.ui.window.PopupProperties
import io.xkeen.mobile.ui.theme.WebPanelPalette
import kotlin.math.abs
import kotlin.math.roundToInt
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
    val scope = rememberCoroutineScope()
    val focusManager = LocalFocusManager.current
    val showDocumentPicker = rememberSaveable { mutableStateOf(false) }

    LaunchedEffect(state.dashboard.endpoint) {
        controller.refreshRoutingDocuments()
    }
    LaunchedEffect(routing.selectedDocumentId) {
        controller.loadSelectedRoutingDocument()
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
            onOpenDocumentPicker = {
                focusManager.clearFocus(force = true)
                showDocumentPicker.value = true
            },
            onEdit = controller::enterRoutingEditMode,
            onValidate = controller::validateRouting,
            onRevert = controller::revertRoutingDraft,
            onSave = controller::saveRouting,
            onApply = controller::requestRoutingApply,
        )
        Box(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth(),
        ) {
            key(selectedDocument.id) {
                RoutingDocumentPage(
                    document = selectedDocument,
                    onValueChange = { value ->
                        controller.updateRoutingDraft(selectedDocument.id, value)
                    },
                    onRetry = {
                        scope.launch { controller.loadSelectedRoutingDocument() }
                    },
                )
            }
        }
        EditorStatusBar(
            document = selectedDocument,
            validation = routing.validation,
        )
    }

    if (showDocumentPicker.value) {
        RoutingDocumentPickerDialog(
            documents = routing.documents,
            selectedDocumentId = selectedDocument.id,
            onDismiss = { showDocumentPicker.value = false },
            onSelectDocument = { documentId ->
                controller.selectRoutingDocument(documentId)
                showDocumentPicker.value = false
            },
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

@Composable
private fun DocumentToolbar(
    document: RoutingDocument,
    documents: List<RoutingDocument>,
    onOpenDocumentPicker: () -> Unit,
    onEdit: () -> Unit,
    onValidate: () -> Unit,
    onRevert: () -> Unit,
    onSave: () -> Unit,
    onApply: () -> Unit,
) {
    val currentIndex = documents.indexOfFirst { it.id == document.id }.coerceAtLeast(0)

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
                    .clickable(onClick = onOpenDocumentPicker)
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
                Text(
                    text = "  ${currentIndex + 1}/${documents.size}  ▾",
                    style = MaterialTheme.typography.labelMedium,
                    color = WebPanelPalette.Muted,
                )
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
private fun RoutingDocumentPickerDialog(
    documents: List<RoutingDocument>,
    selectedDocumentId: String,
    onDismiss: () -> Unit,
    onSelectDocument: (String) -> Unit,
) {
    XkeenDialog(onDismissRequest = onDismiss) {
        Column(
            modifier = Modifier.padding(18.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(
                text = "РОУТИНГ XRAY",
                color = WebPanelPalette.Border,
                style = MaterialTheme.typography.labelSmall,
                fontWeight = FontWeight.Bold,
                letterSpacing = 0.7.sp,
            )
            Text(
                text = "Выберите файл",
                color = WebPanelPalette.TextStrong,
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
            )
            Text(
                text = "Доступно файлов: ${documents.size}",
                color = WebPanelPalette.Muted,
                style = MaterialTheme.typography.bodySmall,
            )
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(max = 380.dp)
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                documents.forEachIndexed { index, item ->
                    val selected = item.id == selectedDocumentId
                    val shape = RoundedCornerShape(12.dp)
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(
                                color = if (selected) {
                                    WebPanelPalette.Accent
                                } else {
                                    WebPanelPalette.Surface
                                },
                                shape = shape,
                            )
                            .border(
                                width = 1.dp,
                                color = if (selected) {
                                    WebPanelPalette.Border.copy(alpha = 0.72f)
                                } else {
                                    WebPanelPalette.AccentMiddle.copy(alpha = 0.28f)
                                },
                                shape = shape,
                            )
                            .clickable { onSelectDocument(item.id) }
                            .padding(horizontal = 13.dp, vertical = 11.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(11.dp),
                    ) {
                        Text(
                            text = (index + 1).toString().padStart(2, '0'),
                            color = if (selected) {
                                WebPanelPalette.TextStrong
                            } else {
                                WebPanelPalette.Muted
                            },
                            style = MaterialTheme.typography.labelMedium,
                            fontFamily = FontFamily.Monospace,
                        )
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = item.title,
                                color = WebPanelPalette.TextStrong,
                                style = MaterialTheme.typography.bodyMedium,
                                fontWeight = FontWeight.Bold,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                            )
                            Text(
                                text = item.path,
                                color = if (selected) {
                                    WebPanelPalette.TextBlue
                                } else {
                                    WebPanelPalette.Muted
                                },
                                style = MaterialTheme.typography.labelSmall,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                            )
                        }
                        if (selected) {
                            Text(
                                text = "ОТКРЫТ",
                                color = WebPanelPalette.TextStrong,
                                style = MaterialTheme.typography.labelSmall,
                                fontWeight = FontWeight.Bold,
                            )
                        }
                    }
                }
            }
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                OutlinedButton(onClick = onDismiss) {
                    Text("Закрыть")
                }
            }
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
    val editorValue = remember { mutableStateOf(TextFieldValue(value)) }
    val textMenu = remember { mutableStateOf<EditorTextMenuState?>(null) }
    val textToolbar = remember { RussianEditorTextToolbar(textMenu) }

    LaunchedEffect(value) {
        if (value != editorValue.value.text) {
            val selection = editorValue.value.selection
            editorValue.value = TextFieldValue(
                text = value,
                selection = TextRange(
                    start = selection.start.coerceIn(0, value.length),
                    end = selection.end.coerceIn(0, value.length),
                ),
            )
        }
    }

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
                LocalTextToolbar provides textToolbar,
            ) {
                BasicTextField(
                    value = editorValue.value,
                    onValueChange = { updated ->
                        editorValue.value = updated
                        if (updated.text != value) {
                            onValueChange(updated.text)
                        }
                    },
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
            textMenu.value?.let { menu ->
                RussianEditorTextMenu(
                    menu = menu,
                    onDismiss = textToolbar::hide,
                )
            }
        }
    }
}

private data class EditorTextMenuState(
    val anchor: Rect,
    val onCopy: (() -> Unit)?,
    val onPaste: (() -> Unit)?,
    val onCut: (() -> Unit)?,
    val onSelectAll: (() -> Unit)?,
)

private class RussianEditorTextToolbar(
    private val menu: MutableState<EditorTextMenuState?>,
) : TextToolbar {
    override val status: TextToolbarStatus
        get() = if (menu.value == null) {
            TextToolbarStatus.Hidden
        } else {
            TextToolbarStatus.Shown
        }

    override fun showMenu(
        rect: Rect,
        onCopyRequested: (() -> Unit)?,
        onPasteRequested: (() -> Unit)?,
        onCutRequested: (() -> Unit)?,
        onSelectAllRequested: (() -> Unit)?,
    ) {
        menu.value = EditorTextMenuState(
            anchor = rect,
            onCopy = onCopyRequested,
            onPaste = onPasteRequested,
            onCut = onCutRequested,
            onSelectAll = onSelectAllRequested,
        )
    }

    override fun hide() {
        menu.value = null
    }
}

@Composable
private fun RussianEditorTextMenu(
    menu: EditorTextMenuState,
    onDismiss: () -> Unit,
) {
    val positionProvider = remember(menu.anchor) {
        EditorTextMenuPositionProvider(menu.anchor)
    }

    Popup(
        popupPositionProvider = positionProvider,
        onDismissRequest = onDismiss,
        properties = PopupProperties(focusable = false),
    ) {
        Surface(
            modifier = Modifier
                .widthIn(min = 190.dp, max = 270.dp)
                .border(
                    width = 1.dp,
                    color = WebPanelPalette.AccentMiddle.copy(alpha = 0.68f),
                    shape = RoundedCornerShape(12.dp),
                ),
            color = WebPanelPalette.BackgroundDeep,
            contentColor = WebPanelPalette.TextStrong,
            shape = RoundedCornerShape(12.dp),
            shadowElevation = 12.dp,
        ) {
            Column(modifier = Modifier.padding(vertical = 6.dp)) {
                menu.onCut?.let { action ->
                    EditorTextMenuAction("Вырезать") {
                        onDismiss()
                        action()
                    }
                }
                menu.onCopy?.let { action ->
                    EditorTextMenuAction("Копировать") {
                        onDismiss()
                        action()
                    }
                }
                menu.onPaste?.let { action ->
                    EditorTextMenuAction("Вставить") {
                        onDismiss()
                        action()
                    }
                }
                menu.onSelectAll?.let { action ->
                    EditorTextMenuAction("Выделить всё") {
                        onDismiss()
                        action()
                    }
                }
            }
        }
    }
}

@Composable
private fun EditorTextMenuAction(
    label: String,
    onClick: () -> Unit,
) {
    Text(
        text = label,
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 11.dp),
        color = WebPanelPalette.TextStrong,
        style = MaterialTheme.typography.bodyMedium,
        fontWeight = FontWeight.Medium,
    )
}

private class EditorTextMenuPositionProvider(
    private val anchor: Rect,
) : PopupPositionProvider {
    override fun calculatePosition(
        anchorBounds: IntRect,
        windowSize: IntSize,
        layoutDirection: LayoutDirection,
        popupContentSize: IntSize,
    ): IntOffset {
        val margin = 12
        val maxX = (windowSize.width - popupContentSize.width - margin).coerceAtLeast(margin)
        val x = anchor.left.roundToInt().coerceIn(margin, maxX)
        val belowSelection = anchor.bottom.roundToInt() + margin
        val aboveSelection = anchor.top.roundToInt() - popupContentSize.height - margin
        val maxY = (windowSize.height - popupContentSize.height - margin).coerceAtLeast(margin)
        val y = if (belowSelection <= maxY) {
            belowSelection
        } else {
            aboveSelection.coerceIn(margin, maxY)
        }
        return IntOffset(x, y)
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
