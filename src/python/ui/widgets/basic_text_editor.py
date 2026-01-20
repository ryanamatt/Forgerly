# src/python/basic_text_editor.py

from PySide6.QtWidgets import (
    QTextEdit, QWidget, QVBoxLayout, QMessageBox
)
from PySide6.QtGui import QTextCharFormat, QTextCursor, QColor, QAction
from PySide6.QtCore import QTimer, Qt, QPoint
import re

from ...utils.spell_checker import get_spell_checker
from ...utils.logger import get_logger
from ...utils.exceptions import EditorContentError
from ...utils.events import Events
from ...utils.event_bus import bus, receiver

logger = get_logger(__name__)

class BasicTextEditor(QWidget):
    """
    A composite :py:class:`~PySide6.QtWidgets.QWidget` that serves as a basic
    text editing widget.

    The Widget contains a text editing editor with basic signals for saving
    content and notifying whethe the editor is dirty. This class also contains 
    public access functions to get the text contained in the editor.
    """

    def __init__(self, parent=None) -> None:
        """
        Initializes the BasicTextEditor and connects its signals

        :param parent: The parent widget. Defaults to ``None``.
        :type parent: :py:class:`PySide6.QtWidgets.QWidget`
        :rtype: None
        """
        super().__init__(parent)

        logger.debug("Initializing BasicTextEditor widget.")

        bus.register_instance(self)

        self.spell_checker = get_spell_checker()
        self.spell_check_timer = QTimer(self)
        self.spell_check_timer.setSingleShot(True)
        self.spell_check_timer.setInterval(2500) # 2.5 Seconds
        self.spell_check_timer.timeout.connect(self.run_spell_check)

        # State tracking for unsaved changes
        self._is_dirty = False
        self._last_saved_content = ""

        # Core component
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Start writing here")
        self.editor.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.editor.customContextMenuRequested.connect(self._show_context_menu)
        
        # Layout setup (similar to your original RichTextEditor setup)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.editor)

        # Connect signals for dirty flag and content change notification
        self.editor.textChanged.connect(self._text_changed)
        self.editor.selectionChanged.connect(self._on_selection_changed)

    # --- Events ---
    
    def _show_context_menu(self, position: QPoint) -> None:
        """
        Shows the context menu.

        :param position: The position of the place to show the menu.
        :type positon: QPoint
        :rtype: None
        """
        # Create the standard context menu
        menu = self.editor.createStandardContextMenu()
        
        # Get the cursor at the position of the right-click
        cursor = self.editor.cursorForPosition(position)
        cursor.select(QTextCursor.WordUnderCursor)
        word = cursor.selectedText().strip()

        # Check if the word is alphabetic and misspelled
        if word and word.isalpha() and not self.spell_checker.is_correct(word):
            suggestions = self.spell_checker.get_suggestions(word)
            
            if suggestions:
                menu.addSeparator()
                suggestion_menu = menu.addMenu(f"Suggestions for '{word}'")
                
                for suggestion in suggestions:
                    suggested_word = suggestion['word']
                    # Apply capitalization to the suggestion if needed
                    display_word = self._apply_casing(word, suggested_word)

                    action = QAction(suggested_word, self)
                    action.triggered.connect(
                        lambda checked=False, w=display_word, c=cursor: self._replace_word(c, w)
                    )
                    suggestion_menu.addAction(action)
            else:
                menu.addSeparator()
                menu.addAction("No suggestions found").setEnabled(False)

        # Show the menu
        menu.exec(self.editor.mapToGlobal(position))

    def _apply_casing(self, original: str, suggestion: str) -> str:
        """
        Adjusts the suggestion string to match the casing of the original word.
        Handles ALL CAPS, Title Case, and lowercase.

        :param original: The original word.
        :type original: str
        :param suggestion: The suggestion word to apply casing to.
        :type suggestion: str
        :returns: The suggested word with correct casing.
        :rtype: str
        """
        if not original:
            return suggestion

        # Case 1: ALL CAPS (e.g., "TEH" -> "THE")
        if original.isupper():
            return suggestion.upper()

        # Case 2: Title Case (e.g., "Teh" -> "The")
        if original[0].isupper():
            return suggestion.capitalize()

        # Case 3: Default lowercase (e.g., "teh" -> "the")
        return suggestion.lower()

    def _replace_word(self, cursor: QTextCursor, new_word: str) -> None:
        """
        Replaces the misspelled word with the selected suggestion.

        :param cursor: The cursor in the text editor.
        :type cursor: QTextCursor.
        :param new_word: The new_word to replace the misspelled word.
        :type new_word: str
        :rtype: None
        """
        cursor.beginEditBlock()
        cursor.insertText(new_word)
        cursor.endEditBlock()
        # Trigger a re-check to clear the red underline immediately
        self.run_spell_check()

    def _text_changed(self) -> None:
        """
        Handles when the text is changed. Emitted the correct signals.
        
        :rtype: None
        """
        self._set_dirty()
        self.spell_check_timer.start()

    # --- Dirty Flag Management ---

    def _set_dirty(self) -> None:
        """
        Sets the dirty flag when the text content changes.
        
        :rtype: None
        """
        if not self._is_dirty:
            self._is_dirty = True

            # KEEP EMITTING SIGNAL TILL EVERYTHING IS IN EVENT BUS
            # self.content_changed.emit()

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

    def run_spell_check(self) -> None:
        """
        Runs the Spell Checking and underlines the in correct word.
        
        :rtype: None
        """
        # Prevent the textChanged signal from firing while we apply formatting
        self.editor.blockSignals(True)
        original_cursor = self.editor.textCursor()
        
        # Define the 'Error' format (Red wavy underline)
        error_format = QTextCharFormat()
        error_format.setUnderlineColor(QColor("red"))
        error_format.setUnderlineStyle(QTextCharFormat.WaveUnderline)
        
        clear_underline_format = QTextCharFormat()
        clear_underline_format.setUnderlineStyle(QTextCharFormat.NoUnderline)

        # Clear ONLY the underlines across the whole document
        cursor = self.editor.textCursor()
        cursor.beginEditBlock() # Group as one undo operation
        cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)

        # Use mergeCharFormat to preserve colors/bold/etc.
        cursor.mergeCharFormat(clear_underline_format) 

        # Apply red underlines to misspelled words
        text = self.editor.toPlainText()
        for match in re.finditer(r"\b[A-Za-z']+\b", text):
            word = match.group()
            word = word.replace("'", "")
            if not self.spell_checker.is_correct(word):
                cursor.setPosition(match.start())
                cursor.setPosition(match.end(), QTextCursor.KeepAnchor)
                # Again, use mergeCharFormat to only add the red wavy line
                cursor.mergeCharFormat(error_format)

        cursor.endEditBlock()
        self.editor.setTextCursor(original_cursor)
        self.editor.blockSignals(False)

    @receiver(Events.LOOKUP_REQUESTED)
    def _send_lookup_text(self, data: dict = None) -> None:
        """
        Called when Selected Text is Pushed in MainMenuBar
        
        :param data: The data, Empty dict
        :type data: dict
        :rtype: None
        """
        selected_text = self.get_selected_text().strip()

        bus.publish(Events.PERFORM_DATABASE_LOOKUP, data={'selected_text': selected_text})

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
            logger.error(f"FATAL: set_html_content received non-string content of type: "
                         f"{type(html_content)}.")
            raise TypeError("Editor content must be a string (HTML or plain text).")

        try:
            # Block signals to prevent _set_dirty from firing during load
            self.editor.blockSignals(True) 
            self.editor.setHtml(html_content)
            self.editor.blockSignals(False) 
            # Manually reset the dirty state after a successful load
            self.mark_saved()
            logger.debug(f"BasicTextEditor content set and marked clean. Content length: "
                         "{len(html_content)} bytes.")
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

        bus.publish(Events.SELECTION_CHANGED, data={
            'editor': self,
            'selected_text': self.get_selected_text(),
        })
        