# Chapter Editor Composite Widget: src/python/ui/chapter_editor.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QSplitter
)
from PyQt6.QtCore import Qt

from ui.widgets.tag_widget import TagManagerWidget
from ui.widgets.rich_text_editor import RichTextEditor

class ChapterEditor(QWidget):
    """
    A composite QWidget that serves as the main editing panel for a chapter.
    It combines the RichTextEditor for content and the TagManagerWidget for metadata.
    
    This component manages the state and provides a single interface for the 
    MainWindow to load and save all chapter data (content and tags).
    """
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        # --- Sub-components ---
        self.rich_text_editor = RichTextEditor()
        self.tag_manager = TagManagerWidget()

        # --- Layout ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 1. Tagging Group Box
        # Using a QGroupBox to clearly separate the tagging area
        tag_group = QGroupBox("Chapter Tags (Genres, Themes, POVs)")
        tag_layout = QVBoxLayout(tag_group)
        tag_layout.setContentsMargins(10, 15, 10, 10)
        tag_layout.addWidget(self.tag_manager)
        
        # 2. Rich Text Editor
        # Title/Separator for the main writing area
        content_label = QLabel("— Manuscript Content —")
        content_label.setStyleSheet("font-weight: bold; padding: 5px 0 5px 0;")
        content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create a vertical QSplitter for Tag Group and Editor
        content_splitter = QSplitter(Qt.Orientation.Vertical)

        # Create a container widget for the content label and the rich text editor
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0) # Use 0 margins to control spacing externally
        content_layout.setSpacing(0) 

        content_layout.addWidget(content_label)
        content_layout.addWidget(self.rich_text_editor)

        content_splitter.addWidget(tag_group)
        content_splitter.addWidget(content_container)

        # Set the initial ratio of the splitter (e.g., 1:8 ratio for Tag Group to Editor)
        content_splitter.setSizes([100, 800]) 
        
        main_layout.addWidget(content_splitter)

        # --- Connections ---
        # Any change in the tags *also* makes the chapter dirty
        self.tag_manager.tags_changed.connect(self._handle_tag_change)
        
        # The RichTextEditor already connects its textChanged signal to its internal dirty flag, 
        # so we only need to handle the TagManager change here.

    def _handle_tag_change(self):
        """Sets the rich text editor's dirty flag when tags are modified."""
        self.rich_text_editor._set_dirty()
        
    # --- Content Passthrough Methods (RichTextEditor) ---
    
    def is_dirty(self) -> bool:
        """Checks if the content or the tags have unsaved changes."""
        return self.rich_text_editor.is_dirty() or self.tag_manager.is_dirty()

    def mark_saved(self) -> None:
        """Marks both content and tags as clean."""
        self.rich_text_editor.mark_saved()
        self.tag_manager.mark_saved()
        
    def set_enabled(self, enabled: bool) -> None:
        """Enables/disables the entire chapter editor panel."""
        self.rich_text_editor.setEnabled(enabled)
        self.tag_manager.setEnabled(enabled)

    def get_html_content(self) -> str:
        """Returns the current rich text content."""
        return self.rich_text_editor.get_html_content()

    def set_html_content(self, html_content: str) -> None:
        """Sets the rich text content."""
        self.rich_text_editor.set_html_content(html_content)

    # --- Tagging Passthrough Methods (TagManagerWidget) ---
    
    def get_tags(self) -> list[str]:
        """Returns the current list of tag names."""
        return self.tag_manager.get_tags()

    def set_tags(self, tag_names: list[str]) -> None:
        """Sets the tags when a chapter is loaded."""
        # This function also clears the tag manager's dirty state internally
        self.tag_manager.set_tags(tag_names)

