# src/python/basic_text_editor.py

from PyQt6.QtWidgets import (
    QTextEdit, QWidget, QVBoxLayout,
)
from PyQt6.QtCore import pyqtSignal

class BasicTextEditor(QWidget):
    """
    A composite :py:class:`PyQt6.QtWidgets.QWidget` that serves as a basic
    text editing widget.

    The Widget contains a text editing editor with basic signals for saving
    content and notifying whethe the editor is dirty. This class also contains 
    public access functions to get the text contained in the editor.
    """
    # Signal to notify listeners (like ChapterEditor/LoreEditor) of content changes
    content_changed = pyqtSignal()
    selection_changed = pyqtSignal()

    def __init__(self, parent=None) -> None:
        """
        Initializes the BasicTextEditor and connects its signals

        :param parent: The parent widget. Defaults to ``None``.
        :type parent: :py:class:`PyQt6.QtWidgets.QWidget`
        """
        super().__init__(parent)

        # State tracking for unsaved changes
        self._is_dirty = False
        self._last_saved_content = ""

        # Core component
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Start writing here")
        
        # Layout setup (similar to your original RichTextEditor setup)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.editor)

        # Connect signals for dirty flag and content change notification
        self.editor.textChanged.connect(self._set_dirty)
        self.editor.textChanged.connect(self.content_changed.emit)
        self.editor.selectionChanged.connect(self.selection_changed.emit)

    # --- Dirty Flag Management ---

    def _set_dirty(self) -> None:
        """Sets the dirty flag when the text content changes."""
        if not self._is_dirty:
            self._is_dirty = True

    def is_dirty(self) -> bool:
        """
        Returns True if the content has been modified since the last save/load.

        :rtype: bool
        """
        return self._is_dirty

    def mark_saved(self) -> None:
        """Clears the dirty flag and updates the last saved content."""
        self._is_dirty = False
        self._last_saved_content = self.editor.toHtml()

    # --- Public Accessors for Content ---

    def get_html_content(self) -> str:
        """
        Returns the editor's content as Rich Text HTML.
        
        :rtype: str
        """
        return self.editor.toHtml()

    def set_html_content(self, html_content: str) -> None:
        """
        Sets the editor's content from Rich Text HTML and marks the content as clean.
        
        The textChanged signal is temporarily blocked to prevent setting the dirty flag.

        :param html_content: The html content that is being set in the editor
        :type html_content: str
        """
        # Block signals to prevent _set_dirty from firing during load
        self.editor.blockSignals(True) 
        self.editor.setHtml(html_content)
        self.editor.blockSignals(False) 
        
        # Manually reset the dirty state after a successful load
        self.mark_saved()

    def get_plain_text(self) -> str:
        """Returns the editor's content as plain text."""
        return self.editor.toPlainText()
    
    def get_selected_text(self) -> str:
        """Returns the currently selected plain text."""
        return self.editor.textCursor().selectedText()
