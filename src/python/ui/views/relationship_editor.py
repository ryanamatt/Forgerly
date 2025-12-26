# src\python\ui\views\relationship_editor.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsLineItem, QMessageBox, 
    QFrame, QDialog, QToolBar
)
from PySide6.QtCore import Qt, Signal, QLineF
from PySide6.QtGui import QPen, QAction, QIcon
from typing import Any

from ...resources_rc import *
from ..widgets.graph_items import CharacterNode, RelationshipEdge
from ..widgets.relationship_canvas import RelationshipCanvas
from ..dialogs.relationship_dialog import RelationshipCreationDialog
from ...utils.nf_core_wrapper import GraphLayoutEngineWrapper
    
class RelationshipEditor(QWidget):
    """
    A composite :py:class:`~PySide6.QtWidgets.QWidget` that provides a visual,
    graph-based editor for managing character relationships.

    It utilizes a :py:class:`~PySide6.QtWidgets.QGraphicsScene` and
    :py:class:`~PySide6.QtWidgets.QGraphicsView` to display :py:class:`.CharacterNode`
    and :py:class:`.RelationshipEdge` objects. This component is primarily responsible
    for the visual arrangement and editing of relationship properties, with the
    persistence managed by an external controller (:py:class:`~app.services.app_coordinator.AppCoordinator`).
    """

    request_load_data = Signal()
    """
    :py:class:`~PySide6.QtCore.Signal`: Emitted to request all graph data from the coordinator.
    """

    save_node_attributes = Signal(int, float, float, str, str, int)
    """
    :py:class:`~PySide6.QtCore.Signal` (int, float, float, str, str, int): 
    Emitted to save a character node's position and attributes.

    Carries the (Character ID, new X position, new Y position, Name, Color, 
    Shape ID, Name, Color, and Shape ID)
    """

    relationship_created = Signal(int, int, int, str, int)
    """
    :py:class:`~PySide6.QtCore.Signal` (int, int, int, str, int): 
    Emitted when a new relationship is created, carrying 
    (Source ID, Target ID, Type ID, Description, Intensity).
    """

    relationship_deleted = Signal(int)
    """:py:class:`~PySide6.QtCore.Signal` (int):
    Emitted when a relationshipo is deleted, carrying
    (Relationship_ID)
    """

    request_load_rel_types = Signal()
    """
    :py:class:`~PySide6.QtCore.Signal`: Emitted to request the list of available relationship types.
    """

    def __init__(self, parent=None) -> None:
        """
        Initializes the :py:class:`.RelationshipEditor`.

        :param parent: The parent Qt widget.
        :type parent: :py:class:`~PySide6.QtWidgets.QWidget` or None
        
        :rtype: None
        """
        super().__init__(parent)

        self.scene = QGraphicsScene(self)
        self.view = RelationshipCanvas(self.scene, self)
        self.view.setFrameShape(QFrame.Shape.NoFrame)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        self.toolbar = QToolBar()
        self.grid_action = QAction("Show Grid", self)
        self.grid_action.setIcon(QIcon(":icons/grid.svg"))
        self.grid_action.setCheckable(True)
        self.grid_action.setChecked(True)
        self.grid_action.triggered.connect(self.view.toggle_grid)
        
        self.snap_action = QAction("Snap to Grid", self)
        self.snap_action.setIcon(QIcon(":icons/snap-grid.svg"))
        self.snap_action.setCheckable(True)
        self.snap_action.setChecked(True)
        self.snap_action.triggered.connect(self.view.toggle_snap)

        self.layout_action = QAction("Auto Layout", self)
        self.layout_action.setIcon(QIcon(":icons/auto-layout.svg"))
        self.layout_action.triggered.connect(self.apply_auto_layout)
        
        self.toolbar.addAction(self.grid_action)
        self.toolbar.addAction(self.snap_action)
        self.toolbar.addAction(self.layout_action)

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

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def set_available_relationship_types(self, rel_types: list[dict]) -> None:
        """
        Receives and stores the list of relationship types from the coordinator.
        
        :param rel_types: The list of relationship type dictionaries.
        :type rel_types: list[dict]
        
        :rtype: None
        """
        self.available_rel_types = rel_types
        
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

    def edit_relationship(self, edge: RelationshipEdge) -> None:
        """
        Opens the dialog with existing data to update the relationship.
        
        :param edge: The RelationshipEdge to edit.
        :type edge: RelationshipEdge

        :type: None
        """
        # Extract existing data from the edge object
        node_a = edge.source_node
        node_b = edge.target_node
        
        dialog = RelationshipCreationDialog(
            relationship_types=self.available_rel_types,
            char_a_name=node_a.name,
            char_b_name=node_b.name,
            parent=self
        )
        
        # Pre-fill logic would go here depending on RelationshipCreationDialog implementation
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            type_id, description, intensity = dialog.get_relationship_data()
            # Emit the same signal; your backend should handle 'UPSERT' 
            # (update if exists) based on the Unique constraint.
            self.relationship_created.emit(
                node_a.char_id,
                node_b.char_id,
                type_id,
                description,
                intensity
            )

    def delete_relationship(self, edge: RelationshipEdge) -> None:
        """
        Prompts for confirmation and requests deletion via the coordinator.
        
        :param edge: The relationship edge to delete.
        :type edge: RelationshipEdge

        :rtype: Noe
        """
        msg = f"Are you sure you want to delete the relationship between {edge.source_node.name} and {edge.target_node.name}?"
        res = QMessageBox.question(self, "Delete Relationship", msg, 
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if res == QMessageBox.StandardButton.Yes:
            self.relationship_deleted.emit(edge.edge_data['id'])

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
        and populates the :py:class:`~PySide6.QtWidgets.QGraphicsScene`.
        
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

    def apply_auto_layout(self) -> None:
        """
        Extracts current graph state, computes Fruchterman-Reingold layout 
        via C++, and updates node positions.

        :rtype: None
        """
        if not self.nodes:
            return
        
        # 1. Prepare NodeInput data for C++
        # Note: 'is_fixed' could be linked to a 'pinned' attribute if you add one
        nodes_input = []
        for node_id, node in self.nodes.items():
            nodes_input.append({
                'id': node_id,
                'x_pos': node.x(),
                'y_pos': node.y(),
                'is_fixed': False 
            })

        # 2. Prepare EdgeInput data for C++
        edges_input = []
        for edge in self.edges:
            edges_input.append({
                'node_a_id': edge.source_node.char_id,
                'node_b_id': edge.target_node.char_id,
                'intensity': edge.edge_data.get('intensity', 5.0)
            })

        # 3. Initialize and run the C++ Engine
        # We use the scene size or view size as the bounding box
        view_rect = self.view.viewport().rect()
        width = float(view_rect.width())
        height = float(view_rect.height())

        if width <= 0 or height <= 0:
            width, height = 400.0, 300.0

        init_temp = max(width, height) / 10.0

        try:
            # Initialize engine with the actual Scene dimensions
            engine = GraphLayoutEngineWrapper(nodes_input, edges_input, width, height)
            
            # Increase iterations for more stability if they are flying off-screen
            new_positions = engine.compute_layout(max_iterations=200, initial_temperature=init_temp)

            self._update_node_positions(new_positions)
            
            # Optional: Auto-zoom to fit the new layout
            self.view.fitInView(self.scene.itemsBoundingRect().adjusted(-50, -50, 50, 50), 
                                Qt.AspectRatioMode.KeepAspectRatio)
            
        except Exception as e:
            QMessageBox.critical(self, "Layout Error", f"C++ Engine failed: {e}")
        
    def _update_node_positions(self, new_positions: list[dict]) -> None:
        """
        Helper to move nodes to their calculated coordinates.
        
        :param new_positions: The new updated positions.
        :type new_positions: list[dict]

        :rtype: None
        """
        for pos_data in new_positions:
            node_id = pos_data['id']
            if node_id in self.nodes:
                node = self.nodes[node_id]
                # setPos triggers ItemPositionHasChanged in CharacterNode, 
                # which automatically updates attached edges.
                node.setPos(pos_data['x_pos'], pos_data['y_pos'])
                
                # Manually trigger the move signal to persist the auto-layout to DB
                node.signals.node_moved.emit(
                    node_id, pos_data['x_pos'], pos_data['y_pos'],
                    node.node_color, node.node_shape, node.is_hidden
                )

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
