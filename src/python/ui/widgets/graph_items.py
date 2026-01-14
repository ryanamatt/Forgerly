# src\python\ui\widgets/graph_items.py

from PySide6.QtWidgets import (
    QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem, QMenu
)
from PySide6.QtCore import Qt, QPointF, Signal, QRectF, QObject, QLineF, QEvent
from PySide6.QtGui import QColor, QPen, QBrush, QFont, QMouseEvent, QCursor, QPainter
import math
from typing import Any, TYPE_CHECKING

from ...utils.events import Events
from ...utils.event_bus import bus

if TYPE_CHECKING:
    from ..views.relationship_editor import RelationshipEditor

class CharacterNodeSignals(QObject):
    """
    Signal Emitter for :py:class:`.CharacterNode`.
    
    This is necessary because :py:class:`.CharacterNode` inherits from 
    :py:class:`~PySide6.QtWidgets.QGraphicsEllipseItem` and cannot be a 
    direct subclass of :py:class:`~PySide6.QtCore.QObject`.
    """
    node_moved = Signal(int, float, float, str, str, bool, bool)
    """
    :py:class:`~PySide6.QtCore.Signal` (int, float, float, str, str, int): 
    Emitted when a node is dragged and released.
    
    Carries the (Character ID, new X position, new Y position, Name, Color, 
    Shape ID, Name, Color, and Shape ID)
    """

