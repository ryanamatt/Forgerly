# src/python/rich_text_editor.py

from PyQt6.QtWidgets import (
    QTextEdit, QToolBar, QWidget, QVBoxLayout, QStyle,
    QFontComboBox, QComboBox, QColorDialog
)
from PyQt6.QtGui import (
    QAction, QTextCharFormat, QFont, QTextCursor, 
    QTextListFormat, QTextBlockFormat, QIcon, QBrush,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize

from .basic_text_editor import BasicTextEditor

class RichTextEditor(BasicTextEditor):
    """
    A Custom QWidget containing a QTextEdit and a formatiing toolbar
    Handles the rich text formating Action
    """

    def __init__(self, parent =None) -> None:
        super().__init__(parent)

        # Map display names to their corresponding QTestFormat block level
        self._block_style_map = {
            "Paragraph": 0,
            "Heading 1": 1,
            "Heading 2": 2,
            "Heading 3": 3,
        }

        # Layout
        main_layout = self.layout()

        # Toolbar setup
        self.toolbar = QToolBar()
        self._setup_toolbar()

        main_layout.insertWidget(0, self.toolbar)

        # Connect signals for dynamic toolbar updates
        self.editor.cursorPositionChanged.connect(self._update_format_controls)
        self.editor.selectionChanged.connect(self._update_toolbar_state)
        self.editor.cursorPositionChanged.connect(self._update_toolbar_state)

    def _setup_toolbar(self):
        """Creates and connects the formatting actions to the editor."""

        self.toolbar.setIconSize(QSize(16, 16))

        # --- Block Style Selector (Paragraph and Headers) ---
        self.style_combo = QComboBox(self.toolbar)
        self.style_combo.addItems(list(self._block_style_map.keys()))
        self.style_combo.setFixedWidth(100)
        self.style_combo.currentTextChanged.connect(self._select_block_style)
        self.toolbar.addWidget(self.style_combo)

        self.toolbar.addSeparator()

        # --- Font and Size Selection ---

        # Font Family Selector
        self.font_combo = QFontComboBox(self.toolbar)
        self.font_combo.currentFontChanged.connect(self._select_font)
        self.toolbar.addWidget(self.font_combo)

        # Font Size Selector
        self.size_combo = QComboBox(self.toolbar)
        self.size_combo.setEditable(True)
        self.size_combo.setFixedWidth(50)
        # Standard sizes for rich text editors
        self.size_combo.addItems([
            "8", "9", "10", "11", "12", "14", "16", "18", "20", "22", "24", "26", "28", "36", "48", "72"
        ])
        self.size_combo.setCurrentText("12") # Set default size
        self.size_combo.textActivated.connect(self._select_font_size)
        self.toolbar.addWidget(self.size_combo)
        
        self.toolbar.addSeparator()
        
        # --- Basic Character Formatting (Bold, Italic, Underline) ---

        # BOLD
        bold_icon = QIcon.fromTheme("format-text-bold", self.style().standardIcon(QStyle.StandardPixmap.SP_DialogYesButton))
        self.bold_action = QAction(bold_icon, "Bold", self)
        self.bold_action.setShortcut("Ctrl+B")
        self.bold_action.triggered.connect(self._toggle_bold)
        self.toolbar.addAction(self.bold_action)

        # ITALIC
        italic_icon = QIcon.fromTheme("format-text-italic", self.style().standardIcon(QStyle.StandardPixmap.SP_DialogNoButton))
        self.italic_action = QAction(italic_icon, "Italic", self)
        self.italic_action.setShortcut("Ctrl+I")
        self.italic_action.triggered.connect(self._toggle_italic)
        self.toolbar.addAction(self.italic_action)

        # UNDERLINE
        underline_icon = QIcon.fromTheme("format-text-underline", self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogInfoView))
        self.underline_action = QAction(underline_icon, "Underline", self)
        self.underline_action.setShortcut("Ctrl+U")
        self.underline_action.triggered.connect(self._toggle_underline)
        self.toolbar.addAction(self.underline_action)
        
        self.toolbar.addSeparator()

        # --- Color Selectinon Actions

        # Foreground Color (Text Color)
        color_icon = QIcon.fromTheme("format-text-color", self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
        color_action = QAction(color_icon, "Text Color", self)
        color_action.triggered.connect(self._select_text_color)
        self.toolbar.addAction(color_action)

        # Background Color (Highlight)
        highlight_icon = QIcon.fromTheme("format-text-highlight", self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowUp))
        highlight_action = QAction(highlight_icon, "Highlight Color", self)
        highlight_action.triggered.connect(self._select_highlight_color)
        self.toolbar.addAction(highlight_action)
        
        self.toolbar.addSeparator()

        # --- List Formatting (Unordered, Ordered) ---
        
        # UNORDERED LIST (Bullet Points)
        list_bullet_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_CustomBase) # Placeholder icon
        self.list_bullet_action = QAction(list_bullet_icon, "Bullet List", self)
        self.list_bullet_action.triggered.connect(lambda: self._toggle_list(QTextListFormat.Style.ListDisc))
        self.toolbar.addAction(self.list_bullet_action)

        # ORDERED LIST (Numbers)
        list_number_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_CustomBase)
        self.list_number_action = QAction(list_number_icon, "Numbered List", self)
        self.list_number_action.triggered.connect(lambda: self._toggle_list(QTextListFormat.Style.ListDecimal))
        self.toolbar.addAction(self.list_number_action)

        self.toolbar.addSeparator()

        # --- Text Alignment ---

        align_left_icon = QIcon.fromTheme("format-justify-left", self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowLeft))
        self.align_left_action = QAction(align_left_icon, "Align Left", self)
        self.align_left_action.triggered.connect(lambda: self._align_text(Qt.AlignmentFlag.AlignLeft))
        self.toolbar.addAction(self.align_left_action)
        
        align_center_icon = QIcon.fromTheme("format-justify-center", self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward))
        self.align_center_action = QAction(align_center_icon, "Align Center", self)
        self.align_center_action.triggered.connect(lambda: self._align_text(Qt.AlignmentFlag.AlignCenter))
        self.toolbar.addAction(self.align_center_action)
        
        align_right_icon = QIcon.fromTheme("format-justify-right", self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowRight))
        self.align_right_action = QAction(align_right_icon, "Align Right", self)
        self.align_right_action.triggered.connect(lambda: self._align_text(Qt.AlignmentFlag.AlignRight))
        self.toolbar.addAction(self.align_right_action)

        self.toolbar.addSeparator()

        # --- Indentation ---

        outdent_icon = QIcon.fromTheme("format-indent-less", self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowLeft))
        self.outdent_action = QAction(outdent_icon, "Decrease Indent", self)
        self.outdent_action.triggered.connect(lambda: self._adjust_indent(-1))
        self.toolbar.addAction(self.outdent_action)
        
        indent_icon = QIcon.fromTheme("format-indent-more", self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowRight))
        self.indent_action = QAction(indent_icon, "Increase Indent", self)
        self.indent_action.triggered.connect(lambda: self._adjust_indent(1))
        self.toolbar.addAction(self.indent_action)

        # --- Clear Formatting ---
        
        clear_format_icon = QIcon.fromTheme("edit-clear-all", self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton))
        self.clear_format_action = QAction(clear_format_icon, "Clear Formatting", self)
        self.clear_format_action.triggered.connect(self._clear_formatting)
        self.toolbar.addAction(self.clear_format_action)

    # --- Formatting Handlers ---

    def _select_block_style(self, style_name: str) -> None:
        """Applies a block-level style (e.g., Heading or Paragraph)."""
        level_value = self._block_style_map.get(style_name)
        
        cursor = self.editor.textCursor()
        block_format = cursor.blockFormat()
        
        block_format.setHeadingLevel(level_value)
        
        cursor.setBlockFormat(block_format)
        self.editor.setTextCursor(cursor)
        self._set_dirty()

    def _select_font(self, font: QFont) -> None:
        """Applies the selected font family to the selected text."""
        # Use mergeCharFormat to ensure only the font family is changed
        char_format = QTextCharFormat()
        char_format.setFontFamily(font.family())
        self.editor.textCursor().mergeCharFormat(char_format)
        self._set_dirty()

    def _select_font_size(self, size_str: str) -> None:
        """Applies the selected font size to the selected text."""
        try:
            # Clean and convert the string input from the QComboBox
            size = int(size_str.strip())
            
            # Use mergeCharFormat to ensure only the font size is changed
            char_format = QTextCharFormat()
            char_format.setFontPointSize(size)
            self.editor.textCursor().mergeCharFormat(char_format)
            self._set_dirty()
        except ValueError:
            # Handle cases where the user types non-numeric text
            print(f"Invalid font size input: {size_str}")
    
    def _toggle_bold(self) -> None:
        """Toggles bold formatting for the selected text."""        
        format = self.editor.currentCharFormat()
        weight = QFont.Weight.Bold if format.fontWeight() != QFont.Weight.Bold else QFont.Weight.Normal
        format.setFontWeight(weight)
        self.editor.mergeCurrentCharFormat(format)
        self._set_dirty()
        
    def _toggle_italic(self) -> None:
        """Toggles italic formatting for the selected text."""            
        format = self.editor.currentCharFormat()
        format.setFontItalic(not format.fontItalic())
        self.editor.mergeCurrentCharFormat(format)
        self._set_dirty()

    def _toggle_underline(self) -> None:
        """Toggles underline formatting for the selected text."""
        format = self.editor.currentCharFormat()
        format.setFontUnderline(not format.fontUnderline())
        self.editor.mergeCurrentCharFormat(format)
        self._set_dirty()

    def _select_text_color(self) -> None:
        """Opens a color dialog to select the foreground (text) color"""
        # Get the current color to use as the default in the dialog
        current_format = self.editor.textCursor().charFormat()
        initial_color = current_format.foreground().color()

        color = QColorDialog.getColor(initial_color, self, "Select Text Color")

        if color.isValid():
            char_format = QTextCharFormat()
            char_format.setForeground(QBrush(color))
            self.editor.textCursor().mergeCharFormat(char_format)
            self._set_dirty()

    def _select_highlight_color(self) -> None:
        """Opens a color dialog to select the background (highlight) color."""
        # Get the current color to use as the default in the dialog
        current_format = self.editor.textCursor().charFormat()
        initial_color = current_format.background().color()

        color = QColorDialog.getColor(initial_color, self, "Select Text Color")

        if color.isValid():
            char_format = QTextCharFormat()
            char_format.setBackground(QBrush(color))
            self.editor.textCursor().mergeCharFormat(char_format)
            self._set_dirty()
         

    def _toggle_list(self, list_style: QTextListFormat.Style) -> None:
        """Toggles the current paragraph(s) into a list format."""
        cursor = self.editor.textCursor()
        
        # Check if we are already in the desired list style
        if cursor.currentList() and cursor.currentList().format().style() == list_style:
            # If so, remove the list format by setting the block format to default
            block_format = QTextBlockFormat()
            block_format.setIndent(0) # Remove list indentation
            cursor.setBlockFormat(block_format)
        else:
            # Apply the new list style
            list_format = QTextListFormat()
            list_format.setStyle(list_style)
            cursor.createList(list_format)

    def _update_toolbar_state(self) -> None:
        """
        Updates the enabled/checked state of toolbar buttons based on the
        current cursor position/selection format.
        """
        format = self.editor.currentCharFormat()
        
        self.bold_action.setChecked(format.fontWeight() == QFont.Weight.Bold)
        self.italic_action.setChecked(format.fontItalic())
        self.underline_action.setChecked(format.fontUnderline())

        # Update List button states
        current_list = self.editor.textCursor().currentList()
        is_list = current_list is not None # Check if it's a list

        is_bullet = is_list and current_list.format().style() == QTextListFormat.Style.ListDisc
        is_numbered = is_list and current_list.format().style() == QTextListFormat.Style.ListDecimal

        self.list_bullet_action.setChecked(is_bullet)
        self.list_number_action.setChecked(is_numbered)

    def _align_text(self, alignment: Qt.AlignmentFlag) -> None:
        """Sets the alignment of the current text block(s) and marks content as dirty."""
        self.editor.setAlignment(alignment)
        self._set_dirty()

    def _adjust_indent(self, direction: int) -> None:
        """Increases or decreases the indentation of the current text block(s) and marks content as dirty."""
        # Get the current cursor
        cursor = self.editor.textCursor()
        
        # Ensure the cursor is valid
        if not cursor.hasSelection() and cursor.block().isValid():
            
            block_format = cursor.blockFormat()
            current_indent = block_format.indent()

            if direction > 0:
                # Increase indent, max 7 for a simple editor
                new_indent = min(current_indent + 1, 7)
            else:
                # Decrease indent, min 0
                new_indent = max(current_indent - 1, 0)
            
            block_format.setIndent(new_indent)
            cursor.setBlockFormat(block_format)
            self.editor.setTextCursor(cursor)
            self._set_dirty()

    def _clear_formatting(self) -> None:
        """Removes character formatting (bold, color, etc.) from the selected text or current word."""
        cursor = self.editor.textCursor()

        if cursor.hasSelection():
            # Apply a default, clean character format to the selection
            clean_char_format = QTextCharFormat()
            cursor.mergeCharFormat(clean_char_format)
            
        else:
            self.editor.setCurrentCharFormat(QTextCharFormat())

        # Clear Block Formatting (heading, alignment, indentation)
        clean_block_format = QTextBlockFormat()
        clean_block_format.setAlignment(Qt.AlignmentFlag.AlignLeft)
        clean_block_format.setIndent(0)
        clean_block_format.setHeadingLevel(0)

        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)

        # Use begin/endEditBlock for better merging
        cursor.beginEditBlock()
        cursor.setBlockFormat(clean_block_format)
        cursor.endEditBlock()
            
        self.editor.setTextCursor(cursor) 
        self._set_dirty()

    def _update_format_controls(self) -> None:
        """
        Updates the state of all toolbar controls (font, size, bold, etc.) 
        based on the formatting at the current cursor position/selection.
        """
        
        # Get the current character format
        current_format = self.editor.textCursor().charFormat()
        
        # --- Update Block Style Combo Box ---
        current_block_format = self.editor.textCursor().blockFormat()
        current_level = current_block_format.headingLevel()
        
        style_name = "Paragraph" # Default value (Paragraph)
        
        if current_level > 0:
            # Find the style name corresponding to the current heading level
            for name, level in self._block_style_map.items():
                if name != "Paragraph" and level == current_level:
                    style_name = name
                    break
        
        self.style_combo.blockSignals(True)
        self.style_combo.setCurrentText(style_name)
        self.style_combo.blockSignals(False)
        
        # --- Update Font Combo Box ---
        self.font_combo.blockSignals(True)
        self.font_combo.setCurrentFont(current_format.font())
        self.font_combo.blockSignals(False)
        
        # --- Update Font Size Combo Box ---
        current_size = int(current_format.fontPointSize())
        if current_size == 0:
            current_size = 12 # Default to a visible size if point size is 0 (e.g., in a heading)
        size_str = str(current_size)

        self.size_combo.blockSignals(True)
        
        # If the current size is not in the predefined list (e.g., user typed it in), temporarily add it
        if self.size_combo.findText(size_str) == -1:
            self.size_combo.addItem(size_str) 
        
        self.size_combo.setCurrentText(size_str)
        self.size_combo.blockSignals(False)

        # --- Update Basic Formatting Actions (Bold, Italic, Underline) ---
        self.bold_action.setChecked(current_format.fontWeight() == QFont.Weight.Bold)
        self.italic_action.setChecked(current_format.fontItalic())
        self.underline_action.setChecked(current_format.fontUnderline())
        