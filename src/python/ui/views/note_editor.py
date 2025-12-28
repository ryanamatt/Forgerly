# src/python/ui/note_editor.py

from PySide6.QtWidgets import QVBoxLayout, QGroupBox, QSplitter
from PySide6.QtCore import Qt

from .base_editor import BaseEditor
from ...ui.widgets.rich_text_editor import RichTextEditor
from ...utils.constants import EntityType
from ...utils.events import Events
from ...utils.event_bus import bus, receiver

class NoteEditor(BaseEditor):
    """
    A composite :py:class:`PyQt6.QtWidgets.QWidget` that serves as the main 
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
    
    def __init__(self, current_settings, parent=None) -> None:
        """
        Initializes the NoteEditor with sub-components and layout.

        :param current_settings: A dictionary containing initial application settings.
        :type current_settings: dict
        :param parent: The parent widget. Defaults to ``None``.
        :type parent: :py:class:`PyQt6.QtWidgets.QWidget`, optional

        :rtype: None
        """
        super().__init__(parent)
        self.current_settings = current_settings

        self.current_lookup_dialog = None

        # --- Sub-components ---
        self.text_editor = RichTextEditor()

        # --- Layout ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 1. Tagging Group Box
        tag_group = QGroupBox("Note Tags (Genres, Themes, POVs)")
        tag_group.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tag_layout = QVBoxLayout(tag_group)
        tag_layout.setContentsMargins(10, 20, 10, 10)
        tag_layout.addWidget(self.tag_manager)

        editor_splitter = QSplitter(Qt.Orientation.Vertical)
        editor_splitter.addWidget(tag_group) # Use the new group containing stats bar
        editor_splitter.addWidget(self.text_editor)
        editor_splitter.setSizes([100, 900]) 

        # Add the splitter to the main layout
        main_layout.addWidget(editor_splitter)


        self.setEnabled(False)
        
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

        content, tags = data['content'], data['tags']

        self.text_editor.set_html_content(content)
        self.tag_manager.set_tags(tags)

        self.mark_saved()
        self.set_enabled(True)
