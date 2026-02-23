# src/python/ui/note_editor.py

from PySide6.QtWidgets import (
    QVBoxLayout, QGroupBox, QSplitter, QLineEdit, QWidget, QHBoxLayout, QLabel
)
from PySide6.QtCore import Qt

from .base_editor import BaseEditor
from ...ui.widgets.rich_text_editor import RichTextEditor
from ...utils.constants import EntityType
from ...utils.events import Events
from ...utils.event_bus import bus, receiver

class NoteEditor(BaseEditor):
    """
    A composite :py:class:`PySide6.QtWidgets.QWidget` that serves as the main 
    editing panel for a note.

    It combines a :py:class:`~.BasicTextEditor` for content and a 
    :py:class:`~.TagManagerWidget` for metadata. This widget manages the 
    state (dirty flags) and provides a single interface for the MainWindow 
    to load and save all note data (content, tags).

    :ivar basic_text_editor: The basic text editor component.
    :vartype basic_text_editor: BasicTextEditor
    :ivar tag_manager: The tag management component.
    :vartype tag_manager: TagManagerWidget
    """

    current_note_id: int | None = None
    """The database ID of the Note currently loaded in the editor, int or None."""
    
    def __init__(self, current_settings, parent=None) -> None:
        """
        Initializes the NoteEditor with sub-components and layout.

        :param current_settings: A dictionary containing initial application settings.
        :type current_settings: dict
        :param parent: The parent widget. Defaults to ``None``.
        :type parent: :py:class:`PySide6.QtWidgets.QWidget`, optional

        :rtype: None
        """
        super().__init__(parent)
        self.current_settings = current_settings

        self.current_lookup_dialog = None

        # --- Sub-components ---
        self.text_editor = RichTextEditor(current_settings)

        # --- Layout ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Title group
        title_group = QWidget()
        title_layout = QHBoxLayout(title_group)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter Note Title (e.g., 'Outline, Story Idea)")
        title_label = QLabel("Title:")
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_input)

        # Tagging Group Box
        tag_group = QGroupBox("Note Tags (Genres, Themes, POVs)")
        tag_group.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tag_layout = QVBoxLayout(tag_group)
        tag_layout.setContentsMargins(10, 20, 10, 10)
        tag_layout.addWidget(self.tag_manager)

        # Splitter
        editor_splitter = QSplitter(Qt.Orientation.Vertical)
        editor_splitter.addWidget(title_group)
        editor_splitter.addWidget(tag_group)
        editor_splitter.addWidget(self.text_editor)
        editor_splitter.setSizes([100, 100, 800]) 

        main_layout.addWidget(editor_splitter)

        self.setEnabled(False)

        self.title_input.textChanged.connect(self._set_dirty)
        self.title_input.editingFinished.connect(self._emit_title_change)

    @receiver(Events.MARK_SAVED)
    def mark_saved_connection(self, data: dict) -> None:
        """
        A connection for the mark saved Event.
        
        :param data: Data dictionary, Empty as function doesn't need it.
        :type data: dict

        :rtype: None
        """
        if data.get('entity_type') != EntityType.NOTE:
            return
        
        self.mark_saved()
        
    # --- Content Passthrough Methods (RichTextEditor) ---

    def get_html_content(self) -> str:
        """
        Returns the current rich text content as an HTML string.

        :returns: The note content as HTML.
        :rtype: str
        """
        return self.text_editor.get_html_content()

    def set_html_content(self, html_content: str) -> None:
        """
        Sets the rich text content.

        :param html_content: The HTML content string to load into the editor.
        :type html_content: str

        :rtype: None
        """
        self.text_editor.set_html_content(html_content)

    def get_save_data(self) -> dict:
        """
        Returns all the current saved data.
        
        :returns: A dictionary of the current lore entry data.
        :rtype: dict
        """
        return {
            'ID': self.current_note_id,
            'title': self.title_input.text(),
            'content': self.text_editor.get_html_content(),
            'tags': self.tag_manager.get_tags()
        }
    
    @receiver(Events.SAVE_REQUESTED)
    def provide_data_for_save(self, data: dict):
        """
        If this editor is dirty, it sends its current content back to the coordinator.

        :param data: The data of the save data.
        :type data: dict

        :rtype: None
        """
        if not self.is_dirty():
            return
        
        if data.get('entity_type') != EntityType.NOTE:
            return

        save_data = self.get_save_data()
        data |= save_data
        data.update({'parent': self})

        bus.publish(Events.SAVE_DATA_PROVIDED, data=data)
    
    @receiver(Events.DATA_LOADED)
    def load_entity(self, data: dict) -> None:
        """
        Loads all the information into the editor
        
        param data: A dict with all Note Data.
        :type data: dict

        :rtype: None
        """
        if data.get('entity_type') != EntityType.NOTE:
            return
        
        self.current_note_id = data.get('ID')
        if not self.current_note_id:
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
        if not self.current_note_id:
            return False
        
        self._dirty = True

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
        if self.current_note_id is not None:
            bus.publish(Events.OUTLINE_NAME_CHANGE, data={
                'entity_type': EntityType.NOTE,
                'ID': self.current_note_id,
                'new_title': self.title_input.text().strip(),
            })