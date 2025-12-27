# src/python/basic_text_editor.py

from PySide6.QtWidgets import (
    QTextEdit, QWidget, QVBoxLayout, QMessageBox
)
from PySide6.QtCore import Signal

from ...utils.logger import get_logger
from ...utils.exceptions import EditorContentError
from ...utils.event_bus import bus
from ...utils.events import Events

logger = get_logger(__name__)

class BasicTextEditor(QWidget):
    """
    A composite :py:class:`~PyQt6.QtWidgets.QWidget` that serves as a basic
    text editing widget.

    The Widget contains a text editing editor with basic signals for saving
    content and notifying whethe the editor is dirty. This class also contains 
    public access functions to get the text contained in the editor.
    """
    # Signal to notify listeners (like ChapterEditor/LoreEditor) of content changes
    content_changed = Signal()
    """
    :py:class:`~PyQt6.QtCore.Signal`: Emitted when the content of the editor changes.
    """

    selection_changed = Signal()
    """
    :py:class:`~PyQt6.QtCore.Signal`: Emitted when the selection has changed..
    """

    def __init__(self, parent=None) -> None:
        """
        Initializes the BasicTextEditor and connects its signals

        :param parent: The parent widget. Defaults to ``None``.
        :type parent: :py:class:`PyQt6.QtWidgets.QWidget`

        :rtype: None
        """
        super().__init__(parent)

        logger.debug("Initializing BasicTextEditor widget.")

        bus.register_instance(self)

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
        self.editor.selectionChanged.connect(self._on_selection_changed)

    # --- Dirty Flag Management ---

    def _set_dirty(self) -> None:
        """
        Sets the dirty flag when the text content changes.
        
        :rtype: None
        """
        if not self._is_dirty:
            self._is_dirty = True

            # KEEP EMITTING SIGNAL TILL EVERYTHING IS IN EVENT BUS
            self.content_changed.emit()

            bus.publish(Events.CONTENT_CHANGED, data={
                'editor': self,
                'is_dirty': True
            })

            logger.debug("BasicTextEditor content changed. Dirty flag set to True.")
        else:
            logger.debug("BasicTextEditor content changed, but already dirty (state remains True).")

    def is_dirty(self) -> bool:
        """
        Returns True if the content has been modified since the last save/load.

        :rtype: bool
        """
        return self._is_dirty

    def mark_saved(self) -> None:
        """
        Clears the dirty flag and updates the last saved content.
        
        :rtype: None
        """
        try:
            self._is_dirty = False
            self._last_saved_content = self.editor.toHtml()

            logger.debug(f"BasicTextEditor content marked as saved.")

        except Exception as e:
            logger.warning(f"Failed to Mark the Text Editor as saved: {e}", exc_info=True)
            QMessageBox.warning(self, "Mark Save Error", "Failed to Mark Saved due to a UI issue.")


    # --- Public Accessors for Content ---

    def get_html_content(self) -> str:
        """
        Returns the editor's content as Rich Text HTML.
        
        :rtype: str
        """
        content = self.editor.toHtml()
        logger.debug(f"Retrieving HTML content. Length: {len(content)} bytes.") 
        return content

    def set_html_content(self, html_content: str) -> None:
        """
        Sets the editor's content from Rich Text HTML and marks the content as clean.
        
        The textChanged signal is temporarily blocked to prevent setting the dirty flag.

        :param html_content: The html content that is being set in the editor
        :type html_content: str

        :rtype: None
        """
        if not isinstance(html_content, str):
            logger.error(f"FATAL: set_html_content received non-string content of type: {type(html_content)}.")
            raise TypeError("Editor content must be a string (HTML or plain text).")

        try:
            # Block signals to prevent _set_dirty from firing during load
            self.editor.blockSignals(True) 
            self.editor.setHtml(html_content)
            self.editor.blockSignals(False) 
            # Manually reset the dirty state after a successful load
            self.mark_saved()
            logger.debug(f"BasicTextEditor content set and marked clean. Content length: {len(html_content)} bytes.")
        except Exception as e:
            # Catch any underlying QWidget/PyQt error and re-raise it as EditorContentError
            logger.error(f"FATAL: Failed to set HTML content in BasicTextEditor.", exc_info=True)
            raise EditorContentError("Failed to display content in the editor due to an internal error.") from e

    def get_plain_text(self) -> str:
        """
        Returns the editor's content as plain text.
        
        :rtype: None
        """
        return self.editor.toPlainText()
    
    def get_selected_text(self) -> str:
        """
        Returns the currently selected plain text.
        
        :rtype: None
        """
        selected_text = self.editor.textCursor().selectedText()
        logger.debug(f"Retrieving Selected Text content. Length: {len(selected_text)} characters.")
        return selected_text

    def _on_selection_changed(self) -> None:
        """
        Handles selection changes by logging and publishing to the event bus.
        
        :rttype: None
        """
        if self.editor.textCursor().hasSelection():
            logger.debug("Text selection changed (active selection).")
        else:
            logger.debug("Cursor position changed (no active selection).")

        self.selection_changed.emit()

        bus.publish(Events.SELECTION_CHANGED, data={
            'editor': self,
            'selected_text': self.get_selected_text(),
        })
        