# src/python/ui/views/relationship_outline_manager.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QMenu, QMessageBox, QDialog, QLabel, QTabWidget, QFrame
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor, QIcon

from ...resources_rc import *
from ..dialogs.relationship_type_editor_dialog import RelationshipTypeEditorDialog
from ..dialogs.char_node_editor_dialog import CharNodeEditorDialog
from ...utils.constants import EntityType
from ...utils.events import Events
from ...utils.event_bus import bus, receiver

class RelationshipOutlineManager(QWidget):
    """
    A custom :py:class:`~PySide6.QtWidgets.QWidget` dedicated to displaying 
    and managing the list of Relationship Types. 
    
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
        self.tabs = QTabWidget()
        self.tabs.setUsesScrollButtons(False)
        self.tabs.setElideMode(Qt.TextElideMode.ElideRight)
        self.tabs.tabBar().setExpanding(True)
        self.tabs.tabBar().setDocumentMode(True)

        self.rel_types_tab = QWidget()
        self.characters_tab = QWidget()

        # List For Relationship Types
        self.rel_type_list_widget = QListWidget()
        self.rel_type_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        self.new_button = QPushButton("New Relationship Type")

        # List for Characters
        self.char_list_widget = QListWidget()
        self.char_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        # --- Layout Setup ---
        tab_layout = QVBoxLayout(self.rel_types_tab)

        # Buttons/Actions area
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.new_button)
        
        tab_layout.addLayout(button_layout)
        tab_layout.addWidget(self.rel_type_list_widget)

        self.tabs.addTab(self.rel_types_tab, 'Relationship Types (Edges)')
        self.tabs.addTab(self.characters_tab, "Characters (Nodes)")

        # Layout for Characters Tab
        char_tab_layout = QVBoxLayout(self.characters_tab)
        char_tab_label = QLabel("Characters")
        char_tab_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        char_tab_layout.addWidget(char_tab_label)
        char_tab_layout.addWidget(self.char_list_widget)

        # 1. Create the Frame
        self.container_frame = QFrame()
        self.container_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.container_frame.setFrameShadow(QFrame.Shadow.Raised)

        # 2. Put the tabs inside the frame's layout
        frame_layout = QVBoxLayout(self.container_frame)
        frame_layout.setContentsMargins(1, 1, 1, 1) # Control thickness of the "padding"
        frame_layout.addWidget(self.tabs)

        # 3. Add the frame to the main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container_frame)


        # --- Connections ---
        self.new_button.clicked.connect(self._create_new_type)

        # List Widget
        self.rel_type_list_widget.customContextMenuRequested.connect(self._show_rel_type_context_menu)
        self.rel_type_list_widget.itemDoubleClicked.connect(self._call_type_editor_details)

        # Char List Widget
        self.char_list_widget.customContextMenuRequested.connect(self._show_char_context_menu)
        self.char_list_widget.itemDoubleClicked.connect(self._call_char_editor_details)
        
    @receiver(Events.OUTLINE_DATA_LOADED)
    @receiver(Events.REL_CHAR_DATA_RETURN)
    def load_outline(self, data: dict) -> None:
        """
        Loads all relationship types from the database via the repository and 
        populates the internal :py:class:`~PySide6.QtWidgets.QListWidget`.
        
        Each item is set with the name as text and its ID and color in the data roles.

        :param data: A dictionary of the needed data containg {entity_type: EntityType.RELATIONSHIP,
            'relationship_types': dict or 'characters': dict}
        :type data: dict
        
        :rtype: None
        """
        entity_type = data.get('entity_type')
        rel_types = data.get('relationship_types')
        characters = data.get('characters')

        if entity_type != EntityType.RELATIONSHIP: 
            return
                        
        if rel_types is not None:
            self.rel_type_list_widget.clear()
            for rel_type in rel_types:
                self._add_rel_type_item(rel_type)
            
        if characters is not None:
            self.char_list_widget.clear()
            for char in characters:
                self._add_character_item(char)

    def _add_rel_type_item(self, rel_type: dict) -> None:
        """
        Helper to add a Relationship Type Item to the 
        Relationship Type List.
        
        :param rel_type: The dictionary of the Rel Type data.
        :type rel_type: dict

        :rtype: None
        """
        type_id = rel_type['ID']
        name = rel_type['Type_Name']
        color = rel_type.get('Default_Color', '#000000') # Default to black
        
        # Create Item
        item = QListWidgetItem(name)
        # Store the Type ID and Color for later use
        item.setData(self.RELATIONSHIP_TYPE_ID_ROLE, type_id)
        # Store Visibility (Default True)
        item.setData(Qt.ItemDataRole.UserRole + 2, True)

        # Create a custom widget for the row
        row_widget = QWidget()
        row_widget.setFixedHeight(36)
        layout = QHBoxLayout(row_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        layout.setContentsMargins(4, 4, 4, 4)

        # Label for Name
        name_label = QLabel(name)
        name_label.setStyleSheet(f"color: {color}; font-weight: bold;")

        # Toggle Visibility Button
        toggle_btn = QPushButton()
        toggle_btn.setFixedSize(24, 24)
        toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent; 
                padding: 0px; 
                margin: 0px;
            }
        """)
        toggle_btn.setIcon(QIcon(":icons/visible-on.svg"))

        toggle_btn.clicked.connect(lambda checked=False, i=item, b=toggle_btn: self._toggle_visibility(i, b))

        layout.addWidget(name_label)
        layout.addStretch()
        layout.addWidget(toggle_btn)

        item.setSizeHint(row_widget.sizeHint())
        self.rel_type_list_widget.addItem(item)
        self.rel_type_list_widget.setItemWidget(item, row_widget)

    def _add_character_item(self, char: dict) -> None:
        """
        Helper to add a Character Item to the 
        Char List.
        
        :param rel_type: The dictionary of the Character data.
        :type rel_type: dict

        :rtype: None
        """
        char_id = char['ID']
        name = char.get('Name', 'Unknown')

        is_visible = not char.get('Is_Hidden', 0)
        
        item = QListWidgetItem(name)
        item.setData(Qt.ItemDataRole.UserRole + 1, char_id)
        item.setData(Qt.ItemDataRole.UserRole + 2, is_visible) # Default visible

        row_widget = QWidget()
        row_widget.setFixedHeight(36)
        layout = QHBoxLayout(row_widget)
        layout.setContentsMargins(4, 4, 4, 4)

        name_label = QLabel(name)
        
        toggle_btn = QPushButton()
        toggle_btn.setFixedSize(24, 24)
        toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent; 
                padding: 0px; 
                margin: 0px;
            }
        """)
        icon_path = ":icons/visible-on" if is_visible else ":icons/visible-off"
        toggle_btn.setIcon(QIcon(icon_path))
        
        # Use a lambda that specifically targets the node visibility event
        toggle_btn.clicked.connect(
            lambda checked=False, i=item, b=toggle_btn: self._toggle_node_visibility(i, b)
        )

        layout.addWidget(name_label)
        layout.addStretch()
        layout.addWidget(toggle_btn)

        item.setSizeHint(row_widget.sizeHint())
        self.char_list_widget.addItem(item)
        self.char_list_widget.setItemWidget(item, row_widget)
                                
    # --- Internal Handlers ---

    def _toggle_visibility(self, item: QListWidgetItem, button: QPushButton) -> None:
        """
        Switches visibility state and updates the UI and Graph.
        
        :param item: The Item button clicked on.
        :type item: QListWidgetItem
        :param button: The button clicked on
        :type button: QPushButton

        :rtype: None
        """
        current_state = item.data(Qt.ItemDataRole.UserRole + 2)
        new_state = not current_state

        item.setData(Qt.ItemDataRole.UserRole + 2, new_state)
        icon_path = ":icons/visible-on" if new_state else ":icons/visible-off"
        button.setIcon(QIcon(icon_path))

        type_id = item.data(self.RELATIONSHIP_TYPE_ID_ROLE)
        bus.publish(Events.GRAPH_EDGE_VISIBILITY_CHANGED, data={
            'type_id': type_id, 'visible': new_state
        })

    def _toggle_node_visibility(self, item: QListWidgetItem, button: QPushButton) -> None:
        """
        Toggles the visibility of a Node.
        
        :param item: The item to toggle its visibility.
        :type item: QListWidgetItem
        :param button: The visibility button.
        :type button: QPushButton

        :rtype: None
        """
        current_state = item.data(Qt.ItemDataRole.UserRole + 2)
        new_state = not current_state

        item.setData(Qt.ItemDataRole.UserRole + 2, new_state)
        icon_path = ":icons/visible-on" if new_state else ":icons/visible-off"
        button.setIcon(QIcon(icon_path))

        char_id = item.data(Qt.ItemDataRole.UserRole + 1)
        
        # Publish the event for the Graph/Coordinator to hide the Node
        bus.publish(Events.GRAPH_NODE_VISIBILTY_CHANGED, data={
            'ID': char_id, 'is_hidden': not new_state
        })

    @receiver(Events.GRAPH_NODE_VISIBILTY_CHANGED)
    def sync_node_visibility_ui(self, data: dict) -> None:
        """
        Updates the character list icon when visibility is toggled from the graph.

        :param data: dict: Data dict carrying {'ID': int, 'is_hidden': bool}
        :type: data: dict:

        :rtype:None
        """
        char_id = data.get('ID')
        is_hidden = data.get('is_hidden')
        is_visible = not is_hidden

        # Find the item in the char_list_widget
        for i in range(self.char_list_widget.count()):
            item = self.char_list_widget.item(i)

            if item.data(Qt.ItemDataRole.UserRole + 1) == char_id:
                # Update the stored data state
                item.setData(Qt.ItemDataRole.UserRole + 2, is_visible)
                
                # Update the widget icon
                row_widget = self.char_list_widget.itemWidget(item)
                if row_widget:
                    # Assuming the toggle button is the last widget added to the layout
                    toggle_btn = row_widget.layout().itemAt(row_widget.layout().count() - 1).widget()
                    icon_path = ":icons/visible-on.svg" if is_visible else ":icons/visible-off.svg"
                    toggle_btn.setIcon(QIcon(icon_path))
                break

    # --- Rel Types Functions ---

    def _show_rel_type_context_menu(self, position: QPoint) -> None:
        """
        Shows the context menu for the relationship types list widget at the right-click position.
        
        The menu contains options to "New Relationship Type" and, if an item 
        is clicked, "Edit Type Properties..." and "Delete Type".

        :param position: The position where the right-click occurred, relative to the list widget.
        :type position: :py:class:`~PySide6.QtCore.QPoint`
        
        :rtype: None
        """
        item = self.rel_type_list_widget.itemAt(position)
        
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

        menu.exec(self.rel_type_list_widget.mapToGlobal(position))

    def _call_type_editor_details(self, item: QListWidgetItem) -> None:
        """
        Calls for all the details for the relationships types.
        When received it will call the _open_type_editor to ope
        up all the details.
        
        :param item: The item that was clicked on.
        :type item: QListWidgetItem

        :rtype: None
        """
        type_id = item.data(self.RELATIONSHIP_TYPE_ID_ROLE)
        bus.publish(Events.REL_TYPE_DETAILS_REQUESTED, data={'ID': type_id})

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
        dialog = RelationshipTypeEditorDialog(details, self)
        
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
            bus.publish(Events.REL_CHAR_DATA_REQUESTED)

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
        dialog = RelationshipTypeEditorDialog(details=default_details, parent=self)
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
        :type item: :py:class:`~PySide6.QtWidgets.QListWidgetItem`
        
        :rtype: None
        """
            
        type_id = item.data(self.RELATIONSHIP_TYPE_ID_ROLE)
        name = item.text()
        
        # Confirmation Dialog
        reply = QMessageBox.question(
            self, 
            "Confirm Deletion",
            f"Are you sure you want to permanently delete the Relationship Type: \n'{name}'?\n\nThis"
             " will also delete ALL character relationships of this type. This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            bus.publish(Events.ITEM_DELETE_REQUESTED, data={'entity_type': EntityType.RELATIONSHIP, 'ID': type_id})

    # --- Char Related Functions ---

    def _show_char_context_menu(self, position: QPoint) -> None:
        """
        Shows the context menu for the characters list widget at the right-click position.

        :param position: The position where the right-click occurred, relative to the list widget.
        :type position: :py:class:`~PySide6.QtCore.QPoint`
        
        :rtype: None
        """
        item = self.char_list_widget.itemAt(position)
        
        menu = QMenu(self)

        if item:
            # Actions available for a selected item
            edit_action = menu.addAction("Edit Character Node Properties...")
            
            edit_action.triggered.connect(lambda: self._call_char_editor_details(item))

        menu.exec(self.char_list_widget.mapToGlobal(position))

    def _call_char_editor_details(self, item: QListWidgetItem) -> None:
        """
        Calls for all the details for the character node.
        When received it will call the _open_type_editor to open
        up all the details.
        
        :param item: The item that was clicked on.
        :type item: QListWidgetItem

        :rtype: None
        """
        char_id = item.data(Qt.ItemDataRole.UserRole + 1)
        bus.publish(Events.REL_CHAR_DETAILS_REQUESTED, data={'ID': char_id})

    @receiver(Events.REL_CHAR_DETAILS_RETURN)
    def _open_char_editor(self, data: dict) -> None:
        """
        Opens a multi-step input dialog flow to edit the core properties of 
        the selected character node (Node_Color, Node_Shape, Is_Hidden, Is_Locked).

        :param data: The dict of data needed to open the char editor.
        :type data: dict
        
        :rtype: None
        """
        char_id = data.pop('ID')
        
        dialog = CharNodeEditorDialog(data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            save_data = dialog.get_values()
            
            save_data.update({'ID': char_id})

            save_data.pop('name')

            # Save and Refresh
            bus.publish(Events.REL_CHAR_DETAILS_SAVE, data=save_data)
            bus.publish(Events.REL_CHAR_DATA_REQUESTED, data={'entity_type': EntityType.RELATIONSHIP})
            bus.publish(Events.GRAPH_LOAD_REQUESTED)
            bus.publish(Events.REL_CHAR_DATA_REQUESTED)