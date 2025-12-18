# src/python/ui/outline_manager.py

from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QHeaderView, QMenu, QInputDialog, QMessageBox,
    QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QDropEvent, QIcon

import src.python.resources_rc as resources_rc
from ...repository.chapter_repository import ChapterRepository 

class ChapterOutlineManager(QTreeWidget):
    """
    A custom :py:class:`~PyQt6.QtWidgets.QTreeWidget` dedicated to displaying the 
    hierarchical outline of Chapters and other narrative elements.
    
    It interacts with the data layer via a :py:class:`.ChapterRepository`.
    """

    CHAPTER_ID_ROLE = Qt.ItemDataRole.UserRole + 1
    """The :py:obj:`int` role used to store the database ID of a Chapter on an item."""

    ROOT_ITEM_ROLE = Qt.ItemDataRole.UserRole + 2
    """The :py:obj:`bool` role used to identify the uneditable project root item."""

    # Signal emitted when a chapter item is selected, carrying the Chapter ID
    chapter_selected = pyqtSignal(int)
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (int): Emitted when a chapter item is selected, 
    carrying the Chapter ID.
    """

    # Emitted before a new chapter is selected, allowing the main window to save
    pre_chapter_change = pyqtSignal()
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (): Emitted before a new chapter is 
    selected, allowing the main window to save the current chapter state.
    """

    def __init__(self, project_title: str = "Narrative Forge Project",
                  chapter_repository: ChapterRepository | None = None) -> None:
        """
        Initializes the ChapterOutlineManager.
        
        :param chapter_repository: The repository object for chapter CRUD operations.
        :type chapter_repository: :py:class:`.ChapterRepository` or :py:obj:`None`, optional
        """
        super().__init__()
        self.project_title = project_title

        # Renamed attribute to clearly show its new role
        self.chapter_repo = chapter_repository 
        self.project_root_item = None

        # Configuration and Styling
        self.setHeaderLabels(["Narrative Outline"])
        self.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.setMidLineWidth(100)
        self.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # --- Enable Drag and Drop for Reordering
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

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
        and populating the :py:class:`~PyQt6.QtWidgets.QTreeWidget`.
        
        It attempts to select the first chapter upon successful load.
        
        :rtype: None
        """
        self.clear()

        chapter_icon = QIcon(":icons/chapter.svg")

        self.blockSignals(True)
        
        # Root item for the Narrative (e.g. The Project)
        self.project_root_item = QTreeWidgetItem(self, [f"{self.project_title}"])
        # Mark as non-editable and assign the ROOT_ITEM_ROLE
        self.project_root_item.setFlags(
            self.project_root_item.flags() & ~Qt.ItemFlag.ItemIsEditable
            & ~Qt.ItemFlag.ItemIsSelectable
            & ~Qt.ItemFlag.ItemIsEditable
            & ~Qt.ItemFlag.ItemIsUserCheckable
            ) 
        self.project_root_item.setData(0, self.ROOT_ITEM_ROLE, True)

        # Fetch the actual chapter data from the database using the Repository
        if self.chapter_repo:
            chapter_data = self.chapter_repo.get_all_chapters()
        else:
            chapter_data = []

        for chapter in chapter_data:
            chap_id = chapter['ID']
            title = chapter['Title']

            chapter_item = QTreeWidgetItem(self.project_root_item, [title])
            chapter_item.setIcon(0, chapter_icon)
            chapter_item.setData(0, self.CHAPTER_ID_ROLE, chap_id)
            chapter_item.setFlags(chapter_item.flags() | Qt.ItemFlag.ItemIsEditable)

        self.blockSignals(False)

        self.project_root_item.setExpanded(True)

        if self.project_root_item.childCount() > 0:
            first_child = self.project_root_item.child(0)
            self.setCurrentItem(first_child)
            self.chapter_selected.emit(first_child.data(0, self.CHAPTER_ID_ROLE))

    def dropEvent(self, event: QDropEvent) -> None:
        """
        Custom drop event to handle chapter reordering.

        It performs the visual move first, then calculates the new sort order 
        for all chapters in the new list, and updates the database.
        
        :param event: The drop event.
        :type event: :py:class:`~PyQt6.QtGui.QDropEvent`
        
        :rtype: None
        """
        self.pre_chapter_change.emit()

        # Get the item being dragged and the target item/position before the drop
        dropped_item = self.currentItem()
        target_item = self.itemAt(event.position().toPoint())
        drop_pos = self.dropIndicatorPosition()

        super().dropEvent(event)

        if not dropped_item:
            event.ignore()
            return
        
        new_parent_item = dropped_item.parent()
        
        # 2. Correction Logic
        
        # Scenario A: Item was dropped 'OnItem' of another chapter (nesting)
        # We must manually insert it above the target item.
        is_nested_on_chapter = (
            target_item and target_item is not self.project_root_item and drop_pos == QAbstractItemView.DropIndicatorPosition.OnItem
        )
        
        if is_nested_on_chapter:
            target_item.removeChild(dropped_item)
            target_index = self.project_root_item.indexOfChild(target_item)
            self.project_root_item.insertChild(target_index, dropped_item)
            self.setCurrentItem(dropped_item)

        # Scenario B: Item became a top-level item (parent is None) or was placed 
        # outside the root's children, which is always an invalid location.
        elif new_parent_item is not self.project_root_item:
            
            # If it became a top-level item (parent is None)
            if new_parent_item is None:
                index_of_top_level_item = self.indexOfTopLevelItem(dropped_item)
                if index_of_top_level_item != -1:
                    self.takeTopLevelItem(index_of_top_level_item)
            # If it was nested under another item (this handles the general case 
            # if the previous specific check wasn't met, though it should be)
            elif new_parent_item:
                new_parent_item.removeChild(dropped_item)
            
            # Place the item at the END of the valid list (the only safe fallback)
            self.project_root_item.addChild(dropped_item)
            self.setCurrentItem(dropped_item)
            self.scrollToItem(dropped_item)

        self._update_all_chapter_sort_orders()

        event.accept()

    def _update_all_chapter_sort_orders(self) -> None:
        """
        Calculates the new Sort_Order for all chapters based on their current 
        visual position under the root item and updates the database via a 
        single transaction.
        
        :rtype: None
        """
        if not self.chapter_repo or not self.project_root_item:
            return

        chapter_updates: list[tuple[int, int]] = []
        
        # Iterate through all children of the root item (which are the chapters)
        # The index 'i' becomes the new Sort_Order (starting from 0, but we use 1-based index)
        for i in range(self.project_root_item.childCount()):
            item = self.project_root_item.child(i)
            chapter_id = item.data(0, self.CHAPTER_ID_ROLE)
            
            # The database Sort_Order will be 1-based (i + 1)
            new_sort_order = i + 1 

            if chapter_id is not None:
                chapter_updates.append((chapter_id, new_sort_order))

        # Check if there are any updates to perform
        if not chapter_updates:
            return

        # Perform the atomic database update
        success = self.chapter_repo.reorder_chapters(chapter_updates)

        if not success:
            QMessageBox.critical(self, "Reordering Error", 
                                 "Database update failed. Reverting chapter outline.")
            # Reload the outline to revert the visual change if the database update failed
            self.load_outline()

    def _handle_item_click(self, item: QTreeWidgetItem, column: int) -> None:
        """
        Handles the click event on a tree item.
        
        If a chapter is clicked, it emits :py:attr:`.pre_chapter_change` followed 
        by :py:attr:`.chapter_selected`.

        :param item: The clicked tree item.
        :type item: :py:class:`~PyQt6.QtWidgets.QTreeWidgetItem`
        :param column: The column index clicked (always 0 in this case).
        :type column: int

        :rtype: None
        """
        chapter_id = item.data(0, self.CHAPTER_ID_ROLE)
        
        if chapter_id is not None:
            # Emit pre-change signal to allow the main window to save the current chapter
            self.pre_chapter_change.emit()

            self.chapter_selected.emit(chapter_id)

    def _handle_item_double_click(self, item: QTreeWidgetItem, column: int) -> None:
        """
        Handles double click to initiate renaming for chapter items.
        
        :param item: The double-clicked tree item.
        :type item: :py:class:`~PyQt6.QtWidgets.QTreeWidgetItem`
        :param column: The column index.
        :type column: :py:obj:`int`

        :rtype: None
        """
        if item.data(0, self.CHAPTER_ID_ROLE) is not None:
            # Only allow renaming for chapter items
            self.editItem(item, 0)

    def _handle_item_renamed(self, item: QTreeWidgetItem, column: int) -> None:
        """
        Handles the signal emitted when a tree item has been successfully renamed.
        
        The new title is saved to the database via the :py:class:`.ChapterRepository`.
        
        :param item: The renamed tree item.
        :type item: :py:class:`~PyQt6.QtWidgets.QTreeWidgetItem`
        :param column: The column index.
        :type column: int

        :rtype: None
        """
        chapter_id = item.data(0, self.CHAPTER_ID_ROLE)
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
        """
        Displays the context menu when right-clicked, offering options 
        like 'Add New Chapter', 'Rename Chapter', and 'Delete Chapter'.
        
        :param pos: The position of the right-click relative to the widget.
        :type pos: :py:class:`~PyQt6.QtCore.QPoint`

        :rtype: None
        """
        item = self.itemAt(pos)

        menu = QMenu(self)
        
        # New Chapter Button
        new_action = menu.addAction("Add New Chapter...")
        new_action.triggered.connect(self.prompt_and_add_chapter)

        if item:            
            is_chapter = item.data(0, self.CHAPTER_ID_ROLE) is not None
        
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
        """
        Prompts the user for a new chapter title, creates the chapter in the 
        database, reloads the outline, and selects the new chapter.
        
        Emits :py:attr:`.pre_chapter_change` before prompting.
        
        :rtype: None
        """
        
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
            
            new_id = self.chapter_repo.create_chapter(
                title=title, 
                sort_order=current_sort_order + 1,
            )

            if new_id:
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
        """
        Handles confirmation and deletion of a chapter item and its corresponding 
        entry in the database.
        
        :param item: The chapter item to be deleted.
        :type item: :py:class:`~PyQt6.QtWidgets.QTreeWidgetItem`

        :rtype: None
        """
        chapter_id = item.data(0, self.CHAPTER_ID_ROLE)
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
        """
        Emits :py:attr:`.pre_chapter_change` to ensure the currently viewed 
        chapter is saved, then triggers the deletion process.

        :param item: The chapter item queued for deletion.
        :type item: :py:class:`~PyQt6.QtWidgets.QTreeWidgetItem`

        :rtype: None
        """
        self.pre_chapter_change.emit()
        self._delete_chapter(item)

    def find_chapter_item_by_id(self, chapter_id: int) -> QTreeWidgetItem | None:
        """
        Helper to find a chapter :py:class:`~PyQt6.QtWidgets.QTreeWidgetItem` 
        by its stored database ID.
        
        :param chapter_id: The unique ID of the chapter to find.
        :type chapter_id: :py:obj:`int`
        
        :returns: The matching item or None.
        :rtype: :py:class:`~PyQt6.QtWidgets.QTreeWidgetItem` or None
        """
        if not self.project_root_item:
            return None
        
        for i in range(self.project_root_item.childCount()):
            item = self.project_root_item.child(i)
            if item.data(0, self.CHAPTER_ID_ROLE) == chapter_id:
                return item
        return None