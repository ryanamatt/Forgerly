# src/python/ui/chapter_editor.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QSplitter, QHBoxLayout,
    QLineEdit, QLabel
)
from PySide6.QtCore import Qt

from .base_editor import BaseEditor
from ...ui.widgets.rich_text_editor import RichTextEditor
from ...utils.text_stats import calculate_word_count, calculate_character_count, calculate_read_time
from ...utils.constants import EntityType
from ...utils.events import Events
from ...utils.event_bus import bus, receiver

class ChapterEditor(BaseEditor):
    """
    A composite :py:class:`PySide6.QtWidgets.QWidget` that serves as the main 
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
    """

    current_chapter_id: int | None = None
    """The database ID of the Chapter currently loaded in the editor, int or None."""
    
    def __init__(self, current_settings: dict, parent=None) -> None:
        """
        Initializes the ChapterEditor with sub-components and layout.

        :param current_settings: A dictionary containing initial application settings, 
                                 including 'words_per_minute'.
        :type current_settings: dict
        :param parent: The parent widget. Defaults to ``None``.
        :type parent: :py:class:`PySide6.QtWidgets.QWidget`, optional

        :rtype: None
        """
        super().__init__(parent)

        bus.register_instance(self)

        self.current_settings = current_settings
        self.wpm = current_settings.get('words_per_minute')
        self.is_showing_stats = current_settings.get('is_showing_chapter_stats', 'FAILED')

        self.current_lookup_dialog = None

        # --- Sub-components ---
        self.text_editor = RichTextEditor(self.current_settings)
        
        # --- Statistics Labels ---
        self.word_count_label = QLabel("Words: 0")
        self.char_count_label = QLabel("Chars: 0")
        self.read_time_label = QLabel(f"Read Time: 0 min (WPM: {self.wpm})")

        # --- Layout ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Title of Chapter Box
        title_group = QWidget()
        title_layout = QHBoxLayout(title_group)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter Chapter Title (e.g., 'Chapter 1: The Sunset)")
        title_label = QLabel("Title:")
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_input)

        # Tagging Group Box
        tag_group = QGroupBox("Chapter Tags (Genres, Themes, POVs)")
        tag_group.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tag_layout = QVBoxLayout(tag_group)
        tag_layout.setContentsMargins(10, 20, 10, 10)
        tag_layout.addWidget(self.tag_manager)
                
        # Statistics Bar at the bottom of everything but on top of RichTextEditor
        self.stats_bar = QWidget()
        stats_layout = QHBoxLayout(self.stats_bar)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.addStretch()
        stats_layout.addWidget(self.word_count_label)
        stats_layout.addWidget(self.char_count_label)
        stats_layout.addWidget(self.read_time_label)
        stats_layout.addStretch() # Push stats to the left
        self.stats_bar.setVisible(self.is_showing_stats)
        
        # Combine the editor and the stats bar
        editor_group = QWidget()
        editor_vbox = QVBoxLayout(editor_group)
        editor_vbox.setContentsMargins(0, 0, 0, 0)
        editor_vbox.addWidget(self.stats_bar)
        editor_vbox.addWidget(self.text_editor)
        
        editor_splitter = QSplitter(Qt.Orientation.Vertical)
        editor_splitter.addWidget(title_group)
        editor_splitter.addWidget(tag_group) # Use the new group containing stats bar
        editor_splitter.addWidget(editor_group)
        editor_splitter.setSizes([100, 100, 800]) 

        # Add the splitter to the main layout
        main_layout.addWidget(editor_splitter)

        self.setEnabled(False)

        self.title_input.textChanged.connect(self._set_dirty)
        self.title_input.editingFinished.connect(self._emit_title_change)

    @receiver(Events.CONTENT_CHANGED)
    @receiver(Events.SELECTION_CHANGED)
    def _update_stats_display(self, data: dict) -> None:
        """
        Calculates and updates the real-time statistics labels based on 
        the selected text or the full content if no text is selected.

        :param data: The data emiited by the Event in the EventBus.
        :type data: dict

        :rtype: None
        """
        editor = data.get('editor')
        if editor != self.text_editor:
            return # Ensure we are getting our own Text Editor

        # Check for selected text first
        selected_text = data.get('selected_text')
        
        if selected_text:
            # Stats for SELECTED text
            source_text = selected_text
            label_prefix = "Selected"
        else:
            # Stats for FULL document
            source_text = self.text_editor.get_plain_text()
            label_prefix = "Total"

        # Calculate statistics
        word_count = calculate_word_count(source_text)
        char_count_with_spaces = calculate_character_count(source_text, include_spaces=True)
        read_time_str = calculate_read_time(int(word_count), int(self.wpm))

        # Update UI Labels with dynamic prefix
        self.word_count_label.setText(f"{label_prefix} Words: {word_count:,}")
        self.char_count_label.setText(f"{label_prefix} Chars: {char_count_with_spaces:,}")
        self.read_time_label.setText(f"Read Time: {read_time_str} (WPM: {self.wpm})")

    @receiver(Events.WPM_CHANGED)
    def set_wpm(self, data: dict) -> None:
        """
        Updates the WPM setting and recalculates the statistics display.
        
        :param dict: Containing The new WPM number to set. Will default to 250 if <= 0.
            {'new_wpm': int}
        :type data: dict

        :rtype: None
        """
        new_wpm = data.get('new_wpm', 250)

        self.wpm = new_wpm
        self._update_stats_display({'editor': self.text_editor})

    @receiver(Events.IS_SHOWING_CHAP_STATS_CHANGED)
    def set_chapter_stats_visibility(self, data: dict) -> None:
        """
        Catches the Change in the visibilty of the Chapter Stats Change and updates
        the Chapter Stats Visibility.

        :param data: A dict containing {'is_showing_chapter_stats': bool}
        :type data: dict
        :rtype: None
        """
        is_showing = data.get('is_showing_chapter_stats', True)
        self.stats_bar.setVisible(is_showing)

    @receiver(Events.MARK_SAVED)
    def mark_saved_connection(self, data: dict) -> None:
        """
        A connection for the mark saved Event.
        
        :param data: Data dictionary, Empty as function doesn't need it.
        :type data: dict

        :rtype: None
        """
        if data.get('entity_type') != EntityType.CHAPTER:
            return
        
        self.mark_saved()
        
    # --- Content Passthrough Methods (RichTextEditor) ---

    def get_html_content(self) -> str:
        """
        Returns the current rich text content as an HTML string.

        :returns: The chapter content as HTML.
        :rtype: str
        """
        return self.text_editor.get_html_content()

    def set_html_content(self, html_content: str) -> None:
        """
        Sets the rich text content and triggers a statistics update.

        :param html_content: The HTML content string to load into the editor.
        :type html_content: str

        :rtype: None
        """
        self.text_editor.set_html_content(html_content)
        self._update_stats_display()

    def get_save_data(self) -> dict:
        """
        Returns all the current saved data.

        :rtype: dict
        """
        return {
            'ID': self.current_chapter_id,
            'title': self.title_input.text(),
            'content': self.text_editor.get_html_content(),
            'tags': self.tag_manager.get_tags()
        }
    
    @receiver(Events.SAVE_REQUESTED)
    def provide_data_for_save(self, data: dict) -> None:
        """
        If this editor is dirty, it sends its current content back to the coordinator.

        :param data: The data of the save data.
        :type data: dict

        :rtype: None
        """
        if not self.is_dirty():
            return
        
        if data.get('entity_type') != EntityType.CHAPTER:
            return

        save_data = self.get_save_data()
        data |= save_data
        data.update({'parent': self})

        bus.publish(Events.SAVE_DATA_PROVIDED, data=data)
    
    @receiver(Events.DATA_LOADED)
    def load_entity(self, data: dict) -> None:
        """
        Loads all the information into the editor and enables the editor.
        
        :param data: A dictionary with all Chapter data.
        :type data: dict

        :rtype: None
        """
        if data.get('entity_type') != EntityType.CHAPTER:
            return
        
        self.current_chapter_id = data.get('ID')
        if not self.current_chapter_id:
            return

        self.title_input.setText((data.get('title')))
        self.tag_manager.set_tags(data.get('tags'))
        self.text_editor.set_html_content(data.get('content'))

        self.mark_saved()
        self.set_enabled(True)

    def is_dirty(self) -> bool:
        """
        Returns the dirty flag to see if the editor is dirty.
        
        :returns: True if changes are detected, False otherwise.
        :rtype: bool
        """
        return self._dirty or super().is_dirty()
    
    def _set_dirty(self) -> None:
        """
        Sets the dirty flag to be True.
        
        :rtype: None
        """
        if not self.current_chapter_id:
            return False
        
        self._dirty = True

    def mark_saved(self) -> None:
        """
        Marks all nested components as clean.
        
        :rtype: None
        """
        # # self.text_editor and self.tag_manager
        super().mark_saved()

        self._dirty = False
        
        
    def set_enabled(self, enabled: bool) -> None:
        """
        Enables/disables the entire editor panel.
        
        :param enabled: True if want to enable editor panel, otherwise False
        :type enabled: bool
        
        :rtype: None
        """
        # self.text_editor and self.tag_manager
        super().set_enabled(enabled)

        self.title_input.setEnabled(enabled)

    def _emit_title_change(self) -> None:
        """
        Emits the signal to update the outline after the user finishes editing the title.
        
        :rtype: None
        """
        if self.current_chapter_id is not None:
            bus.publish(Events.OUTLINE_NAME_CHANGE, data={
                'entity_type': EntityType.CHAPTER,
                'ID': self.current_chapter_id,
                'new_title': self.title_input.text().strip(),
            })