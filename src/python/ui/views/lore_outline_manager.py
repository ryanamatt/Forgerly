# src/python/ui/lore_outline_manager.py

from PySide6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QMenu, QInputDialog, QMessageBox, QTreeWidgetItemIterator
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QIcon
from typing import Any

from .base_outline_manager import BaseOutlineManager
from ...resources_rc import *
from ...repository.lore_repository import LoreRepository

from ...services.app_coordinator import AppCoordinator

class LoreOutlineManager(BaseOutlineManager):
    """
    A custom :py:class:`~PyQt6.QtWidgets.QWidget` dedicated to displaying the 
    hierarchical outline of Lore Entries and other narrative elements.
    
    Inherits from BaseOutlineManager.
    """

    LORE_ID_ROLE = Qt.ItemDataRole.UserRole + 1
    """The int role used to store the database ID of a Lore Entry on an item."""

    def __init__(self, project_title: str = "Narrative Forge Project", lore_repository: LoreRepository | None = None, 
                 coordinator: AppCoordinator | None = None) -> None:
        """
        Initializes the :py:class:`.LoreOutlineManager`.
        
        :param project_title: The title of the project.
        :type project_title: str
        :param lore_repository: The repository object for Lore Entry CRUD operations.
        :type lore_repository: :py:class:`.LoreRepository` or None, optional
        :param coordinator: The coordinator object that coordinates to the main window.
        :type coordinator: :py:class:`.AppCoordinator` or None, optional

        :rtype: None
        """
        self.lore_repo = lore_repository
        self.coordinator = coordinator

        super().__init__(
            project_title=project_title,
            header_text="Lore Entries",
            id_role=self.LORE_ID_ROLE,
            search_placeholder="Search Lore Entries...",
            is_nested_tree=True
        )

        # Connect nested-specific signals not covered by base
        self.tree_widget.item_hierarchy_updated.connect(self._handle_lore_parent_update)
        self.tree_widget.item_parent_id_updated.connect(self._handle_lore_parent_update)

        # Load the initial structure
        self.load_outline()

    def load_outline(self, lore_entries: list[dict] | None = None) -> None:
        """
        Loads the Lore Entries into the outline manager.
        If lore_entries is provided (e.g., from a search), it loads those.
        Otherwise, it loads all entries from the repository.

        :param lore_entries: A list of Lore Entries to load,
            default is None and will load all Lore Entries. 
        :type lore_entries: list[dict], optional

        :rtype: None
        """
        if not self.lore_repo:
            return

        # Fetch all entries if none are provided (default mode)
        if lore_entries is None:
            lore_entries = self.lore_repo.get_all_lore_entries()
            
        self.tree_widget.clear()
        
        # Add all fetched lore entries as children
        if not lore_entries: return

        item_map: dict[int, QTreeWidgetItem] = {}

        # Create all items and populate the map
        for entry in lore_entries:
            item = QTreeWidgetItem([entry['Title']])
            item.setData(0, self.id_role, entry['ID'])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable 
                          | Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsDropEnabled)
            item.setIcon(0, QIcon(":icons/lore-entry.svg"))
            item_map[entry['ID']] = item

        # Build Hierarchy
        for entry in lore_entries:
            lore_id = entry.get('ID')
            parent_id = entry.get('Parent_Lore_ID')
            child_item = item_map.get(lore_id)

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

        if clean_query and self.lore_repo:
            search_results = self.lore_repo.search_lore_entries(clean_query)
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
        
        The new name is saved to the database via the :py:class:`.LoreRepository`.
        
        :param item: The renamed tree item.
        :type item: :py:class:`~PyQt6.QtWidgets.QTreeWidgetItem`
        :param column: The column index.
        :type column: int

        :rtype: None
        """
        lore_id = item.data(0, self.id_role)
        new_title = item.text(0).strip()
        
        # Handle missing repository or root item
        if not self.lore_repo:
            QMessageBox.critical(self, "Internal Error", "LoreRepository is missing.")
            return

        # 1. Prevent action if this is the root item (ID is None)
        if lore_id is None:
            item.setText(0, "World Lore Base") # Revert name
            return
        
        # 2. Handle empty title
        if not new_title:
            QMessageBox.warning(self, "Invalid Title", "Lore Entry title cannot be empty. Reverting.")
            self.load_outline() 
            return # Exit after handling invalid title
        
        # 3. Check if title actually changed
        current_db_title = self.lore_repo.get_lore_entry_title(lore_id)
        if current_db_title and current_db_title == new_title:
            return
        
        # 4. Perform the database update
        # Assuming your update method expects `id` and named parameters for updates
        success = self.lore_repo.update_lore_entry_title(lore_id, new_title)

        if not success:
            QMessageBox.critical(self, "Database Error", "Failed to update Lore Entry title in the database.")
            self.load_outline()

    def _handle_lore_parent_update(self, lore_id: int, new_parent_id: Any) -> None:
        """
        Calls the AppCoordinator to update the database hierarchy.
        
        :param lore_id: The ID of the lore entry to set as sub-entry.
        :type lore_id: int
        :param new_parent_id: The ID of the parent lore entry.
        :type new_parent_id: int or None
        """
        if not self.coordinator.update_lore_parent_id(lore_id, new_parent_id):
            QMessageBox.critical(self, "Hierarchy Error", 
                                 "Database update failed. Reverting lore outline.")
            self.load_outline()

    def _show_context_menu(self, pos: QPoint) -> None:
        """
        Displays the context menu when right-clicked, offering options 
        like 'Add New Lore Entry' and 'Delete Lore Entry'.
        
        :param pos: The position of the right-click relative to the widget.
        :type pos: :py:class:`~PyQt6.QtCore.QPoint`

        :rtype: None
        """
        item = self.tree_widget.itemAt(pos)

        menu = QMenu(self)

        new_action = menu.addAction("Add New Lore Entry...")
        new_action.triggered.connect(self.prompt_and_add_lore)
        
        if item:
            is_lore_entry = item.data(0, self.id_role)

            if is_lore_entry:
                rename_action = menu.addAction("Rename Lore Entry")
                delete_action = menu.addAction("Delete Lore Entry")

                rename_action.triggered.connect(lambda: self.tree_widget.editItem(item, 0))
                delete_action.triggered.connect(lambda: self.check_save_and_delete(item))

        if menu.actions():
            menu.exec(self.mapToGlobal(pos))

    def prompt_and_add_lore(self) -> None:
        """
        Prompts the user for a new Lore Entry name, creates the Lore Entry in 
        the database, reloads the outline, and selects the new Lore Entry.
        
        Emits :py:attr:`.pre_item_change` before prompting.
        
        :rtype: None
        """
    
        if not self.lore_repo:
            QMessageBox.critical(self, "Internal Error", "LoreRepository is missing.")
            return
        
        # Check save status before creating a new Lore Entry (which implicitly changes selection)
        self.pre_item_change.emit()

        title, ok = QInputDialog.getText(
            self,
            "New Lore Entry",
            "Enter the title for the new Lore Entry",
            text="New Lore Entry"
        )

        if not ok:
            return
        
        if not title:
            QMessageBox.warning(self, "Invalid Title", "Title cannot be empty.")
            return

        new_id = self.lore_repo.create_lore_entry(title=title)
        
        if new_id:
            self.new_item_created.emit()
            self.load_outline()
            new_item = self.find_lore_item_by_id(new_id)
            if new_item:
                self.tree_widget.setCurrentItem(new_item)
                self._on_item_clicked(new_item, 0)

    def _delete_lore(self, item: QTreeWidgetItem) -> None:
        """
        Handles confirmation and deletion of a Lore Entry item and its corresponding 
        entry in the database.
        
        :param item: The Lore Entry item to be deleted.
        :type item: :py:class:`~PyQt6.QtWidgets.QTreeWidgetItem`

        :rtype: None
        """
        lore_id = item.data(0, self.id_role)
        title = item.text(0)

        if lore_id is None:
            return
        
        if not self.lore_repo:
            QMessageBox.critical(self, "Internal Error", "LoreRepository is missing.")
            return
        
        # Confirmation Dialog
        reply = QMessageBox.question(
            self, 
            "Confirm Deletion",
            f"Are you sure you want to permanently delete the Lore Entry:\n'{title}'?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.lore_repo.delete_lore_entry(lore_id=lore_id):
                self.load_outline()
        else:
                QMessageBox.critical(self, "Deletion Error", "A database error occurred while trying to delete the lore entry.")
                
    def check_save_and_delete(self, item: QTreeWidgetItem) -> None:
        """
        Emits :py:attr:`.pre_item_change` to ensure the currently viewed 
        Lore Entry is saved, then triggers the deletion process.

        :param item: The Lore Entry item queued for deletion.
        :type item: :py:class:`~PyQt6.QtWidgets.QTreeWidgetItem`

        :rtype: None
        """
        self.pre_item_change.emit()
        self._delete_lore(item)

    def find_lore_item_by_id(self, lore_id: int) -> QTreeWidgetItem | None:
        """
        Helper to find a Lore Entry :py:class:`~PyQt6.QtWidgets.QTreeWidgetItem` 
        by its stored database ID.
        
        :param lore_id: The unique ID of the Lore Entry to find.
        :type lore_id: int

        :returns: The matching item or None
        :rtype: :py:class:`~PyQt6.QtWidgets.QTreeWidgetItem` or None
        """
        iterator = QTreeWidgetItemIterator(self.tree_widget)
        while iterator.value():
            item = iterator.value()
            if item.data(0, self.id_role) == lore_id:
                return item
            iterator += 1
        return None
