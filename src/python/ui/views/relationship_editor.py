# src\python\ui\views\relationship_editor.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, 
    QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem, 
    QMessageBox, QFrame, QDialog, QFormLayout, QComboBox, QLineEdit,
    QSpinBox, QDialogButtonBox, QLabel
)
from PyQt6.QtCore import Qt, QPointF, pyqtSignal, QRectF, QObject, QLineF
from PyQt6.QtGui import QColor, QPen, QBrush, QFont
import math
from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from services.app_coordinator import AppCoordinator

class CharacterNodeSignals(QObject):
    """Signal Emitter for CharacterNode, which cannot inherit from QObject."""
    node_moved = pyqtSignal(int, float, float, str, str, int)

class CharacterNode(QGraphicsEllipseItem):
    """A draggable character node (an ellipse)"""

    def __init__(self, char_id: int, name: str, x: float, y: float, color: str, shape: str, parent=None) -> None:
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
        """Updates the brush/pen based on current attributes."""
        brush = QBrush(QColor(self.node_color))
        pen = QPen(QColor(Qt.GlobalColor.black), 2)
        
        self.setBrush(brush)
        self.setPen(pen)

    def _itemChange(self, change: QGraphicsEllipseItem.GraphicsItemChange, value: Any) -> Any:
        """Called when item changes (likes position)"""
        if change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionHasChanged:
            # When position changes, update connected edges
            if self.scene():
                for item in self.scene().items():
                    if isinstance(item, RelationshipEdge):
                        # Use a direct update call to refresh the line
                        item.update_position()

    def mouseReleaseEvent(self, event) -> None:
        """Emit signal to save position when dragging stops"""
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
        """Toggles the highlight for relationship selection."""
        if not self.scene():
            return

        self.is_selected_for_connect = highlight
        self._update_appearance()
        self.update() # Force redraw

    def mousePressEvent(self, event) -> None:
        """Handle mouse clicks for selection and dragging."""
        
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
    """A line representing a relationship between two CharacterNodes."""
    
    def __init__(self, edge_data: dict[str, Any], nodes: dict[int, CharacterNode], parent=None):
        super().__init__(parent)
        self.edge_data = edge_data
        self.source_node = nodes[edge_data['source']]
        self.target_node = nodes[edge_data['target']]

        # Add a label in the middle of the edge
        self.label_item = QGraphicsTextItem(edge_data['label'], self)

        self._update_pen()
        self.update_position()

    def _update_pen(self):
        """Sets the pen properties based on edge data"""
        color = QColor(self.edge_data['color'])
        thickness = max(10, min(100, 10 * self.edge_data['intensity']))
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

    def update_position(self) -> None:
        """Recalculates line start/end points based on node positions."""

        start_point = self.source_node.scenePos()
        end_point = self.target_node.scenePos()

        self.setLine(start_point.x(), start_point.y(), end_point.x(), end_point.y())

        mid_point = (start_point + end_point) / 2

        label_rect = self.label_item.boundingRect()
        self.label_item.setPos(mid_point.x() - label_rect.width() / 2, mid_point.y() - label_rect.height() / 2)
        self.label_item.setRotation(self._calculate_angle(start_point, end_point))

    def _calculate_angle(self, p1: QPointF, p2: QPointF) -> float:
        """Calculates the angle of the line for rotating the label."""
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        # Angle in radians so convert to degrees
        angle = math.atan2(-dy, dx)
        return math.degrees(angle)
    
class RelationshipCreationDialog(QDialog):
    """Dialog to gather details for a new relationship."""
    def __init__(self, relationship_types: list[dict], char_a_name: str, char_b_name: str, parent=None):
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
        
        # Intensity (e.g., a simple 0-10 scale)
        self.intensity_input = QSpinBox()
        self.intensity_input.setRange(0, 10)
        self.intensity_input.setValue(5)
        layout.addRow("Intensity (0-10):", self.intensity_input)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def get_relationship_data(self) -> tuple[int, str, int]:
        """Returns (Type ID, Description, Intensity)."""
        # Retrieve the type ID from the stored UserRole data
        type_id = self.type_combo.currentData(Qt.ItemDataRole.UserRole) 
        description = self.description_input.text()
        intensity = self.intensity_input.value()
        return type_id, description, intensity
    
