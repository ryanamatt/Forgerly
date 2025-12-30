# src/python/ui/views/relationship_outline_manager.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QMenu, QMessageBox, QDialog
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor

from ..dialogs.relationship_type_editor_dialog import RelationshipTypeEditorDialog
from ...utils.constants import EntityType
from ...utils.events import Events
from ...utils.event_bus import bus, receiver

class RelationshipOutlineManager(QWidget):
    """
    A custom :py:class:`~PyQt6.QtWidgets.QWidget` dedicated to displaying 
    and managing the list of Relationship Types. 
    
    It interacts with the data layer via :py:class:`~app.repository.relationship_repository.RelationshipRepository`.
    This manager allows users to define/edit the fundamental properties of a 
    relationship type (name, color, line style, directionality).
    """

    RELATIONSHIP_TYPE_ID_ROLE = Qt.ItemDataRole.UserRole + 1
    """The :py:obj:`int` role used to store the database ID of a Relationship_Type on an item."""

    def __init__(self) -> None:
        """
        Initializes the :py:class:`.RelationshipOutlineManager`.
        
        :rtype: None
        """
        super().__init__()

        bus.register_instance(self)
        
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
        
    @receiver(Events.OUTLINE_DATA_LOADED)
    def load_outline(self, data: dict) -> None:
        """
        Loads all relationship types from the database via the repository and 
        populates the internal :py:class:`~PyQt6.QtWidgets.QListWidget`.
        
        Each item is set with the name as text and its ID and color in the data roles.

        :param data: A dictionary of the needed data containg {entity_type: EntityType.}
        :type data: dict
        
        :rtype: None
        """
        entity_type = data.get('entity_type')
        rel_types = data.get('relationship_types')
        if entity_type != EntityType.RELATIONSHIP or not rel_types: 
            return
        
        self.list_widget.clear()
                
        if rel_types:
            for rel_type in rel_types:
                type_id = rel_type['ID']
                name = rel_type['Type_Name']
                color = rel_type.get('Default_Color', '#000000') # Default to black
                
                item = QListWidgetItem(name)
                # Store the Type ID and Color for later use
                item.setData(self.RELATIONSHIP_TYPE_ID_ROLE, type_id)
                item.setForeground(QColor(color))
                
                self.list_widget.addItem(item)
                                
    # --- Internal Handlers ---

    def _handle_item_clicked(self, item: QListWidgetItem) -> None:
        """
        Handles a single click on a list item.
        
        :param item: The list item that was clicked.
        :type item: :py:class:`~PyQt6.QtWidgets.QListWidgetItem`
        
        :rtype: None
        """
        type_id = item.data(self.RELATIONSHIP_TYPE_ID_ROLE)

    def _show_context_menu(self, position: QPoint) -> None:
        """
        Shows the context menu for the list widget at the right-click position.
        
        The menu contains options to "New Relationship Type" and, if an item 
        is clicked, "Edit Type Properties..." and "Delete Type".

        :param position: The position where the right-click occurred, relative to the list widget.
        :type position: :py:class:`~PyQt6.QtCore.QPoint`
        
        :rtype: None
        """
        item = self.list_widget.itemAt(position)
        
        menu = QMenu(self)
        
        # Action to always be available (Create)
        new_action = menu.addAction("New Relationship Type")
        new_action.triggered.connect(self._create_new_type)

        if item:
            # Actions available for a selected item
            edit_action = menu.addAction("Edit Type Properties...")
            delete_action = menu.addAction("Delete Type")
            
            edit_action.triggered.connect(lambda: self._call_type_editor_details(item))
            delete_action.triggered.connect(lambda: self._delete_type(item))

        menu.exec(self.list_widget.mapToGlobal(position))

    def _call_type_editor_details(self, item: QListWidgetItem) -> None:
        """
        Calls for all the details for the relationships types.
        When received it will call the _open_type_editor to ope
        up all the details.
        
        :param item: The item that was clicked on.
        :type item: QListWidgetItem

        :rtype: None
        """
        bus.publish(Events.REL_TYPE_DETAILS_REQUESTED, data={'ID': item.data(self.RELATIONSHIP_TYPE_ID_ROLE)})

    @receiver(Events.REL_TYPE_DETAILS_RETURN)
    def _open_type_editor(self, data: dict) -> None:
        """
        Opens a multi-step input dialog flow to edit the core properties of 
        the selected Relationship Type (Name, Short Label, Color, Style, Direction).

        :param data:
        :param dict:
        
        :rtype: None
        """
        type_id = data.pop('ID')
        details = data

        # Initialize and show the custom dialog
        dialog = RelationshipTypeEditorDialog(self, details)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            values = dialog.get_values()
            
            # Validation: Ensure name is not empty
            if not values.get('name'):
                QMessageBox.warning(self, "Validation Error", "Type Name cannot be empty.")
                return
            
            save_data = {
                'entity_type': EntityType.RELATIONSHIP,
                'ID': type_id,
                'type_name': values.get('name'),
                'short_label': values.get("short_label"),
                'default_color': values.get('color'),
                'is_directed': values.get('is_directed'),
                'line_style': values.get('style')
            }

            bus.publish(Events.NO_CHECK_SAVE_DATA_PROVIDED, data=save_data)
            bus.publish(Events.OUTLINE_LOAD_REQUESTED, data={'entity_type': EntityType.RELATIONSHIP})
            bus.publish(Events.GRAPH_LOAD_REQUESTED)

    def _create_new_type(self) -> None:
        """
        Handles the creation of a new relationship type by prompting the user for a name.
        
        Saves the new type with default properties to the repository, reloads 
        the list, and emits the event NEW_ITEM_REQUESTED.
        
        :rtype: None
        """
        # Define default values for a brand new relationship type
        default_details = {
            'Type_Name': '',
            'Short_Label': '',
            'Default_Color': '#FFFFFF',
            'Line_Style': 'Solid',
            'Is_Directed': 0
        }

        # Open the same dialog used for editing
        dialog = RelationshipTypeEditorDialog(self, default_details)
        dialog.setWindowTitle("Create New Relationship Type") # Override title for clarity

        if dialog.exec() == QDialog.DialogCode.Accepted:
            values = dialog.get_values()
            
            # Validation: Ensure name is not empty
            if not values.get('name'):
                QMessageBox.warning(self, "Validation Error", "Type Name cannot be empty.")
                return
            
            save_data = {
                'entity_type': EntityType.RELATIONSHIP,
                'type_name': values.get('name'),
                'short_label': values.get("short_label"),
                'default_color': values.get('color'),
                'is_directed': values.get('is_directed'),
                'line_style': values.get('style')
            }

            bus.publish(Events.NEW_ITEM_REQUESTED, data=save_data)
            bus.publish(Events.OUTLINE_LOAD_REQUESTED, data={'entity_type': EntityType.RELATIONSHIP})

    def _delete_type(self, item: QListWidgetItem) -> None:
        """
        Handles the deletion of a relationship type after user confirmation.
        
        If deleted, it removes the item from the list and emits. Warns the user 
        that all relationships of this type will also be deleted.

        :param item: The list item corresponding to the Relationship Type to be deleted.
        :type item: :py:class:`~PyQt6.QtWidgets.QListWidgetItem`
        
        :rtype: None
        """
            
        type_id = item.data(self.RELATIONSHIP_TYPE_ID_ROLE)
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
            bus.publish(Events.ITEM_DELETE_REQUESTED, data={'entity_type': EntityType.RELATIONSHIP, 'ID': type_id})
