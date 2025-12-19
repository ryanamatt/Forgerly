# src\python\ui\views\relationship_editor.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, 
    QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem, 
    QMessageBox, QFrame, QDialog, QFormLayout, QComboBox, QLineEdit,
    QSpinBox, QDialogButtonBox, QLabel, QToolBar
)
from PyQt6.QtCore import Qt, QPointF, pyqtSignal, QRectF, QObject, QLineF
from PyQt6.QtGui import QColor, QPen, QBrush, QFont, QAction
import math
from typing import Any
from ...services.app_coordinator import AppCoordinator
from ..widgets.relationship_canvas import RelationshipCanvas

class CharacterNodeSignals(QObject):
    """
    Signal Emitter for :py:class:`.CharacterNode`.
    
    This is necessary because :py:class:`.CharacterNode` inherits from 
    :py:class:`~PyQt6.QtWidgets.QGraphicsEllipseItem` and cannot be a 
    direct subclass of :py:class:`~PyQt6.QtCore.QObject`.
    """
    node_moved = pyqtSignal(int, float, float, str, str, int)
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (int, float, float, str, str, int): 
    Emitted when a node is dragged and released.
    
    Carries the Character ID, new X position, new Y position, Name, Color, and Shape ID.
    The Name, Color, and Shape ID are included to allow the editor to persist 
    node attributes along with position.
    """

class CharacterNode(QGraphicsEllipseItem):
    """
    A draggable and interactive representation of a Character on the 
    relationship graph canvas.
    """

    def __init__(self, char_id: int, name: str, x: float, y: float, color: str, shape: str, parent=None) -> None:
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
        :type parent: :py:class:`~PyQt6.QtWidgets.QGraphicsItem` or None

        :rtype: None
        """
        self.NODE_RADIUS = 30
        rect = QRectF(-self.NODE_RADIUS, -self.NODE_RADIUS, 2 * self.NODE_RADIUS, 2 * self.NODE_RADIUS)
        super().__init__(rect, parent)

        self.char_id = char_id
        self.name = name
        self.node_color = color
        self.node_shape = shape
        self.is_hidden = 0

        self.signals = CharacterNodeSignals()

        self.setPos(x, y)
        self._update_appearance()

        # set up dragging
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

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

    def itemChange(self, change: QGraphicsEllipseItem.GraphicsItemChange, value: Any) -> Any:
        """
        Handles changes to the item's state, specifically for movement.
        
        Ensures the node position is correctly snapped to the grid (if any) 
        and updates connected edges.

        :param change: The type of state change.
        :type change: :py:class:`~PyQt6.QtWidgets.QGraphicsItem.GraphicsItemChange`
        :param value: The new value for the state change.
        :type value: Any
        
        :returns: The potentially modified new value.
        :rtype: :py:obj:`Any`
        """
        """Called when item changes (likes position)"""
        if change == self.GraphicsItemChange.ItemPositionChange and self.scene():
            # Access the canvas settings through the scene's view
            view = self.scene().views()[0]
            if isinstance(view, RelationshipCanvas) and view.snap_to_grid:
                grid = view.grid_size
                new_pos = value.toPoint()
                x = round(new_pos.x() / grid) * grid
                y = round(new_pos.y() / grid) * grid
                return QPointF(x, y)
        

        if change == self.GraphicsItemChange.ItemPositionHasChanged:
            if self.scene():
                for item in self.scene().items():
                    if isinstance(item, RelationshipEdge):
                        item.update_position()
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event) -> None:
        """
        Handles the mouse release event. Emits the :py:attr:`.node_moved` 
        signal if the node has been dragged from its original position.
        
        :param event: The mouse event.
        :type event: :py:class:`~PyQt6.QtGui.QGraphicsSceneMouseEvent`

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
            self.is_hidden
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
        :type event: :py:class:`~PyQt6.QtGui.QGraphicsSceneMouseEvent`

        :rtype: None
        """
        
        # If left click, proceed with standard dragging/moving
        if event.button() == Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
        
        # If right click, signal to the editor that this node was right-clicked
        elif event.button() == Qt.MouseButton.RightButton:
            # We don't call super() here because we want the editor to handle the context menu/selection logic
            editor = self.scene().views()[0].parent()
            if isinstance(editor, RelationshipEditor):
                editor.handle_node_right_click(self)


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
        :type parent: :py:class:`~PyQt6.QtWidgets.QGraphicsItem` or None

        :rtype: None
        """
        super().__init__(parent)
        self.edge_data = edge_data
        self.source_node = nodes[edge_data['source']]
        self.target_node = nodes[edge_data['target']]

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
        color = QColor(self.edge_data['color'])
        thickness = max(1, self.edge_data['intensity']) # Value between 1-10
        thickness = 0.25 * thickness # Multiple by Scaling Factor
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

    def paint(self, painter, option, widget) -> None:
        """
        Docstring for paint
        
        :param self: Description
        :param painter: Description
        :param option: Description
        :param widget: Description
        """
        self.update_position()
        super().paint(painter, option, widget)

    def _calculate_angle(self, p1: QPointF, p2: QPointF) -> float:
        """
        Calculates the angle of the line for rotating the label. Flips the
        angle by 180 degrees if the text would otherwise be upside down.
        
        :param p1: The first point (:py:class:`~PyQt6.QtCore.QPointF`).
        :type p1: :py:class:`~PyQt6.QtCore.QPointF`
        :param p2: The second point (:py:class:`~PyQt6.QtCore.QPointF`).
        :type p2: :py:class:`~PyQt6.QtCore.QPointF`

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
    
