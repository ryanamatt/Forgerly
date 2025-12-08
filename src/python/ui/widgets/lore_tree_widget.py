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

    def __init__(self, id_role: int, root_item_role: int, parent=None):
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
        self.root_item_role = root_item_role
        
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

        logger.debug(f"LoreTreeWidget initialized with ID role {self.id_role}")

    def dropEvent(self, event: QDropEvent) -> None:
        """
        Handles the drop event: moves the item visually and updates the database.

        :rtype: None
        """
        try:
            # Allow the base QTreeWidget to handle the visual move
            super().dropEvent(event)
            logger.info("Lore item drop event handled visually.")

            # Get the item that was just dropped (it will be the current item)
            dropped_item: QTreeWidgetItem | None = self.currentItem()

            if not dropped_item: 
                logger.debug("Drop event: No current item after drop. Ignoring.")
                return

            lore_id = dropped_item.data(0, self.id_role)

            if lore_id is None: 
                logger.warning(f"Drop event: Dropped item has no associated ID in role {self.id_role}. Ignoring.")
                return

            # Determine the new parent
            new_parent_item: QTreeWidgetItem | None = dropped_item.parent()
            new_parent_id: int | None = None # The None value represents the root of the tree (NULL parent ID in DB)

            if new_parent_item:
                # If the new parent item is the root placeholder, the ID should be NULL
                if new_parent_item.data(0, self.id_role) == self.root_item_role:
                    new_parent_id = None
                    logger.debug(f"Lore ID {lore_id} dropped under the virtual root.")
                else:
                    # Otherwise, get the ID of the actual new parent lore entry
                    new_parent_id = new_parent_item.data(0, self.id_role)
                    logger.debug(f"Lore ID {lore_id} dropped under parent ID {new_parent_id}.")
            else:
                # Dropped at the top level (no parent item), which corresponds to the virtual root
                new_parent_id = None
                logger.debug(f"Lore ID {lore_id} dropped at the top level (None parent).")

            # Emit the signal to notify the manager/repository to update the DB
            logger.info(f"Signal: lore_parent_id_updated emitted (Lore ID: {lore_id}, New Parent ID: {new_parent_id})")
            self.lore_parent_id_updated.emit(lore_id, new_parent_id)
        
        except Exception as e:
            logger.error(f"An unexpected error occurred during the drop operation on LoreTreeWidget.", exc_info=True)
            # Display an error message to the user
            QMessageBox.critical(
                self,
                "Lore Hierarchy Error",
                "An internal error occurred while attempting to change the lore entry's hierarchy."
            )