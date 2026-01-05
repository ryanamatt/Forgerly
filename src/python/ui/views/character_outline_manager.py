# src/python/ui/views/character_outline_manager.py

from PySide6.QtWidgets import (
    QTreeWidgetItem, QMenu, QInputDialog, QMessageBox, QTreeWidgetItemIterator, QTreeWidget
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QIcon

from .base_outline_manager import BaseOutlineManager
from ...resources_rc import *
from ...utils.constants import EntityType
from ...utils.events import Events
from ...utils.event_bus import bus, receiver

class CharacterOutlineManager(BaseOutlineManager):
    """
    A custom widget for managing the outline and hierarchy of Characters.
    
    It combines a search bar (:py:class:`~PySide6.QtWidgets.QLineEdit`) and a 
    tree structure (:py:class:`~PySide6.QtWidgets.QTreeWidget`) for navigation.
    It interacts with the data layer via a :py:class:`.CharacterRepository`.
    """

    CHARACTER_ID_ROLE = Qt.ItemDataRole.UserRole + 1
    """The :py:obj:`int` role used to store the database ID of a Character on an item."""

    def __init__(self, project_title: str = "Narrative Forge Project") -> None:
        """
        Initializes the :py:class:`.CharacterOutlineManager`.
        
        :param project_title: The Title of the Current Project.
        :type project_title: str

        :rtype: None
        """
        super().__init__(
            project_title=project_title,
            header_text="Characters",
            id_role=self.CHARACTER_ID_ROLE,
            search_placeholder="Search Characters...",
            is_nested_tree=False,
            type=EntityType.CHARACTER
        )

        bus.register_instance(self)

        # Turn off Drag and Drop for tree widget
        self.tree_widget.setDragEnabled(True)
        self.tree_widget.setAcceptDrops(True)
        self.tree_widget.setDropIndicatorShown(True)
        self.tree_widget.setDragDropMode(QTreeWidget.DragDropMode.NoDragDrop)
        
    @receiver(Events.OUTLINE_DATA_LOADED)
    def load_outline(self, data: dict) -> None:
        """
        Fetches all characters from the database and populates the 
        :py:class:`~PySide6.QtWidgets.QTreeWidget`.
        
        It attempts to restore the selection if a character was previously selected.
        
        :rtype: None
        """
        entity_type = data.get('entity_type')
        char_data = data.get('characters')
        if entity_type != EntityType.CHARACTER or not char_data: 
            return

        self.tree_widget.clear()

        for character in char_data:
            name = character.get("Name", "Unnamed")

            item = QTreeWidgetItem([name])
            item.setData(0, self.id_role, character["ID"])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            item.setIcon(0, QIcon(":icons/character.svg"))

            self.tree_widget.addTopLevelItem(item)

        self.tree_widget.expandAll()

    def _send_search_request(self, query: str) -> None:
        """
        Filters the visible items in the outline based on the text entered in 
        the search bar.
        
        The search is case-insensitive.
        
        :param text: The current text in the search input field.
        :type text: :py:class:`str`

        :rtype: None
        """
        clean_query = query.strip()
        if clean_query:
            bus.publish(Events.OUTLINE_SEARCH_REQUESTED, data={
                'entity_type': EntityType.CHARACTER, 'query': clean_query
            })
        else:
            bus.publish(Events.OUTLINE_LOAD_REQUESTED, data={'entity_type': EntityType.CHARACTER})

    @receiver(Events.OUTLINE_SEARCH_RETURN)
    def _handle_search_return(self, data: dict) -> None:
        """
        Handles the return of the neede search data.
        
        :param data: The return search data containing
            {'entity_type': EntityType.CHARACTER, 'characters': dict}
        :type data: dict

        :rtype: None
        """
        search_results = data.get('characters')
        entity_type = data.get('entity_type')
        if entity_type != EntityType.CHARACTER: return

        if search_results:
            self.load_outline(data)
        else:
            self.tree_widget.clear()
            no_result_item = QTreeWidgetItem(self.tree_widget, ["No search results found."])
            no_result_item.setData(0, self.id_role, -1)
            self.tree_widget.expandAll()

    def _handle_item_renamed(self, item: QTreeWidgetItem, column: int) -> None:
        """
        Handles the signal emitted when a tree item has been successfully renamed.
        
        The new name is saved to the database via the :py:class:`.CharacterRepository`.
        
        :param item: The renamed tree item.
        :type item: :py:class:`~PySide6.QtWidgets.QTreeWidgetItem`
        :param column: The column index.
        :type column: int

        :rtype: None
        """
        char_id = item.data(0, self.id_role)
        new_name = item.text(0).strip()

        # Prevent actions if this is the root item or if the title is empty
        if char_id is None or not new_name:
            if not new_name:
                # If the title was cleared, revert the name (requires re-loading or smarter logic)
                QMessageBox.warning(self, "Invalid Name", "Character name cannot be empty. Reverting.")
                self.load_outline() 
            return

        bus.publish(Events.OUTLINE_NAME_CHANGE, data={
            'entity_type': EntityType.CHARACTER, 'ID': char_id, 'new_title': new_name 
        })

    def _show_context_menu(self, pos: QPoint) -> None:
        """
        Displays the context menu when right-clicked, offering options 
        like 'Add New Character' and 'Delete Character'.
        
        :param pos: The position of the right-click relative to the widget.
        :type pos: :py:class:`~PySide6.QtCore.QPoint`

        :rtype: None
        """
        item = self.tree_widget.itemAt(pos)

        menu = QMenu(self)

        # New Character Action
        new_action = menu.addAction("Add New Character...")
        new_action.triggered.connect(self.prompt_and_add_character)

        if item:
            is_character = item.data(0, self.id_role) is not None

            if is_character:
                rename_action = menu.addAction("Rename Character")
                delete_action = menu.addAction("Delete Character")
                
                rename_action.triggered.connect(lambda: self.editItem(item, 0))
                # Wrap the delete action to ensure save check occurs
                delete_action.triggered.connect(lambda: self.check_save_and_delete(item))

        # Show the menu
        if menu.actions():
            menu.exec(self.mapToGlobal(pos))
        
    @receiver(Events.NEW_CHARACTER_REQUESTED)
    def prompt_and_add_character(self, data: dict = None) -> None:
        """
        Prompts the user for a new character name, creates the character in the 
        database, reloads the outline, and selects the new character.
        
        :param data: Data dictionary, Empty as function doesn't need it.
        :type data: dict
        
        :rtype: None
        """        
        name, ok = QInputDialog.getText(
            self, 
            "New Character", 
            "Enter the name for the new character:",
            text="New Character"
        )

        if not ok:
            return
        
        if not name:
            QMessageBox.warning(self, "Invalid Name", "Name cannot be empty.")
            return
        
        bus.publish(Events.NEW_ITEM_REQUESTED, data={
            'entity_type': EntityType.CHARACTER, 'title': name
        })

    @receiver(Events.NEW_ITEM_CREATED)
    def _select_new_character(self, data: dict):
        """
        Selects the newly created Character
        
        :param data: A dictionary of the needed data containing {type: EntityType.Character,
        ID: int}
        :type data: dict

        :rtype: None
        """
        if data.get('entity_type') != EntityType.CHARACTER:
            return
        
        id = data.get('ID')
        if not id:
            return
        
        bus.publish(Events.OUTLINE_LOAD_REQUESTED, data={'entity_type': EntityType.CHARACTER})
        
        new_item = self.find_character_item_by_id(id)
        if new_item:
            self.tree_widget.setCurrentItem(new_item)
            self._on_item_clicked(new_item, 0)


    def _delete_chapter(self, item: QTreeWidgetItem) -> None:
        """
        Handles confirmation and deletion of a character item and its corresponding 
        entry in the database.
        
        :param item: The character item to be deleted.
        :type item: :py:class:`~PySide6.QtWidgets.QTreeWidgetItem`

        :rtype: None
        """
        character_id = item.data(0, self.id_role)
        title = item.text(0)
        
        if character_id is None:
            return
            
        # Confirmation Dialog
        reply = QMessageBox.question(
            self, 
            "Confirm Deletion",
            f"Are you sure you want to permanently delete the chapter:\n'{title}'?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            bus.publish(Events.ITEM_DELETE_REQUESTED, data={
                'entity_type': EntityType.CHARACTER, 'ID': character_id
            })

    def check_save_and_delete(self, item: QTreeWidgetItem) -> None:
        """
        Emits :py:attr:`.pre_char_change` to ensure the currently viewed 
        character is saved, then triggers the deletion process.

        :param item: The character item queued for deletion.
        :type item: :py:class:`~PySide6.QtWidgets.QTreeWidgetItem`

        :rtype: None
        """
        bus.publish(Events.PRE_ITEM_CHANGE, data={'entity_type': EntityType.CHARACTER, 
                                                  'ID': self.current_item_id, 'parent': self})
        self._delete_chapter(item)

    def find_character_item_by_id(self, char_id: int) -> QTreeWidgetItem | None:
        """
        Helper to find a character :py:class:`~PySide6.QtWidgets.QTreeWidgetItem` 
        by its stored database ID.
        
        :param char_id: The unique ID of the character to find.
        :type char_id: int

        :returns: The matching item or None
        :rtype: :py:class:`~PySide6.QtWidgets.QTreeWidgetItem` or None
        """
        iterator = QTreeWidgetItemIterator(self.tree_widget)
        while iterator.value():
            item = iterator.value()
            if item.data(0, self.id_role) == char_id:
                return item
            iterator += 1
        return None