class RelationshipCreationDialog(QDialog):
    """
    A Dialog to gather details for a new relationship.
    
    Presents fields for Relationship Type, Description, and Intensity.
    """
    def __init__(self, relationship_types: list[dict], char_a_name: str, char_b_name: str, parent=None) -> None:
        """
        Initializes :py:class:`.RelationshipCreationDialog`.
        
        :param relationship_types: A list of all the existing Relationship Types (dicts containing 'ID' and 'Type_Name').
        :type relationship_types: list[dict]
        :param char_a_name: The name of the first Character.
        :type char_a_name: str
        :param char_b_name: The name of the second Charcter.
        :type char_b_name: str
        :param parent: The parent object.
        :type parent: :py:class:`~PyQt6.QtWidgets.QWidget`

        :rtype: None
        """
        super().__init__(parent)
        self.setWindowTitle(f"Create Relationship: {char_a_name} ↔ {char_b_name}")
        
        self.type_data = {t['ID']: t['Type_Name'] for t in relationship_types}
        
        layout = QFormLayout(self)
        
        # Display the characters being connected
        layout.addRow(QLabel(f"Connecting: **{char_a_name}** to **{char_b_name}**"))
        
        # Relationship Type selection
        self.type_combo = QComboBox()
        for type_id, type_name in self.type_data.items():
            # Store ID as UserRole data
            self.type_combo.addItem(type_name, type_id) 
        layout.addRow("Type:", self.type_combo)
        
        # Description
        self.description_input = QLineEdit()
        layout.addRow("Description:", self.description_input)
        
        # Intensity (e.g., a simple 1-10 scale)
        self.intensity_input = QSpinBox()
        self.intensity_input.setRange(1, 10) # Intensity is on Simple 1-10 Scale but multipled by scalar later
        self.intensity_input.setValue(5)
        layout.addRow("Intensity (0-10):", self.intensity_input)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def get_relationship_data(self) -> tuple[int, str, int]:
        """
        Retrieves the data entered by the user in the dialog controls.
        
        :returns: A tuple containing the selected Relationship Type ID, Description, and Intensity.
        :rtype: tuple[int, str, int]
        """
        # Retrieve the type ID from the stored UserRole data
        type_id = self.type_combo.currentData(Qt.ItemDataRole.UserRole) 
        description = self.description_input.text()
        intensity = self.intensity_input.value()
        return type_id, description, intensity
    
