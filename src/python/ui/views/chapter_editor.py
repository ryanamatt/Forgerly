# src/python/ui/chapter_editor.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QSplitter, QHBoxLayout, QTextEdit,
    QDialog, QSizePolicy, QLabel
)
from PyQt6.QtCore import Qt

from ...services.app_coordinator import AppCoordinator
from ...ui.widgets.tag_widget import TagManagerWidget
from ...ui.widgets.rich_text_editor import RichTextEditor

def calculate_word_count(text: str) -> int:
    """
    Calculates the word count of the plain text content.

    Words are counted by splitting the text using various whitespace separators.

    :param text: The plain text content string.
    :type text: str

    :returns: The calculated number of words.
    :rtype: int
    """
    # Use split() without arguments to handle various whitespace separators
    words = text.split()
    return len(words)

def calculate_character_count(text: str, include_spaces: bool = True) -> int:
    """
    Calculates the character count of the plain text content.

    :param text: The plain text content string.
    :type text: str
    :param include_spaces: If ``True`` (default), spaces and all other whitespace 
                           characters are included in the count. If ``False``, 
                           all whitespace is excluded.
    :type include_spaces: bool

    :returns: The calculated number of characters.
    :rtype: int
    """
    if include_spaces:
        return len(text)
    else:
        return len("".join(text.split())) # Counts characters excluding all whitespace

def calculate_read_time(word_count: int, wpm: int = 250) -> str:
    """
    Calculates the estimated read time based on word count and words-per-minute (WPM).

    The time is rounded up to the nearest whole minute and formatted as 'X min'.
    Uses a default WPM of 250 if not specified.

    :param word_count: The total number of words in the text.
    :type word_count: int
    :param wpm: The assumed reading speed in words per minute. Must be greater than 0.
    :type wpm: int

    :returns: A formatted string for the estimated read time (e.g., '5 min', '<1 min', '0 min').
    :rtype: str
    """
    if wpm <= 0 or word_count == 0:
        return "0 min"
    
    # Calculate time in minutes (round up to nearest whole minute)
    minutes = (word_count + wpm - 1) // wpm # Integer division equivalent of ceil(word_count / wpm)
    
    # Handle hours/minutes if needed, but for simplicity, stick to minutes
    if minutes == 0:
        # If words > 0 but time is less than 1 min, show '<1 min'
        return "<1 min" if word_count > 0 else "0 min"
    
    return f"{minutes} min"

