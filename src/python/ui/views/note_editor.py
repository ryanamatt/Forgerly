# src/python/ui/note_editor.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QSplitter, QHBoxLayout, QTextEdit,
    QDialog, QSizePolicy, QLabel
)
from PyQt6.QtCore import Qt

from .base_editor import BaseEditor
from ...services.app_coordinator import AppCoordinator
from ...ui.widgets.tag_widget import TagManagerWidget
from ...ui.widgets.rich_text_editor import RichTextEditor

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
    
    def __init__(self, current_settings, coordinator: AppCoordinator, parent=None) -> None:
        """
        Initializes the NoteEditor with sub-components and layout.

        :param current_settings: A dictionary containing initial application settings.
        :type current_settings: dict
        :param coordinator: The AppCoordinator.
        :type coordinator: :py:class:`services.AppCoordinator`
        :param parent: The parent widget. Defaults to ``None``.
        :type parent: :py:class:`PyQt6.QtWidgets.QWidget`, optional

        :rtype: None
        """
        super().__init__(parent)
        self.current_settings = current_settings
        self.coordinator = coordinator

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
