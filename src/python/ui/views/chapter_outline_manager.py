# Outline Manager Component: src/python/ui/outline_manager.py

from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QHeaderView, QStyle, QMenu, QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint

from ...repository.chapter_repository import ChapterRepository 


# Define the roles for the custom data we want to store in the QTreeWidget
# This makes it easy to retrieve the Chapter ID associated with a clicked item.
CHAPTER_ID_ROLE = Qt.ItemDataRole.UserRole + 1
# Role to identify the root item (which is not a chapter)
ROOT_ITEM_ROLE = Qt.ItemDataRole.UserRole + 2

class ChapterOutlineManager(QTreeWidget):
    """
    A custom QTreeWidget dedicated to displaying the hierarchical outline 
    of Chapters and other narrative elements.
    It interacts with the data layer via ChapterRepository.
    """

    # Signal emitted when a chapter item is selected, carrying the Chapter ID
    chapter_selected = pyqtSignal(int)
    # Emitted before a new chapter is selected, allowing the main window to save
    pre_chapter_change = pyqtSignal()

    def __init__(self, chapter_repository: ChapterRepository | None = None) -> None:
        super().__init__()
        # Renamed attribute to clearly show its new role
        self.chapter_repo = chapter_repository 
        self.project_root_item = None

        # Configuration and Styling
        self.setHeaderLabels(["Narrative Outline"])
        self.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.setMidLineWidth(100)
        self.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Connect Signals
        self.itemClicked.connect(self._handle_item_click)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemDoubleClicked.connect(self._handle_item_double_click)
        self.itemChanged.connect(self._handle_item_renamed)

        # Load the initial structure
        self.load_outline()

    def load_outline(self) -> None:
        """
        Loads the outline structure by fetching all chapters from the database 
        and populating the QTreeWidget.
        """
        self.clear()

        # Placeholder Icons (using a simple style icon)
        chapter_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView)

        self.blockSignals(True)
        
        # Root item for the Narrative (e.g. The Project)
        self.project_root_item = QTreeWidgetItem(self, ["The Story of Narrative Forge"])
        # Mark as non-editable and assign the ROOT_ITEM_ROLE
        self.project_root_item.setFlags(self.project_root_item.flags() & ~Qt.ItemFlag.ItemIsEditable) 
        self.project_root_item.setData(0, ROOT_ITEM_ROLE, True)

        # Fetch the actual chapter data from the database using the Repository
        if self.chapter_repo:
            chapter_data = self.chapter_repo.get_all_chapters()
        else:
            chapter_data = []
            print("Warning: ChapterOutlineManager has no ChapterRepository. Using empty set.")

        for chapter in chapter_data:
            chap_id = chapter['ID']
            title = chapter['Title']

            chapter_item = QTreeWidgetItem(self.project_root_item, [title])
            chapter_item.setIcon(0, chapter_icon)
            chapter_item.setData(0, CHAPTER_ID_ROLE, chap_id)
            chapter_item.setFlags(chapter_item.flags() | Qt.ItemFlag.ItemIsEditable)

        self.blockSignals(False)

        self.project_root_item.setExpanded(True)

        if self.project_root_item.childCount() > 0:
            first_child = self.project_root_item.child(0)
            self.setCurrentItem(first_child)
            self.chapter_selected.emit(first_child.data(0, CHAPTER_ID_ROLE))

    def _handle_item_click(self, item: QTreeWidgetItem, column: int) -> None:
        """Handles the click event on a tree item."""
        chapter_id = item.data(0, CHAPTER_ID_ROLE)
        
        if chapter_id is not None:
            # Emit pre-change signal to allow the main window to save the current chapter
            self.pre_chapter_change.emit()

            self.chapter_selected.emit(chapter_id)

    def _handle_item_double_click(self, item: QTreeWidgetItem, column: int) -> None:
        """Handles double click to initiate renaming"""
        if item.data(0, CHAPTER_ID_ROLE) is not None:
            # Only allow renaming for chapter items
            self.editItem(item, 0)

    def _handle_item_renamed(self, item: QTreeWidgetItem, column: int) -> None:
        """
        Handles the signal emitted when a tree item has been successfully renamed.
        """
        chapter_id = item.data(0, CHAPTER_ID_ROLE)
        new_title = item.text(0).strip()
        
        if not self.chapter_repo:
            QMessageBox.critical(self, "Internal Error", "ChapterRepository is missing.")
            return

        # Prevent actions if this is the root item or if the title is empty
        if chapter_id is None or not new_title:
            if not new_title:
                # If the title was cleared, revert the name (requires re-loading or smarter logic)
                QMessageBox.warning(self, "Invalid Title", "Chapter title cannot be empty. Reverting.")
                self.load_outline() 
            return

        # Check if the title actually changed
        current_db_title = self.chapter_repo.get_chapter_title(chapter_id) 
        if current_db_title and current_db_title == new_title:
            return

        # Update the database
        success = self.chapter_repo.update_chapter_title(chapter_id, new_title)
        
        if not success:
            QMessageBox.critical(self, "Database Error", "Failed to update chapter title in the database.")
            # Revert the item name visually if the DB update failed
            self.load_outline()

    def _show_context_menu(self, pos: QPoint) -> None:
        """Displays the context menu when right-clicked."""
        item = self.itemAt(pos)

        menu = QMenu(self)
        
        # New Chapter Button
        new_action = menu.addAction("Add New Chapter...")
        new_action.triggered.connect(self.prompt_and_add_chapter)

        if item:            
            is_chapter = item.data(0, CHAPTER_ID_ROLE) is not None
        
            # Actions for Chapters (visible if clicking a chapter item)
            if is_chapter:
                rename_action = menu.addAction("Rename Chapter")
                delete_action = menu.addAction("Delete Chapter")
                
                rename_action.triggered.connect(lambda: self.editItem(item, 0))
                # Wrap the delete action to ensure save check occurs
                delete_action.triggered.connect(lambda: self.check_save_and_delete(item))

        # Show the menu
        if menu.actions():
            menu.exec(self.mapToGlobal(pos))

    def prompt_and_add_chapter(self) -> None:
        """Prompts the user for a new chapter title and adds it to the DB and outline."""
        
        if not self.chapter_repo:
            QMessageBox.critical(self, "Internal Error", "ChapterRepository is missing.")
            return

        # Check save status before creating a new chapter (which implicitly changes selection)
        self.pre_chapter_change.emit() 
        
        title, ok = QInputDialog.getText(
            self, 
            "New Chapter", 
            "Enter the title for the new chapter:",
            text="New Chapter"
        )

        if ok and title:
            # Determine the sort order for the new chapter (place it last at the root level)
            current_sort_order = self.project_root_item.childCount()
            
            # Precursor_Chapter_ID is None for top-level chapters
            new_id = self.chapter_repo.create_chapter(
                title=title, 
                sort_order=current_sort_order + 1,
                precursor_id=None
            )

            if new_id:
                print(f"Successfully created chapter with ID: {new_id}")
                # Reload the outline to display the new chapter
                self.load_outline()
                # Automatically select the new chapter
                new_item = self.find_chapter_item_by_id(new_id)
                if new_item:
                     self.setCurrentItem(new_item)
                     self._handle_item_click(new_item, 0) 
            else:
                QMessageBox.warning(self, "Database Error", "Failed to save the new chapter to the database.")

    def _delete_chapter(self, item: QTreeWidgetItem) -> None:
        """Handles confirmation and deletion of a chapter."""
        chapter_id = item.data(0, CHAPTER_ID_ROLE)
        title = item.text(0)
        
        if chapter_id is None:
            return
            
        if not self.chapter_repo:
            QMessageBox.critical(self, "Internal Error", "ChapterRepository is missing.")
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
            if self.chapter_repo.delete_chapter(chapter_id):
                self.load_outline()
            else:
                QMessageBox.critical(self, "Deletion Error", "A database error occurred while trying to delete the chapter.")

    def check_save_and_delete(self, item: QTreeWidgetItem) -> None:
        """Emits pre-change signal, then deletes the chapter"""
        self.pre_chapter_change.emit()
        self._delete_chapter(item)

    def find_chapter_item_by_id(self, chapter_id: int) -> QTreeWidgetItem | None:
        """Helper to find a chapter item by its stored ID."""
        if not self.project_root_item:
            return None
        
        for i in range(self.project_root_item.childCount()):
            item = self.project_root_item.child(i)
            if item.data(0, CHAPTER_ID_ROLE) == chapter_id:
                return item
        return None