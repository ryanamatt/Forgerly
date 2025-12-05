# src/python/ui/widgets/flow_layout.py

from PyQt6.QtWidgets import QLayout, QLayoutItem
from PyQt6.QtCore import Qt, QSize, QRect, QPoint

class QFlowLayout(QLayout):
    """
    A custom :py:class:`~PyQt6.QtWidgets.QLayout` that arranges items in a flow, 
    wrapping to the next line when the row is full. 
    
    This layout is essential for dynamic content like a tag list where widgets 
    need to utilize horizontal space efficiently and wrap dynamically.
    It implements the core :py:class:`~PyQt6.QtWidgets.QLayout` methods 
    required for dynamic resizing and flow control.
    """
    def __init__(self, parent=None, margin=0, spacing=-1) -> None:
        """
        Initializes the :py:class:`.QFlowLayout`.
        
        :param parent: The parent widget.
        :type parent: :py:class:`~PyQt6.QtWidgets.QWidget`, optional
        :param margin: The margin around the content.
        :type margin: :py:obj:`int`
        :param spacing: The spacing between items. Defaults to -1 (parent's style).
        :type spacing: :py:obj:`int`

        :rtype: None
        """
        super().__init__(parent)

        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)

        self.item_list = []
    
    def __del__(self) -> None:
        """
        Clears all items upon deletion.
        
        :rtype: None
        """
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item) -> None:
        """
        Adds a layout item to the end of the layout.
        
        :param item: The layout item to add.
        :type item: :py:class:`~PyQt6.QtWidgets.QLayoutItem`

        :rtype: None
        """
        self.item_list.append(item)

    def count(self) -> int:
        """
        Returns the number of items in the layout.
        
        :rtype: int
        """
        return len(self.item_list)

    def itemAt(self, index) -> QLayoutItem | None:
        """
        Returns the item at the given index.
        
        :param index: The index of the item.
        :type index: int

        :returns: The layout item at the index, or None if the index is out of bounds.
        :rtype: :py:class:`~PyQt6.QtWidgets.QLayoutItem` or None
        """
        if 0 <= index < len(self.item_list):
            return self.item_list[index]
        return None

    def takeAt(self, index) -> QLayoutItem | None:
        """
        Removes the item at the given index and returns it.
        
        :param index: The index of the item to remove.
        :type index: :py:obj:`int`
        :returns: The removed layout item, or None if the index is out of bounds.
        :rtype: :py:class:`~PyQt6.QtWidgets.QLayoutItem` or None
        """
        if 0 <= index < len(self.item_list):
            return self.item_list.pop(index)
        return None
    
    def expandingDirections(self) -> Qt.Orientation:
        """
        Indicates that the layout can expand both horizontally and vertically.
        
        :returns: The orientation flags.
        :rtype: :py:class:`~PyQt6.QtCore.Qt.Orientation`
        """
        return Qt.Orientation.Horizontal | Qt.Orientation.Vertical

    def hasHeightForWidth(self) -> bool:
        """
        Returns True because the preferred height depends on the available width (due to wrapping).
        
        :rtype: bool
        """
        return True

    def heightForWidth(self, width) -> int:
        """
        Calculates the minimum required height for a given width to fit all items.
        
        :param width: The available width.
        :type width: int

        :returns: The minimum height required.
        :rtype: int
        """
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect) -> None:
        """
        Sets the geometry of the layout and performs the actual layout of items.
        
        :param rect: The rectangle defining the layout's new geometry.
        :type rect: :py:class:`~PyQt6.QtCore.QRect`
        
        :rtype: None
        """
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self) -> QSize:
        """
        Returns a suggested size for the layout. Defaults to :py:meth:`.minimumSize`.
        
        :returns: The suggested size.
        :rtype: :py:class:`~PyQt6.QtCore.QSize`
        """
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        """
        Returns the minimum size required by the layout.
        
        :returns: The minimum size.
        :rtype: :py:class:`~PyQt6.QtCore.QSize`
        """
        size = QSize()
        for item in self.item_list:
            size = size.expandedTo(item.minimumSize())
        
        # Add margins and spacing
        margin = self.contentsMargins()
        size += QSize(margin.left() + margin.right(), margin.top() + margin.bottom())
        return size
    
    def _do_layout(self, rect: QRect, test_only) -> int:
        """
        Performs the actual layout calculation, determining item positions and wrapping.
        
        :param rect: The available rectangle for layout.
        :type rect: :py:class:`~PyQt6.QtCore.QRect`
        :param test_only: If True, only calculates the height without moving items.
        :type test_only: bool

        :returns: The total height used by the layout.
        :rtype: int
        """
        x = rect.x()
        y = rect.y()
        line_height = 0
        
        spacing = self.spacing()

        for item in self.item_list:
            next_x = x + item.sizeHint().width() + spacing
            
            if next_x - spacing > rect.right() and line_height > 0:
                # Move to next line
                x = rect.x()
                y = y + line_height + spacing
                next_x = x + item.sizeHint().width() + spacing
                line_height = 0
            
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        # Returns the height used by the layout
        return y + line_height - rect.y() if line_height > 0 else 0