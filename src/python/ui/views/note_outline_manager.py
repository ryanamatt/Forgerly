# src/python/ui/views/note_outline_manger

from PyQt6.QtWidgets import (
    QTreeWidgetItem, QMenu, QInputDialog, QMessageBox, QTreeWidgetItemIterator
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QIcon
from typing import Any

from .base_outline_manager import BaseOutlineManager
from ...resources_rc import *
from ...repository.note_repository import NoteRepository

from ...services.app_coordinator import AppCoordinator

class NoteOutlineManager(BaseOutlineManager):
    """
    A custom :py:class:`~PyQt6.QtWidgets.QWidget` dedicated to displaying the 
    hierarchical outline of Notes and other narrative elements.
    
    It interacts with the data layer via a :py:class:`.NoteRepository`.
    """

    NOTE_ID_ROLE = Qt.ItemDataRole.UserRole + 1
    """The int role used to store the database ID of a Note on an item."""

    def __init__(self, project_title: str = "Narrative Forge Project", note_repository: NoteRepository | None = None, coordinator: AppCoordinator | None = None) -> None:
        """
        Initializes the :py:class:`.NoteOutlineManager`.
        
        :param note_repository: The repository object for Note CRUD operations.
        :type note_repository: :py:class:`.NoteRepository` or None, optional
        :param coordinator: The coordinator object that coordinates to the main window.
        :type coordinator: :py:class:`.AppCoordinator` or None, optional

        :rtype: None
        """
        

        self.note_repo = note_repository
        self.coordinator = coordinator

        super().__init__(
            project_title=project_title,
            header_text=f"{project_title} Notes",
            id_role=self.NOTE_ID_ROLE,
            search_placeholder="Search Notes...",
            is_nested_tree=True
        )

        # Connect nested-specific signals not covered by base
        self.tree_widget.item_hierarchy_updated.connect(self._handle_note_parent_update)
        self.tree_widget.item_parent_id_updated.connect(self._handle_note_parent_update)

        # Load the initial structure
        self.load_outline()

    def load_outline(self, notes: list[dict] | None = None) -> None:
        """
        Loads the Notes into the outline manager.
        If notes is provided (e.g., from a search), it loads those.
        Otherwise, it loads all notes from the repository.

        :param notes: A list of Notes  to load,
            default is None and will load all Notes. 
        :type notes: list[dict], optional

        :rtype: None
        """
        if not self.note_repo:
            return
        
        # Fetch all notes if notes is none
        if notes is None:
            notes = self.note_repo.get_all_notes()

        self.tree_widget.clear()

        if not notes: return

        item_map: dict[int, QTreeWidgetItem] = {}

        # Create all items and populate the map
        for note in notes:
            item = QTreeWidgetItem([note['Title']])
            item.setData(0, self.id_role, note['ID'])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsDropEnabled)
            item.setIcon(0, QIcon(":icons/note.svg"))
            item_map[note['ID']] = item

        # Build Hierarchy
        for note in notes:
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

    def _handle_search_input(self, query: str) -> None:
        """
        Handles text changes in the search bar. 
        Performs SQL Like search or reverts to the full outline.

        :param query: The search query to search for.
        :type query: str

        :rtype: None
        """
        clean_query = query.strip()

        if clean_query and self.note_repo:
            search_results = self.note_repo.search_notes(clean_query)
            if search_results:
                self.load_outline(search_results)
            else:
                self.tree_widget.clear()
                no_result_item = QTreeWidgetItem(self.tree_widget, ["No search results found."])
                no_result_item.setData(0, self.id_role, -1)
                self.tree_widget.expandAll()
        
        # Search is cleared, revert to full outline
        elif not clean_query:
            self.load_outline()

    def _handle_item_renamed(self, item: QTreeWidgetItem, column: int) -> None:
        """
        Handles the signal emitted when a tree item has been successfully renamed.
        
        The new name is saved to the database via the :py:class:`.NoteRepository`.
        
        :param item: The renamed tree item.
        :type item: :py:class:`~PyQt6.QtWidgets.QTreeWidgetItem`
        :param column: The column index.
        :type column: int

        :rtype: None
        """
        note_id = item.data(0, self.id_role)
        new_title = item.text(0).strip()
        
        # Handle missing repository or root item
        if not self.note_repo:
            QMessageBox.critical(self, "Internal Error", "NoteRepository is missing.")
            return

        # 1. Prevent action if this is the root item (ID is None)
        if note_id is None:
            item.setText(0, "World Notes") # Revert name
            return
        
        # 2. Handle empty title
        if not new_title:
            QMessageBox.warning(self, "Invalid Title", "Note title cannot be empty. Reverting.")
            self.load_outline() 
            return # Exit after handling invalid title
        
        # 3. Check if title actually changed
        current_db_title = self.note_repo.get_note_title(note_id)
        if current_db_title and current_db_title == new_title:
            return
        
        # 4. Perform the database update
        # Assuming your update method expects `id` and named parameters for updates
        success = self.note_repo.update_note_title(note_id, new_title)

        if not success:
            QMessageBox.critical(self, f"Database Error", "Failed to update Note title in the database. ID: {note_id}")
            self.load_outline()

    def _handle_note_parent_update(self, note_id: int, new_parent_id: Any) -> None:
        """
        Calls the AppCoordinator to update the database hierarchy.
        
        :param note_id: The ID of the note to set as sub-note.
        :type note_id: int
        :param new_parent_id: The ID of the parent note.
        :type new_parent_id: int or None
        """
        if not self.coordinator.update_note_parent_id(note_id, new_parent_id):
            QMessageBox.critical(self, "Hierarchy Error", 
                                 "Database update failed. Reverting note outline.")
            self.load_outline()

    def _show_context_menu(self, pos: QPoint) -> None:
        """
        Displays the context menu when right-clicked, offering options 
        like 'Add New Note' and 'Delete Note'.
        
        :param pos: The position of the right-click relative to the widget.
        :type pos: :py:class:`~PyQt6.QtCore.QPoint`

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

    def prompt_and_add_note(self) -> None:
        """
        Prompts the user for a new note name, creates the note in 
        the database, reloads the outline, and selects the new note.
        
        Emits :py:attr:`.pre_note_change` before prompting.
        
        :rtype: None
        """
    
        if not self.note_repo:
            QMessageBox.critical(self, "Internal Error", "NoteRepository is missing.")
            return
        
        # Check save status before creating a new note (which implicitly changes selection)
        self.pre_item_change.emit()

        title, ok = QInputDialog.getText(
            self,
            "New Note",
            "Enter the title for the new note",
            text="New Note"
        )

        if ok and title:
            current_sort_order = self.tree_widget.topLevelItemCount() + 1
            
            new_id = self.note_repo.create_note(title=title, sort_order=current_sort_order + 1)
            
            if new_id:
                self.new_item_created.emit()
                self.load_outline()
                new_item = self.find_note_item_by_id(new_id)
                if new_item:
                    self.tree_widget.setCurrentItem(new_item)
                    self._on_item_clicked(new_item, 0)
        else:
            QMessageBox.warning(self, "Database Error", "Failed to save the new Note to the database.")

    def _delete_note(self, item: QTreeWidgetItem) -> None:
        """
        Handles confirmation and deletion of a Note item and its corresponding 
        entry in the database.
        
        :param item: The Note item to be deleted.
        :type item: :py:class:`~PyQt6.QtWidgets.QTreeWidgetItem`

        :rtype: None
        """
        note_id = item.data(0, self.id_role)
        title = item.text(0)

        if note_id is None:
            return
        
        if not self.note_repo:
            QMessageBox.critical(self, "Internal Error", "NoteRepository is missing.")
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
            if self.note_repo.delete_note(note_id=note_id):
                self.load_outline()

    def check_save_and_delete(self, item: QTreeWidgetItem) -> None:
        """
        Emits :py:attr:`.pre_note_change` to ensure the currently viewed 
        Note is saved, then triggers the deletion process.

        :param item: The Note item queued for deletion.
        :type item: :py:class:`~PyQt6.QtWidgets.QTreeWidgetItem`

        :rtype: None
        """
        self.pre_item_change.emit()
        self._delete_note(item)

    def find_note_item_by_id(self, note_id: int) -> QTreeWidgetItem | None:
        """
        Helper to find a Note :py:class:`~PyQt6.QtWidgets.QTreeWidgetItem` 
        by its stored database ID.
        
        :param char_id: The unique ID of the Note to find.
        :type char_id: int

        :returns: The matching item or None
        :rtype: :py:class:`~PyQt6.QtWidgets.QTreeWidgetItem` or None
        """
        iterator = QTreeWidgetItemIterator(self.tree_widget)
        while iterator.value():
            item = iterator.value()
            if item.data(0, self.id_role) == note_id:
                return item
            iterator += 1
        return None