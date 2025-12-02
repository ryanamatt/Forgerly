# src/python/ui/lore_outline_manager.py

from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QMenu, QInputDialog, QMessageBox,
    QWidget, QVBoxLayout, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint

from ...repository.lore_repository import LoreRepository

# Define the roles for the custom data we want to store in the QTreeWidget
# This makes it easy to retrieve the Lore Entry ID associated with a clicked item.
LORE_ID_ROLE = Qt.ItemDataRole.UserRole + 1
# Role to identify the root item (which is not a Lore Entry)
ROOT_ITEM_ROLE = Qt.ItemDataRole.UserRole + 2

class LoreOutlineManager(QWidget):
    """
    A custom QTreeWidget dedicated to displaying the hierarchical outline 
    of Lore elements.
    It interacts with the data layer via LoreRepositroy.
    """

    # Signal emitted when a lore item is selected, carrying the lore ID
    lore_selected = pyqtSignal(int)
    # Emitted before a new lore is selected, allowing the main window to save
    pre_lore_change = pyqtSignal()

    
    def __init__(self, lore_repository: LoreRepository | None = None) -> None:
        super().__init__()

        self.lore_repo = lore_repository
        self.project_root_item = None

        # --- 1. Setup Main Layout and Components ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create the Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Search Lore Entries...')
        self.search_input.textChanged.connect(self._handle_search_input)

        # The actual tree widget is a child
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Lore Items"])

        main_layout.addWidget(self.search_input)
        main_layout.addWidget(self.tree_widget)

        # --- 2. Configuration and Signals  ---
        self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self._show_context_menu)
        self.tree_widget.itemSelectionChanged.connect(self._handle_selection_change)

        # Load the initial structure
        self.load_outline()

    def load_outline(self, lore_entries: list[dict] | None = None) -> None:
        """
        Loads the Lore Entries into the outline manager.
        If lore_entries is provided (e.g., from a search), it loads those.
        Otherwise, it loads all entries from the repository.
        """
        if not self.lore_repo:
            return

        # Fetch all entries if none are provided (default mode)
        if lore_entries is None:
            lore_entries = self.lore_repo.get_all_lore_entries()
            
        self.tree_widget.clear()
        
        # Create the root item
        self.project_root_item = QTreeWidgetItem(self.tree_widget, ["World Lore Base"])
        self.project_root_item.setData(0, ROOT_ITEM_ROLE, True)
        self.project_root_item.setFlags(self.project_root_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        self.project_root_item.setFlags(self.project_root_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        # Add all fetched lore entries as children
        if lore_entries:
            for entry in lore_entries:
                # The search function returns Title and Category, so we can use them here
                title = entry.get("Title", "Untitled Entry")
                category = entry.get("Category", "Uncategorized")
                
                item = QTreeWidgetItem(self.project_root_item, [title])
                item.setData(0, LORE_ID_ROLE, entry["ID"])
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                item.setToolTip(0, f"Category: {category}") 
                
        self.tree_widget.expandAll()
        self.tree_widget.setCurrentItem(self.project_root_item)

    def _handle_search_input(self, query: str) -> None:
        """
        Handles text changes in the search bar. 
        Performs FTS search or reverts to the full outline.
        """
        clean_query = query.strip()

        if clean_query and self.lore_repo:
            search_results = self.lore_repo.search_lore_entries(clean_query)
            if search_results:
                self.load_outline(search_results)
            else:
                self.tree_widget.clear()
                no_result_item = QTreeWidgetItem(self.tree_widget, ["No search results found."])
                no_result_item.setData(0, LORE_ID_ROLE, -1)
                self.tree_widget.expandAll()
        
        # Search is cleared, revert to full outline
        elif not clean_query:
            self.load_outline()

    def _handle_selection_change(self) -> None:
        """Emits a signal with the selected Lore ID when the selection changes."""
        current_item = self.tree_widget.currentItem()
        if current_item:
            lore_id = current_item.data(0, LORE_ID_ROLE)
            # Only emit if a valid lore entry (not the root or a 'no result' message) is selected
            if isinstance(lore_id, int) and lore_id > 0:
                self.lore_selected.emit(lore_id)

    def _handle_item_click(self, item: QTreeWidgetItem, column: int) -> None:
        """Handles the click event on a tree item"""
        lore_id = item.data(0, LORE_ID_ROLE)

        if lore_id is not None:
            # Emit pre-change signal to allow the main window to save the current lore entry
            self.pre_lore_change.emit()

            self.lore_selected.emit(lore_id)

    def _handle_item_double_click(self, item: QTreeWidget, column: int) -> None:
        """Handles double click to initiate renaming"""
        if item.data(0, LORE_ID_ROLE) is not None:
            self.tree_widget.editItem(item, 0)

    def _handle_item_renamed(self, item: QTreeWidgetItem, column: int) -> None:
        """
        Handles the signal emitted when a tree item has been successfully renamed.
        """
        lore_id = item.data(0, LORE_ID_ROLE)
        new_title = item.text(0).strip()

        if not self.lore_repo:
            QMessageBox.critical(self, "Internal Error", "LoreRepository is missing.")
            return
        
        # Prevent actions if this is the root item or if the title is empty
        if lore_id is not None or new_title:
            if not new_title:
                # If the title was cleared, revert the name (requires re-loading or smarter logic)
                QMessageBox.warning(self, "Invalid Title", "Lore Entry title cannot be empty. Reverting.")
                self.load_outline() 
            return
        
        # Check if title actually changed
        current_db_title = self.lore_repo.get_lore_entry_title(lore_id)
        if current_db_title and current_db_title == new_title:
            return
        
        success = self.lore_repo.update_lore_entry(lore_id, new_title)

        if not success:
            QMessageBox.critical(self, "Database Error", "Failed to update Lore Entry title in the database.")
            # Revert the item name visually if the DB update failed
            self.load_outline()

    def _show_context_menu(self, pos: QPoint) -> None:
        """Displays the context menu when right-clicked"""
        item = self.tree_widget.itemAt(pos)

        menu = QMenu(self)

        new_action = menu.addAction("Add New Lore Entry...")
        new_action.triggered.connect(self.prompt_and_add_lore)
        
        if item:
            is_lore_entry = item.data(0, LORE_ID_ROLE)

            if is_lore_entry:
                rename_action = menu.addAction("Rename Lore Entry")
                delete_action = menu.addAction("Delete Lore Entry")

                rename_action.triggered.connect(lambda: self.tree_widget.editItem(item, 0))
                delete_action.triggered.connect(lambda: self.check_save_and_delete(item))

        if menu.actions():
            menu.exec(self.mapToGlobal(pos))

    def prompt_and_add_lore(self) -> None:
        """Prompts the user for a new lore entry title ands adds it to the DB and outline."""
    
        if not self.lore_repo:
            QMessageBox.critical(self, "Internal Error", "LoreRepository is missing.")
            return
        
        # Check save status before creating a new Lore Entry (which implicitly changes selection)
        self.pre_lore_change.emit()

        title, ok = QInputDialog.getText(
            self,
            "New Lore Entry",
            "Enter the title for the new Lore Entry",
            text="New Lore Entry"
        )

        if ok and title:
            new_id = self.lore_repo.create_lore_entry(title=title)
            
            if new_id:
                self.load_outline()
                new_item = self.find_lore_item_by_id(new_id)
                if new_item:
                    self.tree_widget.setCurrentItem(new_item)
                    self._handle_item_click(new_item, 0)
        else:
            QMessageBox.warning(self, "Database Error", "Failed to save the new Lore Entry to the database.")


    def _delete_lore(self, item: QTreeWidgetItem) -> None:
        """Handles confirmation and deletion of a lore entry"""
        lore_id = item.data(0, LORE_ID_ROLE)
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
        """Emits pre-change signal, then deletes the chapter"""
        self.pre_lore_change.emit()
        self._delete_lore(item)

    def find_lore_item_by_id(self, lore_id: int) -> QTreeWidgetItem | None:
        """Helper to find a lore entry item by its stored ID"""
        if not self.project_root_item:
            return None
        
        for i in range(self.project_root_item.childCount()):
            item = self.project_root_item.child(i)
            if item.data(0, LORE_ID_ROLE) == lore_id:
                return item
        return None