# Outline Manager Component: src/python/outline_manager.py

from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QHeaderView, QStyle, QMenu, QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QIcon
import os
from db_connector import DBConnector 

# Define the roles for the custom data we want to store in the QTreeWidget
# This makes it easy to retrieve the Chapter ID associated with a clicked item.
CHAPTER_ID_ROLE = Qt.ItemDataRole.UserRole + 1
# Role to identify the root item (which is not a chapter)
ROOT_ITEM_ROLE = Qt.ItemDataRole.UserRole + 2

class OutlineManager(QTreeWidget):
    """
    A custom QTreeWidget dedicated to displaying the hierarchical outline 
    of Chapters and other narrative elements.
    """
    # Signal emitted when a chapter item is selected, carrying the Chapter ID
    chapter_selected = pyqtSignal(int)

    def __init__(self, db_connector: DBConnector= None) -> None:
        super().__init__()
        self.db = db_connector
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
        self.itemChanged.connect(self._handle_item_changed)

        # Load the initial structure
        self.load_outline()

    def load_outline(self) -> None:
        """
        Loads the outline structure by fetching all chapters from the database 
        and populating the QTreeWidget.
        """
        self.clear()

        # Placeholder Icons (using a simple style icon)
        # We'll use the style engine to get standard icons for a professional look.
        chapter_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView)
        
        # Root item for the Narrative (e.g. The Project)
        self.project_root_item = QTreeWidgetItem(self, ["The Story of Narrative Forge"])
        # Mark as non-editable and assign the ROOT_ITEM_ROLE
        self.project_root_item.setFlags(self.project_root_item.flags() & ~Qt.ItemFlag.ItemIsEditable) 
        self.project_root_item.setData(0, ROOT_ITEM_ROLE, True)

        # Fetch the actual chapter data from the database
        if self.db:
            chapter_data = self.db.fetch_all_chapters()
        else:
            chapter_data = []
            print("Warning: OutlineManager has no DB connection. Using empty set.")

        for chapter in chapter_data:
            chap_id = chapter['ID']
            title = chapter['Title']

            chapter_item = QTreeWidgetItem(self.project_root_item, [title])
            chapter_item.setIcon(0, chapter_icon)
            chapter_item.setData(0, CHAPTER_ID_ROLE, chap_id)
            chapter_item.setFlags(chapter_item.flags() | Qt.ItemFlag.ItemIsEditable)

        self.project_root_item.setExpanded(True)

        if self.project_root_item.childCount() > 0:
            first_child = self.project_root_item.child(0)
            self.setCurrentItem(first_child)
            self.chapter_selected.emit(first_child.data(0, CHAPTER_ID_ROLE))

    def _handle_item_click(self, item, column) -> None:
        """Handles the click event on a tree item."""
        chapter_id = item.data(0, CHAPTER_ID_ROLE)
        
        if chapter_id is not None:
            self.chapter_selected.emit(chapter_id)
            print(f"Outline Clicked: Selected Chapter ID: {chapter_id}")

    def _handle_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        """
        Handles the signal emitted when a user finishes editing an item's text.
        Updates the chapter title in the database.
        """
        chapter_id = item.data(0, CHAPTER_ID_ROLE)

        # Ensure it's a chapter item and not the root
        if chapter_id is not None:
            new_title = item.text(column)
            if self.db and new_title.strip():
                if self.db.update_chapter_title(chapter_id, new_title):
                    print(f"DB Update: Chapter ID {chapter_id} renamed to '{new_title}'.")
                else:
                    print(f"DB Error: Failed to rename chapter ID {chapter_id}.")

    def _show_context_menu(self, position: QPoint) -> None:
        """Displays a context menu when the user right-clicks the widget."""
        menu = QMenu(self)

        # Determine the item under the mouse position
        item = self.itemAt(position)

        # Action for all items/empty space: New Chapter
        new_action = menu.addAction("New Chapter...")
        new_action.triggered.connect(self.prompt_and_add_chapter)

        if item and item.data(0, CHAPTER_ID_ROLE) is not None:
            # Only show Rename and Delete for actual Chapter items
            menu.addSeparator()
            rename_action = menu.addAction("Rename Chapter")
            delete_action = menu.addAction("Delete Chapter")

            rename_action.triggered.connect(lambda: self._start_rename_editing(item))
            delete_action.triggered.connect(lambda: self._delete_chapter(item))

        menu.exec(self.viewport().mapToGlobal(position))

    def _start_rename_editing(self, item: QTreeWidgetItem) -> None:
        """Starts the inline editing for the selected item"""
        self.editItem(item)

    def prompt_and_add_chapter(self):
        """Prompts the user for a new chapter title and creates the chapter."""
        title, ok = QInputDialog.getText(
            self, 
            "New Chapter", 
            "Enter the title for the new chapter:",
            text="Untitled Chapter"
        )

        if ok and title:
            new_id = self.db.create_chapter(title)

            if new_id:
                print(f"Successfully created chapter with ID: {new_id}")
                # Reload the outline to display the new chapter
                self.load_outline()
            else:
                QMessageBox.warning(self, "Database Error", "Failed to save the new chapter to the database.")

    def _delete_chapter(self, item: QTreeWidgetItem):
        """Handles confirmation and deletion of a chapter."""
        chapter_id = item.data(0, CHAPTER_ID_ROLE)
        title = item.text(0)
        
        if chapter_id is None:
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
            if self.db.delete_chapter(chapter_id):
                print(f"Successfully deleted chapter ID: {chapter_id}")
                # Reload the outline after deletion
                self.load_outline()
            else:
                QMessageBox.critical(self, "Deletion Error", "A database error occurred while trying to delete the chapter.")