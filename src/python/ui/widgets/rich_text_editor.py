# src/python/rich_text_editor.py

from PySide6.QtWidgets import (
    QToolBar, QWidget, QFontComboBox, QComboBox, QColorDialog, QMessageBox,
    QSizePolicy
)
from PySide6.QtGui import (
    QAction, QTextCharFormat, QFont, QTextCursor, QKeyEvent,
    QTextListFormat, QTextBlockFormat, QIcon, QBrush, QIcon
)
from PySide6.QtCore import Qt, QSize

from ...resources_rc import *
from .basic_text_editor import BasicTextEditor
from ...utils.logger import get_logger
from ...utils.exceptions import EditorContentError
from ...utils.event_bus import bus
from ...utils.events import Events

logger = get_logger(__name__)

class RichTextEditor(BasicTextEditor):
    """
    A Custom QWidget containing a QTextEdit and a formatting toolbar.

    Inherits from :py:class:`~.BasicTextEditor` and extends it by adding
    rich text formatting capabilities via a :py:class:`PySide6.QtWidgets.QToolBar`.

    This class handles all rich text formatting actions such as font selection,
    size, bold, italic, underline, color, highlighting, lists, alignment, and
    indentation. It also dynamically updates the toolbar controls
    based on the current cursor position or selection.

    :ivar toolbar: The formatting toolbar containing all controls and actions.
    :vartype toolbar: :py:class:`PySide6.QtWidgets.QToolBar`
    :ivar editor: The core text editor component inherited from BasicTextEditor.
    :vartype editor: :py:class:`PySide6.QtWidgets.QTextEdit`
    """

    def __init__(self, current_settings: dict={}, parent=None) -> None:
        """
        Initializes the RichTextEditor and connects its signals

        :param current_settings: A dictionary containing initial application settings.
        :type current_settings: dict
        :param parent: The parent widget. Defaults to ``None``.
        :type parent: :py:class:`PySide6.QtWidgets.QWidget`

        :rtype: None
        """
        super().__init__(is_spell_checking=current_settings.get('is_spell_checking', False), parent=parent)

        logger.debug("Initializing RichTextEditor (including its toolbar).")

        bus.register_instance(self)

        # Map display names to their corresponding QTextFormat block level
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

    def _setup_toolbar(self) -> None:
        """
        Creates and connects the formatting actions to the editor.
        
        :rtype: None
        """
        logger.debug("Starting toolbar configuration...")

        try:
            self.toolbar.setIconSize(QSize(16, 16))

            # Add Spacer to Push Everything to right
            left_spacer = QWidget()
            left_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            self.toolbar.addWidget(left_spacer)

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
            self.font_combo.setFontFilters(QFontComboBox.FontFilter.ScalableFonts)
            self.font_combo.setFixedWidth(100)
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
            self.bold_icon = QIcon(":icons/bold.svg")
            self.bold_action = QAction(self.bold_icon, "Bold", self)
            self.bold_action.setShortcut("Ctrl+B")
            self.bold_action.triggered.connect(self._toggle_bold)
            self.toolbar.addAction(self.bold_action)

            # ITALIC
            self.italic_icon = QIcon(":icons/italic.svg")
            self.italic_action = QAction(self.italic_icon, "Italic", self)
            self.italic_action.setShortcut("Ctrl+I")
            self.italic_action.triggered.connect(self._toggle_italic)
            self.toolbar.addAction(self.italic_action)

            # UNDERLINE
            self.underline_icon = QIcon(":icons/underline.svg")
            self.underline_action = QAction(self.underline_icon, "Underline", self)
            self.underline_action.setShortcut("Ctrl+U")
            self.underline_action.triggered.connect(self._toggle_underline)
            self.toolbar.addAction(self.underline_action)
            
            self.toolbar.addSeparator()

            # --- Color Selectinon Actions

            # Foreground Color (Text Color)
            self.color_icon = QIcon(":icons/font-color.svg")
            self.color_action = QAction(self.color_icon, "Text Color", self)
            self.color_action.triggered.connect(self._select_text_color)
            self.toolbar.addAction(self.color_action)

            # Background Color (Highlight)
            self.highlight_icon = QIcon(":icons/highlight-color.svg")
            self.highlight_action = QAction(self.highlight_icon, "Highlight Color", self)
            self.highlight_action.triggered.connect(self._select_highlight_color)
            self.toolbar.addAction(self.highlight_action)
            
            self.toolbar.addSeparator()

            # --- List Formatting (Unordered, Ordered) ---
            
            # UNORDERED LIST (Bullet Points)
            self.list_bullet_icon = QIcon(":icons/list-unordered.svg")
            self.list_bullet_action = QAction(self.list_bullet_icon, "Bullet List", self)
            self.list_bullet_action.triggered.connect(lambda: self._toggle_list(
                QTextListFormat.Style.ListDisc))
            self.toolbar.addAction(self.list_bullet_action)

            # ORDERED LIST (Numbers)
            self.list_number_icon = QIcon(":icons/list-ordered.svg")
            self.list_number_action = QAction(self.list_number_icon, "Numbered List", self)
            self.list_number_action.triggered.connect(lambda: self._toggle_list(
                QTextListFormat.Style.ListDecimal))
            self.toolbar.addAction(self.list_number_action)

            self.toolbar.addSeparator()

            # --- Text Alignment ---

            self.align_left_icon = QIcon(":icons/align-left.svg")
            self.align_left_action = QAction(self.align_left_icon, "Align Left", self)
            self.align_left_action.triggered.connect(lambda: self._align_text(Qt.AlignmentFlag.AlignLeft))
            self.toolbar.addAction(self.align_left_action)
            
            self.align_center_icon = QIcon(":icons/align-center.svg")
            self.align_center_action = QAction(self.align_center_icon, "Align Center", self)
            self.align_center_action.triggered.connect(lambda: self._align_text(Qt.AlignmentFlag.AlignCenter))
            self.toolbar.addAction(self.align_center_action)
            
            self.align_right_icon = QIcon(":icons/align-right.svg")
            self.align_right_action = QAction(self.align_right_icon, "Align Right", self)
            self.align_right_action.triggered.connect(lambda: self._align_text(Qt.AlignmentFlag.AlignRight))
            self.toolbar.addAction(self.align_right_action)

            self.toolbar.addSeparator()

            # --- Indentation ---

            self.outdent_icon = QIcon(":icons/indent-decrease.svg")
            self.outdent_action = QAction(self.outdent_icon, "Decrease Indent", self)
            self.outdent_action.triggered.connect(lambda: self._adjust_indent(-1))
            self.toolbar.addAction(self.outdent_action)
            
            self.indent_icon = QIcon(":icons/indent-increase.svg")
            self.indent_action = QAction(self.indent_icon, "Increase Indent", self)
            self.indent_action.triggered.connect(lambda: self._adjust_indent(1))
            self.toolbar.addAction(self.indent_action)

            # --- Clear Formatting ---
            
            self.clear_format_icon = QIcon(":icons/format-clear.svg")
            self.clear_format_action = QAction(self.clear_format_icon, "Clear Formatting", self)
            self.clear_format_action.triggered.connect(self._clear_formatting)
            self.toolbar.addAction(self.clear_format_action)

            # Add Spacer to Push Everything to left w/ left spacer makes everything in middle
            right_spacer = QWidget()
            right_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            self.toolbar.addWidget(right_spacer)

            logger.debug("Toolbar configuration complete.")
        except Exception as e:
            # Catch any error during resource loading or UI creation
            logger.critical("FATAL: Failed to initialize RichTextEditor toolbar.", exc_info=True)
            raise EditorContentError("Rich Text Editor failed to build its formatting controls.") from e

    # --- Formatting Handlers ---

    def _select_block_style(self, style_name: str) -> None:
        """
        Applies a block-level style (e.g., Heading or Paragraph).
        
        :param style_name: The name of the heading style
        :type style_name: str

        :rtype: None
        """
        try:
            level_value = self._block_style_map.get(style_name)

            if level_value is None:
                logger.warning(f"Attempted to apply unknown style: '{style_name}'.")
                return
            
            cursor = self.editor.textCursor()
            block_format = cursor.blockFormat()
            
            block_format.setHeadingLevel(level_value)
            
            cursor.setBlockFormat(block_format)
            self.editor.setTextCursor(cursor)
            self._set_dirty()
            logger.debug(f"Applying style: '{style_name}' (Level {level_value}) to current block.")

        except Exception as e:
            logger.error(f"Failed to apply text style '{style_name}'. Error: {e}", exc_info=True)
            QMessageBox.warning(self, "Style Error", f"Failed to apply style '{style_name}'.")

    def _select_font(self, font: QFont) -> None:
        """
        Applies the selected font family to the selected text 
        or cursor if no selected text.
        
        :param font: The selected font to change the text to.
        :type font: :py:class:`PySide6.QtGui.QFont`

        :rtype: None
        """
        try:
            char_format = QTextCharFormat()
            char_format.setFontFamily(font.family())
            self.editor.textCursor().mergeCharFormat(char_format)
            self._set_dirty()
            logger.debug(f"Applying font: '{font}' to current block.")
        except Exception as e:
            logger.error(f"Failed to apply font: '{font}'. Error: {e}", exc_info=True)
            QMessageBox.warning(self, "Font Error", f"Failed to apply font '{font}'.")

    def _select_font_size(self, size_str: str) -> None:
        """
        Applies the selected font size to the selected text.
        
        :param size_str: The font size that is selected
        :type size_str: str

        :rtype: None
        """
        try:
            # Clean and convert the string input from the QComboBox
            size = int(size_str.strip())
            
            # Use mergeCharFormat to ensure only the font size is changed
            char_format = QTextCharFormat()
            char_format.setFontPointSize(size)
            self.editor.textCursor().mergeCharFormat(char_format)
            self._set_dirty()
            logger.debug(f"Applying font size: '{size_str}' to current block.")

        except ValueError:
            logger.error(f"Failed to apply font size: '{size_str}'. Error: {e}", exc_info=True)
            QMessageBox.warning(self, "Font Size ValueError", f"Failed to apply font size '{size_str}'.")
        
        except Exception as e:
            logger.error(f"Failed to apply font size: '{size_str}'. Error: {e}", exc_info=True)
            QMessageBox.warning(self, "Font Size Error", f"Failed to apply font size '{size_str}'.")
    
    def _toggle_bold(self) -> None:
        """
        Toggles bold formatting for the selected text.
        
        :rtype: None
        """       
        try: 
            format = self.editor.currentCharFormat()
            weight = QFont.Weight.Bold if format.fontWeight() != QFont.Weight.Bold else QFont.Weight.Normal
            format.setFontWeight(weight)
            self.editor.mergeCurrentCharFormat(format)
            self._set_dirty()
            logger.debug(f"Applying bold to current block.")

        except Exception as e:
            logger.error(f"Failed to apply Bold. Error: {e}", exc_info=True)
            QMessageBox.warning(self, "Bold Error", f"Failed to apply bold.")

        
    def _toggle_italic(self) -> None:
        """
        Toggles italic formatting for the selected text.
        
        :rtype: None
        """   
        try:         
            format = self.editor.currentCharFormat()
            format.setFontItalic(not format.fontItalic())
            self.editor.mergeCurrentCharFormat(format)
            self._set_dirty()
            logger.debug(f"Applying Italic to current block.")

        except Exception as e:
            logger.error(f"Failed to apply Italic. Error: {e}", exc_info=True)
            QMessageBox.warning(self, "Italic Error", f"Failed to apply Italic.")

    def _toggle_underline(self) -> None:
        """
        Toggles underline formatting for the selected text.
        
        :rtype: None
        """
        try:
            format = self.editor.currentCharFormat()
            format.setFontUnderline(not format.fontUnderline())
            self.editor.mergeCurrentCharFormat(format)
            self._set_dirty()
            logger.debug(f"Applying Underline to current block.")

        except Exception as e:
            logger.error(f"Failed to apply Underline. Error: {e}", exc_info=True)
            QMessageBox.warning(self, "Underline Error", f"Failed to apply Underline.")

    def _select_text_color(self) -> None:
        """
        Opens a color dialog to select the foreground (text) color
        
        :rtype: None
        """
        # Get the current color to use as the default in the dialog
        current_format = self.editor.textCursor().charFormat()
        initial_color = current_format.foreground().color()

        try:
            color = QColorDialog.getColor(initial_color, self, "Select Text Color")

            if color.isValid():
                char_format = QTextCharFormat()
                char_format.setForeground(QBrush(color))
                self.editor.textCursor().mergeCharFormat(char_format)
                self._set_dirty()
                logger.debug(f"Text color changed to: {color.name()}.")
            else:
                logger.debug("Text color change cancelled by user.")
        except Exception as e:
            logger.warning(f"Failed to display or process color dialog: {e}", exc_info=True)
            # Display a non-critical UI message to the user
            QMessageBox.warning(self, "Formatting Error", "Failed to change text color due to a UI issue.")

    def _select_highlight_color(self) -> None:
        """
        Opens a color dialog to select the background (highlight) color
        and marks the editor as dirty.

        :rtype: None
        """
        try:
            # Get the current color to use as the default in the dialog
            current_format = self.editor.textCursor().charFormat()
            initial_color = current_format.background().color()

            color = QColorDialog.getColor(initial_color, self, "Select Text Color")

            if color.isValid():
                char_format = QTextCharFormat()
                char_format.setBackground(QBrush(color))
                self.editor.textCursor().mergeCharFormat(char_format)
                self._set_dirty()
                logger.debug("Select Highlight Color")
        except Exception as e:
            logger.warning(f"Failed to display or process color highlight dialog: {e}", exc_info=True)
            QMessageBox.warning(self, "Formatting Error", "Failed to change text highlight color "
                                "due to a UI issue.")
         

    def _toggle_list(self, list_style: QTextListFormat.Style) -> None:
        """
        Toggles the current paragraph(s) into a list format in the editor.
        
        :param list_style: The style of list that is selected (order or unordered).
        :type list_style: :py:class:'PySide6.QtGui.QTextListFormat.Style'

        :rtype: None
        """
        try:
            cursor = self.editor.textCursor()
            
            # Check if we are already in the desired list style
            if cursor.currentList() and cursor.currentList().format().style() == list_style:
                # If so, remove the list format by setting the block format to default
                block_format = QTextBlockFormat()
                block_format.setIndent(0) # Remove list indentation
                cursor.setBlockFormat(block_format)
                logger.debug("Un-Toggle Ordered List")
            else:
                # Apply the new list style
                list_format = QTextListFormat()
                list_format.setStyle(list_style)
                cursor.createList(list_format)
                logger.debug("Toggle Ordered List")
        except Exception as e:
            logger.warning(f"Failed to display or process list: {e}", exc_info=True)
            QMessageBox.warning(self, "Formatting Error", "Failed to change the list due to a UI issue.")


    def _update_toolbar_state(self) -> None:
        """
        Updates the enabled/checked state of toolbar buttons based on the
        current cursor position/selection format.

        :rtype: None
        """
        was_blocked = self.editor.signalsBlocked()
        self.editor.blockSignals(True)

        try:
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

            logger.debug("Updated the Toolbar State.")

        except Exception as e:
            logger.warning(f"Failed to update toolbar: {e}", exc_info=True)
            QMessageBox.warning(self, "Update Toolbar Error", "Failed to Update Toolbar due to a UI issue.")

        finally:
            if not was_blocked:
                self.editor.blockSignals(False)

    def _align_text(self, alignment: Qt.AlignmentFlag) -> None:
        """
        Sets the alignment of the current text block(s) and marks content as dirty.
        
        :param alignment: The alignment flag that sets the editor to the correct alignment
        :type alignment: :py:class:'PySide6.QtCore.Qt.AlignmentFlag'

        :rtype: None
        """
        try:
            self.editor.setAlignment(alignment)
            self._set_dirty()
            logger.debug(f"Apply Alignment '{alignment}' to text")

        except Exception as e:
            logger.error(f"Failed to Align Text: '{alignment}'. Error: {e}", exc_info=True)
            QMessageBox.warning(self, "Text Alignment Error", f"Failed to apply Text Alignment '{alignment}'.")

    def _adjust_indent(self, direction: int) -> None:
        """
        Increases or decreases the indentation of the current text block(s) and marks content as dirty.
        
        :param direction: The direction the indent is moving (increasing/decreasing).
                  Positive moves right (increase), negative moves left (decrease).
        :type int: Positive move to right, negative move to left

        :rtype: None
        """
        try:
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
                logger.debug(f"Adjust Indent in direction: '{direction}' to text.")

        except Exception as e:
            logger.error(f"Failed to Adjust Indent in direction: '{direction}'. Error: {e}", exc_info=True)
            QMessageBox.warning(self, "Adjust Indent Error", f"Failed to Adjust Indent in direction '{direction}'.")

    def _clear_formatting(self) -> None:
        """
        Removes character formatting (bold, color, etc.) from the selected text or current word.
        
        :rtype: None
        """
        try:
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
            logger.debug("Clear Formatting of the text.")

        except Exception as e:
            logger.error(f"Failed to clear formatting. Error: {e}", exc_info=True)
            QMessageBox.warning(self, "Formatting Error", f"Failed to clear formatting'.")

    def _update_format_controls(self) -> None:
        """
        Updates the state of all toolbar controls (font, size, bold, etc.) 
        based on the formatting at the current cursor position/selection.

        :rtype: None
        """
        try:
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

            logger.debug("Update the Format Controls")

        except Exception as e:
            logger.warning(f"Failed to Update the Format Controls: {e}", exc_info=True)
            QMessageBox.warning(self, "Format Controls Error", "Failed to Update the Format Controls "
                                "due to a UI issue.")
