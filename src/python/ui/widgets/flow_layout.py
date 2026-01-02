# src/python/ui/widgets/flow_layout.py

from PySide6.QtWidgets import QLayout, QLayoutItem, QWidget
from PySide6.QtCore import Qt, QSize, QRect, QPoint

from ...utils.logger import get_logger #

logger = get_logger(__name__)

class QFlowLayout(QLayout):
    """
    A custom :py:class:`~PySide6.QtWidgets.QLayout` that arranges items in a flow, 
    wrapping to the next line when the row is full. 
    
    This layout is essential for dynamic content like a tag list where widgets 
    need to utilize horizontal space efficiently and wrap dynamically.
    It implements the core :py:class:`~PySide6.QtWidgets.QLayout` methods 
    required for dynamic resizing and flow control.
    """
    def __init__(self, parent=None, margin=0, spacing=-1) -> None:
        """
        Initializes the :py:class:`.QFlowLayout`.
        
        :param parent: The parent widget.
        :type parent: :py:class:`~PySide6.QtWidgets.QWidget`, optional
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

        logger.debug(f"QFlowLayout initialized. Margin: {margin}, Spacing: {self.spacing()}")
    
    def __del__(self) -> None:
        """
        Clears all items upon deletion.
        
        :rtype: None
        """
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)
        logger.debug("QFlowLayout destroyed and all items removed.")

    def addItem(self, item: QLayoutItem) -> None:
        """
        Adds a layout item to the end of the layout.
        
        :param item: The layout item to add.
        :type item: :py:class:`~PySide6.QtWidgets.QLayoutItem`

        :rtype: None
        """
        try:
            if item.widget():
                widget: QWidget = item.widget()
                logger.debug(f"Adding widget item to flow layout: {widget.objectName() or widget.__class__.__name__}")
            else:
                logger.debug("Adding non-widget item to flow layout.")

            self.item_list.append(item)
            self.invalidate() # Force a relayout
        except Exception as e:
            logger.error(f"Failed to add item to QFlowLayout: {item}", exc_info=True)

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
        :rtype: :py:class:`~PySide6.QtWidgets.QLayoutItem` or None
        """
        if 0 <= index < len(self.item_list):
            return self.item_list[index]
        return None

    def takeAt(self, index: int) -> QLayoutItem | None:
        """
        Removes the item at the given index and returns it.
        
        :param index: The index of the item to remove.
        :type index: :py:obj:`int`
        :returns: The removed layout item, or None if the index is out of bounds.
        :rtype: :py:class:`~PySide6.QtWidgets.QLayoutItem` or None
        """
        if 0 <= index < len(self.item_list):
            item = self.item_list.pop(index)
            self.invalidate() # Force a relayout
            
            widget_name = item.widget().objectName() if item.widget() else "non-widget item"
            logger.debug(f"Taking item at index {index} from flow layout: {widget_name}")
            return item
        
        logger.warning(f"Attempted to take item at invalid index {index}. Item count: {self.count()}")
        return None
    
    def expandingDirections(self) -> Qt.Orientation:
        """
        Indicates that the layout can expand both horizontally and vertically.
        
        :returns: The orientation flags.
        :rtype: :py:class:`~PySide6.QtCore.Qt.Orientation`
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
        logger.debug(f"Calculating height for width: {width}")

        rect = QRect(0, 0, width, 0)
        return self._do_layout(rect, test_only=True)

    def setGeometry(self, rect) -> None:
        """
        Sets the geometry of the layout and performs the actual layout of items.
        
        :param rect: The rectangle defining the layout's new geometry.
        :type rect: :py:class:`~PySide6.QtCore.QRect`
        
        :rtype: None
        """
        super().setGeometry(rect)
        self._do_layout(rect, False)
        logger.debug(f"Geometry set and layout performed for rect: ({rect.width()}x{rect.height()})")

    def sizeHint(self) -> QSize:
        """
        Returns the preferred size of the layout. This is usually the size 
        of all items arranged in one row, if possible, or the size required
        to fit them all with a reasonable width.
        
        :returns: The suggested size.
        :rtype: :py:class:`~PySide6.QtCore.QSize`
        """
        logger.debug("Calculating size hint.")
        
        # Determine the size of the contents area (subtract margins)
        margin = self.contentsMargins()
        
        # We need a parent to get its width for a sensible sizeHint for flow layouts
        parent = self.parentWidget()
        effective_width = parent.width() if parent else 500 # Use a default if no parent
        effective_width -= margin.left() + margin.right()

        # Calculate the height required for the current effective width
        height = self.heightForWidth(effective_width)
        
        # Calculate the total width of all items (as if they were in a single row)
        total_width = 0
        spacing = self.spacing()
        
        for item in self.item_list:
            total_width += item.sizeHint().width()
            if total_width > 0:
                total_width += spacing # Add spacing after the item
        
        # If there are items, subtract the trailing spacing
        if self.item_list and total_width > 0:
            total_width -= spacing
            
        # Add back the margins
        size = QSize(total_width, height)
        size += QSize(margin.left() + margin.right(), margin.top() + margin.bottom())
        
        logger.debug(f"Size hint calculated: {size.width()}x{size.height()}.")
        return size

    def minimumSize(self) -> QSize:
        """
        Returns the minimum size required by the layout.
        
        :returns: The minimum size.
        :rtype: :py:class:`~PySide6.QtCore.QSize`
        """
        min_size = self.sizeHint()
        logger.debug(f"Minimum size calculated: {min_size.width()}x{min_size.height()}.")
        return min_size
    
    def _do_layout(self, rect: QRect, test_only) -> int:
        """
        Performs the actual layout calculation, determining item positions and wrapping.
        
        :param rect: The available rectangle for layout.
        :type rect: :py:class:`~PySide6.QtCore.QRect`
        :param test_only: If True, only calculates the height without moving items.
        :type test_only: bool

        :returns: The total height used by the layout.
        :rtype: int
        """
        if test_only:
            logger.debug(f"Starting layout calculation (test_only) for width {rect.width()}")
        else:
            logger.debug(f"Starting layout execution for rect: {rect.width()}x{rect.height()}")
            
        x = rect.x()
        y = rect.y()
        line_height = 0
        
        spacing = self.spacing()

        for i, item in enumerate(self.item_list):
            try:
                size_hint = item.sizeHint()
                item_width = size_hint.width()
                item_height = size_hint.height()
                next_x = x + item_width + spacing
                
                # Check for wrapping
                if next_x - spacing > rect.right() and line_height > 0:
                    # Move to next line
                    x = rect.x()
                    y = y + line_height + spacing
                    next_x = x + item_width + spacing
                    line_height = 0
                    logger.debug(f"Item {i}: Wrapping to new line at y={y}")
                
                # Update line height (maximum height of items on the current line)
                line_height = max(line_height, item_height)
                
                if not test_only:
                    # Execute the layout (move the item)
                    item.setGeometry(QRect(QPoint(x, y), size_hint))
                    
                x = next_x
            
            except Exception as e:
                # Catch any unexpected errors during geometry calculation or setting
                widget_name = item.widget().objectName() if item.widget() else f"item_index_{i}"
                logger.error(f"Error encountered during layout for item: {widget_name}", exc_info=True)
                # Continue to the next item instead of crashing the layout

        # The total height used includes the last line's height
        used_height = y + line_height
        
        logger.debug(f"Layout finished. Total content height used: {used_height}")
        return used_height
