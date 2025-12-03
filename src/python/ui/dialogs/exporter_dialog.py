# src/python/ui/diaglogs/exporter_dialog.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QComboBox, 
    QLabel, QDialogButtonBox, QHBoxLayout, QPushButton,
    QMessageBox
)

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QComboBox, 
    QLabel, QDialogButtonBox, QHBoxLayout, QPushButton,
    QMessageBox, QWidget, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal

from ...services.story_exporter import StoryExporter # Keep this, though it might become ExporterFactory
from ...utils.theme_utils import get_available_themes

class ExportType:
    STORY = "Story (All Chapters)"
    CHAPTERS = "Selected Chapters"
    LORE = "Selected Lore Entries"
    CHARACTERS = "Selected Characters"

class ExporterDialog(QDialog):
    """A small dialog window to manager exporting parts of the project"""

    # Signal to request data from the Coordinator upon dialog acceptance
    export_requested = pyqtSignal(str, list) # (export_type, selected_ids)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Exporter")
        # Increase size to accommodate a selection list
        self.setGeometry(200, 200, 700, 500) 

        # State to track selected items and type
        self.selected_export_type = ExportType.STORY
        self.selected_item_ids = []

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Sets up the UI for the ExporterDialog"""
        main_layout = QVBoxLayout(self)

        # 1. Export Type Selection Group
        type_group = QGroupBox("Export Settings")
        type_layout = QHBoxLayout(type_group)

        type_layout.addWidget(QLabel("Export Type:"))
        self.export_type_combo = QComboBox()
        self.export_type_combo.addItem(ExportType.STORY)
        self.export_type_combo.addItem(ExportType.CHAPTERS)
        self.export_type_combo.addItem(ExportType.LORE)
        self.export_type_combo.addItem(ExportType.CHARACTERS)
        type_layout.addWidget(self.export_type_combo)
        type_layout.addStretch(1)

        main_layout.addWidget(type_group)

        # 2. Content Selector Group (A stacked widget will hold different selectors)
        content_group = QGroupBox("Content Selection")
        content_layout = QVBoxLayout(content_group)
        
        self.content_stack = QStackedWidget()
        
        # Add placeholder widgets for now
        self.placeholder_widget = QLabel("Select 'Story (All Chapters)' or choose a specific item type to enable selection.")
        self.content_stack.addWidget(self.placeholder_widget) # Index 0: Default/Story
        
        # Future selectors will go here:
        # Chapter Selector (Index 1)
        # Lore Selector (Index 2)
        # Character Selector (Index 3)
        self.content_stack.addWidget(QWidget()) # Placeholder for Chapter Selector
        self.content_stack.addWidget(QWidget()) # Placeholder for Lore Selector
        self.content_stack.addWidget(QWidget()) # Placeholder for Character Selector

        content_layout.addWidget(self.content_stack)
        main_layout.addWidget(content_group)
        
        # Start with the default/story view
        self.content_stack.setCurrentIndex(0)


        # 3. Dialog Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

    def _connect_signals(self) -> None:
        """Connects the UI components' signals."""
        self.export_type_combo.currentTextChanged.connect(self._handle_type_change)

    def _handle_type_change(self, new_type: str) -> None:
        """Switches the content selector based on the export type."""
        self.selected_export_type = new_type

        # Map export type to stacked widget index
        index_map = {
            ExportType.STORY: 0,
            ExportType.CHAPTERS: 1,
            ExportType.LORE: 2,
            ExportType.CHARACTERS: 3,
        }
        
        # Update the content stack
        self.content_stack.setCurrentIndex(index_map.get(new_type, 0))
        
        # Reset selected IDs when type changes (important for the real implementation)
        self.selected_item_ids = []

    def accept(self) -> None:
        """Override to emit the export_requested signal before closing."""
        
        # NOTE: When implemented, you will retrieve the selected IDs from the active selector widget
        if self.selected_export_type == ExportType.STORY:
            # Story export means all chapters, so selected_item_ids remains empty list
            pass 
        else:
            # TODO: In the final version, this will fetch selected IDs from the active selector
            # For now, let's pretend a few IDs are selected for testing non-Story flow
            self.selected_item_ids = [1, 2, 3] 
            QMessageBox.information(self, "WIP", f"Selected {self.selected_export_type} with IDs: {self.selected_item_ids}. Exporting is still pending implementation of item selection.", QMessageBox.StandardButton.Ok)


        # Emit the signal for the MainWindow/Coordinator to handle
        self.export_requested.emit(self.selected_export_type, self.selected_item_ids)
        super().accept()

    def get_export_details(self) -> tuple[str, list]:
        """Returns the selected export type and item IDs."""
        return self.selected_export_type, self.selected_item_ids