class ChapterEditor(QWidget):
    """
    A composite :py:class:`PyQt6.QtWidgets.QWidget` that serves as the main 
    editing panel for a chapter.

    It combines a :py:class:`~.RichTextEditor` for content and a 
    :py:class:`~.TagManagerWidget` for metadata. This widget manages the 
    state (dirty flags) and provides a single interface for the MainWindow 
    to load and save all chapter data (content, tags, and statistics).

    The editor displays real-time statistics (word count, character count, 
    and estimated read time) for either the **full document** or the 
    **currently selected text**.

    :ivar rich_text_editor: The rich text editor component.
    :vartype rich_text_editor: RichTextEditor
    :ivar tag_manager: The tag management component.
    :vartype tag_manager: TagManagerWidget
    :ivar wpm: The words-per-minute setting used for read time calculation.
    :vartype wpm: int
    """
    
    def __init__(self, current_settings, coordinator: AppCoordinator, parent=None) -> None:
        """
        Initializes the ChapterEditor with sub-components and layout.

        :param current_settings: A dictionary containing initial application settings, 
                                 including 'words_per_minute'.
        :type current_settings: dict
        :param parent: The parent widget. Defaults to ``None``.
        :type parent: :py:class:`PyQt6.QtWidgets.QWidget`, optional

        :rtype: None
        """
        super().__init__(parent)
        self.current_settings = current_settings
        self.coordinator = coordinator
        self.wpm = current_settings['words_per_minute']

        self.current_lookup_dialog = None

        # --- Sub-components ---
        self.rich_text_editor = RichTextEditor()
        self.tag_manager = TagManagerWidget()
        
        # --- Statistics Labels (New Components) ---
        self.word_count_label = QLabel("Words: 0")
        self.char_count_label = QLabel("Chars: 0")
        self.read_time_label = QLabel(f"Read Time: 0 min (WPM: {self.wpm})")

        # --- Layout ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 1. Tagging Group Box (Existing Code)
        tag_group = QGroupBox("Chapter Tags (Genres, Themes, POVs)")
        tag_layout = QVBoxLayout(tag_group)
        tag_layout.setContentsMargins(10, 20, 10, 10)
        tag_layout.addWidget(self.tag_manager)
        
        # 2. Editor and Stats (Modified Layout)
        
        # Statistics Bar at the bottom of the editor
        stats_bar = QWidget()
        stats_layout = QHBoxLayout(stats_bar)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.addWidget(self.word_count_label)
        stats_layout.addWidget(self.char_count_label)
        stats_layout.addWidget(self.read_time_label)
        stats_layout.addStretch() # Push stats to the left
        
        # Combine the editor and the stats bar
        editor_group = QWidget()
        editor_vbox = QVBoxLayout(editor_group)
        editor_vbox.setContentsMargins(0, 0, 0, 0)
        editor_vbox.addWidget(stats_bar)
        editor_vbox.addWidget(self.rich_text_editor)
        
        editor_splitter = QSplitter(Qt.Orientation.Vertical)
        editor_splitter.addWidget(tag_group) # Use the new group containing stats bar
        editor_splitter.addWidget(editor_group)
        editor_splitter.setSizes([100, 900]) 

        # Add the splitter to the main layout
        main_layout.addWidget(editor_splitter)

        # --- Signal Connections ---
        self.rich_text_editor.content_changed.connect(self._update_stats_display)
        self.rich_text_editor.selection_changed.connect(self._update_stats_display)
        self.rich_text_editor.popup_lookup_requested.connect(self._handle_popup_lookup_request)

    def _update_stats_display(self) -> None:
        """
        Calculates and updates the real-time statistics labels based on 
        the selected text or the full content if no text is selected.

        This method is connected to the :py:attr:`~.RichTextEditor.content_changed`
        and :py:attr:`~.RichTextEditor.selection_changed` signals.

        :rtype: None
        """
        # 1. Check for selected text first
        selected_text = self.rich_text_editor.get_selected_text()
        
        if selected_text:
            # Stats for SELECTED text
            source_text = selected_text
            label_prefix = "Selected"
        else:
            # Stats for FULL document
            source_text = self.rich_text_editor.get_plain_text()
            label_prefix = "Total"

        # 2. Calculate statistics
        word_count = calculate_word_count(source_text)
        char_count_with_spaces = calculate_character_count(source_text, include_spaces=True)
        read_time_str = calculate_read_time(word_count, self.wpm)

        # 3. Update UI Labels with dynamic prefix
        self.word_count_label.setText(f"{label_prefix} Words: {word_count:,}")
        self.char_count_label.setText(f"{label_prefix} Chars: {char_count_with_spaces:,}")
        self.read_time_label.setText(f"Read Time: {read_time_str} (WPM: {self.wpm})")

    def set_wpm(self, new_wpm: int) -> None:
        """
        Updates the WPM setting and recalculates the statistics display.
        
        :param new_wpm: The new WPM number to set. Will default to 250 if <= 0.
        :type new_wpm: int

        :rtype: None
        """
        if new_wpm <= 0:
            new_wpm = 250
        self.wpm = new_wpm
        self._update_stats_display

    def _handle_tag_change(self):
        """
        Sets the rich text editor's dirty flag when tags are modified.

        (Currently commented out as signal name is hypothetical)

        :rtype: None
        """
        self.rich_text_editor._set_dirty()
        
    # --- Content Passthrough Methods (RichTextEditor) ---
    
    def is_dirty(self) -> bool:
        """
        Checks if the content (RichTextEditor) or the tags (TagManagerWidget) 
        have unsaved changes.

        :returns: ``True`` if content or tags are modified, ``False`` otherwise.
        :rtype: bool
        """
        return self.rich_text_editor.is_dirty() or self.tag_manager.is_dirty()

    def mark_saved(self) -> None:
        """
        Marks both the rich text content and the tags as clean (saved).

        :rtype: None
        """
        self.rich_text_editor.mark_saved()
        self.tag_manager.mark_saved()
        
    def set_enabled(self, enabled: bool) -> None:
        """
        Enables or disables the entire chapter editor panel by setting the 
        state of its main sub-components.

        :param enabled: ``True`` to enable, ``False`` to disable.
        :type enabled: bool

        :rtype: None
        """
        self.rich_text_editor.setEnabled(enabled)
        self.tag_manager.setEnabled(enabled)

    def get_html_content(self) -> str:
        """
        Returns the current rich text content as an HTML string.

        :returns: The chapter content as HTML.
        :rtype: str
        """
        return self.rich_text_editor.get_html_content()

    def set_html_content(self, html_content: str) -> None:
        """
        Sets the rich text content and triggers a statistics update.

        :param html_content: The HTML content string to load into the editor.
        :type html_content: str

        :rtype: None
        """
        self.rich_text_editor.set_html_content(html_content)
        self._update_stats_display()

    def _handle_popup_lookup_request(self, text_to_lookup: str) -> None:
        """
        Receives the lookup request from the editor, queries the AppCoordinator, 
        and displays the result in a modal pop-up window.

        :param text_to_lookup: The text to lookup.
        :type text_to_lookup: str

        :rtype: None
        """
        result = self.coordinator.lookup_entity_content_by_name(text_to_lookup)
        if result:
            entity_type, title, content = result
            self._show_lookup_popup(entity_type, title, content)
        else:
            # TODO Make Simple Message Saying Nothing FOund
            print(f"Lookup failed: No entity found matching '{text_to_lookup}'")

    def _show_lookup_popup(self, entity_type: str, title: str, content: str) -> None:
        """
        Creates and displays a small, modal dialog containing the content of the linked entity.
        
        :param entity_type: The type of entity to that was found while looking up.
        :type entity_type: str
        :param title: The title of the entity that was found.
        :type title: str
        :param content: The content/description of the entity that was found.
        :type content: str

        :rtype: None
        """
        # 1. Close the old dialog if it's still open
        if self.current_lookup_dialog is not None:
            self.current_lookup_dialog.close()
            
        dialog = QDialog(self)
        
        # 2. Store the new dialog reference
        self.current_lookup_dialog = dialog
        
        # --- Existing UI Setup (no change here) ---
        dialog.setWindowTitle(f"Information: {title} ({entity_type})")
        dialog.setMinimumSize(450, 350) 
        
        layout = QVBoxLayout(dialog)
        
        title_label = QLabel(f"**{title}** ({entity_type})")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title_label)
        
        content_viewer = QTextEdit()
        content_viewer.setReadOnly(True)
        content_viewer.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        content_viewer.setHtml(content)
        content_viewer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(content_viewer)
        
        # --- KEY CHANGE: Use .show() instead of .exec() ---
        dialog.show()

    # --- Tagging Passthrough Methods (TagManagerWidget) ---
    
    def get_tags(self) -> list[str]:
        """
        Returns the current list of tag names entered in the tag manager.

        :returns: A list of tag names (strings).
        :rtype: list[str]
        """
        return self.tag_manager.get_tags()

    def set_tags(self, tag_names: list[str]) -> None:
        """
        Sets the tags when a chapter is loaded.

        This function also clears the tag manager's dirty state internally.

        :param tag_names: A list of tag names (strings) to set.
        :type tag_names: list[str]
        """
        self.tag_manager.set_tags(tag_names)

