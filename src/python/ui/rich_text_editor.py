# Rich Text Editor Component: src/python/rich_text_editor.py

from PyQt6.QtWidgets import (
    QTextEdit, QToolBar, QWidget, QVBoxLayout, 
    QApplication, QMainWindow, QStatusBar
)
from PyQt6.QtGui import (
    QAction, QTextCharFormat, QFont, QTextCursor, 
    QTextListFormat, QTextList, QTextBlockFormat
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QStyle
import sys

class RichTextEditor(QWidget):
    """
    A Custom QWidget containing a QTextEdit and a formatiing toolbar
    Handles the rich text formating Action
    """
    # signal to notify listeners (like ChapterEditor/LoreEditor) of content changes
    content_changed = pyqtSignal()

    def __init__(self, parent =None) -> None:
        super().__init__(parent)

        # State tracking for unsaved changes
        self._is_dirty = False
        self._last_saved_content = ""

        # Core components
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Start writing your chapter here")

        # Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar setup
        self.toolbar = QToolBar()
        self._setup_toolbar()

        main_layout.addWidget(self.toolbar)
        main_layout.addWidget(self.editor)

        # Connect signals for dynamic toolbar updates
        self.editor.selectionChanged.connect(self._update_toolbar_state)
        self.editor.cursorPositionChanged.connect(self._update_toolbar_state)
        self.editor.textChanged.connect(self._set_dirty)
        self.editor.textChanged.connect(self.content_changed.emit)

    # --- Dirty Flag Management ---

    def _set_dirty(self) -> None:
        """Sets the dirty flag when the text content changes."""
        if not self._is_dirty:
            self._is_dirty = True
            # print("Editor: Content is now DIRTY.") # Debugging line

    def is_dirty(self) -> bool:
        """Returns True if the content has been modified since the last save/load."""
        return self._is_dirty

    def mark_saved(self) -> None:
        """Clears the dirty flag and updates the last saved content."""
        self._is_dirty = False
        self._last_saved_content = self.editor.toHtml()
        # print("Editor: Content marked as clean.") # Debugging line

    def _setup_toolbar(self):
        """Creates and connects the formatting actions to the editor."""
        
        # --- Basic Text Formatting Actions ---

        # BOLD
        bold_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_CustomBase) #Placeholder icon
        bold_action = QAction(bold_icon, "Bold", self)
        bold_action.setShortcut("Ctrl+B")
        bold_action.triggered.connect(self._toggle_bold)
        self.toolbar.addAction(bold_action)

        # ITALIC
        italic_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_CustomBase) # Placeholder icon
        italic_action = QAction(italic_icon, "Italic", self)
        italic_action.setShortcut("Ctrl+I")
        italic_action.triggered.connect(self._toggle_italic)
        self.toolbar.addAction(italic_action)

        # UNDERLINE
        underline_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_CustomBase) # Placeholder icon
        underline_action = QAction(underline_icon, "Underline", self)
        underline_action.setShortcut("Ctrl+U")
        underline_action.triggered.connect(self._toggle_underline)
        self.toolbar.addAction(underline_action)
        
        self.toolbar.addSeparator()

        # --- List Formatting Actions ---
        
        # UNORDERED LIST (Bullet Points)
        list_bullet_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_CustomBase) # Placeholder icon
        list_bullet_action = QAction(list_bullet_icon, "Bullet List", self)
        list_bullet_action.triggered.connect(lambda: self._toggle_list(QTextListFormat.Style.ListDisc))
        self.toolbar.addAction(list_bullet_action)

        # ORDERED LIST (Numbers)
        list_number_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_CustomBase) # Placeholder icon
        list_number_action = QAction(list_number_icon, "Numbered List", self)
        list_number_action.triggered.connect(lambda: self._toggle_list(QTextListFormat.Style.ListDecimal))
        self.toolbar.addAction(list_number_action)

    # --- Formatting Handlers ---
    
    def _toggle_bold(self):
        """Toggles bold formatting for the selected text."""
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        
        format = cursor.charFormat()
        weight = QFont.Weight.Bold if format.fontWeight() != QFont.Weight.Bold else QFont.Weight.Normal
        format.setFontWeight(weight)
        cursor.mergeCharFormat(format)
        self.editor.mergeCurrentCharFormat(format)
        
    def _toggle_italic(self):
        """Toggles italic formatting for the selected text."""
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            
        format = cursor.charFormat()
        format.setFontItalic(not format.fontItalic())
        cursor.mergeCharFormat(format)
        self.editor.mergeCurrentCharFormat(format)

    def _toggle_underline(self):
        """Toggles underline formatting for the selected text."""
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            
        format = cursor.charFormat()
        format.setFontUnderline(not format.fontUnderline())
        cursor.mergeCharFormat(format)
        self.editor.mergeCurrentCharFormat(format)

    def _toggle_list(self, list_style: QTextListFormat.Style):
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

    def _update_toolbar_state(self):
        """
        Updates the enabled/checked state of toolbar buttons based on the
        current cursor position/selection format.
        """
        format = self.editor.currentCharFormat()
        
        # Update Bold button state
        bold_action = self.toolbar.actions()[0] # Assuming position 0 is Bold
        bold_action.setChecked(format.fontWeight() == QFont.Weight.Bold)
        
        # Update Italic button state
        italic_action = self.toolbar.actions()[1] # Assuming position 1 is Italic
        italic_action.setChecked(format.fontItalic())
        
        # Update Underline button state
        underline_action = self.toolbar.actions()[2] # Assuming position 2 is Underline
        underline_action.setChecked(format.fontUnderline())
        
        # Update List button states
        current_list = self.editor.textCursor().currentList()
        if current_list is None: current_list = False

        list_bullet_action = self.toolbar.actions()[4] # Assuming position 4 is Bullet List (index 3 is the separator)
        list_number_action = self.toolbar.actions()[5] # Assuming position 5 is Numbered List

        is_bullet = current_list and current_list.format().style() == QTextListFormat.Style.ListDisc
        is_numbered = current_list and current_list.format().style() == QTextListFormat.Style.ListDecimal

        list_bullet_action.setChecked(is_bullet)
        list_number_action.setChecked(is_numbered)
        
    # --- Public Accessors for Content (Story 2.6) ---

    def get_html_content(self) -> str:
        """Returns the editor's content as Rich Text HTML."""
        return self.editor.toHtml()

    def set_html_content(self, html_content: str) -> None:
        """
        Sets the editor's content from Rich Text HTML and marks the content as clean.
        The textChanged signal is temporarily blocked to prevent setting the dirty flag.
        """
        # Block signals to prevent _set_dirty from firing during load
        self.editor.blockSignals(True) 
        self.editor.setHtml(html_content)
        # Unblock signals
        self.editor.blockSignals(False) 
        
        # Manually reset the dirty state after a successful load
        self.mark_saved()
        # print("Editor: Content loaded and marked as clean.") # Debugging line

if __name__ == '__main__':
    app = QApplication([])
    
    # Create the main window to host the editor (for testing purposes)
    main_window = QMainWindow()
    main_window.setWindowTitle("RichTextEditor Test")
    main_window.setGeometry(100, 100, 800, 600)
    
    editor = RichTextEditor(main_window)
    main_window.setCentralWidget(editor)
    main_window.show()
    
    # Example content to load
    editor.set_html_content(
        "<h1>Hello World!</h1>"
        "<p>This is a test of the <b>Rich Text Editor</b>.</p>"
        "<ul><li>Bullet 1</li><li>Bullet 2</li></ul>"
        "<ol><li>Numbered 1</li><li>Numbered 2</li></ol>"
    )

    sys.exit(app.exec())