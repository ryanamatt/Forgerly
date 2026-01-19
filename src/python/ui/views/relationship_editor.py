# src\python\ui\views\relationship_editor.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsLineItem, QMessageBox, 
    QFrame, QDialog, QToolBar
)
from PySide6.QtCore import Qt, QLineF, QPointF
from PySide6.QtGui import QPen, QAction, QIcon
from typing import Any
import math

from ...resources_rc import *
from ..widgets.graph_items import CharacterNode, RelationshipEdge
from ..widgets.relationship_canvas import RelationshipCanvas
from ..dialogs.relationship_dialog import RelationshipCreationDialog
from ...utils.graph_layout import GraphLayoutEngineWrapper
from ...utils.constants import EntityType
from ...utils.events import Events
from ...utils.event_bus import bus, receiver
    
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

    def __init__(self, parent=None) -> None:
        """
        Initializes the :py:class:`.RelationshipEditor`.

        :param parent: The parent Qt widget.
        :type parent: :py:class:`~PySide6.QtWidgets.QWidget` or None
        
        :rtype: None
        """
        super().__init__(parent)

        bus.register_instance(self)

        self._setup_ui()

        # Storage for current graph items
        self.nodes: dict[int, CharacterNode] = {}
        self.edges: list[RelationshipEdge] = []

        self.available_rel_types: list[dict] = []
        self.selected_node_a: CharacterNode | None = None
        self.selected_node_b: CharacterNode | None = None

        self.bulk_is_locked: bool = False
        self.is_label_visible: bool = True

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def _setup_ui(self) -> None:
        """
        Sets up the UI for the RelationshipEditor.
        
        :rtype: None
        """
        self.scene = QGraphicsScene(self)
        self.view = RelationshipCanvas(self.scene, self)
        self.view.setFrameShape(QFrame.Shape.NoFrame)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        # Large window for free screen movement
        self.scene.setSceneRect(-2000, -2000, 4000, 4000)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self._setup_toolbar()

        main_layout.addWidget(self.toolbar)
        main_layout.addWidget(self.view)

    def _setup_toolbar(self) -> None:
        """
        Setups the top toolbar for RelationshipEditor.
        
        :rtype: None
        """
        self.toolbar = QToolBar()

        def add_btn(text: str, icon: str, slot: callable, checkable: bool = False) -> QAction:
            action = QAction(text, self)
            action.setIcon(QIcon(f":icons/{icon}"))
            if checkable:
                action.setCheckable(checkable)
                action.setChecked(checkable)
            action.triggered.connect(slot)
            self.toolbar.addAction(action)
            return action


        self.grid_action = add_btn("Show Grid", "grid.svg", self.view.toggle_grid, True)
        self.snap_action = add_btn("Snap to Grid", "snap-grid.svg", self.view.toggle_snap, True)
        self.layout_action = add_btn("Auto Layout", "auto-layout.svg", self.apply_auto_layout)
        self.lock_all_action = add_btn("Lock/Unlock All Characters", "lock.svg", self.toggle_lock_nodes, True)

        self.toolbar.addSeparator()

        self.reset_zoom_action = add_btn("Reset Zoom", "zoom-reset.svg", self.reset_view_zoom)
        self.toggle_labels_action = add_btn("Toggle Label Visbility", "visible-on", self.toggle_labels, True)

    @receiver(Events.REL_TYPES_RECEIVED)
    def set_available_relationship_types(self, data: dict) -> None:
        """
        Receives and stores the list of relationship types from the coordinator.
        
        :param rel_types: The data containing {relationship_types: list[str]}
        :type rel_types: list[dict]
        
        :rtype: None
        """
        rel_types = data.get('relationship_types')
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
            QMessageBox.critical(self, "Error", "No relationship types defined. Please define types"
            " in the Outline Manager first.")
            return
            
        # Open dialog for user input
        dialog = RelationshipCreationDialog(
            relationship_types=self.available_rel_types, 
            char_a_name=node_a.name, 
            char_b_name=node_b.name, 
            parent=self
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get user data
            type_id, description, intensity = dialog.get_relationship_data()
            
            # Emit signal to coordinator to save the new relationship
            bus.publish(Events.REL_CREATE_REQUESTED, data={
                'char_a_id': node_a.char_id, 'char_b_id': node_b.char_id,
                'type_id': type_id, 'description': description, 'intensity': intensity
            })

    @receiver(Events.REL_DETAILS_RETURN)
    def edit_relationship(self, data: dict) -> None:
        """
        Opens the dialog with existing data to update the relationship.
        
        :param edge: The RelationshipEdge to edit.
        :type edge: RelationshipEdge

        :type: None
        """
        node_a = data.get('source')
        node_b = data.get('target')
        
        dialog = RelationshipCreationDialog(
            relationship_types=self.available_rel_types,
            char_a_name=node_a.name,
            char_b_name=node_b.name,
            description=data.get('Description', ''),
            intensity=data.get('Intensity', '5'),
            parent=self
        )
                
        if dialog.exec() == QDialog.DialogCode.Accepted:
            type_id, description, intensity = dialog.get_relationship_data()
            bus.publish(Events.REL_UPDATE_REQUESTED, data={
                'relationship_id': data.get('ID'), 'type_id': type_id, 
                'description': description, 'intensity': intensity,
            })

    @receiver(Events.GRAPH_DATA_LOADED)
    def load_graph(self, graph_data: dict[str, list[dict[str, Any]]]) -> None:
        """
        Recieves graph data from :py:class:`~app.services.app_coordinator.AppCoordinator` 
        and populates the :py:class:`~PySide6.QtWidgets.QGraphicsScene`.
        
        This clears the existing graph and draws all new nodes and edges based on the data.
        
        :param graph_data: A dictionary containing 'nodes' (list of character data) and 'edges' 
            (list of relationship data).
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
                is_hidden = bool(node_data.get('is_hidden', 0))
                is_locked = bool(node_data.get('is_locked', 0))

                # Get initial coordinates
                nx = node_data.get('x', 0)
                ny = node_data.get('y', 0)

                # If the node is at the default origin, find a better spot
                if nx == 0 and ny == 0:
                    nx, ny = self._find_empty_space(nx, ny)

                # Create Node Item
                node = CharacterNode (
                    char_id=char_id,
                    name=node_data['name'],
                    x=nx,
                    y=ny,
                    color=node_data.get('color', '#60A5FA'),
                    shape=node_data.get('shape', 'Circle'),
                )

                node.setVisible(not is_hidden)
                node.is_hidden = is_hidden
                node.is_locked = is_locked

                # Connect node's movement signal to the editor's save signal so every node movement 
                # is tracked and persisted
                node.signals.node_moved.connect(self._save_node_positions)

                self.scene.addItem(node)
                self.nodes[char_id] = node

            if self.nodes:
                all_locked = all(node.is_locked for node in self.nodes.values())
                self.bulk_is_locked = all_locked
                self.lock_all_action.setChecked(self.bulk_is_locked)

                icon_name = "unlock.svg" if self.bulk_is_locked else "lock.svg"
                self.lock_all_action.setIcon(QIcon(f":icons/{icon_name}"))
            else:
                self.bulk_is_locked = False
                self.lock_all_action.setChecked(False)

            # Create Edges (Relationships)
            for edge_data in graph_data.get('edges', []):
                source_id = edge_data['source']
                target_id = edge_data['target']
                
                # Only draw edges between loaded nodes
                if source_id in self.nodes and target_id in self.nodes:
                    edge = RelationshipEdge(edge_data, self.nodes)

                    # Hide edge if either the source or target node is hidden
                    source_hidden = self.nodes[source_id].is_hidden
                    target_hidden = self.nodes[target_id].is_hidden

                    if source_hidden or target_hidden:
                        edge.setVisible(False)
                        edge.label_item.setVisible(False)

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

    def _find_empty_space(self, start_x: float, start_y: float) -> tuple[float, float]:
        """
        Finds the nearest available grid spot that doesn't collide with existing nodes.
        
        :param start_x: The starting value of X.
        :type start_x: float
        :param start_y: The starting value of Y.
        :type start_y: float
        :returns: The New X and Y Postion.
        :rtype: tuple[float, float]
        """
        grid_spacing = 80  # Slightly more than 2 * NODE_RADIUS
        attempts = 0
        max_attempts = 100 
        
        curr_x, curr_y = start_x, start_y
        
        # Simple spiral search or linear offset
        while attempts < max_attempts:
            collision = False
            potential_pos = QPointF(curr_x, curr_y)
            
            for existing_node in self.nodes.values():
                # Calculate distance between centers
                dx = potential_pos.x() - existing_node.scenePos().x()
                dy = potential_pos.y() - existing_node.scenePos().y()
                if math.sqrt(dx*dx + dy*dy) < (grid_spacing):
                    collision = True
                    break
            
            if not collision:
                return curr_x, curr_y
            
            # Move to next slot (Simple row/column logic)
            attempts += 1
            curr_x += grid_spacing
            if attempts % 5 == 0: # Move to next row every 5 nodes
                curr_x = start_x
                curr_y += grid_spacing
                
        return curr_x, curr_y
        
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
                    node.node_color, node.node_shape, node.is_hidden, node.is_locked
                )

    def _save_node_positions(self, char_id: int, x_pos: int, y_pos: int, node_color: str, node_shape: str, 
                             is_hidden: int, is_locked: int) -> None:
        """
        Calls the Event to Save the Node Positions.
        
        :param char_id: The ID of the node.
        :type char_id: int
        :param x_pos: The X position of the node.
        :type x_pos: int
        :param y_pos: The Y_Position of the node.
        :type y_pos: int
        :param node_color: The color of the node.
        :type node_color: str
        :param node_shape: The shape of the node
        :type node_shape: str
        :param is_hidden: Whether the node is hidden.
        :type is_hidden: int
        :param is_locked: Whether the node is locked.
        :type is_locked: int

        :rtype: None
        """
        bus.publish(Events.NODE_SAVE_REQUESTED, data={
                'character_id': char_id, 'x_pos': x_pos, 'y_pos': y_pos, 'node_color': node_color, 
                'node_shape': node_shape, 'is_hidden': is_hidden, 'is_locked': is_locked
            })

    @receiver(Events.GRAPH_EDGE_VISIBILITY_CHANGED)
    def handle_type_visibility(self, data: dict) -> None:
        """
        Shows or hides all edges of a specific relationship type.
        
        :param data: Dictionary containing {'type_id': int, 'visible': bool}
        :type data: dict

        :rtype: None
        """
        target_type_id = data.get('type_id')
        is_visible = data.get('visible')

        if target_type_id is None or is_visible is None:
            return
        
        for edge in self.edges:
            if edge.edge_data.get('type_id') == target_type_id:
                edge.setVisible(is_visible)
                edge.label_item.setVisible(is_visible)

    @receiver(Events.GRAPH_NODE_VISIBILTY_CHANGED)
    def handle_node_visibility(self, data: dict) -> None:
        """
        Shows or hides a character node.
        
        :param data: Dictionary containing {'ID': int, 'is_hidden': bool}
        :type data: dict

        :rtype: None
        """
        node_id = data.get('ID')
        is_hidden = data.get('is_hidden')

        if node_id in self.nodes:
            is_visible = not is_hidden
            node_item = self.nodes[node_id]
            node_item.setVisible(is_visible)
            
            # Make Connected Edges Invisible
            for edge in self.edges:
                if edge.source_node == node_item or edge.target_node == node_item:
                    edge.setVisible(is_visible)

    # --- Toolbar Connection Functions ---

    def apply_auto_layout(self) -> None:
        """
        Extracts current graph state, computes Fruchterman-Reingold layout 
        via C++, and updates node positions.

        :rtype: None
        """
        if not self.nodes:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Auto Layout",
            "Auto Layout will rearrange all unlocked nodes. This cannot be undone.\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # Default to No for safety
        )

        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # 1. Prepare NodeInput data for C++
        nodes_input = []
        for node_id, node in self.nodes.items():
            nodes_input.append({
                'id': node_id,
                'x_pos': node.x(),
                'y_pos': node.y(),
                'is_fixed': node.is_locked 
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
            new_positions = engine.compute_layout(max_iterations=200, initial_temperature=init_temp)

            self._update_node_positions(new_positions)

        except Exception as e:
            QMessageBox.critical(self, "Layout Error", f"C++ Engine failed: {e}")

    def toggle_lock_nodes(self) -> None:
        """
        Toggles wether to lock/unlock all nodes.
        """
        self.bulk_is_locked = not self.bulk_is_locked

        icon_name = "unlock.svg" if self.bulk_is_locked else "lock.svg"
        self.lock_all_action.setIcon(QIcon(f":icons/{icon_name}"))

        node_ids = []
        for node_id, node in self.nodes.items():
            node.is_locked = self.bulk_is_locked
            node_ids.append(node_id)
        
        # Publish one event for the entire operation
        bus.publish(Events.GRAPH_NODE_LOCKED_BULK_CHANGED, data={
            'char_ids': node_ids, 
            'is_locked': self.bulk_is_locked
    })

    def reset_view_zoom(self) -> None:
        """
        Resets the canvas zoom to 100%.

        :rtype: None
        """
        self.view.reset_zoom()

        self.view.scale(0.75, 0.75)
        if self.nodes:
            center_point = self.scene.itemsBoundingRect().center()
            self.view.centerOn(center_point)
        else:
            self.view.centerOn(0, 0)

    def toggle_labels(self) -> None:
        """
        Toggles Whether or not the Short Labels are Visible on the Graph Edges.

        :rtype: None        
        """
        self.is_label_visible = not self.is_label_visible

        # for edge_id, edge in self.edges.items():
        #     print
        for edge in self.edges:
            edge.label_item.setVisible(self.is_label_visible)

        icon_name = "visible-on.svg" if self.is_label_visible else "visible-off.svg"
        self.toggle_labels_action.setIcon(QIcon(f":icons/{icon_name}"))

    # --- State Managers --- 

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
