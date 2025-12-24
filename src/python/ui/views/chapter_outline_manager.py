# src/python/ui/outline_manager.py

from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator, QMenu, QInputDialog, QMessageBox,
    QAbstractItemView, QWidget, QVBoxLayout, QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QIcon

from ...resources_rc import *
from ...repository.chapter_repository import ChapterRepository
from ..widgets.reordering_tree_widget import ReorderingTreeWidget 

class ChapterOutlineManager(QWidget):
    """
    A custom :py:class:`~PyQt6.QtWidgets.QWidget` dedicated to displaying the 
    hierarchical outline of Chapters and other narrative elements.
    
    It interacts with the data layer via a :py:class:`.ChapterRepository`.
    """

    CHAPTER_ID_ROLE = Qt.ItemDataRole.UserRole + 1
    """The int role used to store the database ID of a Chapter on an item."""

    chapter_selected = pyqtSignal(int)
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (int): Emitted when a chapter item is selected, 
    carrying the Chapter ID.
    """

    new_chapter_created = pyqtSignal()
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal`: Emitted when a new chapter is created. Tells
    MainWindow to switch the view to Chapter View.
    """

    pre_chapter_change = pyqtSignal()
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (): Emitted before a new chapter is 
    selected, allowing the main window to save the current chapter state.
    """

    def __init__(self, project_title: str = "Narrative Forge Project",
                  chapter_repository: ChapterRepository | None = None) -> None:
        """
        Initializes the ChapterOutlineManager.
        
        :param project_title: The Title of the Current Project.
        :type project_title: str
        :param chapter_repository: The repository object for chapter CRUD operations.
        :type chapter_repository: :py:class:`.ChapterRepository` or :py:obj:`None`, optional
        """
        super().__init__()
        self.project_title = project_title

        # Renamed attribute to clearly show its new role
        self.chapter_repo = chapter_repository 

        # UI Setup
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Header Layout
        self.header_label = QLabel(f"{project_title} Chapters")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.header_label.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 1)
        self.header_label.setFont(font)
        self.header_label.setStyleSheet("""
            QLabel {
                padding: 5px
                }
        """            
        )

        # Configuration and Styling
        self.tree_widget = ReorderingTreeWidget(editor=self)
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setIndentation(0)
        self.tree_widget.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # --- Enable Drag and Drop for Reordering
        self.tree_widget.setDragEnabled(True)
        self.tree_widget.setAcceptDrops(True)
        self.tree_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

        self.tree_widget.installEventFilter(self)

        # Connect Signals for Tree Widget
        self.tree_widget.itemClicked.connect(self._handle_item_click)
        self.tree_widget.customContextMenuRequested.connect(self._show_context_menu)
        self.tree_widget.itemDoubleClicked.connect(self._handle_item_double_click)
        self.tree_widget.itemChanged.connect(self._handle_item_renamed)


        container_frame = QFrame(self)
        container_frame.setObjectName("MainBorderFrame")

        # Create a layout FOR the frame and add the widgets to it
        frame_layout = QVBoxLayout(container_frame)
        frame_layout.addWidget(self.header_label)
        frame_layout.addWidget(self.tree_widget)

        main_layout.addWidget(container_frame)

        # Load the initial structure
        self.load_outline()

    def load_outline(self) -> None:
        """
        Loads the outline structure by fetching all chapters from the database 
        and populating the :py:class:`~PyQt6.QtWidgets.QTreeWidget`.
        
        It attempts to select the first chapter upon successful load.
        
        :rtype: None
        """
        if not self.chapter_repo:
            return

        self.tree_widget.clear()
        self.tree_widget.blockSignals(True)

        chapter_data = self.chapter_repo.get_all_chapters()
        chapter_icon = QIcon(":icons/chapter.svg")

        for chapter in chapter_data:
            item = QTreeWidgetItem([chapter['Title']])
            item.setData(0, self.CHAPTER_ID_ROLE, chapter['ID'])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            item.setIcon(0, chapter_icon)
            self.tree_widget.addTopLevelItem(item)

        self.tree_widget.blockSignals(False)

        # # Auto-select first chapter if available
        # if self.tree_widget.topLevelItemCount() > 0:
        #     first_item = self.tree_widget.topLevelItem(0)
        #     self.tree_widget.setCurrentItem(first_item)
        #     self.chapter_selected.emit(first_item.data(0, self.CHAPTER_ID_ROLE))

    def _update_all_chapter_sort_orders(self) -> None:
        """
        Calculates the new Sort_Order for all chapters based on their current 
        visual position under the root item and updates the database via a 
        single transaction.
        
        :rtype: None
        """
        if not self.chapter_repo:
            return

        chapter_updates: list[tuple[int, int]] = []
        
        for i in range(self.tree_widget.topLevelItemCount()):
            item = self.tree_widget.topLevelItem(i)
            chapter_id = item.data(0, self.CHAPTER_ID_ROLE)
            if chapter_id is not None:
                # 1-based index for Sort_Order
                chapter_updates.append((chapter_id, i + 1))

        if chapter_updates:
            success = self.chapter_repo.reorder_chapters(chapter_updates)
            if not success:
                QMessageBox.critical(self, "Reordering Error", "Database update failed.")
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
            self.tree_widget.editItem(item, 0)

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
        item = self.tree_widget.itemAt(pos)

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
            menu.exec(self.tree_widget.mapToGlobal(pos))

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
            current_sort_order = self.tree_widget.topLevelItemCount() + 1
            
            new_id = self.chapter_repo.create_chapter(
                title=title, 
                sort_order=current_sort_order + 1,
            )

            if new_id:
                self.new_chapter_created.emit()
                # Reload the outline to display the new chapter
                self.load_outline()
                # Automatically select the new chapter
                new_item = self.find_chapter_item_by_id(new_id)
                if new_item:
                     self.tree_widget.setCurrentItem(new_item)
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
        iterator = QTreeWidgetItemIterator(self.tree_widget)
        while iterator.value():
            item = iterator.value()
            if item.data(0, self.CHAPTER_ID_ROLE) == chapter_id:
                return item
            iterator += 1
        return None