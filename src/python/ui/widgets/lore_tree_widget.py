# src/python/ui/widgets/lore_tree_widget.py

from PyQt6.QtWidgets import QTreeWidget, QAbstractItemView, QTreeWidgetItem, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDropEvent

from ...utils.logger import get_logger

logger = get_logger(__name__)

class LoreTreeWidget(QTreeWidget):
    """
    A custom :py:class:`~PyQt6.QtWidgets.TreeWidget` that is used to manage
    the Tree layout of Lore Entries.

    It allows to drag-and-drop setting of lore entries in a hierachical fashin.
    """

    lore_parent_id_updated = pyqtSignal(int, object)
    """:py:class:`~PyQt6.QtCore.pyqtSignal` (int, object): Signal to connect back to the LoreOutlineManager"""

    lore_hierarchy_updated = pyqtSignal(int, int)
    """:py:class:`~PyQt6.QtCore.pyqtSignal` (int, int, int): Signal to connect back to the LoreOutlineManager"""

    def __init__(self, id_role: int, parent=None):
        """
        Initializes a LoreTreeWidget.
        
        :param id_role: The ID of the current entry.
        :type id_role: int
        :param root_item_role: The root item role.
        :type root_item_role: int
        :param parent: The parent widget.
        :type parent: :py:class:`~PyQt6.QtWidgets.QWidget`, optional
        """
        super().__init__(parent)

        self.id_role = id_role
        
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

        logger.debug(f"LoreTreeWidget initialized with ID role {self.id_role}")

    def dropEvent(self, event: QDropEvent) -> None:
        """
        Handles the drop event: moves the item visually and updates the database.

        :param event: The event.
        :type event: :py:class:`~PyQt6.QtCore.QDropEvent`

        :rtype: None
        """
        # 1. Capture the drop position details BEFORE super().dropEvent()
        pos = event.position().toPoint()
        target_item = self.itemAt(pos)
        indicator = self.dropIndicatorPosition()

        # 2. Perform the visual move
        super().dropEvent(event)

        dropped_item = self.currentItem()
        if not dropped_item:
            return

        # 3. Determine the correct Parent based on where it was dropped
        # If dropped ON an item, that item is the parent.
        # If dropped ABOVE/BELOW, the parent is the target_item's parent.
        actual_parent = None
        if target_item:
            if indicator == QAbstractItemView.DropIndicatorPosition.OnItem:
                actual_parent = target_item
            else:
                actual_parent = target_item.parent()

        # 4. Extract the ID from the determined parent
        new_parent_id = actual_parent.data(0, self.id_role) if actual_parent else None

        # 5. Update siblings for sort order
        iteration_root = actual_parent or self.invisibleRootItem()
        for i in range(iteration_root.childCount()):
            child = iteration_root.child(i)
            child_id = child.data(0, self.id_role)
            
            # This will now correctly report the parent ID instead of None
            self.lore_hierarchy_updated.emit(child_id, new_parent_id)