class CharacterNode(QGraphicsEllipseItem):
    """
    A draggable and interactive representation of a Character on the 
    relationship graph canvas.
    """

    def __init__(self, char_id: int, name: str, x: float, y: float, color: str, shape: str, 
                 parent=None) -> None:
        """
        Initializes the character node.
        
        :param char_id: The unique database ID of the character.
        :type char_id: int
        :param name: The character's display name.
        :type name: str
        :param x: The initial X position of the node.
        :type x: float
        :param y: The initial Y position of the node.
        :type y: float
        :param color: The color string for the node (e.g., "#RRGGBB").
        :type color: str
        :param shape: The shape type for the node (e.g., "ellipse").
        :type shape: str
        :param parent: The parent Qt item.
        :type parent: :py:class:`~PySide6.QtWidgets.QGraphicsItem` or None

        :rtype: None
        """
        self.NODE_RADIUS = 30
        rect = QRectF(-self.NODE_RADIUS, -self.NODE_RADIUS, 2 * self.NODE_RADIUS, 2 * self.NODE_RADIUS)
        super().__init__(rect, parent)

        self.char_id = char_id
        self.name = name
        self.node_color = color
        self.node_shape = shape
        self.is_hidden = False
        self.is_locked = False

        self.signals = CharacterNodeSignals()

        self.setPos(x, y)
        self._update_appearance()

        # set up dragging
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        
        self.setAcceptHoverEvents(True)

        # Add a name label
        self.label = QGraphicsTextItem(name, self)
        label_rect = self.label.boundingRect()
        self.label.setPos(-label_rect.width() / 2, self.NODE_RADIUS + 5)
        self.label.setFont(QFont("Arial", 10))

    def _update_appearance(self) -> None:
        """
        Updates the brush/pen based on current attributes.
        
        This method is called during initialization and when the node's visual 
        state (like selection highlight) changes.
        
        :rtype: None
        """
        brush = QBrush(QColor(self.node_color))
        if getattr(self, 'is_selected_for_connect', False):
            pen = QPen(QColor("gold"), 4, Qt.PenStyle.DashLine)
        else:
            pen = QPen(QColor(Qt.GlobalColor.black), 2)
        
        self.setBrush(brush)
        self.setPen(pen)

    def hoverEnterEvent(self, event) -> None:
        """
        Changes cursor to drag cursor when hovering over the node.
        
        :param event: The hover event.
        :type event: :py:class:`~PySide6.QtWidgets.QGraphicsSceneHoverEvent`
        
        :rtype: None
        """
        self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        """
        Restores default cursor when leaving the node.
        
        :param event: The hover event.
        :type event: :py:class:`~PySide6.QtWidgets.QGraphicsSceneHoverEvent`
        
        :rtype: None
        """
        self.unsetCursor()
        super().hoverLeaveEvent(event)

    def itemChange(self, change: QGraphicsEllipseItem.GraphicsItemChange, value: Any) -> Any:
        """
        Handles changes to the item's state, specifically for movement.
        
        Ensures the node position is correctly snapped to the grid (if any),
        prevents collision with other nodes, and updates connected edges.

        :param change: The type of state change.
        :type change: :py:class:`~PySide6.QtWidgets.QGraphicsItem.GraphicsItemChange`
        :param value: The new value for the state change.
        :type value: Any
        
        :returns: The potentially modified new value.
        :rtype: :py:obj:`Any`
        """
        if change == self.GraphicsItemChange.ItemPositionChange and self.scene():
            new_pos = value
            view = self.scene().views()[0]

            if view.snap_to_grid:
                grid = view.grid_size
                new_pos = value.toPoint()
                x = round(new_pos.x() / grid) * grid
                y = round(new_pos.y() / grid) * grid
                new_pos = QPointF(x, y)
            
            # Check for Collision with other nodes
            if not self._would_collide_at_position(new_pos):
                return new_pos
            else:
                # Return current pos to prevent movement
                return self.scenePos()

        if change == self.GraphicsItemChange.ItemPositionHasChanged:
            if self.scene():
                for item in self.scene().items():
                    if isinstance(item, RelationshipEdge):
                        item.update_position()
        return super().itemChange(change, value)
    
    def _would_collide_at_position(self, new_pos: QPointF) -> None:
        """
        Checks if moving to the new position would cause a collision with 
        another CharacterNode.
        
        Two nodes collide if the distance between their centers is less than 
        twice the node radius (i.e., they would overlap).
        
        :param new_pos: The proposed new position for this node.
        :type new_pos: :py:class:`~PySide6.QtCore.QPointF`
        
        :returns: True if collision would occur, False otherwise.
        :rtype: bool
        """
        if not self.scene():
            return
        
        for item in self.scene().items():
            if isinstance(item, CharacterNode) and item is not self:
                other_pos = item.scenePos()
                dx = new_pos.x() - other_pos.x()
                dy = new_pos.y() - other_pos.y()
                distance = math.sqrt(dx * dx + dy * dy)
                min_dist = (self.NODE_RADIUS + item.NODE_RADIUS) * 1.1

                if distance < min_dist:
                    return True
                
        return False

    def mouseReleaseEvent(self, event) -> None:
        """
        Handles the mouse release event. Emits the :py:attr:`.node_moved` 
        signal if the node has been dragged from its original position.
        
        :param event: The mouse event.
        :type event: :py:class:`~PySide6.QtGui.QGraphicsSceneMouseEvent`

        :rtype: None
        """
        super().mouseReleaseEvent(event)

        pos = self.scenePos()

        # Emit signal to AppCoordinator for saving
        self.signals.node_moved.emit(
            self.char_id,
            pos.x(),
            pos.y(),
            self.node_color,
            self.node_shape,
            self.is_hidden,
            self.is_locked
        )

    def set_selection_highlight(self, highlight: bool) -> None:
        """
        Toggles the highlight for relationship selection.
        
        :param highlight: True if to set highlight for relationship selection,
            otherwise False.
        :type highlight: bool

        :rtype: None
        """
        if not self.scene():
            return

        self.is_selected_for_connect = highlight
        self._update_appearance()
        self.update() # Force redraw

    def mousePressEvent(self, event) -> None:
        """
        Handles the mouse press event. Stores the initial position for change detection.
        
        If the left button is clicked, it allows for dragging. If the right button 
        is clicked, it signals the parent :py:class:`.RelationshipEditor` to handle 
        the selection logic for relationship creation.
        
        :param event: The mouse event.
        :type event: :py:class:`~PySide6.QtGui.QGraphicsSceneMouseEvent`

        :rtype: None
        """
        
        # If left click, proceed with standard dragging/moving
        if event.button() == Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)

    def contextMenuEvent(self, event: QMouseEvent) -> None:
        """
        Custom context menu for the character node.

        :param event: The right click event.
        :type event: QMouseEvent

        :rtype: None
        """
        menu = QMenu()

        connect_action = menu.addAction("Connect to Character...")
        set_visible_action = menu.addAction("Make Character Invisible")

        lock_node_action_text = "Unlock Character" if self.is_locked else "Lock Character"
        lock_node_action = menu.addAction(lock_node_action_text)
    
        view = self.scene().views()[0]
        editor: 'RelationshipEditor' = view.parent()

        action = menu.exec(event.screenPos())

        if action == connect_action:
            editor.handle_node_right_click(self)

        elif action == set_visible_action:
            self.is_hidden = not self.is_hidden

            bus.publish(Events.GRAPH_NODE_VISIBILTY_CHANGED, data={
                'ID': self.char_id, 'is_hidden': self.is_hidden
            })

        elif action == lock_node_action:
            self.is_locked = not self.is_locked

            bus.publish(Events.GRAPH_NODE_LOCKED_CHANGED, data={
                'ID': self.char_id, 'is_locked': self.is_locked
            })

