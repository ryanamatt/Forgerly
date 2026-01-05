# src/python/ui/diaglogs/exporter_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QComboBox, 
    QLabel, QDialogButtonBox, QHBoxLayout,
    QMessageBox, QListWidget, QWidget
)

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QComboBox, 
    QLabel, QDialogButtonBox, QHBoxLayout,
    QMessageBox, QWidget, QStackedWidget
)
from PySide6.QtCore import Signal

from ...utils.constants import ExportType
from ...utils.event_bus import bus
from ...utils.events import Events

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from services.app_coordinator import AppCoordinator

class ExporterDialog(QDialog):
    """
    A modal dialog window used to configure and initiate the project export process.
    
    This dialog allows the user to select the type of content to export (e.g., Story, 
    Lore, Character data) and choose the specific items to include. It uses a 
    :py:class:`~PySide6.QtWidgets.QStackedWidget` to switch between content-specific 
    selection widgets.
    """

    export_requested = Signal(str, list) # (export_type, selected_ids)
    """
    :py:class:`~PySide6.QtCore.Signal` (str, list): Emitted when the user confirms 
    the export. Carries the selected export type (str) and a list of selected 
    item IDs (list[int]).
    """

    def __init__(self, coordinator: 'AppCoordinator', parent=None) -> None:
        """
        Initializes the :py:class:`.ExporterDialog`.

        :param coordinator: The application coordinator for data access and export logic.
        :type coordinator: :py:class:`~services.app_coordinator.AppCoordinator`
        :param parent: The parent Qt widget.
        :type parent: :py:class:`~PySide6.QtWidgets.QWidget` or None
        
        :rtype: None
        """
        super().__init__(parent)

        bus.register_instance(self)

        self.coordinator = coordinator # Store coordinator reference
        
        self.setWindowTitle("Exporter")
        self.setGeometry(200, 200, 700, 500) 

        self.selected_export_type = ExportType.STORY
        self.selected_item_ids = []

        self._setup_ui()
        self._set_initial_state()
        
    def _setup_ui(self) -> None:
        """
        Sets up the layout of the dialog, including the export type selector 
        and the stacked widget that holds the specific item selectors.
        
        :rtype: None
        """
        main_layout = QVBoxLayout(self)
        
        # --- 1. Type Selection (Combo Box) ---
        type_group = QGroupBox("Export Type")
        type_layout = QHBoxLayout(type_group)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            ExportType.STORY, 
            ExportType.CHAPTERS, 
            ExportType.LORE, 
            ExportType.CHARACTERS
        ])
        type_combo_label = QLabel("What to Export:")
        type_layout.addWidget(type_combo_label)
        type_layout.addWidget(self.type_combo)
        main_layout.addWidget(type_group)
        
        # Connect signal *before* creating content stack to avoid initial trigger issues
        self.type_combo.currentTextChanged.connect(self._update_content_stack)

        # --- 2. Content Stack (List Selectors) ---
        self.content_stack = QStackedWidget()
        
        # 2a. Dummy Widget for STORY (All Chapters)
        story_widget = QWidget()
        story_layout = QVBoxLayout(story_widget)
        story_layout.addWidget(QLabel("The entire story will be exported (all chapters, in order)."))
        self.content_stack.addWidget(story_widget)
        
        # 2b. Chapter Selector
        self.chapter_selector = ChapterSelector(self.coordinator)
        self.content_stack.addWidget(self.chapter_selector)
        
        # 2c. Lore Selector
        self.lore_selector = LoreSelector(self.coordinator)
        self.content_stack.addWidget(self.lore_selector)
        
        # 2d. Character Selector
        self.character_selector = CharacterSelector(self.coordinator)
        self.content_stack.addWidget(self.character_selector)

        main_layout.addWidget(self.content_stack)

        # --- 3. Buttons ---
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
        
    def _set_initial_state(self) -> None:
        """
        Sets the initial state of the dialog. Default is ExportType.STORY
        
        :rtype: None
        """
        self.selected_export_type = ExportType.STORY
        self.content_stack.setCurrentIndex(0) # Index 0 is the Story widget

    def _update_content_stack(self, new_type: str) -> None:
        """
        Updates the visible selector widget based on the combo box selection.
        
        :param new_type: The new type of export option
        :type new_type: str

        :rtype: None
        """
        self.selected_export_type = new_type
        
        index_map = {
            ExportType.STORY: 0,       # Dummy Widget
            ExportType.CHAPTERS: 1,    # ChapterSelector
            ExportType.LORE: 2,        # LoreSelector
            ExportType.CHARACTERS: 3,  # CharacterSelector
        }
        
        # Update the content stack
        self.content_stack.setCurrentIndex(index_map.get(new_type, 0))
        
        # Reset selected IDs when type changes
        self.selected_item_ids = []

    def accept(self) -> None:
        """
        Override to retrieve selected IDs and emit the export_requested signal before closing.
        Handles the Accpetance of the 'Ok' button.
        
        :rtype: None
        """
        
        # 1. Determine which selector is active and get its selected IDs
        if self.selected_export_type == ExportType.STORY:
            # Story export means all chapters, ID list remains empty for the exporter to fetch all
            self.selected_item_ids = [] 
        
        elif self.selected_export_type == ExportType.CHAPTERS:
            self.selected_item_ids = self.chapter_selector.get_selected_ids()
        
        elif self.selected_export_type == ExportType.LORE:
            self.selected_item_ids = self.lore_selector.get_selected_ids()
        
        elif self.selected_export_type == ExportType.CHARACTERS:
            self.selected_item_ids = self.character_selector.get_selected_ids()

        # 2. Validation check: Ensure items are selected for non-Story exports
        if self.selected_export_type != ExportType.STORY and not self.selected_item_ids:
            QMessageBox.warning(self, "Selection Required", f"Please select one or more items to "
                                f"export under the '{self.selected_export_type}' category.")
            return # Stop acceptance process

        # self.export_requested.emit(self.selected_export_type, self.selected_item_ids)
        bus.publish(Events.EXPORT_PERFORM, data={
            'export_type': self.selected_export_type, 'selected_ids': self.selected_item_ids,
            'parent': self.parent()
        })
        
        super().accept()

    def get_export_details(self) -> tuple[str, list]:
        """Returns the selected export type and item IDs."""
        return self.selected_export_type, self.selected_item_ids

