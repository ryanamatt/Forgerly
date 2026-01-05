# src/python/ui/outline_manager.py

from PySide6.QtWidgets import (
    QTreeWidgetItem, QTreeWidgetItemIterator, QMenu, QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QIcon

from .base_outline_manager import BaseOutlineManager
from ...resources_rc import *
from ...utils.constants import ViewType
from ...utils.constants import EntityType
from ...utils.events import Events
from ...utils.event_bus import bus, receiver

class ChapterOutlineManager(BaseOutlineManager):
    """
    A custom :py:class:`~PySide6.QtWidgets.QWidget` dedicated to displaying the 
    hierarchical outline of Chapters and other narrative elements.
    
    It interacts with the data layer via a :py:class:`.ChapterRepository`.
    """

    CHAPTER_ID_ROLE = Qt.ItemDataRole.UserRole + 1
    """The int role used to store the database ID of a Chapter on an item."""

    def __init__(self, project_title: str = "Narrative Forge Project") -> None:
        """
        Initializes the ChapterOutlineManager.
        
        :param project_title: The Title of the Current Project.
        :type project_title: str
        :param chapter_repository: The repository object for chapter CRUD operations.
        :type chapter_repository: :py:class:`.ChapterRepository` or :py:obj:`None`, optional
        """
        super().__init__(
            project_title=project_title,
            header_text="Chapters",
            id_role=self.CHAPTER_ID_ROLE,
            search_placeholder="Search Chapters...",
            is_nested_tree=False,
            type=EntityType.CHAPTER
        )

        self.search_input.setHidden(True)

        bus.register_instance(self)

        self.tree_widget.order_changed.connect(self._update_sort_orders)

    @receiver(Events.OUTLINE_DATA_LOADED)
    def load_outline(self, data: dict) -> None:
        """
        Loads the outline structure by fetching all chapters from the database 
        and populating the :py:class:`~PySide6.QtWidgets.QTreeWidget`.
        
        It attempts to select the first chapter upon successful load.
        
        :rtype: None
        """
        entity_type = data.get('entity_type')
        chapter_data = data.get('chapters')
        if entity_type != EntityType.CHAPTER or not chapter_data: 
            return

        self.tree_widget.clear()
        self.tree_widget.blockSignals(True)

        chapter_icon = QIcon(":icons/chapter.svg")

        for chapter in chapter_data:
            item = QTreeWidgetItem([chapter['Title']])
            item.setData(0, self.id_role, chapter['ID'])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            item.setIcon(0, chapter_icon)
            self.tree_widget.addTopLevelItem(item)

        self.tree_widget.blockSignals(False)

    def _update_sort_orders(self) -> None:
        """
        Calculates the new Sort_Order for all chapters based on their current 
        visual position under the root item and updates the database via a 
        single transaction.
        
        :rtype: None
        """
        chapter_updates: list[tuple[int, int]] = []
        
        for i in range(self.tree_widget.topLevelItemCount()):
            item = self.tree_widget.topLevelItem(i)
            chapter_id = item.data(0, self.id_role)
            if chapter_id is not None:
                # 1-based index for Sort_Order
                chapter_updates.append((chapter_id, i + 1))

        bus.publish(Events.OUTLINE_REORDER, data={
            'editor': self, 'view': ViewType.CHAPTER_EDITOR, 'updates': chapter_updates
        })

    def _handle_item_renamed(self, item: QTreeWidgetItem, column: int) -> None:
        """
        Handles the signal emitted when a tree item has been successfully renamed.
        
        The new title is saved to the database via the :py:class:`.ChapterRepository`.
        
        :param item: The renamed tree item.
        :type item: :py:class:`~PySide6.QtWidgets.QTreeWidgetItem`
        :param column: The column index.
        :type column: int

        :rtype: None
        """
        chapter_id = item.data(0, self.id_role)
        new_title = item.text(0).strip()
        
        # Prevent actions if this is the root item or if the title is empty
        if chapter_id is None or not new_title:
            if not new_title:
                # If the title was cleared, revert the name (requires re-loading or smarter logic)
                QMessageBox.warning(self, "Invalid Title", "Chapter title cannot be empty. Reverting.")
                bus.publish(Events.OUTLINE_LOAD_REQUESTED, data={'entity_type': EntityType.CHAPTER})
            return
        
        bus.publish(Events.OUTLINE_NAME_CHANGE, data={
            'entity_type': EntityType.CHAPTER, 'ID': chapter_id, 'new_title': new_title
        })

    def _show_context_menu(self, pos: QPoint) -> None:
        """
        Displays the context menu when right-clicked, offering options 
        like 'Add New Chapter', 'Rename Chapter', and 'Delete Chapter'.
        
        :param pos: The position of the right-click relative to the widget.
        :type pos: :py:class:`~PySide6.QtCore.QPoint`

        :rtype: None
        """
        item = self.tree_widget.itemAt(pos)

        menu = QMenu(self)
        
        # New Chapter Button
        new_action = menu.addAction("Add New Chapter...")
        new_action.triggered.connect(self.prompt_and_add_chapter)

        if item:            
            is_chapter = item.data(0, self.id_role) is not None
        
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

    @receiver(Events.NEW_CHAPTER_REQUESTED)
    def prompt_and_add_chapter(self, data: dict = None) -> None:
        """
        Prompts the user for a new chapter title, creates the chapter in the 
        database, reloads the outline, and selects the new chapter.
        
        :param data: Data dictionary, Empty as function doesn't need it.
        :type data: dict
        
        :rtype: None
        """        
        title, ok = QInputDialog.getText(
            self, 
            "New Chapter", 
            "Enter the title for the new chapter:",
            text="New Chapter"
        )

        if ok and title:
            # Determine the sort order for the new chapter (place it last at the root level)
            current_sort_order = self.tree_widget.topLevelItemCount() + 1
            
            bus.publish(Events.NEW_ITEM_REQUESTED, data={
                'entity_type': EntityType.CHAPTER, 'title': title, 'sort_order': current_sort_order
            })

    @receiver(Events.NEW_ITEM_CREATED)
    def _select_new_chapter(self, data: dict) -> None:
        """
        Selects the newly created chapter.
        
        :param data: A dictionary of the needed data containing {type: EntityType.Chapter,
        ID: int}
        :type data: dict

        :rtype: None
        """
        if data.get('entity_type') != EntityType.CHAPTER:
            return
        
        id = data.get('ID')
        if not id:
            return
        
        bus.publish(Events.OUTLINE_LOAD_REQUESTED, data={'entity_type': EntityType.CHAPTER})
        
        new_item = self.find_chapter_item_by_id(id)
        if new_item:
            self.tree_widget.setCurrentItem(new_item)
            self._on_item_clicked(new_item, 0)


    def _delete_chapter(self, item: QTreeWidgetItem) -> None:
        """
        Handles confirmation and deletion of a chapter item and its corresponding 
        entry in the database.
        
        :param item: The chapter item to be deleted.
        :type item: :py:class:`~PySide6.QtWidgets.QTreeWidgetItem`

        :rtype: None
        """
        chapter_id = item.data(0, self.id_role)
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
            bus.publish(Events.ITEM_DELETE_REQUESTED, data={
                'entity_type': EntityType.CHAPTER, 'ID': chapter_id
            })

    def check_save_and_delete(self, item: QTreeWidgetItem) -> None:
        """
        Emits :py:attr:`.pre_chapter_change` to ensure the currently viewed 
        chapter is saved, then triggers the deletion process.

        :param item: The chapter item queued for deletion.
        :type item: :py:class:`~PySide6.QtWidgets.QTreeWidgetItem`

        :rtype: None
        """
        bus.publish(Events.PRE_ITEM_CHANGE, data={'entity_type': EntityType.CHAPTER, 
                                                  'ID': self.current_item_id, 'parent': self})
        self._delete_chapter(item)

    def find_chapter_item_by_id(self, chapter_id: int) -> QTreeWidgetItem | None:
        """
        Helper to find a chapter :py:class:`~PySide6.QtWidgets.QTreeWidgetItem` 
        by its stored database ID.
        
        :param chapter_id: The unique ID of the chapter to find.
        :type chapter_id: :py:obj:`int`
        
        :returns: The matching item or None.
        :rtype: :py:class:`~PySide6.QtWidgets.QTreeWidgetItem` or None
        """
        iterator = QTreeWidgetItemIterator(self.tree_widget)
        while iterator.value():
            item = iterator.value()
            if item.data(0, self.id_role) == chapter_id:
                return item
            iterator += 1
        return None
