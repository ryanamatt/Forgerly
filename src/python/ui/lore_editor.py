# src/python/ui/lore_editor.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QSplitter, 
    QLineEdit, QComboBox, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Any

from .tag_widget import TagManagerWidget
from .rich_text_editor import RichTextEditor

class LoreEditor(QWidget):
    """
    A composite QWidget for editing a Lore Entry (Title, Category, Content, Tags).
    It is a pure UI component and does not interact with repositories directly.
    """
    lore_title_changed = pyqtSignal(int, str)
    
    # State tracking for unsaved changes
    _initial_title = ""
    _initial_category = ""
    current_lore_id: int | None = None
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        
        # --- Sub-components ---
        self.rich_text_editor = RichTextEditor()
        self.tag_manager = TagManagerWidget()

        # --- Lore-Specific Components (Title and Category) ---
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter Lore Entry Title (e.g., 'The Sunken City of K'tal')")

        self.category_combo = QComboBox()
        self.category_combo.addItems(["Character", "Location", "Magic System", "Creature", "Event", "Concept"])
        self.category_combo.setEditable(True) 

        # --- Layout Setup ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 1. Title Input (Top)
        main_layout.addWidget(self.title_input)

        # 2. Category Group Box
        cat_group = QGroupBox("Lore Type")
        cat_layout = QHBoxLayout(cat_group)
        cat_layout.addWidget(QLabel("Category:"))
        cat_layout.addWidget(self.category_combo)
        
        # 3. Tagging Group Box
        tag_group = QGroupBox("Lore Tags")
        tag_layout = QVBoxLayout(tag_group)
        tag_layout.setContentsMargins(10, 15, 10, 10)
        tag_layout.addWidget(self.tag_manager)

        # 4. Vertical Splitter for Metadata (Category/Tags) and Content
        content_splitter = QSplitter(Qt.Orientation.Vertical)
        
        metadata_container = QWidget()
        metadata_layout = QVBoxLayout(metadata_container)
        metadata_layout.setContentsMargins(0, 0, 0, 0)
        metadata_layout.addWidget(cat_group)
        metadata_layout.addWidget(tag_group)
        
        content_splitter.addWidget(metadata_container)
        content_splitter.addWidget(self.rich_text_editor)
        
        content_splitter.setSizes([300, 700]) 
        main_layout.addWidget(content_splitter)
        
        # --- Connections: All changes trigger a dirtiness state check ---
        self.rich_text_editor.content_changed.connect(self._set_dirty)
        self.tag_manager.tags_changed.connect(self._set_dirty)
        self.title_input.textChanged.connect(self._set_dirty)
        self.category_combo.currentIndexChanged.connect(self._set_dirty)
        
        # Emit signal when title edit is finished (for Outline update)
        self.title_input.editingFinished.connect(self._emit_title_change)
        
        self.set_enabled(False)
        self.mark_saved()
        
    # =========================================================================
    # PUBLIC API: Used by MainWindow
    # =========================================================================

    def load_lore(self, lore_id: int, title: str, category: str, content: str, tag_names: list[str]) -> None:
        """Loads all data into the UI, setting the internal clean state."""
        self.set_enabled(False)
        self.current_lore_id = lore_id

        self.title_input.setText(title)
        
        # Handle Category: Add if it doesn't exist, then set current index
        index = self.category_combo.findText(category)
        if index == -1:
            self.category_combo.insertItem(0, category)
            self.category_combo.setCurrentIndex(0)
        else:
            self.category_combo.setCurrentIndex(index)
            
        self.rich_text_editor.set_html_content(content)
        self.tag_manager.set_tags(tag_names)
        
        # Store initial state for dirtiness check
        self._initial_title = title
        self._initial_category = category
        self.mark_saved()
        self.set_enabled(True)

    def get_data(self) -> dict[str, Any]:
        """Returns the current state of all editable fields for MainWindow to save."""
        return {
            'id': self.current_lore_id,
            'title': self.title_input.text().strip(),
            'category': self.category_combo.currentText().strip(),
            'content': self.rich_text_editor.get_html_content(),
            'tags': self.tag_manager.get_tags()
        }
        
    def is_dirty(self) -> bool:
        """Checks if any component (Title, Category, Content, Tags) has unsaved changes."""
        if not self.current_lore_id:
            return False # Nothing is loaded, so nothing is dirty

        title_changed = self.title_input.text().strip() != self._initial_title
        category_changed = self.category_combo.currentText().strip() != self._initial_category
        
        return (title_changed or 
                category_changed or
                self.rich_text_editor.is_dirty() or 
                self.tag_manager.is_dirty())

    def mark_saved(self) -> None:
        """Marks all nested components as clean."""
        self.rich_text_editor.mark_saved()
        self.tag_manager.mark_saved()
        
    def set_enabled(self, enabled: bool) -> None:
        """Enables/disables the entire editor panel."""
        self.title_input.setEnabled(enabled)
        self.category_combo.setEnabled(enabled)
        self.rich_text_editor.setEnabled(enabled)
        self.tag_manager.setEnabled(enabled)
        
    # =========================================================================
    # INTERNAL HANDLERS
    # =========================================================================
        
    def _set_dirty(self, *args) -> None:
        """Placeholder for dirtiness signals. Actual dirtiness is checked in is_dirty()."""
        pass

    def _emit_title_change(self) -> None:
        """Emits the signal to update the outline after the user finishes editing the title."""
        if self.current_lore_id is not None:
             self.lore_title_changed.emit(self.current_lore_id, self.title_input.text().strip())