class RelationshipEdge(QGraphicsLineItem):
    """
    A line item representing a relationship between two :py:class:`.CharacterNode`'s.
    
    It updates its position dynamically as the connected nodes are moved and 
    displays the relationship label.
    """
    
    def __init__(self, edge_data: dict[str, Any], nodes: dict[int, CharacterNode], parent=None):
        """
        Initializes the relationship edge.
        
        :param edge_data: A dictionary containing relationship data (source, target, type, style, etc.).
        :type edge_data: dict[str, Any]
        :param nodes: A dictionary mapping character IDs to :py:class:`.CharacterNode` objects.
        :type nodes: dict[int, :py:class:`.CharacterNode`]
        :param parent: The parent Qt item.
        :type parent: :py:class:`~PySide6.QtWidgets.QGraphicsItem` or None

        :rtype: None
        """
        super().__init__(parent)
        self.edge_data = edge_data
        self.source_node = nodes[edge_data['source']]
        self.target_node = nodes[edge_data['target']]

        # Enable selection so the edge can be right-clicked easily
        self.setFlag(QGraphicsLineItem.GraphicsItemFlag.ItemIsSelectable, True)

        # Add a label in the middle of the edge
        self.label_item = QGraphicsTextItem(self.edge_data.get('label', ''), self)

        self._update_pen()
        self.update_position()

    def _update_pen(self):
        """
        Sets the pen properties based on edge data, including color, thickness 
        (based on 'intensity'), and line style.
        
        :rtype: None
        """
        intensity = self.edge_data.get('intensity', 5) # Value between 1-10

        color = QColor(self.edge_data.get('color', '#f0f0f0'))
        intensity = self.edge_data.get('intensity', 5)

        # Intensity-based opacity (50% to 100%)
        opacity = 0.5 + (intensity / 10.0) * 0.5  # Maps 1-10 to 0.5-1.0
        color.setAlphaF(opacity)
        
        # Power-scaled thickness
        normalized = intensity / 10.0
        thickness = 1 + (normalized ** 1.5) * 9
        
        pen = QPen(color, thickness)

        # Line Style (Apply Solid, Dash, or Dot based on Data)
        match self.edge_data['style'].lower():

            case 'dashed':
                pen.setStyle(Qt.PenStyle.DashLine)
            
            case 'dotted':
                pen.setStyle(Qt.PenStyle.DotLine)

            case 'dashdot':
                pen.setStyle(Qt.PenStyle.DashDotLine)

            case _:
                pen.setStyle(Qt.PenStyle.SolidLine)

        self.setPen(pen)

    def update_position(self) -> None:
        """
        Recalculates the start and end points of the line based on the 
        current positions of the source and target nodes.
        
        The line is drawn from the center of the source node to the center 
        of the target node. It also updates the position and rotation of the 
        relationship label.
        
        :rtype: None
        """
        # Get Center Points
        p1 = self.source_node.scenePos()
        p2 = self.target_node.scenePos()

        line = QLineF(p1, p2)
        length = line.length()

        # Avoid division by zero if nodes are on top of each other
        if length > self.source_node.NODE_RADIUS + 2:
            dx = p2.x() - p1.x()
            dy = p2.y() - p1.y()
            ratio = self.source_node.NODE_RADIUS / length

            offset_x = dx * ratio
            offset_y = dy * ratio
            start_point = QPointF(p1.x() + offset_x, p1.y() + offset_y)
            end_point = QPointF(p2.x() - offset_x, p2.y() - offset_y)
        else:
            return

        self.setLine(start_point.x(), start_point.y(), end_point.x(), end_point.y())

        # --- Label Orientation ---
        mid_point = (start_point + end_point) / 2
        label_rect = self.label_item.boundingRect()

        # Calculate angle and handle 'upside down' prevention
        angle = self._calculate_angle(start_point, end_point)
        
        # Apply rotation first
        self.label_item.setRotation(angle)
        
        # Re-center the label after rotation
        # We use the label's local center to ensure it rotates around its own middle
        self.label_item.setTransformOriginPoint(label_rect.width() / 2, label_rect.height() / 2)
        self.label_item.setPos(mid_point.x() - label_rect.width() / 2, mid_point.y() - label_rect.height() / 2)

    def paint(self, painter: QPainter, option, widget) -> None:
        """
        Paints the RelationshipEdge.
        
        :param painter: The QPainter object.
        :type painter: QPainter
        :param option: The option.
        :param widget: The Widget to apply to.

        :rtype: None
        """
        self.update_position()
        super().paint(painter, option, widget)

    def _calculate_angle(self, p1: QPointF, p2: QPointF) -> float:
        """
        Calculates the angle of the line for rotating the label. Flips the
        angle by 180 degrees if the text would otherwise be upside down.
        
        :param p1: The first point (:py:class:`~PySide6.QtCore.QPointF`).
        :type p1: :py:class:`~PySide6.QtCore.QPointF`
        :param p2: The second point (:py:class:`~PySide6.QtCore.QPointF`).
        :type p2: :py:class:`~PySide6.QtCore.QPointF`

        :returns: Returns the value of the angle in degrees, used to align the label with the edge.
        :rtype: float
        """
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        # Angle in radians so convert to degrees
        angle = math.degrees(math.atan2(-dy, dx))
        if angle > 90 or angle < -90:
            angle += 180
        return angle
    
    # --- Event Handling ---

    def contextMenuEvent(self, event: QEvent) -> None:
        """
        Displays the custom context menu for RelationshipEdge.
        
        :param event: The event.
        :type event: :py:class:`~PySide6.QtCore.QEvent`

        :rtype: None
        """
        menu = QMenu()
        edit_action = menu.addAction("Edit Relationship")
        delete_action = menu.addAction("Delete Relationship")
        
        # Map the menu to the editor through the view
        view = self.scene().views()[0]
        editor = view.parent()
        
        action = menu.exec(event.screenPos())
        
        if action == edit_action:
            bus.publish(Events.REL_DETAILS_REQUESTED, data={'source': self.source_node, 
                                        'target': self.target_node, 'ID': self.edge_data.get('id')})
        elif action == delete_action:
            bus.publish(Events.REL_DELETE_REQUESTED, data={'source': self.source_node, 
                                        'target': self.target_node, 'ID': self.edge_data.get('id')})