# --- Class Selectors ---

class LoreSelector(QWidget):
    """Widget to display and select Lore Entries."""
    def __init__(self, coordinator, parent=None) -> None:
        """
        A custom :py:class:`~PySide6.QtWidgets.QWidget` dedicated to displaying 
        and selecting Lore Entries for export.
        
        This widget is designed to be placed inside the 
        :py:class:`~PySide6.QtWidgets.QStackedWidget` of :py:class:`.ExporterDialog`.
        """
        super().__init__(parent)
        self.coordinator = coordinator
        self.all_data = [] # To store the full list of dictionaries
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select Lore Entries to Export:"))
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self.list_widget)
        
        self.load_data()

    def load_data(self):
        """
        Fetches all Lore entries from the repository and populates the 
        :py:class:`~PySide6.QtWidgets.QListWidget` with their titles.
        
        :rtype: None
        """
        self.list_widget.clear()
        # Fetching all lore entries (ID, Title, Category)
        self.all_data = self.coordinator.lore_repo.get_all_lore_entries()
        if self.all_data:
            for entry in self.all_data:
                self.list_widget.addItem(f"[{entry['Category']}] {entry['Title']}")

    def get_selected_ids(self) -> list[int]:
        """
        Retrieves the unique database IDs of all Lore Entries currently selected in the list widget.
        
        :returns: A list of integer IDs for the selected Lore Entries.
        :rtype: list[int]
        """
        selected_ids = []
        for item in self.list_widget.selectedItems():
            # Find the ID corresponding to the selected row index
            row_index = self.list_widget.row(item)
            selected_ids.append(self.all_data[row_index]['ID'])
        return selected_ids

