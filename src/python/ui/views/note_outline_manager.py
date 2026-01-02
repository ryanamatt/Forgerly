# src/python/ui/views/note_outline_manger

from PySide6.QtWidgets import (
    QTreeWidgetItem, QMenu, QInputDialog, QMessageBox, QTreeWidgetItemIterator
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QIcon
from typing import Any

from .base_outline_manager import BaseOutlineManager
from ...resources_rc import *
from ...utils.constants import EntityType
from ...utils.events import Events
from ...utils.event_bus import bus, receiver


from ...repository.note_repository import NoteRepository
from ...services.app_coordinator import AppCoordinator

class NoteOutlineManager(BaseOutlineManager):
    """
    A custom :py:class:`~PySide6.QtWidgets.QWidget` dedicated to displaying the 
    hierarchical outline of Notes and other narrative elements.
    
    It interacts with the data layer via a :py:class:`.NoteRepository`.
    """

    NOTE_ID_ROLE = Qt.ItemDataRole.UserRole + 1
    """The int role used to store the database ID of a Note on an item."""

    def __init__(self, project_title: str = "Narrative Forge Project") -> None:
        """
        Initializes the :py:class:`.NoteOutlineManager`.
        
        :param note_repository: The repository object for Note CRUD operations.
        :type note_repository: :py:class:`.NoteRepository` or None, optional
        :param coordinator: The coordinator object that coordinates to the main window.
        :type coordinator: :py:class:`.AppCoordinator` or None, optional

        :rtype: None
        """

        super().__init__(
            project_title=project_title,
            header_text=f"{project_title} Notes",
            id_role=self.NOTE_ID_ROLE,
            search_placeholder="Search Notes...",
            is_nested_tree=True,
            type=EntityType.NOTE
        )

        bus.register_instance(self)

        # Connect nested-specific signals not covered by base
        self.tree_widget.item_hierarchy_updated.connect(self._handle_note_parent_update)
        self.tree_widget.item_parent_id_updated.connect(self._handle_note_parent_update)

    @receiver(Events.OUTLINE_DATA_LOADED)
    def load_outline(self, data: dict) -> None:
        """
        Loads the Notes into the outline manager.
        If notes is provided (e.g., from a search), it loads those.
        Otherwise, it loads all notes from the repository.

        :param data: A list of Notes  to load,
            default is None and will load all Notes. 
        :type data: dict

        :rtype: None
        """
        if data.get('entity_type') != EntityType.NOTE:
            return
        notes_data = data.get('notes')

        self.tree_widget.clear()

        item_map: dict[int, QTreeWidgetItem] = {}

        # Create all items and populate the map
        for note in notes_data:
            item = QTreeWidgetItem([note['Title']])
            item.setData(0, self.id_role, note['ID'])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsDropEnabled)
            item.setIcon(0, QIcon(":icons/note.svg"))
            item_map[note['ID']] = item

        # Build Hierarchy
        for note in notes_data:
            note_id = note['ID']
            parent_id = note['Parent_Note_ID']
            child_item = item_map.get(note_id)

            if parent_id is not None and parent_id in item_map:
                parent_item = item_map[parent_id]
                parent_item.addChild(child_item)
            else:
                # Add to top level if no parent or parent not in current set (e.g. filtered search)
                self.tree_widget.addTopLevelItem(child_item)
                
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
                'entity_type': EntityType.NOTE, 'query': clean_query
            })
        else:
            bus.publish(Events.OUTLINE_LOAD_REQUESTED, data={'entity_type': EntityType.NOTE})

    @receiver(Events.OUTLINE_SEARCH_RETURN)
    def _handle_search_return(self, data: dict) -> None:
        """
        Handles the return of the search query data.
        
        :param data: The return data in the form {'entity_type': EntityType.NOTE,
            'notes': dict}
        :type data: dict

        :rtype: None
        """
        search_results = data.get('notes')
        entity_type = data.get('entity_type')
        if entity_type != EntityType.NOTE: return

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
        
        The new name is saved to the database via the :py:class:`.NoteRepository`.
        
        :param item: The renamed tree item.
        :type item: :py:class:`~PySide6.QtWidgets.QTreeWidgetItem`
        :param column: The column index.
        :type column: int

        :rtype: None
        """
        note_id = item.data(0, self.id_role)
        new_title = item.text(0).strip()

        # Prevent actions if this is the root item or if the title is empty
        if note_id is None or not new_title:
            if not new_title:
                # If the title was cleared, revert the name (requires re-loading or smarter logic)
                QMessageBox.warning(self, "Invalid Title", "Note title cannot be empty. Reverting.")
                self.load_outline() 
            return

        bus.publish(Events.OUTLINE_NAME_CHANGE, data={
            'entity_type': EntityType.NOTE, 'ID': note_id, 'new_title': new_title 
        })

    def _handle_note_parent_update(self, note_id: int, new_parent_id: Any) -> None:
        """
        Calls the AppCoordinator to update the database hierarchy.
        
        :param note_id: The ID of the note to set as sub-note.
        :type note_id: int
        :param new_parent_id: The ID of the parent note.
        :type new_parent_id: int or None
        """
        bus.publish(Events.OUTLINE_PARENT_UPDATE, data={
            'entity_type': EntityType.NOTE, 'ID': note_id, 'new_parent_id': new_parent_id
        })

    def _show_context_menu(self, pos: QPoint) -> None:
        """
        Displays the context menu when right-clicked, offering options 
        like 'Add New Note' and 'Delete Note'.
        
        :param pos: The position of the right-click relative to the widget.
        :type pos: :py:class:`~PySide6.QtCore.QPoint`

        :rtype: None
        """
        item = self.tree_widget.itemAt(pos)

        menu = QMenu(self)

        new_action = menu.addAction("Add New Note...")
        new_action.triggered.connect(self.prompt_and_add_note)
        
        if item:
            is_note = item.data(0, self.id_role)

            if is_note:
                rename_action = menu.addAction("Rename Note")
                delete_action = menu.addAction("Delete Note")

                rename_action.triggered.connect(lambda: self.tree_widget.editItem(item, 0))
                delete_action.triggered.connect(lambda: self.check_save_and_delete(item))

        if menu.actions():
            menu.exec(self.mapToGlobal(pos))

    @receiver(Events.NEW_NOTE_REQUESTED)
    def prompt_and_add_note(self, data: dict = None) -> None:
        """
        Prompts the user for a new note name, creates the note in 
        the database, reloads the outline, and selects the new note.
        
        :param data: Data dictionary, Empty as function doesn't need it.
        :type data: dict
        
        :rtype: None
        """            
        title, ok = QInputDialog.getText(
            self, 
            "New Note", 
            "Enter the Title for the new Note:",
            text="New Note"
        )

        if not ok:
            return
        
        if not title:
            QMessageBox.warning(self, "Invalid Title", "Title cannot be empty.")
            return
        
        current_sort_order = self.tree_widget.topLevelItemCount() + 1
        
        bus.publish(Events.NEW_ITEM_REQUESTED, data={
            'entity_type': EntityType.NOTE, 'title': title, 'sort_order': current_sort_order
        })

    @receiver(Events.NEW_ITEM_CREATED)
    def _select_new_character(self, data: dict):
        """
        Selects the newly created note.
        
        :param data: A dictionary of the needed data containing {type: EntityType.NOTE,
        ID: int}
        :type data: dict

        :rtype: None
        """
        if data.get('entity_type') != EntityType.NOTE:
            return
        
        id = data.get('ID')
        if not id:
            return
        
        bus.publish(Events.OUTLINE_LOAD_REQUESTED, data={'entity_type': EntityType.NOTE})
        
        new_item = self.find_note_item_by_id(id)
        if new_item:
            self.tree_widget.setCurrentItem(new_item)
            self._on_item_clicked(new_item, 0)

    def _delete_note(self, item: QTreeWidgetItem) -> None:
        """
        Handles confirmation and deletion of a Note item and its corresponding 
        entry in the database.
        
        :param item: The Note item to be deleted.
        :type item: :py:class:`~PySide6.QtWidgets.QTreeWidgetItem`

        :rtype: None
        """
        note_id = item.data(0, self.id_role)
        title = item.text(0)

        if note_id is None:
            return
        
        # Confirmation Dialog
        reply = QMessageBox.question(
            self, 
            "Confirm Deletion",
            f"Are you sure you want to permanently delete the Note:\n'{title}'?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            bus.publish(Events.ITEM_DELETE_REQUESTED, {
                'entity_type': EntityType.NOTE, 'ID': note_id
            })

    def check_save_and_delete(self, item: QTreeWidgetItem) -> None:
        """
        Emits :py:attr:`.pre_note_change` to ensure the currently viewed 
        Note is saved, then triggers the deletion process.

        :param item: The Note item queued for deletion.
        :type item: :py:class:`~PySide6.QtWidgets.QTreeWidgetItem`

        :rtype: None
        """
        bus.publish(Events.PRE_ITEM_CHANGE, data={'entity_type': EntityType.NOTE, 'ID': self.current_item_id, 'parent': self})
        self._delete_note(item)

    def find_note_item_by_id(self, note_id: int) -> QTreeWidgetItem | None:
        """
        Helper to find a Note :py:class:`~PySide6.QtWidgets.QTreeWidgetItem` 
        by its stored database ID.
        
        :param char_id: The unique ID of the Note to find.
        :type char_id: int

        :returns: The matching item or None
        :rtype: :py:class:`~PySide6.QtWidgets.QTreeWidgetItem` or None
        """
        iterator = QTreeWidgetItemIterator(self.tree_widget)
        while iterator.value():
            item = iterator.value()
            if item.data(0, self.id_role) == note_id:
                return item
            iterator += 1
        return None
