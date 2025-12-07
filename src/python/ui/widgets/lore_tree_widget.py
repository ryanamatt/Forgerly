# src/python/ui/widgets/lore_tree_widget.py

from PyQt6.QtWidgets import QTreeWidget, QAbstractItemView, QTreeWidgetItem, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDropEvent

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

    def dropEvent(self, event: QDropEvent) -> None:
        """
        Handles the drop event: moves the item visually and updates the database.

        :rtype: None
        """
        super().dropEvent(event)

        dropped_item: QTreeWidgetItem | None = self.currentItem()

        if not dropped_item: return

        lore_id = dropped_item.data(0, self.id_role)

        if lore_id is None: return

        new_parent_item: QTreeWidgetItem | None = dropped_item.parent()
        new_parent_id: int | None = None

        if new_parent_item:
            if new_parent_item.data(0, self.root_item_role):
                new_parent_id = None
            else:
                new_parent_id = new_parent_item.data(0, self.id_role)

        if lore_id is not None:
            self.lore_parent_id_updated.emit(lore_id, new_parent_id)