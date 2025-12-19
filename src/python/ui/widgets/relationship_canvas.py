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

        # Grid Settings
        self.grid_size = 20
        self.show_grid = True

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