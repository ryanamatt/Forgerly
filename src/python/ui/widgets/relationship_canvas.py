# src/python/ui/widgets/relationship_canvas.py

from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import QLineF, QRectF
from PyQt6.QtGui import QWheelEvent, QPainter, QMouseEvent, QPen, QColor

class RelationshipCanvas(QGraphicsView):
    """
    A custom QGraphicsView that handles zooming, panning, and background drawing.
    This replaces the raw QGraphicsView inside RelationshipEditor.
    """
    def __init__(self, scene, parent=None) -> None:
        """
        Instantiate a RelationshipCanvas

        :param parent: The parent widget. Default is None:
        :type: :py:class:`~PyQt6.QtWidgets.QWidget`

        :rtype: None
        """
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)

        # Grid Settings
        self.grid_size = 20
        self.show_grid = True
        self.snap_to_grid = True

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        """
        Draws a coordinate grid background.
        
        :param painter: The QPainter
        :type painter: :py:class:`~PyQt6.QtGui.QPainter`
        :param rect: The rectangle
        :type rect: :py:class:`~PyQt6.QtGui.QRectF`

        :rtype: None
        """
        if not self.show_grid:
            super().drawBackground(painter, rect)
            return

        left = int(rect.left()) - (int(rect.left()) % self.grid_size)
        top = int(rect.top()) - (int(rect.top()) % self.grid_size)
        
        lines = []
        for x in range(left, int(rect.right()), self.grid_size):
            lines.append(QLineF(x, rect.top(), x, rect.bottom()))
        for y in range(top, int(rect.bottom()), self.grid_size):
            lines.append(QLineF(rect.left(), y, rect.right(), y))

        painter.setPen(QPen(QColor(220, 220, 220), 0.5))
        painter.drawLines(lines)

    def toggle_grid(self, enabled: bool) -> None:
        """
        Toggles the grid
        
        :param enabled: True to enable the grid otherwise False.
        :type enabled: bool
        """
        self.show_grid = enabled
        self.viewport().update()

    def toggle_snap(self, enabled: bool) -> None:
        """
        Toggles the snap to grid.
        
        :param enabled: True to enable snap to grid otherwise False
        :type enabled: bool

        :rtype: None
        """
        self.snap_to_grid = enabled

    # --- Events Handling ---

    def wheelEvent(self, event: QWheelEvent) -> None:
        """
        Custom zoom logic for smoother navigation using
        the scroll wheel.
        
        :param event: The scrool event.
        :type event: :py:class:`~PyQt6.QtGui.QWheelEvent`

        :rtype: None
        """
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """
        Docstring for mouseMoveEvent
        
        :param self: Description
        :param event: Description
        """
        editor = self.parent()
        if hasattr(editor, 'temp_line') and editor.temp_line and editor.selected_node_a:
            start_pos = editor.selected_node_a.scenePos()
            end_pos = self.mapToScene(event.pos())
            editor.temp_line.setLine(QLineF(start_pos, end_pos))

        super().mouseMoveEvent(event)