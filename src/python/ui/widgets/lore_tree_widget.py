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
            # 1. Determine the item being dropped (must be done before the visual move)
            drop_target_item: QTreeWidgetItem | None = self.itemAt(event.position().toPoint())
            
            # 2. Let the base QTreeWidget handle the visual move (this updates the hierarchy in the model)
            super().dropEvent(event)
            logger.info("Lore item drop event handled visually.")

            # 3. Get the item that was just moved (it will be the current item)
            dropped_item: QTreeWidgetItem | None = self.currentItem()

            if not dropped_item: 
                logger.debug("Drop event: No current item after drop. Ignoring.")
                return

            lore_id = dropped_item.data(0, self.id_role)

            if lore_id is None: 
                logger.warning(f"Drop event: Dropped item has no associated ID in role {self.id_role}. Ignoring.")
                return

            # 4. Determine the new parent ID using the intended target from step 1.
            new_parent_id: int | None = None 
            
            # The actual parent (dropped_item.parent()) is unreliable, so we use the target.
            if drop_target_item:
                # Retrieve the ID from the intended target item.
                # If the target is a regular lore entry, new_parent_id is the int ID.
                # If the target is the root placeholder, new_parent_id is None.
                new_parent_id = drop_target_item.data(0, self.id_role)
                
                # Check the target item's root status for debugging/confirmation
                is_root_placeholder = drop_target_item.data(0, self.root_item_role)

                if new_parent_id is None and is_root_placeholder is True:
                    # Target is confirmed to be the root placeholder.
                    new_parent_id = None
                    logger.debug(f"Lore ID {lore_id} dropped under the virtual root (Target ID is None).")
                elif new_parent_id is not None:
                    # Target is a valid lore entry item.
                    logger.debug(f"Lore ID {lore_id} dropped under parent ID {new_parent_id}.")
                else:
                    # Item was found, but it has no valid ID (e.g., placeholder, error item). Default to None.
                    new_parent_id = None
                    logger.warning(f"Drop event: Intended parent item '{drop_target_item.text(0)}' has no valid ID. Defaulting parent to None.")
            else:
                # Case: Dropped at the top level (no item found at the drop position).
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