class CharacterSelector(QWidget):
    """Widget to display and select Characters."""
    def __init__(self, coordinator, parent=None) -> None:
        """
        A custom :py:class:`~PySide6.QtWidgets.QWidget` dedicated to displaying 
        and selecting Characters for export.
        
        This widget is designed to be placed inside the 
        :py:class:`~PySide6.QtWidgets.QStackedWidget` of :py:class:`.ExporterDialog`.
        """
        super().__init__(parent)
        self.coordinator = coordinator
        self.all_data = [] # To store the full list of dictionaries

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select Characters to Export:"))
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self.list_widget)

        self.load_data()

    def load_data(self):
        """
        Fetches all character entries from the repository and populates the 
        :py:class:`~PySide6.QtWidgets.QListWidget` with their names.
        
        :rtype: None
        """
        self.list_widget.clear()
        # Fetching all character entries (ID, Name, Status)
        self.all_data = self.coordinator.character_repo.get_all_characters()
        if self.all_data:
            for entry in self.all_data:
                self.list_widget.addItem(f"{entry['Name']}")

    def get_selected_ids(self) -> list[int]:
        """
        Retrieves the unique database IDs of all characters currently selected in the list widget.
        
        :returns: A list of integer IDs for the selected characters.
        :rtype: list[int]
        """
        selected_ids = []
        for item in self.list_widget.selectedItems():
            # Find the ID corresponding to the selected row index
            row_index = self.list_widget.row(item)
            selected_ids.append(self.all_data[row_index]['ID'])
        return selected_ids


class ChapterSelector(QWidget):
    """
    A custom :py:class:`~PySide6.QtWidgets.QWidget` dedicated to displaying 
    and selecting Chapters for export.
    
    This widget is designed to be placed inside the 
    :py:class:`~PySide6.QtWidgets.QStackedWidget` of :py:class:`.ExporterDialog`.
    """
    def __init__(self, coordinator, parent=None) -> None:
        """
        Initializes the :py:class:`.ChapterSelector`.

        :param coordinator: The application coordinator to access the chapter repository.
        :type coordinator: :py:class:`~services.app_coordinator.AppCoordinator`
        :param parent: The parent Qt widget.
        :type parent: :py:class:`~PySide6.QtWidgets.QWidget` or None
        
        :rtype: None
        """
        super().__init__(parent)
        self.coordinator = coordinator
        self.all_data = [] # To store the full list of dictionaries
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select Chapters to Export:"))
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self.list_widget)

        self.load_data()

    def load_data(self):
        """
        Fetches all chapter entries from the repository and populates the 
        :py:class:`~PySide6.QtWidgets.QListWidget` with their titles and sort order.
        
        :rtype: None
        """
        self.list_widget.clear()
        # Fetching all chapter entries (ID, Title)
        self.all_data = self.coordinator.chapter_repo.get_all_chapters()
        if self.all_data:
            for entry in self.all_data:
                # Assuming chapter repo returns Sort_Order
                order = entry.get('Sort_Order', 0)
                self.list_widget.addItem(f"Chapter {order}: {entry['Title']}")

    def get_selected_ids(self) -> list[int]:
        """
        Retrieves the unique database IDs of all chapters currently selected in the list widget.
        
        :returns: A list of integer IDs for the selected chapters.
        :rtype: list[int]
        """
        selected_ids = []
        for item in self.list_widget.selectedItems():
            # Find the ID corresponding to the selected row index
            row_index = self.list_widget.row(item)
            selected_ids.append(self.all_data[row_index]['ID'])
        return selected_ids