class RelationshipEditor(QWidget):
    """
    A composite :py:class:`~PyQt6.QtWidgets.QWidget` that provides a visual,
    graph-based editor for managing character relationships.

    It utilizes a :py:class:`~PyQt6.QtWidgets.QGraphicsScene` and
    :py:class:`~PyQt6.QtWidgets.QGraphicsView` to display :py:class:`.CharacterNode`
    and :py:class:`.RelationshipEdge` objects. This component is primarily responsible
    for the visual arrangement and editing of relationship properties, with the
    persistence managed by an external controller (:py:class:`~app.services.app_coordinator.AppCoordinator`).
    """

    request_load_data = pyqtSignal()
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal`: Emitted to request all graph data from the coordinator.
    """

    save_node_attributes = pyqtSignal(int, float, float, str, str, int)
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (int, float, float, str, str, int): 
    Emitted to save a character node's position and attributes.
    """

    relationship_created = pyqtSignal(int, int, int, str, int)
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (int, int, int, str, int): 
    Emitted when a new relationship is created, carrying 
    (Source ID, Target ID, Type ID, Description, Intensity).
    """

    request_load_rel_types = pyqtSignal()
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal`: Emitted to request the list of available relationship types.
    """

    def __init__(self, coordinator: AppCoordinator, parent=None) -> None:
        """
        Initializes the :py:class:`.RelationshipEditor`.

        :param coordinator: The application coordinator for data persistence and signals.
        :type coordinator: :py:class:`~app.services.app_coordinator.AppCoordinator`
        :param parent: The parent Qt widget.
        :type parent: :py:class:`~PyQt6.QtWidgets.QWidget` or None
        
        :rtype: None
        """
        super().__init__(parent)

        self.coordinator = coordinator

        self.scene = QGraphicsScene(self)
        self.view = RelationshipCanvas(self.scene, self)
        self.view.setFrameShape(QFrame.Shape.NoFrame)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        self.toolbar = QToolBar()
        self.grid_action = QAction("Show Grid", self)
        self.grid_action.setCheckable(True)
        self.grid_action.setChecked(True)
        self.grid_action.triggered.connect(self.view.toggle_grid)
        
        self.snap_action = QAction("Snap to Grid", self)
        self.snap_action.setCheckable(True)
        self.snap_action.setChecked(True)
        self.snap_action.triggered.connect(self.view.toggle_snap)
        
        self.toolbar.addAction(self.grid_action)
        self.toolbar.addAction(self.snap_action)

        # Large window for free screen movement
        self.scene.setSceneRect(-2000, -2000, 4000, 4000)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.addWidget(self.toolbar)
        main_layout.addWidget(self.view)

        # Storage for current graph items
        self.nodes: dict[int, CharacterNode] = {}
        self.edges: list[RelationshipEdge] = []

        self.available_rel_types: list[dict] = []
        self.selected_node_a: CharacterNode | None = None
        self.selected_node_b: CharacterNode | None = None

        # Connect the coordinator signal to receive relationship types
        self.coordinator.relationship_types_available.connect(self.set_available_relationship_types)
        
        # Request the relationship types on startup
        self.coordinator.load_relationship_types_for_editor()

        # Connect node movement signal to the coordinator to save positions
        for node in self.nodes.values():
            node.signals.node_moved.connect(self.coordinator.save_node_position)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def set_available_relationship_types(self, rel_types: list[dict]) -> None:
        """
        Receives and stores the list of relationship types from the coordinator.
        
        :param rel_types: The list of relationship type dictionaries.
        :type rel_types: list[dict]
        
        :rtype: None
        """
        self.available_rel_types = rel_types

    def set_coordinator_signals(self, coordinator: AppCoordinator) -> None:
        """
        Connects editor-specific signals to the :py:class:`~app.services.app_coordinator.AppCoordinator`.
        
        This method is called to establish the communication links required for 
        loading and saving graph data and relationship types.
        
        :param coordinator: The application coordinator instance.
        :type coordinator: :py:class:`~app.services.app_coordinator.AppCoordinator`
        
        :rtype: None
        """
        self.request_load_data.connect(coordinator.load_relationship_graph_data)
        self.save_node_attributes.connect(coordinator.save_node_position)

        self.request_load_rel_types.connect(coordinator.load_relationship_types_for_editor)
        coordinator.relationship_types_available.connect(self.set_available_relationship_types)
        
        # Request the relationship types on editor start
        self.request_load_rel_types.emit()
        
    def clear_selection(self) -> None:
        """
        Clears the current node selection (both A and B) and removes the visual highlight.
        
        :rtype: None
        """
        # Reset the cursor to the default arrow
        self.view.unsetCursor()
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        if hasattr(self, 'temp_line') and self.temp_line:
            self.scene.removeItem(self.temp_line)
            self.temp_line = None
            self.view.setMouseTracking(False)

        if self.selected_node_a:
            self.selected_node_a.set_selection_highlight(False)
            self.selected_node_a = None
        if self.selected_node_b:
            self.selected_node_b.set_selection_highlight(False)
            self.selected_node_b = None
            
    def handle_node_right_click(self, node: CharacterNode) -> None:
        """
        Manages the two-click process for relationship creation.
        
        1. First right-click sets :py:attr:`.selected_node_a` and highlights it.
        2. Second right-click on a *different* node sets :py:attr:`.selected_node_b`, 
           opens the creation dialog, and then clears both selections.
        3. Second right-click on the *same* node clears the selection.
        
        :param node: The :py:class:`.CharacterNode` that was right-clicked.
        :type node: :py:class:`.CharacterNode`
        
        :rtype: None
        """
        if self.selected_node_a is None:
            # First selection
            self.clear_selection()
            self.selected_node_a = node
            self.selected_node_a.set_selection_highlight(True)

            # Can't drag characters when trying to make a connection
            self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.view.setCursor(Qt.CursorShape.CrossCursor)

            # Create a temporary line that follows the mouse
            start_pos = node.scenePos()
            self.temp_line = QGraphicsLineItem(QLineF(start_pos, start_pos))
            self.temp_line.setPen(QPen(Qt.GlobalColor.gray, 1, Qt.PenStyle.DashLine))
            self.scene.addItem(self.temp_line)
            self.view.setMouseTracking(True)

            self.view.setToolTip(f"Connecting {node.name}... Right-click another node to finish.")
            
        elif self.selected_node_a is node:
            # Clicking the same node clears the selection
            self.clear_selection()
            self.view.setToolTip("")
            
        else:
            # Second selection - ready to connect
            self.selected_node_b = node
            
            # --- CONNECTION LOGIC ---
            self.create_relationship_dialog(self.selected_node_a, self.selected_node_b)
            self.clear_selection() # Clear selection regardless of dialog result
            self.view.setToolTip("")

    def create_relationship_dialog(self, node_a: CharacterNode, node_b: CharacterNode) -> None:
        """
        Opens a dialog to get relationship details and emits the save signal.
        
        This method is the core logic for initiating a new relationship.
        
        :param node_a: The first selected :py:class:`.CharacterNode`.
        :type node_a: :py:class:`.CharacterNode`
        :param node_b: The second selected :py:class:`.CharacterNode`.
        :type node_b: :py:class:`.CharacterNode`
        
        :rtype: None
        """
        
        if node_a.char_id == node_b.char_id:
            QMessageBox.warning(self, "Warning", "Cannot create a relationship to the same character.")
            return
        
        if not self.available_rel_types:
            QMessageBox.critical(self, "Error", "No relationship types defined. Please define types in the Outline Manager first.")
            return
            
        # 1. Open dialog for user input
        dialog = RelationshipCreationDialog(
            relationship_types=self.available_rel_types, 
            char_a_name=node_a.name, 
            char_b_name=node_b.name, 
            parent=self
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 2. Get user data
            type_id, description, intensity = dialog.get_relationship_data()
            
            # 3. Emit signal to coordinator to save the new relationship
            # Order A->B is kept consistent for storage.
            self.relationship_created.emit(
                node_a.char_id, 
                node_b.char_id, 
                type_id, 
                description, 
                intensity
            )
            QMessageBox.information(self, "Success", f"Relationship creation request sent for {node_a.name} and {node_b.name}.")

    def connect_selected_characters(self, node_a: 'CharacterNode', node_b: 'CharacterNode') -> None:
        """
        Opens a dialog to create a relationship between two nodes.
        
        This method is an alternative entry point for relationship creation, 
        often used by menu actions or external triggers.
        
        :param node_a: The first selected :py:class:`.CharacterNode`.
        :type node_a: :py:class:`.CharacterNode`
        :param node_b: The second selected :py:class:`.CharacterNode`.
        :type node_b: :py:class:`.CharacterNode`
        
        :rtype: None
        """
        
        # Prevent connecting a node to itself
        if node_a.char_id == node_b.char_id:
            QMessageBox.warning(self, "Warning", "Cannot create a relationship to the same character.")
            return

        if not self.available_rel_types:
            QMessageBox.critical(self, "Error", "No relationship types defined. Please define types in the Outline Manager first.")
            return
        
        # 1. Open dialog for user input
        dialog = RelationshipCreationDialog(self.available_rel_types, parent=self)
        
        # Pre-fill names in the dialog for clarity (optional, but good UX)
        dialog.setWindowTitle(f"Create Relationship: {node_a.name} ↔ {node_b.name}")
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 2. Get user data
            type_id, description, intensity = dialog.get_relationship_data()
            
            # 3. Emit signal to coordinator to save the new relationship
            # Note: We enforce a consistent order A->B for storage. The graph handles visual direction.
            self.relationship_created.emit(
                node_a.char_id, 
                node_b.char_id, 
                type_id, 
                description, 
                intensity
            )
            QMessageBox.information(self, "Success", f"Relationship creation request sent for {node_a.name} and {node_b.name}.")

    def update_types_available(self, types: list[dict]) -> None:
        """
        Updates the internal cache of available relationship types.
        
        :param types: List of types to update.
        :type types: list[dict]

        :rtype: None
        """
        self.available_rel_types = types

    def load_graph(self, graph_data: dict[str, list[dict[str, Any]]]) -> None:
        """
        Recieves graph data from :py:class:`~app.services.app_coordinator.AppCoordinator` 
        and populates the :py:class:`~PyQt6.QtWidgets.QGraphicsScene`.
        
        This clears the existing graph and draws all new nodes and edges based on the data.
        
        :param graph_data: A dictionary containing 'nodes' (list of character data) and 'edges' (list of relationship data).
        :type graph_data: dict[str, list[dict[str, Any]]]
        
        :rtype: None
        """
        try:
            self.clear_selection()

            # Clear existing scene
            self.scene.clear()
            self.nodes = {}
            self.edges = []

            # Create and place Nodes (Characters)
            for node_data in graph_data.get('nodes', []):
                char_id = node_data['id']

                # Create Node Item
                node = CharacterNode (
                    char_id=char_id,
                    name=node_data['name'],
                    x=node_data['x'],
                    y=node_data['y'],
                    color=node_data.get('color', '#60A5FA'),
                    shape=node_data.get('shape', 'Circle'),
                )

                # Connect node's movement signal to the editor's save signal so every node movement is tracked and persisted
                node.signals.node_moved.connect(self.save_node_attributes)

                self.scene.addItem(node)
                self.nodes[char_id] = node

            # Create Edges (Relationships)
            for edge_data in graph_data.get('edges', []):
                source_id = edge_data['source']
                target_id = edge_data['target']
                
                # Only draw edges between loaded nodes
                if source_id in self.nodes and target_id in self.nodes:
                    edge = RelationshipEdge(edge_data, self.nodes)
                    self.scene.addItem(edge)
                    self.edges.append(edge)

            # Fit the view to the new content (or center on (0,0) if empty)
            if self.nodes:
                # Calculate the bounding box for all nodes
                all_items_rect = self.scene.itemsBoundingRect()
                # Add padding to the fit
                padded_rect = all_items_rect.adjusted(-100, -100, 100, 100)
                # Fit the padded area into the view
                self.view.fitInView(padded_rect, Qt.AspectRatioMode.KeepAspectRatio)

            else:
                self.view.centerOn(0, 0)

        except Exception as e:
            QMessageBox.critical(self, "Graph Load Error", f"An error occurred while loading graph data: {e}")
            self.scene.clear()

    def set_enabled(self, enabled: bool) -> None:
        """
        Enables/disables the editor panel's interaction.
        
        :param enabled: True to enable interaction, False to disable.
        :type enabled: bool
        
        :rtype: None
        """
        self.view.setEnabled(enabled)

    def is_dirty(self) -> bool:
        """
        Indicates if the editor has unsaved changes.
        
        Positions are saved immediately upon release, so the editor is never 
        considered dirty by its own state.
        
        :returns: Always False.
        :rtype: bool
        """
        return False
    
    def mark_saved(self) -> None:
        """
        Placeholder method to conform to standard editor interface.
        
        Since node positions are saved immediately, there is no state to mark as saved.
        
        :rtype: None
        """
        pass