class RelationshipEditor(QWidget):
    """
    Main Widget for visualizing and editing character relationships as a graph.
    Allows for node dragging and saving node positions.
    """
    # Signal to request data load from AppCoordinator
    request_load_data = pyqtSignal()
    # Signal to save a single node's attributes after being moved
    save_node_attributes = pyqtSignal(int, float, float, str, str, int)
    # Emitted when the user wants to save a new relationship
    relationship_created = pyqtSignal(int, int, int, str, int)
    # Signal to request relationship types when loaded
    request_load_rel_types = pyqtSignal()

    def __init__(self, coordinator: AppCoordinator, parent=None) -> None:
        super().__init__(parent)

        self.coordinator = coordinator

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setFrameShape(QFrame.Shape.NoFrame)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        # Large window for free screen movement
        self.scene.setSceneRect(-2000, -2000, 4000, 4000)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
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
        """Receives and stores the list of relationship types from the coordinator."""
        self.available_rel_types = rel_types

    def set_coordinator_signals(self, coordinator: AppCoordinator) -> None:
        """Connects signals to the AppCoordinator"""
        self.request_load_data.connect(coordinator.load_relationship_graph_data)
        self.save_node_attributes.connect(coordinator.save_node_position)

        self.request_load_rel_types.connect(coordinator.load_relationship_types_for_editor)
        coordinator.relationship_types_available.connect(self.set_available_relationship_types)
        
        # Request the relationship types on editor start
        self.request_load_rel_types.emit()

    def set_available_relationship_types(self, rel_types: list[dict]) -> None:
        """Receives and stores the list of relationship types from the coordinator."""
        self.available_rel_types = rel_types
        
    def clear_selection(self) -> None:
        """Clears the current node selection."""
        if self.selected_node_a:
            self.selected_node_a.set_selection_highlight(False)
            self.selected_node_a = None
        if self.selected_node_b:
            self.selected_node_b.set_selection_highlight(False)
            self.selected_node_b = None
            
    def handle_node_right_click(self, node: CharacterNode) -> None:
        """
        Manages the two-click process for relationship creation.
        1. First click sets A.
        2. Second click sets B and opens the dialog.
        """
        if self.selected_node_a is None:
            # First selection
            self.clear_selection()
            self.selected_node_a = node
            self.selected_node_a.set_selection_highlight(True)
            QMessageBox.information(self, "Select Start", f"**{node.name}** selected as Relationship Start. Click a second character to connect.")
            
        elif self.selected_node_a is node:
            # Clicking the same node clears the selection
            self.clear_selection()
            
        else:
            # Second selection - ready to connect
            self.selected_node_b = node
            
            # --- CONNECTION LOGIC ---
            self.create_relationship_dialog(self.selected_node_a, self.selected_node_b)
            self.clear_selection() # Clear selection regardless of dialog result

    def create_relationship_dialog(self, node_a: CharacterNode, node_b: CharacterNode) -> None:
        """Opens a dialog to get relationship details and emits the save signal."""
        
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
        """Opens a dialog to create a relationship between two nodes."""
        
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

    def load_graph(self, graph_data: dict[str, list[dict[str, Any]]]) -> None:
        """
        Recieves graph data from App Coordinator and populates the QGraphicsScene.
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
        """Enables/disables the editor panel"""
        self.view.setEnabled(enabled)

    def is_dirty(self) -> bool:
        """Positions are saved immediatrly so editor is never dirty"""
        return False
    
    def mark_saved(self) -> None:
        """No state to mark as saved"""
        pass