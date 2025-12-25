# src/python/ui/widgets/reordering_tree_widget.py

from PySide6.QtWidgets import QTreeWidget, QAbstractItemView
from PySide6.QtGui import QDropEvent
from PySide6.QtCore import Signal

class ReorderingTreeWidget(QTreeWidget):
    """
    A specialized :py:class:`~PyQt6.QtWidgets.QTreeWidget` that handles the 
    visual representation and drag-and-drop reordering of items.

    This widget is designed to work in tandem with a parent editor to ensure that 
    any structural changes made via the UI are synchronized with the underlying 
    database.
    """

    order_changed = Signal()
    """
    :py:class:`~PyQt6.QtCore.Signal` (): Emitted to notify a 
    successfuly drop to the manager.
    """

    def __init__(self, parent=None) -> None:
        """
        Initializes the ChapterTree.
        
        :param parent: The parent. Default None
        :type editor: :py:class:`~PyQt6.QtWidgets.QWidget``, optional
        """
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)

    def dropEvent(self, event: QDropEvent) -> None:
        """
        Overrides the default drop event to handle chapter reordering.
        
        When an item is dropped, this method triggers a save of the current 
        work, updates the sort orders of all chapters in the database based 
        on the new visual order, and reloads the outline to ensure UI/DB 
        consistency.

        :param event: The drop event containing information about the operation.
        :type event: :py:class:`~PyQt6.QtGui.QDropEvent`
        
        :rtype: None
        """
        if self.dropIndicatorPosition() == QAbstractItemView.DropIndicatorPosition.OnItem:
            event.ignore()
            return

        super().dropEvent(event)

        dropped_item = self.currentItem()
        if not dropped_item:
            return

        if dropped_item.parent() is not None:
            parent = dropped_item.parent()
            index = parent.indexOfChild(dropped_item)
            item = parent.takeChild(index)
            self.addTopLevelItem(item)
            self.setCurrentItem(item)

        self.order_changed.emit()
        
        event.accept()
