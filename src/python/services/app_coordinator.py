# src/python/services/app_coordinator.py

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox

from ..db_connector import DBConnector
from ..repository.chapter_repository import ChapterRepository
from ..repository.lore_repository import LoreRepository
from ..repository.tag_repository import TagRepository
from ..repository.character_repository import CharacterRepository
from ..repository.relationship_repository import RelationshipRepository

from ..utils.constants import ViewType

from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from ..ui.views.chapter_editor import ChapterEditor
    from ..ui.views.lore_editor import LoreEditor
    from ..ui.views.character_editor import CharacterEditor
    from ..ui.views.relationship_editor import RelationshipEditor

class AppCoordinator(QObject):
    """
    Coordinates data flow between the UI components (Outline/Editor) and the 
    database repositories. Centralizes save/load/dirty checking logic.
    """
    # --- Signals for Editor Panel Updates ---
    chapter_loaded = pyqtSignal(int, str, list)      # id, content_html, tags
    lore_loaded = pyqtSignal(int, str, str, str, list) # id, title, category, content_html, tags
    char_loaded = pyqtSignal(int, str, str, str)
    graph_data_loaded = pyqtSignal(dict)
    
    relationship_types_available = pyqtSignal(list) # list[dict]

    # --- Signals for Outline Manager Updates (UI IN) ---
    lore_title_updated_in_outline = pyqtSignal(int, str)
    char_name_updated_in_ouline = pyqtSignal(int, str)

    def __init__(self, db_connector: DBConnector) -> None:
        super().__init__()

        self.db = db_connector

        # Create Repositorys
        self.chapter_repo = ChapterRepository(self.db)
        self.lore_repo = LoreRepository(self.db)
        self.character_repo = CharacterRepository(self.db)
        self.tag_repo = TagRepository(self.db)
        self.relationship_repo = RelationshipRepository(self.db)

        # State Tracking
        self.current_item_id = 0
        self.current_view = ViewType.CHAPTER_EDITOR

        # References to the active Outline/Editor panels (set by MainWindow)
        self.editors = {}
        # Keep for signal
        self.lore_editor = None
        self.character_editor = None
        self.relationship_editor = None
        
    def connect_signals(self):
        """Connect signals. Called in MainWindow after set_editors"""
        self.relationship_editor.relationship_created.connect(self.save_new_relationship)

    # --- View Logic ---

    def set_editors(self, editor_map: dict[ViewType, Any]) -> None:
        """
        Sets all editor references using a dictionary map where keys are ViewType constants.
        Example: {ViewType.CHAPTER_EDITOR: chapter_editor, ViewType.LORE_EDITOR: lore_editor...}
        """
        self.editors = editor_map
        
        # Handle specific editor connections separately (like title change signals)
        if ViewType.LORE_EDITOR in self.editors:
            self.lore_editor: LoreEditor = self.editors[ViewType.LORE_EDITOR]
            # Connect the specific signal
            self.lore_editor.lore_title_changed.connect(self.lore_title_updated_in_outline)

        if ViewType.CHARACTER_EDITOR in self.editors:
            self.character_editor: CharacterEditor = self.editors[ViewType.CHARACTER_EDITOR]
            self.character_editor.char_name_changed.connect(self.char_name_updated_in_ouline)

        if ViewType.RELATIONSHIP_GRAPH in self.editors:
            self.relationship_editor: RelationshipEditor = self.editors[ViewType.RELATIONSHIP_GRAPH]
            # The editor signals the coordinator to load the data when it becomes visible
            self.relationship_editor.request_load_data.connect(self.load_relationship_graph_data)

    def set_current_view(self, view_type: ViewType) -> None:
        """Called by MainWindow when the view is explicitly switched."""
        self.current_view = view_type

        if view_type != ViewType.RELATIONSHIP_GRAPH:
            self.current_item_id = 0 # Reset current item id
        elif view_type == ViewType.RELATIONSHIP_GRAPH:
            self.load_relationship_graph_data()

    # --- Save / Dirty Check Logic (Core Business Logic) ---

    def get_current_editor(self):
        """Helper to get the currently visible editor panel"""
        return self.editors.get(self.current_view)

    def check_and_save_dirty(self, parent=None) -> bool:
        """
        Prompts the user to save if the active editor is dirty.
        Returns True if safe to proceed (saved or discarded), False otherwise (canceled).
        """
        if self.current_view == ViewType.RELATIONSHIP_GRAPH:
            return True

        if self.current_item_id == 0:
            return True # No item loeaded
        
        editor_panel = self.get_current_editor()
        if not editor_panel or not editor_panel.is_dirty():
            return True # Editor is clean
        
        save_reply = QMessageBox.question(
            parent, # Use parent for dialog centering
            "Unsaved Changes",
            f"The current item has unsaved changes. Do you want to save before continuing?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save
        )

        if save_reply == QMessageBox.StandardButton.Cancel:
            return False
        
        if save_reply == QMessageBox.StandardButton.Save:
            self.save_current_item(self.current_item_id, self.current_view, parent)
        
        # If discard proceed
        return True
    
    def save_current_item(self, item_id: int, view: ViewType, parent=None) -> bool:
        """General Method to save either chapter or a lore entry."""

        if self.current_view == ViewType.RELATIONSHIP_GRAPH:
            return True

        if item_id <= 0:
            return False
        
        match view:
            case ViewType.CHAPTER_EDITOR:
                return self._save_chapter_content(item_id, parent)
            
            case ViewType.LORE_EDITOR:
                return self._save_lore_entry_content(item_id, parent)
            
            case ViewType.CHARACTER_EDITOR:
                return self._save_character_content(item_id, parent)
            
            case _:
                return False
            
    def _save_chapter_content(self, chapter_id: int, parent=None) -> bool:
        """Saves the current chapter content and tags to the database"""
        editor: ChapterEditor = self.editors[ViewType.CHAPTER_EDITOR]
        content = editor.get_html_content()
        tags = editor.get_tags()

        content_saved = self.chapter_repo.update_chapter_content(chapter_id, content)
        tags_saved = self.tag_repo.set_tags_for_chapter(chapter_id, tags)

        if content_saved and tags_saved:
            editor.mark_saved()
            return True
        else:
            QMessageBox.critical(parent, "Save Failed", f"Failed to save Chapter ID {chapter_id}.")
            return False

    def _save_lore_entry_content(self, lore_id: int, parent=None) -> bool:
        """Saves the current lore content and tags to the database"""
        editor: LoreEditor = self.lore_editor
        data = editor.get_data()
        
        title = data['title']
        category = data['category']
        content = data['content']
        tags = data['tags']

        content_saved = self.lore_repo.update_lore_entry(lore_id, title, content, category)
        tags_saved = self.tag_repo.set_tags_for_lore_entry(lore_id, tags)

        if content_saved and tags_saved:
            # Reload to reset the editor's internal state (dirtiness tracking)
            editor.load_lore(lore_id, title, category, content, tags) 
            editor.mark_saved()
            return True
        else:
            QMessageBox.critical(parent, "Save Failed", f"Failed to save Lore Entry ID {lore_id}.")
            return False
        
    def _save_character_content(self, char_id: int, parent=None) -> bool:
        """Saves the current Character content"""
        editor: CharacterEditor = self.character_editor

        data = editor.get_data()

        name = data['name']
        description = data['description']
        status = data['status']

        content_saved = self.character_repo.update_character(char_id, name, description, status)

        if content_saved:
            editor.load_character(char_id, name, description, status)
            editor.mark_saved()
            return True
        else:
            QMessageBox.critical(parent, "Save Failed", f"Failed to save Character ID {char_id}.")
            return False
        
    def save_node_position(self, char_id: int, x_pos: float, y_pos: float, node_color: str, node_shape: str, is_hidden: int) -> bool:
        """
        Receives node position/attribute updates from RelationshipEditor and persists them.
        """
        return self.relationship_repo.save_node_attributes(
            character_id=char_id,
            x_pos=x_pos,
            y_pos=y_pos,
            node_color=node_color,
            node_shape=node_shape,
            is_hidden=is_hidden
        )
    
    def save_new_relationship(self, char_a_id: int, char_b_id: int, type_id: int,
                              description: str = "", intensity: int = 5) -> bool:
        # 1. Save to DB
        new_id = self.relationship_repo.create_relationship(
            char_a_id, char_b_id, type_id, None, description, intensity
        )

        if new_id:
            # 2. Reload graph data to show the new edge
            self.reload_relationship_graph_data()
            return True
        else:
            QMessageBox.critical(
                None, 
                "Save Error", 
                "Failed to create new character relationship in the database."
            )
            return False
        
    # --- Load Content Logic (Called by Outline Managers) ---

    def load_chapter(self, chapter_id: int) -> None:
        """Loads chapter data and emits a signal to update the editor."""
        
        # 1. Update Coordinator State
        self.current_item_id = chapter_id
        self.current_view = ViewType.CHAPTER_EDITOR

        # 2. Load Content
        content = self.chapter_repo.get_chapter_content(chapter_id)
        
        if content is None:
            content = "<h1>Error Loading Chapter</h1><p>Content could not be retrieved from the database.</p>"

        # 3. Load Tags
        tags_data = self.tag_repo.get_tags_for_chapter(chapter_id)
        tag_names = [name for _, name in tags_data] if tags_data else []
        
        # 4. Emit signal to the ChapterEditor
        self.chapter_loaded.emit(chapter_id, content, tag_names)

    def load_lore(self, lore_id: int) -> None:
        """Loads lore data and emits a signal to update the editor."""
        
        # 1. Update Coordinator State
        self.current_item_id = lore_id
        self.current_view = ViewType.LORE_EDITOR

        # 2. Load Lore Details
        lore_details = self.lore_repo.get_lore_entry_details(lore_id)
        
        if lore_details is None:
            # Emit empty content to disable editor
            self.lore_loaded.emit(lore_id, "", "", "", [])
            return
        
        title = lore_details['Title']
        category = lore_details['Category']
        content = lore_details['Content']

        # 3. Load Tags
        tags_data = self.tag_repo.get_tags_for_lore_entry(lore_id)
        tag_names = [name for _, name in tags_data] if tags_data else []
        
        # 4. Emit signal to the LoreEditor
        self.lore_loaded.emit(lore_id, title, category, content, tag_names)

    def load_character(self, char_id: int) -> None:
        """Loads character data and emits a signal to update the editor."""
        # 1. Update Coordinator State
        self.current_item_id = char_id
        self.current_view = ViewType.CHARACTER_EDITOR

        # 2. Load Lore Details
        char_details = self.character_repo.get_character_details(char_id)
        
        if char_details is None:
            # Emit empty content to disable editor
            self.char_loaded.emit(char_id, "", "", "")
            return
        
        name = char_details['Name']
        description = char_details['Description']
        status = char_details['Status']

        self.char_loaded.emit(char_id, name, description, status)

    def load_relationship_graph_data(self) -> None:
        """
        Fetches all data requires to render the character relationship graph
        and emits a signal to update the RelationshipEditor
        """
        # Update Coordinator State
        self.current_item_id = 0
        self.current_view = ViewType.RELATIONSHIP_GRAPH

        # Fetch all components
        relationships = self.relationship_repo.get_all_relationships_for_graph() or []
        node_positons = self.relationship_repo.get_all_node_positions() or []
        relationship_types = self.relationship_repo.get_all_relationship_types() or []

        # Process data into a standard graph dictionary structure
        graph_data = self._process_graph_data(relationships, node_positons, relationship_types)

        # Emit signal to the RelationshipEditor
        self.graph_data_loaded.emit(graph_data)

    def load_relationship_types_for_editor(self) -> None:
        """
        Fetches all available relationship types and sends them to the editor.
        The editor will use this list to populate the 'new relationship' dialog.
        """
        try:
            rel_types = self.relationship_repo.get_all_relationship_types()
            self.relationship_types_available.emit(rel_types)
        except Exception as e:
            QMessageBox.critical(None, "Data Error", f"Failed to load relationship types: {e}")

    def _process_graph_data(self, relationships: list[dict], node_positions: list[dict], relationship_types: list[dict]) -> dict:
        """
        Converts the database results into the 'nodes' and 'edges' format expected by Relationship Editor
        """
        # --- Node Processing ---
        char_ids = set()
        for rel in relationships:
            char_ids.add(rel['Character_A_ID'])
            char_ids.add(rel['Character_B_ID'])

        # Get all characters (nodes) including those without relationships
        all_characters = self.character_repo.get_all_characters()

        # Map node positions for quick lookup
        pos_map = {pos['Character_ID']: pos for pos in node_positions}

        nodes = []
        for char in all_characters:
            char_id = char['ID']
            pos_data = pos_map.get(char_id, {})

            nodes.append({
                'id': char_id,
                'name': char['Name'],
                'x': pos_data.get('X_Position', 0),    # Default to 0,0
                'y': pos_data.get('Y_Position', 0),
                'color': pos_data.get('Node_Color', '#60A5FA'), # Default color
                'shape': pos_data.get('Node_Shape', 'Circle'), # Default shape
                'is_hidden': pos_data.get('Is_Hidden', 0)
            })

        # --- Edge Processing ---
        edges = []
        type_map = {rt['ID']: rt for rt in relationship_types}

        for rel in relationships:
            rel_type = type_map.get(rel['Type_ID'], {})
            
            edges.append({
                'id': rel['Relationship_ID'],
                'source': rel['Character_A_ID'],
                'target': rel['Character_B_ID'],
                'label': rel_type.get('Short_Label', 'Rel.'),
                'color': rel_type.get('Default_Color', '#000000'),
                'style': rel_type.get('Line_Style', 'Solid'),
                'intensity': rel.get('Intensity', 5),
                'is_directed': rel_type.get('Is_Directed', 0),
                'description': rel.get('Description'),
            })

        return {'nodes': nodes, 'edges': edges}
    
    def reload_relationship_graph_data(self) -> None:
        """
        Fetches and emits the current graph data for the editor to display.
        Called when a relationship type is created/edited/deleted, forcing a graph refresh.
        """
        try:
            self.load_relationship_graph_data()
        
        except Exception as e:
            QMessageBox.critical(None, "Data Error", f"Failed to reload graph data: {e}")

    # --- Cross-Update Logic ---

    def update_lore_outline_title(self, lore_id: int, new_title: str) -> None:
        """
        Receives title change from LoreEditor and relays it to the LoreOutlineManager.
        Note: The editor is responsible for setting the item as dirty,
        and the save logic handles persisting the new title to the DB.
        """
        self.lore_title_updated_in_outline.emit(lore_id, new_title)

    def update_character_outline_title(self, char_id: int, new_name: str) -> None:
        """
        Receives name change from CharacterEditor and relays it to the CharacterOutlineManager.
        Note: The editor is responsible for setting the item as dirty,
        and the save logic handles persisting the new title to the DB.
        """
        self.char_name_updated_in_ouline.emit(char_id, new_name)

    # --- Export Logic Helper (For use by the new StoryExporter class) ---
    
    def get_chapter_data_for_export(self):
        """Fetches all chapter data needed for export."""
        return self.chapter_repo.get_all_chapters_with_content()