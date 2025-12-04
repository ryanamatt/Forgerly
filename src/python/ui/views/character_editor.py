# src/python/ui/views/character_editor.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, 
    QLineEdit, QComboBox, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Any

from ...ui.widgets.basic_text_editor import BasicTextEditor

class CharacterEditor(QWidget):
    """
    A composite QWidget for editing a Character (Name, Status, Description).
    It is a pure UI component and does not interact with repositories directly.
    
    It is designed to be managed by the AppCoordinator.
    """
    # Signal emitted when the character's name changes, for the Outline Manager to update its list item.
    char_name_changed = pyqtSignal(int, str)

    # State tracking for unsaved changes
    _initial_name: str = ""
    _initial_status: str = ""
    current_char_id: int | None = None

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        # --- Sub-components (Description) ---
        self.basic_text_editor = BasicTextEditor()

        # --- Character-Specific Components (Name and Status) ---
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter Character Name")
        
        self.status_combo = QComboBox()
        # Populating Status options based on typical database fields
        self.status_combo.addItems(["Alive", "Deceased", "Unknown", "Retired/Removed"])

        # --- Layout Setup ---
        
        # 1. Name & Status Header Group (Horizontal layout for top controls)
        header_group = QWidget()
        header_layout = QHBoxLayout(header_group)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Name Input
        name_label = QLabel("Name:")
        header_layout.addWidget(name_label)
        header_layout.addWidget(self.name_input, 3) # Give more horizontal space for name

        # Status Combo
        status_label = QLabel("Status:")
        header_layout.addWidget(status_label)
        header_layout.addWidget(self.status_combo, 1) # Less space for status
        header_layout.addStretch(1) # Push everything to the left
        
        # 2. Main Description Editor Group
        description_group = QGroupBox("Description & Biography")
        description_layout = QVBoxLayout(description_group)
        description_layout.setContentsMargins(10, 10, 10, 10)
        description_layout.addWidget(self.basic_text_editor)
        
        # 3. Overall Layout (Vertical)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        main_layout.addWidget(header_group)
        main_layout.addWidget(description_group)
        
        # --- Connections ---
        # Any change to these components should flag the item as dirty
        self.basic_text_editor.content_changed.connect(self._set_dirty)
        self.name_input.textChanged.connect(self._set_dirty)
        self.status_combo.currentTextChanged.connect(self._set_dirty)
        
        # Emit name change signal when the user finishes editing the name, 
        # allowing the Outline Manager to update the list item's text.
        self.name_input.editingFinished.connect(self._emit_name_change)
        
        # Initialize disabled until a character is loaded
        self.setEnabled(False)

    # =========================================================================
    # PUBLIC INTERFACE (Data/State Management)
    # =========================================================================

    def load_character(self, char_id: int, name: str, description: str, status: str) -> None:
        """
        Loads character data into the editor components and marks the state as clean.
        """
        self.current_char_id = char_id
        
        # 1. Update UI
        self.name_input.setText(name)
        
        # Temporarily block signals to prevent triggering _set_dirty when setting new text
        self.status_combo.blockSignals(True)
        # Find the status string in the combo box, fall back to 'Unknown' if not found
        index = self.status_combo.findText(status, Qt.MatchFlag.MatchExactly)
        if index == -1:
            index = self.status_combo.findText("Unknown", Qt.MatchFlag.MatchExactly)
        self.status_combo.setCurrentIndex(index)
        self.status_combo.blockSignals(False)
        
        self.basic_text_editor.set_html_content(description)
        
        # 2. Save initial state for dirty check
        self._initial_name = name
        self._initial_status = status
        
        # 3. Mark all as saved and enable the editor
        self.mark_saved()
        self.setEnabled(True)

    def get_data(self) -> dict[str, Any]:
        """Returns the current state of all editable fields for MainWindow to save."""
        return {
            'id': self.current_char_id,
            'name': self.name_input.text().strip(),
            'description': self.basic_text_editor.get_html_content(),
            'status': self.status_combo.currentText().strip()
        }
        
    def is_dirty(self) -> bool:
        """
        Checks if the character data (name, status, or description) has unsaved changes.
        """
        if self.current_char_id is None:
            return False 

        name_changed = self.name_input.text().strip() != self._initial_name
        status_changed = self.status_combo.currentText().strip() != self._initial_status
        
        return (name_changed or 
                status_changed or
                self.basic_text_editor.is_dirty())

    def mark_saved(self) -> None:
        """
        Marks all nested components as clean and resets initial state trackers.
        """
        self.basic_text_editor.mark_saved()
        
        # Recapture the current state as the new saved state
        self._initial_name = self.name_input.text().strip()
        self._initial_status = self.status_combo.currentText().strip()
        
    def set_enabled(self, enabled: bool) -> None:
        """Enables/disables the entire editor panel."""
        self.name_input.setEnabled(enabled)
        self.status_combo.setEnabled(enabled)
        self.basic_text_editor.setEnabled(enabled)
        
    # --- Data Retrieval Methods ---
    
    def get_name(self) -> str:
        """Returns the current character name."""
        return self.name_input.text().strip()
    
    def get_status(self) -> str:
        """Returns the current character status."""
        return self.status_combo.currentText().strip()

    def get_description_content(self) -> str:
        """Returns the current basic text description content (HTML)."""
        return self.basic_text_editor.get_html_content()
    
    # =========================================================================
    # INTERNAL HANDLERS
    # =========================================================================
        
    def _set_dirty(self) -> None:
        """
        Handler for UI input. We don't need to do anything here, as the dirtiness
        is checked dynamically in `is_dirty()`.
        """
        pass 

    def _emit_name_change(self) -> None:
        """
        Emits the signal to update the outline after the user finishes editing the name.
        """
        if self.current_char_id is not None:
             self.char_name_changed.emit(self.current_char_id, self.get_name())