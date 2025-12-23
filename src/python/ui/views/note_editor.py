# src/python/ui/note_editor.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QSplitter, QHBoxLayout, QTextEdit,
    QDialog, QSizePolicy, QLabel
)
from PyQt6.QtCore import Qt

from ...services.app_coordinator import AppCoordinator
from ...ui.widgets.tag_widget import TagManagerWidget
from ...ui.widgets.rich_text_editor import RichTextEditor

class NoteEditor(QWidget):
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
        self.tag_manager = TagManagerWidget()

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
    
    def is_dirty(self) -> bool:
        """
        Checks if the content (BasicTextEditor) or the tags (TagManagerWidget) 
        have unsaved changes.

        :returns: ``True`` if content or tags are modified, ``False`` otherwise.
        :rtype: bool
        """
        return self.text_editor.is_dirty() or self.tag_manager.is_dirty()

    def mark_saved(self) -> None:
        """
        Marks both the basic text content and the tags as clean (saved).

        :rtype: None
        """
        self.text_editor.mark_saved()
        self.tag_manager.mark_saved()
        
    def set_enabled(self, enabled: bool) -> None:
        """
        Enables or disables the entire note editor panel by setting the 
        state of its main sub-components.

        :param enabled: ``True`` to enable, ``False`` to disable.
        :type enabled: bool

        :rtype: None
        """
        self.text_editor.setEnabled(enabled)
        if self.tag_manager is not None:
            try:
                self.tag_manager.setEnabled(enabled)
            except RuntimeError:
                pass
        self.setEnabled(enabled)

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
        Sets the tags when a note is loaded.

        This function also clears the tag manager's dirty state internally.

        :param tag_names: A list of tag names (strings) to set.
        :type tag_names: list[str]
        """
        self.tag_manager.set_tags(tag_names)

