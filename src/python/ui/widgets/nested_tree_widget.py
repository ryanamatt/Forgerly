# src/python/ui/widgets/nested_tree_widget.py

from PySide6.QtWidgets import QTreeWidget, QAbstractItemView, QTreeWidgetItem, QMessageBox
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDropEvent

from ...utils.logger import get_logger

logger = get_logger(__name__)

class NestedTreeWidget(QTreeWidget):
    """
    A custom :py:class:`~PyQt6.QtWidgets.TreeWidget` that is used to manage
    the Tree layout of items.

    It allows to drag-and-drop setting of items in a hierachical fashin.
    """

    item_parent_id_updated = Signal(int, object)
    """:py:class:`~PyQt6.QtCore.Signal` (int, object): Signal to connect back to the OutlineManager"""

    item_hierarchy_updated = Signal(int, object)
    """:py:class:`~PyQt6.QtCore.Signal` (int, object): Signal to connect back to the OutlineManager"""

    def __init__(self, id_role: int, parent=None):
        """
        Initializes a NestedTreeWidget.
        
        :param id_role: The ID of the current entry.
        :type id_role: int
        :param parent: The parent widget.
        :type parent: :py:class:`~PyQt6.QtWidgets.QWidget`, optional
        """
        super().__init__(parent)

        self.id_role = id_role
        
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

        logger.debug(f"NestedTreeWidget initialized with ID role {self.id_role}")

    def dropEvent(self, event: QDropEvent) -> None:
        """
        Handles the drop event: moves the item visually and updates the database.

        :param event: The event.
        :type event: :py:class:`~PyQt6.QtCore.QDropEvent`

        :rtype: None
        """
        # 1. Capture the drop position details BEFORE the visual move
        pos = event.position().toPoint()
        target_item = self.itemAt(pos)
        indicator = self.dropIndicatorPosition()
        
        # Identify which item is being dragged
        dragged_item = self.currentItem()
        if not dragged_item:
            return

        # Store the dragged item's ID before the move
        dragged_item_id = dragged_item.data(0, self.id_role)
        if dragged_item_id is None or dragged_item_id <= 0:
            return

        # Determine the target parent BEFORE the move based on drop indicator
        target_parent_id = None
        if target_item:
            if indicator == QAbstractItemView.DropIndicatorPosition.OnItem:
                # Dropping ON an item -> that item becomes the parent
                target_parent_id = target_item.data(0, self.id_role)
                logger.debug(f"Drop ON item {target_parent_id} (nesting)")
            else:
                # Dropping ABOVE or BELOW an item -> sibling relationship
                parent = target_item.parent()
                if parent:
                    target_parent_id = parent.data(0, self.id_role)
                    logger.debug(f"Drop BESIDE item, parent is {target_parent_id}")
                else:
                    target_parent_id = None
                    logger.debug(f"Drop BESIDE root item, parent is None")
        else:
            # Dropped on empty space -> root level
            target_parent_id = None
            logger.debug("Drop on empty space, parent is None")

        # Normalize parent ID (0 or invalid IDs become None)
        if target_parent_id == 0:
            target_parent_id = None

        # 2. Perform the visual move
        super().dropEvent(event)

        # 3. Update the dropped item's parent in the database
        logger.info(f"Updating item {dragged_item_id} to parent {target_parent_id}")
        self.item_parent_id_updated.emit(dragged_item_id, target_parent_id)
        
        # 4. Update sort order for all siblings at the new level
        # Determine which parent to iterate over for sort order updates
        if target_parent_id is None:
            iteration_root = self.invisibleRootItem()
        else:
            # Find the parent item by ID
            iteration_root = self._find_item_by_id(target_parent_id)
            if iteration_root is None:
                # Fallback to invisible root if parent not found
                iteration_root = self.invisibleRootItem()
        
        # Safely iterate through children to update sort order
        try:
            child_count = iteration_root.childCount()
            logger.debug(f"Updating sort order for {child_count} children under parent {target_parent_id}")
            
            for i in range(child_count):
                try:
                    child = iteration_root.child(i)
                    if child is None:
                        continue
                        
                    child_id = child.data(0, self.id_role)
                    if child_id is not None and child_id > 0:
                        # Emit hierarchy update for sort order
                        self.item_hierarchy_updated.emit(child_id, target_parent_id)
                        
                except (RuntimeError, AttributeError) as e:
                    logger.warning(f"Error accessing child at index {i}: {e}")
                    continue
                    
        except (RuntimeError, AttributeError) as e:
            logger.error(f"Error iterating children: {e}")
            # Parent update already succeeded, so this is not critical

    def _find_item_by_id(self, item_id: int) -> QTreeWidgetItem | None:
        """
        Helper method to find a tree item by its ID.
        
        :param item_id: The ID to search for.
        :type item_id: int
        
        :returns: The matching QTreeWidgetItem or None.
        :rtype: QTreeWidgetItem | None
        """
        from PySide6.QtWidgets import QTreeWidgetItemIterator
        
        iterator = QTreeWidgetItemIterator(self)
        while iterator.value():
            item = iterator.value()
            try:
                if item.data(0, self.id_role) == item_id:
                    return item
            except RuntimeError:
                pass
            iterator += 1
        return None