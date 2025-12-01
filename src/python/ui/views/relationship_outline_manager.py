# src/python/ui/views/relationship_outline_manager.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QMenu, QMessageBox, QInputDialog, QColorDialog, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QColor
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from repository.relationship_repository import RelationshipRepository

# Define the role for storing the custom data (Relationship Type ID)
RELATIONSHIP_TYPE_ID_ROLE = Qt.ItemDataRole.UserRole + 1

class RelationshipOutlineManager(QWidget):
    """
    A custom QWidget dedicated to displaying and managing the list of
    Relationship Types. It interacts with the data layer via RelationshipRepository.
    
    This manager allows users to define/edit the fundamental properties of a 
    relationship type (name, color, line style).
    """

    # Signal emitted when a relationship type is selected (e.g., to load its details)
    type_selected = pyqtSignal(int)
    
    # Signal emitted after a relationship type is created, edited, or deleted.
    # This is for the AppCoordinator to tell the RelationshipEditor (graph) to refresh.
    relationship_types_updated = pyqtSignal() 

    def __init__(self, relationship_repository: RelationshipRepository | None = None) -> None:
        super().__init__()

        self.rel_repo = relationship_repository
        
        # --- UI Components ---
        self.list_widget = QListWidget()
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        self.new_button = QPushButton("New Relationship Type")
        
        # --- Layout Setup ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Buttons/Actions area
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.new_button)
        main_layout.addLayout(button_layout)
        
        # List of types
        main_layout.addWidget(self.list_widget)

        # --- Connections ---
        self.new_button.clicked.connect(self._create_new_type)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        self.list_widget.itemDoubleClicked.connect(self._open_type_editor)
        self.list_widget.itemClicked.connect(self._handle_item_clicked)
        
        # Load initial data
        self.load_outline()
        
    def set_repository(self, repo: RelationshipRepository) -> None:
        """Sets the repository dependency, usually called by AppCoordinator."""
        self.rel_repo = repo
        self.load_outline()
        
    def load_outline(self) -> None:
        """Loads all relationship types from the database and populates the list."""
        if not self.rel_repo:
            return
        
        self.list_widget.clear()
        
        all_types = self.rel_repo.get_all_relationship_types()
        
        if all_types:
            for rel_type in all_types:
                type_id = rel_type['ID']
                name = rel_type['Type_Name']
                color = rel_type.get('Default_Color', '#000000') # Default to black
                
                item = QListWidgetItem(name)
                # Store the Type ID and Color for later use
                item.setData(RELATIONSHIP_TYPE_ID_ROLE, type_id)
                item.setForeground(QColor(color))
                
                self.list_widget.addItem(item)
                
    # --- Internal Handlers ---

    def _handle_item_clicked(self, item: QListWidgetItem) -> None:
        """Emits the signal to tell the coordinator that a relationship type has been selected."""
        type_id = item.data(RELATIONSHIP_TYPE_ID_ROLE)
        if type_id is not None:
            self.type_selected.emit(type_id)

    def _show_context_menu(self, position: QPoint) -> None:
        """Shows the context menu for the list widget."""
        item = self.list_widget.itemAt(position)
        
        menu = QMenu(self)
        
        # Action to always be available (Create)
        new_action = menu.addAction("New Relationship Type")
        new_action.triggered.connect(self._create_new_type)

        if item:
            # Actions available for a selected item
            edit_action = menu.addAction("Edit Type Properties...")
            delete_action = menu.addAction("Delete Type")
            
            edit_action.triggered.connect(lambda: self._open_type_editor(item))
            delete_action.triggered.connect(lambda: self._delete_type(item))

        menu.exec(self.list_widget.mapToGlobal(position))

    def _open_type_editor(self, item: QListWidgetItem) -> None:
        """
        A simple, self-contained editor for the core properties (Name, Color, Style, Direction).
        This can be replaced with a full custom QDialog later for better UX.
        """
        if not self.rel_repo:
            QMessageBox.critical(self, "Error", "RelationshipRepository is missing.")
            return

        type_id = item.data(RELATIONSHIP_TYPE_ID_ROLE)
        current_name = item.text()
        
        # 1. Get all details for editing (Requires new repo method)
        details = self.rel_repo.get_relationship_type_details(type_id)
        if not details:
            QMessageBox.critical(self, "Error", "Could not retrieve relationship type details.")
            return
        
        current_color = details.get('Default_Color', '#000000')
        current_style = details.get('Line_Style', 'Solid')
        current_directed = details.get('Is_Directed', 0)
        current_short_label = details.get('Short_Label', '')

        # --- Simple Edit Flow using QInputDialogs (multi-step) ---
        
        # a) Edit Name
        new_name, ok = QInputDialog.getText(
            self, "Edit Type Name", "Relationship Type Name:", QLineEdit.EchoMode.Normal, current_name
        )
        if not ok or not new_name.strip(): return
            
        new_name = new_name.strip()
        
        # b) Edit Short Label
        new_short_label, ok = QInputDialog.getText(
            self, "Edit Type Short Label", "Short Label (e.g., 'Fr', 'Ri'):", QLineEdit.EchoMode.Normal, current_short_label
        )
        if not ok: return
        new_short_label = new_short_label.strip()

        # c) Edit Color
        color_dialog = QColorDialog()
        color_dialog.setCurrentColor(QColor(current_color))
        if color_dialog.exec() == QColorDialog.DialogCode.Accepted:
            new_color = color_dialog.selectedColor().name()
        else:
            new_color = current_color 
            
        # d) Edit Line Style 
        styles = ['Solid', 'Dash', 'Dot', 'DashDot']
        style_idx = styles.index(current_style) if current_style in styles else 0
        new_style, ok = QInputDialog.getItem(
            self, "Edit Line Style", "Line Style:", styles, current=style_idx, editable=False
        )
        if not ok: return
        
        # e) Edit Is_Directed 
        directed_options = ['Undirected (A <-> B)', 'Directed (A -> B)']
        directed_idx = 1 if current_directed else 0
        selected_direction, ok = QInputDialog.getItem(
            self, "Edit Directionality", "Relationship Direction:", directed_options, current=directed_idx, editable=False
        )
        if not ok: return
            
        new_directed = 1 if selected_direction == directed_options[1] else 0

        # --- Save Changes ---
        success = self.rel_repo.update_relationship_type(
            type_id=type_id,
            type_name=new_name,
            short_label=new_short_label,
            default_color=new_color,
            is_directed=new_directed,
            line_style=new_style
        )
        
        if success:
            # Update the list item in the UI
            item.setText(new_name)
            item.setForeground(QColor(new_color))
            self.relationship_types_updated.emit()
            QMessageBox.information(self, "Success", f"Relationship Type '{new_name}' updated.")
        else:
            QMessageBox.critical(self, "Error", f"Failed to update relationship type '{current_name}' in the database.")


    def _create_new_type(self) -> None:
        """Handles the creation of a new relationship type."""
        if not self.rel_repo:
            QMessageBox.critical(self, "Error", "RelationshipRepository is missing.")
            return

        name, ok = QInputDialog.getText(
            self, "New Relationship Type", "Enter name for the new Relationship Type:"
        )
        
        if ok and name.strip():
            new_name = name.strip()
            # Use sensible defaults for creation
            new_id = self.rel_repo.create_relationship_type(
                type_name=new_name, 
                short_label=new_name[:3], # Default short label to first 3 chars
                default_color="#FFFFFF", # Default to white
                is_directed=0,
                line_style="Solid"
            )
            
            if new_id:
                self.load_outline() 
                self.relationship_types_updated.emit()
                QMessageBox.information(self, "Success", f"Relationship Type '{new_name}' created.")
            else:
                QMessageBox.critical(self, "Error", f"Failed to create relationship type '{new_name}' in the database.")

    def _delete_type(self, item: QListWidgetItem) -> None:
        """Handles the deletion of a relationship type."""
        if not self.rel_repo:
            QMessageBox.critical(self, "Error", "RelationshipRepository is missing.")
            return
            
        type_id = item.data(RELATIONSHIP_TYPE_ID_ROLE)
        name = item.text()
        
        # Confirmation Dialog
        reply = QMessageBox.question(
            self, 
            "Confirm Deletion",
            f"Are you sure you want to permanently delete the Relationship Type: \n'{name}'?\n\nThis will also delete ALL character relationships of this type. This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.rel_repo.delete_relationship_type(type_id):
                # Remove from UI and notify
                self.list_widget.takeItem(self.list_widget.row(item))
                self.relationship_types_updated.emit()
                QMessageBox.information(self, "Success", f"Relationship Type '{name}' deleted.")
            else:
                QMessageBox.critical(self, "Deletion Error", "A database error occurred while trying to delete the relationship type.")