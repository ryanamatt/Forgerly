# src/python/ui/chapter_editor.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QSplitter, QHBoxLayout, QTextEdit,
    QDialog, QSizePolicy, QLabel
)
from PySide6.QtCore import Qt

from .base_editor import BaseEditor
from ...ui.widgets.rich_text_editor import RichTextEditor
from ...utils.nf_core_wrapper import calculate_word_count, calculate_character_count, calculate_read_time
from ...utils.constants import EntityType
from ...utils.events import Events
from ...utils.event_bus import bus, receiver

class ChapterEditor(BaseEditor):
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
    """
    
    def __init__(self, current_settings, parent=None) -> None:
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

        bus.register_instance(self)

        self.current_settings = current_settings
        self.wpm = current_settings['words_per_minute']

        self.current_lookup_dialog = None

        # --- Sub-components ---
        self.text_editor = RichTextEditor()
        
        # --- Statistics Labels ---
        self.word_count_label = QLabel("Words: 0")
        self.char_count_label = QLabel("Chars: 0")
        self.read_time_label = QLabel(f"Read Time: 0 min (WPM: {self.wpm})")

        # --- Layout ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 1. Tagging Group Box
        tag_group = QGroupBox("Chapter Tags (Genres, Themes, POVs)")
        tag_group.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tag_layout = QVBoxLayout(tag_group)
        tag_layout.setContentsMargins(10, 20, 10, 10)
        tag_layout.addWidget(self.tag_manager)
        
        # 2. Editor and Stats (Modified Layout)
        
        # Statistics Bar at the bottom of everything but on top of RichTextEditor
        stats_bar = QWidget()
        stats_layout = QHBoxLayout(stats_bar)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.addStretch()
        stats_layout.addWidget(self.word_count_label)
        stats_layout.addWidget(self.char_count_label)
        stats_layout.addWidget(self.read_time_label)
        stats_layout.addStretch() # Push stats to the left
        
        # Combine the editor and the stats bar
        editor_group = QWidget()
        editor_vbox = QVBoxLayout(editor_group)
        editor_vbox.setContentsMargins(0, 0, 0, 0)
        editor_vbox.addWidget(stats_bar)
        editor_vbox.addWidget(self.text_editor)
        
        editor_splitter = QSplitter(Qt.Orientation.Vertical)
        editor_splitter.addWidget(tag_group) # Use the new group containing stats bar
        editor_splitter.addWidget(editor_group)
        editor_splitter.setSizes([100, 900]) 

        # Add the splitter to the main layout
        main_layout.addWidget(editor_splitter)

        self.setEnabled(False)

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
        read_time_str = calculate_read_time(word_count, self.wpm)

        # Update UI Labels with dynamic prefix
        self.word_count_label.setText(f"{label_prefix} Words: {word_count:,}")
        self.char_count_label.setText(f"{label_prefix} Chars: {char_count_with_spaces:,}")
        self.read_time_label.setText(f"Read Time: {read_time_str} (WPM: {self.wpm})")

    @receiver(Events.WPM_CHANGED)
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
        self._update_stats_display()

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

    @receiver(Events.LOOKUP_RESULT)
    def display_lookup_result(self, data: dict) -> None:
        """
        Creates and displays a small, modal dialog containing the content of the linked entity.
        
        :param data: The data needed contains {type: EntityType, title: str, content: str}

        :rtype: None
        """
        entity_type = data.get('type')
        title = data.get('title')
        content = data.get('content')

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
        
        dialog.show()

    def get_save_data(self) -> dict:
        """
        Returns all the current saved data.

        :rtype: dict
        """
        return {
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

        self.text_editor.set_html_content(data['content'])
        self.tag_manager.set_tags(data['tags'])

        self.mark_saved()
        self.set_enabled(True)