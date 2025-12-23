# src/python/services/app_coordinator.py

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox

from ..db_connector import DBConnector
from ..repository.chapter_repository import ChapterRepository
from ..repository.lore_repository import LoreRepository
from ..repository.tag_repository import TagRepository
from ..repository.character_repository import CharacterRepository
from ..repository.note_repository import NoteRepository
from ..repository.relationship_repository import RelationshipRepository

from ..utils.nf_core_wrapper import calculate_read_time
from ..utils.constants import ViewType, EntityType

from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from ..ui.views.chapter_editor import ChapterEditor
    from ..ui.views.lore_editor import LoreEditor
    from ..ui.views.character_editor import CharacterEditor
    from ..ui.views.note_editor import NoteEditor
    from ..ui.views.relationship_editor import RelationshipEditor

class AppCoordinator(QObject):
    """
    Coordinates data flow between the UI components (Outline/Editor) and the 
    database repositories. Centralizes save/load/dirty checking logic.
    
    This class acts as the central hub for all application events that involve 
    data retrieval or persistence, ensuring that UI components only interact 
    with each other via signals, and interact with the database only via this coordinator.
    """

    # --- Signals for Editor Panel Updates ---
    chapter_loaded = pyqtSignal(int, str, list)      # id, content_html, tags
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (int, str, list): Emitted to load a 
    chapter's content into the editor. Carries the Chapter ID, its content 
    as HTML, and a list of associated tags.
    """

    lore_loaded = pyqtSignal(int, str, str, str, list) # id, title, category, content_html, tags
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (int, str, str, str, list): Emitted 
    to load a lore item's content. Carries the Lore ID, title, category, 
    content as HTML, and a list of associated tags.
    """

    char_loaded = pyqtSignal(int, str, str, str, int, str, str, str)
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (int, str, str, str): Emitted to load 
    a character's data into the editor. Carries (ID, Name, Description, Status, 
    Age, DOB, Occupation, Physical).
    """

    note_loaded = pyqtSignal(int, str , list) # id, content_html, tags
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (int, str, list): Emitted to load a 
    notes's content into the editor. Carries the Note ID, its content 
    as HTML, and a list of associated tags.
    """

    graph_data_loaded = pyqtSignal(dict)
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (dict): Emitted to provide all necessary 
    data for the relationship graph. Carries a dictionary containing node and edge data.
    """
    
    relationship_types_available = pyqtSignal(list) # list[dict]
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (list): Emitted to provide the list of 
    all defined relationship types (names, colors, IDs) to the graph and outline manager.
    """
    
    # --- Signals for Outline Panel Updates ---
    chapter_created = pyqtSignal(int, str)           # id, title
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (int, str): Emitted after a new chapter 
    is successfully created in the database. Carries the new Chapter ID and title.
    """

    lore_created = pyqtSignal(int, str, str)         # id, title, category
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (int, str, str): Emitted after a new 
    lore item is successfully created. Carries the new Lore ID, title, and category.
    """

    character_created = pyqtSignal(int, str)         # id, name
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (int, str): Emitted after a new character 
    is successfully created. Carries the new Character ID and name.
    """

    note_created = pyqtSignal(int, str) # id, title
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (int, str): Emitted after a new note 
    is successfully created. Carries the new Note ID and name.
    """

    chapter_editor_dirty_status = pyqtSignal(bool)
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (bool): Emitted to indicate the chapter 
    editor's dirty (unsaved changes) status.
    """

    lore_editor_dirty_status = pyqtSignal(bool)
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (bool): Emitted to indicate the lore 
    editor's dirty status.
    """

    character_editor_dirty_status = pyqtSignal(bool)
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (bool): Emitted to indicate the character 
    editor's dirty status.
    """

    note_editor_dirty_status = pyqtSignal(bool)
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (bool): Emitted to indicate the note 
    editor's dirty status.
    """

    lore_categories_changed = pyqtSignal(list) 
    """:py:class:`~PyQt6.QtCore.pyqtSignal` Emitted when the list of available 
    categories is refreshed containing list[str] of all unique category names.
    """

    def __init__(self, db_connector: DBConnector) -> None:
        """
        Initializes the :py:class:`.AppCoordinator` and sets up the database repositories.

        :param db_connector: The active connection object to the SQLite database.
        :type db_connector: :py:class:`~app.db_connector.DBConnector`
        
        :rtype: None
        """
        super().__init__()

        self.db = db_connector

        # Create Repositorys
        self.chapter_repo = ChapterRepository(self.db)
        self.lore_repo = LoreRepository(self.db)
        self.character_repo = CharacterRepository(self.db)
        self.note_repo = NoteRepository(self.db)
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
        self.note_editor = None
        self.relationship_editor = None
        
    def connect_signals(self) -> None:
        """
        Connects signals. Called in MainWindow after set_editors
        
        :rtype: None
        """
        self.relationship_editor.relationship_created.connect(self.save_new_relationship)
        self.relationship_editor.relationship_deleted.connect(self.handle_relationship_deletion)

    # --- View Logic ---

    def set_editors(self, editor_map: dict[ViewType, Any]) -> None:
        """
        Sets all editor references using a dictionary map where keys are ViewType constants.
        Example: {ViewType.CHAPTER_EDITOR: chapter_editor, ViewType.LORE_EDITOR: lore_editor...}
        
        :param editor_map: A dictionary map of all

        :rtype: None
        """
        self.editors = editor_map

        if ViewType.LORE_EDITOR in self.editors:
            self.lore_editor: LoreEditor = self.editors[ViewType.LORE_EDITOR]
        if ViewType.CHARACTER_EDITOR in self.editors:
            self.character_editor: CharacterEditor = self.editors[ViewType.CHARACTER_EDITOR]
        if ViewType.NOTE_EDITOR in self.editors:
            self.note_editor: NoteEditor = self.editors[ViewType.NOTE_EDITOR]
        
        # Handle specific editor connections separately (like title change signals)
        if ViewType.RELATIONSHIP_GRAPH in self.editors:
            self.relationship_editor: RelationshipEditor = self.editors[ViewType.RELATIONSHIP_GRAPH]
            # The editor signals the coordinator to load the data when it becomes visible
            self.relationship_editor.request_load_data.connect(self.load_relationship_graph_data)

        self.connect_signals()

    def set_current_view(self, view_type: ViewType) -> None:
        """
        Called by MainWindow when the view is explicitly switched.
        
        :param view_type: The view that is being set as the current view.
        :type view_type: :py:class:`~.ViewType`

        :rtype: None
        """
        self.current_view = view_type

        if view_type != ViewType.RELATIONSHIP_GRAPH:
            self.current_item_id = 0 # Reset current item id
        elif view_type == ViewType.RELATIONSHIP_GRAPH:
            self.load_relationship_graph_data()

    # --- Save / Dirty Check Logic (Core Business Logic) ---

    def get_current_editor(self) -> ViewType:
        """
        Helper to get the currently visible editor panel
        
        :rtype: :py:class:`~.ViewType`
        """
        return self.editors.get(self.current_view)

    def check_and_save_dirty(self, parent=None) -> bool:
        """
        Prompts the user to save if the active editor is dirty.
        Returns True if safe to proceed (saved or discarded), False otherwise (canceled).

        :param parent: The parent. Default is None.
        :type parent: :py:class:`~PyQt6.QtWidgets.QWidget`

        :returns: Returns True if saved, otherwise False
        :rtype: bool
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
        """
        General Method to save either chapter, character or a lore entry.
        
        :param item_id: The ID number of the item to save.
        :type item_id: int
        :param view: The current view of the application.
        :type view: :py:class:`~.ViewType`
        :param parent: The parent. Default is None.
        :type parent: :py:class:`~PyQt6.QtWidgets.QWidget`

        :returns: Returns True if saved, otherwise False
        :rtype: bool
        """

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
            
            case ViewType.NOTE_EDITOR:
                return self._save_note_content(item_id, parent)
            
            case _:
                return False
            
    def _save_chapter_content(self, chapter_id: int, parent=None) -> bool:
        """
        Saves the current chapter content.
        
        :param chapter_id: The ID number of the chapter item to save.
        :type chapter_id: int
        :param parent: The parent. Default is None.
        :type parent: :py:class:`~PyQt6.QtWidgets.QWidget`

        :returns: Returns True if saved, otherwise False
        :rtype: bool
        """
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
        """
        Saves the current lore entry content.
        
        :param lore_id: The ID number of the lore item to save.
        :type lore_id: int
        :param parent: The parent. Default is None.
        :type parent: :py:class:`~PyQt6.QtWidgets.QWidget`

        :returns: Returns True if saved, otherwise False
        :rtype: bool
        """
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
        """
        Saves the current character content.
        
        :param char_id: The ID number of the character item to save.
        :type char_id: int
        :param parent: The parent. Default is None.
        :type parent: :py:class:`~PyQt6.QtWidgets.QWidget`

        :returns: Returns True if saved, otherwise False
        :rtype: bool
        """
        editor: CharacterEditor = self.character_editor
        data = editor.get_data()

        content_saved = self.character_repo.update_character(
            char_id, 
            data['name'], data['description'], data['status'],
            data['age'], data['date_of_birth'], data['occupation_school'], data['physical_description']
        )

        if content_saved:
            editor.load_character(
                char_id, 
                data['name'], data['description'], data['status'],
                data['age'], data['date_of_birth'], data['occupation_school'], data['physical_description']
            )
            editor.mark_saved()
            return True
        else:
            QMessageBox.critical(parent, "Save Failed", f"Failed to save Character ID {char_id}.")
            return False
        
    def _save_note_content(self, note_id: int, parent=None) -> bool:
        """
        Saves the current note content.
        
        :param note_id: The ID number of the chapter item to save.
        :type note_id: int
        :param parent: The parent. Default is None.
        :type parent: :py:class:`~PyQt6.QtWidgets.QWidget`

        :returns: Returns True if saved, otherwise False
        :rtype: bool
        """
        editor: NoteEditor = self.editors[ViewType.NOTE_EDITOR]
        content = editor.get_html_content()
        tags = editor.get_tags()

        content_saved = self.note_repo.update_note_content(note_id, content)
        tags_saved = self.tag_repo.set_tags_for_note(note_id, tags)

        if content_saved and tags_saved:
            editor.mark_saved()
            return True
        else:
            QMessageBox.critical(parent, "Save Failed", f"Failed to save note ID {note_id}.")
            return False
        
    def save_node_position(self, char_id: int, x_pos: float, y_pos: float, node_color: str, node_shape: str, is_hidden: int) -> bool:
        """
        Saves the position and presentation attributes of a character node in the database.
        
        This method is typically called frequently (e.g., on mouse release after a drag) 
        and does not affect the dirty status of the main character editor.

        :param char_id: The ID of the character node.
        :type char_id: int
        :param x_pos: The new X-coordinate for the node.
        :type x_pos: float
        :param y_pos: The new Y-coordinate for the node.
        :type y_pos: float
        :param node_color: The color of the node.
        :type node_color: str
        :param node_shape: The shape of the node.
        :type node_shape: str
        :param is_hidden: To tell whether the Node is hidden. 1 if True, otherwise 0
        :type is_hidden: int
        
        :returns: True if the save was successful, False otherwise.
        :rtype: bool
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
        """
        Saves the new relationship by creating a new relationship.
        
        :param char_a_id: The ID of the first character
        :type char_a_id: int
        :param char_b_id: The ID of the second character
        :type char_b_id: int
        :param type_id: The ID of the type of relationship
        :type type_id: int
        :param description: A description of the relationship
        :type description: str
        :param intensity: The intensity (thickness) of the line
        :type intensity: int

        :return: Returns the True if successfully created and saved new relationship.
        :rtype: bool
        """
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
        """
        Fetches a chapter from the repository and emits the :py:attr:`.chapter_loaded` signal.

        :param chapter_id: The ID of the chapter to load.
        :type chapter_id: int
        
        :rtype: None
        """
        
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
        """
        Fetches a lore item from the repository and emits the :py:attr:`.lore_loaded` signal.

        :param lore_id: The ID of the lore item to load.
        :type lore_id: int
        
        :rtype: None
        """
        
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
        """
        Fetches a character from the repository and emits the :py:attr:`.char_loaded` signal.

        :param char_id: The ID of the character to load.
        :type char_id: int
        
        :rtype: None
        """
        self.current_item_id = char_id
        self.current_view = ViewType.CHARACTER_EDITOR
        
        char_details = self.character_repo.get_character_details(char_id)
        if char_details:
            self.char_loaded.emit(
                char_id, 
                char_details['Name'], char_details['Description'], char_details['Status'],
                char_details.get('Age', -1),
                char_details.get('Date_Of_Birth', ""),
                char_details.get('Occupation_School', ""),
                char_details.get('Physical_Description', "")
            )

    def load_note(self, note_id: int) -> None:
        """
        Fetches a note from the repository and emits the :py:attr:`.note_loaded` signal.

        :param note_id: The ID of the note to load.
        :type note_id: int
        
        :rtype: None
        """
        
        # 1. Update Coordinator State
        self.current_item_id = note_id
        self.current_view = ViewType.NOTE_EDITOR

        # 2. Load Content
        content = self.note_repo.get_note_content(note_id)
        
        if content is None:
            content = "<h1>Error Loading Note</h1><p>Content could not be retrieved from the database.</p>"

        # 3. Load Tags
        tags_data = self.tag_repo.get_tags_for_note(note_id)
        tag_names = [name for _, name in tags_data] if tags_data else []
        
        # 4. Emit signal to the ChapterEditor
        self.note_loaded.emit(note_id, content, tag_names)

    # --- Updating Parent Lore ID ---

    def update_lore_parent_id(self, lore_id: int, new_parent_id: int | None) -> bool:
        """
        Updates the parent ID of a Lore Entry via the repository.

        :param lore_id: The ID of the lore entry to update.
        :param new_parent_id: The ID of the new parent, or None.

        :returns: True on successful database update, False otherwise.
        """
        if isinstance(new_parent_id, int) and new_parent_id <= 0:
            new_parent_id = None
        result = self.lore_repo.update_lore_entry_parent_id(lore_id, new_parent_id)
        if result:
            pass
        return result
    
    def refresh_lore_categories(self) -> None:
        """
        Fetches unique categories and notifies the Lore Editor.
        
        :rtype: None
        """
        categories = self.lore_repo.get_unique_categories()
        self.lore_categories_changed.emit(categories)

    def update_note_parent_id(self, note_id: int, new_parent_id: int | None) -> bool:
        """
        Updates the parent ID of a note via the repository.

        :param note_id: The ID of the note to update.
        :param new_parent_id: The ID of the new parent, or None.

        :returns: True on successful database update, False otherwise.
        """
        if isinstance(new_parent_id, int) and new_parent_id <= 0:
            new_parent_id = None
        result = self.note_repo.update_note_parent_id(note_id, new_parent_id)
        if result:
            pass
        return result
    
    # --- Relationship Graph Methods ---

    def load_relationship_graph_data(self) -> None:
        """
        Fetches all character nodes, relationship edges, and relationship types 
        required for the graph editor.

        Emits :py:attr:`.relationship_types_available` and :py:attr:`.graph_data_loaded`.
        
        :rtype: None
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
        Fetches and emits the current list of relationship types.

        Emits :py:attr:`.relationship_types_available`.
        
        :rtype: None
        """
        try:
            rel_types = self.relationship_repo.get_all_relationship_types()
            self.relationship_types_available.emit(rel_types)
        except Exception as e:
            QMessageBox.critical(None, "Data Error", f"Failed to load relationship types: {e}")

    def handle_relationship_deletion(self, relationship_id: int) -> None:
        """
        handles the deletion of a relationshipo
        
        :param relationship_id: The relationship ID
        :type relationship_id: int

        :rtype: None
        """
        success = self.relationship_repo.delete_relationship(relationship_id)
        self.reload_relationship_graph_data()


    def _process_graph_data(self, relationships: list[dict], node_positions: list[dict], relationship_types: list[dict]) -> dict:
        """
        Docstring for _process_graph_data
        
        :param relationships: A list of relationships with the relationship attributes a dict.
        :type relationships: list[dict]
        :param node_positions: The postition of the nodes (characters)
        :type node_positions: list[dict]
        :param relationship_types: A list of the types of relationships with the relationship_types
            attributes as dict.
        :type relationship_types: list[dict]

        :return: Returns a dict of nodes and edges.
        :rtype: dict
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

        :rtype: None
        """
        try:
            self.relationship_editor.update_types_available(self.relationship_repo.get_all_relationship_types())
            self.load_relationship_graph_data()
        
        except Exception as e:
            QMessageBox.critical(None, "Data Error", f"Failed to reload graph data: {e}")

    # --- Export Logic Helper (For use by the new Exporter classes) ---
    
    def get_chapter_data_for_export(self, chapter_ids: list[int] = []) -> list[int]:
        """
        Fetches all chapter data required for a full or partial story export.
        
        :param chapter_ids: A list of chapter IDs to fetch. If empty, all chapters are fetched.
        :type chapter_ids: list[int]
        
        :returns: A list of dictionaries, where each dictionary contains all data for a chapter.
        :rtype: list[:py:obj:`Any`]
        """
        return self.chapter_repo.get_all_chapters_for_export(chapter_ids)
    
    def get_character_data_for_export(self, character_ids: list[int] = []) -> list[int]:
        """
        Fetches all character data required for all or some characters export.
        
        :param character_ids: A list of character IDs to fetch. If empty, all characters are fetched.
        :type character_ids: list[int]
        
        :returns: A list of dictionaries, where each dictionary contains all data for a character.
        :rtype: list[:py:obj:`Any`]
        """
        return self.character_repo.get_all_characters_for_export(character_ids)
    
    def get_lore_data_for_export(self, lore_ids: list[int] = []) -> list[int]:
        """
        Fetches all lore entry data required for all or some Lore_Entries export.
        
        :param lore_ids: A list of lore IDs to fetch. If empty, all lore entries are fetched.
        :type lore_ids: list[int]
        
        :returns: A list of dictionaries, where each dictionary contains all data for a lore entry.
        :rtype: list[:py:obj:`Any`]
        """
        return self.lore_repo.get_lore_entries_for_export(lore_ids)
    
    # -----------------------------------
    # Entity Lookup Methods
    #------------------------------------

    def lookup_entity_content_by_name(self, name: str) -> tuple[str, str, str] | None:
        """
        Sequentially looks up an entity by name/title across all relevant repositories.
        
        The lookup order (Character -> Lore -> Chapter) is strategic: characters and 
        lore entries are usually more unique and concise than chapter titles.

        :param name: The highlighted text string (e.g., "Sir Kaelan").
        :type name: str

        :returns: A tuple (EntityType, Title, Content) or None if not found.
        :rtype: tuple[str, str, str]
        """
        name = name.strip()

        # Start Searching For Characters
        if hasattr(self, 'character_repo'):
            data = self.character_repo.get_content_by_name(name=name)
            if data: 
                return (EntityType.CHARACTER, data['Name'], data.get('Description', ''))
            
        # Search Through Lore Entries
        if hasattr(self, 'lore_repo'):
            data = self.lore_repo.get_content_by_title(title=name)
            if data: 
                return (EntityType.CHARACTER, data['Title'], data.get('Content', ''))
            
        return None # Found Nothing
    
    def get_project_stats(self, wpm: int) -> dict[str, str]:
        """
        A function to retrive the project stats from each of the repositories.
    

        :returns: A dictionary of the project statistics.
        :rtype: dict[str, int | str]
        """
        chapter_stats = self.chapter_repo.get_all_chapters_stats()

        total_word_count, char_count_no_spaces = 0, 0
        for chapter in chapter_stats:
            total_word_count += chapter['word_count']
            char_count_no_spaces += chapter['char_count_no_spaces']
        read_time = calculate_read_time(total_word_count, wpm)

        lore_count = self.lore_repo.get_number_of_lore_entries()
        char_count = self.character_repo.get_number_of_characters()

        return {
            "total_word_count": f"{total_word_count}",
            "char_count_no_spaces": f"{char_count_no_spaces}",
            "read_time": f"{read_time}",
            "chapter_count": f"{len(chapter_stats)}",
            "lore_count": f"{lore_count}", 
            "character_count": f"{char_count}"
        } 