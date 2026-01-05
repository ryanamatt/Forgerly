# src/python/services/app_coordinator.py

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMessageBox

from ..db_connector import DBConnector
from ..repository.chapter_repository import ChapterRepository
from ..repository.lore_repository import LoreRepository
from ..repository.tag_repository import TagRepository
from ..repository.character_repository import CharacterRepository
from ..repository.note_repository import NoteRepository
from ..repository.relationship_repository import RelationshipRepository

from ..utils.nf_core_wrapper import calculate_read_time
from ..utils.constants import ViewType, EntityType
from ..utils.events import Events
from ..utils.event_bus import bus, receiver

class AppCoordinator(QObject):
    """
    Coordinates data flow between the UI components (Outline/Editor) and the 
    database repositories. Centralizes save/load/dirty checking logic.
    
    This class acts as the central hub for all application events that involve 
    data retrieval or persistence, ensuring that UI components only interact 
    with each other via signals, and interact with the database only via this coordinator.
    """

    def __init__(self, db_connector: DBConnector) -> None:
        """
        Initializes the :py:class:`.AppCoordinator` and sets up the database repositories.

        :param db_connector: The active connection object to the SQLite database.
        :type db_connector: :py:class:`~app.db_connector.DBConnector`
        
        :rtype: None
        """
        super().__init__()

        bus.register_instance(self)

        self.db = db_connector

        # Create Repositorys
        self.chapter_repo = ChapterRepository(self.db)
        self.lore_repo = LoreRepository(self.db)
        self.character_repo = CharacterRepository(self.db)
        self.note_repo = NoteRepository(self.db)
        self.tag_repo = TagRepository(self.db)
        self.relationship_repo = RelationshipRepository(self.db)

        # State Tracking
        self.current_item_id: int = 0
        self.current_entity_type: EntityType = EntityType.CHAPTER

    @receiver(Events.DATA_LOADED)
    def set_state_tracking(self, data: dict) -> None:
        """
        Sets the current state of ID and EntityType.
        
        :param data: The data needed to set the state variables containing
            {'entity_type': EntityType, 'ID': int}
        :type data: dict
        """
        self.current_item_id = data.get('ID')
        self.current_entity_type = data.get('entity_type')

    # --- Save / Dirty Check Logic (Core Business Logic) ---

    @receiver(Events.OUTLINE_NAME_CHANGE)
    def save_name_change(self, data: dict) -> None:
        """
        Recieves the OUTLINE_NAME_CHANGE event and saves
        the new name/title of the item.
        
        :param data: The data containing {type: EntityType, id: int, new_title: str}
        :type data: dict

        :rtype: None
        """
        entity_type = data.get('entity_type')
        id = data.get('ID')
        title = data.get('new_title')

        if not entity_type or not id or not title:
            return
        
        match entity_type:
            case EntityType.CHAPTER:
                self.chapter_repo.update_chapter_title(id, title)

            case EntityType.LORE:
                self.lore_repo.update_lore_entry_title(id, title)

            case EntityType.CHARACTER:
                self.character_repo.update_character_name(id, title)

            case EntityType.NOTE:
                self.note_repo.update_note_title(id, title)

        bus.publish(Events.OUTLINE_LOAD_REQUESTED, data=data)

    @receiver(Events.PRE_ITEM_CHANGE)
    def handle_pre_change_request(self, data: dict = {}) -> None:
        """
        Called before a UI change (like switching chapters). 
        Tells the current active editor to provide its data if dirty.
        
        :param data: Description
        :type data: dict

        :rtype: None
        """
        data |= {'ID': self.current_item_id}
        if 'entity_type' not in data:
            data |= {'entity_type': self.current_entity_type}
        
        bus.publish(Events.SAVE_REQUESTED, data=data)

    @receiver(Events.SAVE_DATA_PROVIDED)
    def check_and_save_dirty(self, data: dict) -> None:
        """
        Checks to see if it is dirty and if it is dirty
        asks user if they want to save.
        
        :param data: Description
        :type data: dict
        """
        id = data.get('ID')
        parent = data.pop('parent', None)

        if id == -1 or not parent:
            return True # No item loaded
        
        skip_check = data.pop('skip_check', False)
        if skip_check:
            return self.save_current_item(data=data)
            
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
            return self.save_current_item(data=data)
        
        # If discard proceed
        return True

    @receiver(Events.NO_CHECK_SAVE_DATA_PROVIDED)
    def save_current_item(self, data: dict) -> None:
        """
        This functions saves the current item to the database.
        
        :param data: The dictionary of data containing {entity_type: EntityType,
            'ID': int (Item ID), 'tags': list[str] (list of the tags)}
        :type data: dict

        :rtype: None
        """
        content_success, tag_success = False, False

        entity_type = data.pop('entity_type', self.current_entity_type)
        id = data.pop('ID', self.current_item_id)
        tags = data.pop('tags', None)

        match entity_type:
            case EntityType.CHAPTER:
                content_success = self.chapter_repo.update_chapter_content(id, **data)
                tag_success = self.tag_repo.set_tags_for_chapter(id, tags)

            case EntityType.CHARACTER:
                content_success = self.character_repo.update_character(id, **data)
                tag_success = True # No Tags for Character

            case EntityType.LORE:
                content_success = self.lore_repo.update_lore_entry(id, **data)
                tag_success = self.tag_repo.set_tags_for_lore_entry(self.current_item_id, tags)

            case EntityType.NOTE:
                content_success = self.note_repo.update_note_content(id, **data)
                tag_success = self.tag_repo.set_tags_for_note(id, tags)

            case EntityType.RELATIONSHIP:
                content_success = self.relationship_repo.update_relationship_type(id, **data)
                tag_success = True # No Tags for Relationship

        if content_success and tag_success:
            bus.publish(Events.MARK_SAVED, data={'entity_type': entity_type})
            return True
        
        return False
        
    @receiver(Events.NODE_SAVE_REQUESTED)
    def save_node_position(self, data: dict) -> bool:
        """
        Saves the position and presentation attributes of a character node in the database.
        
        This method is typically called frequently (e.g., on mouse release after a drag) 
        and does not affect the dirty status of the main character editor.

        :param data: Dict containg all data to save for the node. Contians
            {'char_id': int, 'x_pos': float, 'y_pos': float, 'node_color': str, 
            'node_shape': str, 'is_hidden': int}
        :type data: dict
        
        :returns: True if the save was successful, False otherwise.
        :rtype: bool
        """
        return self.relationship_repo.save_node_attributes(**data)
    
    @receiver(Events.REL_CREATE_REQUESTED)
    def save_new_relationship(self, data: dict) -> bool:
        """
        Saves the new relationship by creating a new relationship.
        
        :param data: A dictionary containing all need data for a new relationship,
            {char_a_id: int, char_b_id: int, ID: int, description: str, intensity: int}
        :type data: dict

        :return: Returns the True if successfully created and saved new relationship.
        :rtype: bool
        """
        # 1. Save to DB
        new_id = self.relationship_repo.create_relationship(**data)

        if new_id:
            # 2. Reload graph data to show the new edge
            self.load_relationship_graph_data()
            return True
        else:
            QMessageBox.critical(
                None, 
                "Save Error", 
                "Failed to create new character relationship in the database."
            )
            return False
    
    @receiver(Events.GRAPH_NODE_VISIBILTY_CHANGED)
    def save_character_node_is_hidden(self, data: dict) -> None:
        """
        Saves the status of a change is_hidden attribute.
        
        :param data: A dictionary of the data containing {'ID': int,
            'is_hidden': bool}
        :type data: dict

        :rtype: None
        """
        self.relationship_repo.update_node_is_hidden(char_id=data.get('ID'), is_hidden=data.get('is_hidden'))

    @receiver(Events.GRAPH_NODE_LOCKED_CHANGED)
    def save_character_node_is_locked(self, data: dict) -> None:
        """
        Saves the status of a change is_locked attribute.
        
        :param data: A dictionary of the data containing {'ID': int,
            'is_locked': bool}
        :type data: dict

        :rtype: None
        """
        success = self.relationship_repo.update_node_is_locked(char_id=data.get('ID'), is_locked=data.get('is_locked'))

    # --- Update ---

    @receiver(Events.REL_UPDATE_REQUESTED)
    def update_relationship(self, data: dict) -> None:
        """
        Updates a relationship in the Databsase.
        
        :param data: The data needed to update the relationship.
            {char_a_id: int, char_b_id: int, ID: int, description: str, intensity: int}
        :type data: dict

        :rtype: None
        """
        self.relationship_repo.update_relationship_details(**data)
        self.load_relationship_graph_data()

    # --- Load Content Logic (Called by Outline Managers) ---

    @receiver(Events.OUTLINE_LOAD_REQUESTED)
    def load_outline(self, data: dict) -> None:
        """
        Calls the correct repository and publishes an event with
        all the necessary data to load.
        
        :param data: The dictionary of data needed to load the outline.
            Contains {'view': ViewType}
        :type data: dict

        :rtype: None
        """
        entity_type = data.get('entity_type')

        return_data = {}

        match entity_type:
            case EntityType.CHAPTER:
                chapters = self.chapter_repo.get_all_chapters()
                return_data = {'entity_type': entity_type, 'chapters': chapters}

            case EntityType.LORE:
                lore_entries = self.lore_repo.get_all_lore_entries()
                return_data = {'entity_type': entity_type, 'lore_entries': lore_entries}

            case EntityType.CHARACTER:
                characters = self.character_repo.get_all_characters()
                return_data = {'entity_type': entity_type, 'characters': characters}

            case EntityType.NOTE:
                notes = self.note_repo.get_all_notes()
                return_data = {'entity_type': entity_type, 'notes': notes}

            case EntityType.RELATIONSHIP:
                relationship_types = self.relationship_repo.get_all_relationship_types()
                bus.publish(Events.REL_TYPES_RECEIVED, data={'relationship_types': relationship_types})
                return_data = {'entity_type': entity_type, 'relationship_types': relationship_types}

        self.current_entity_type = entity_type
        bus.publish(Events.OUTLINE_DATA_LOADED, return_data)

    @receiver(Events.REL_CHAR_DATA_REQUESTED)
    def load_relationship_characters(self, data: dict = None) -> None:
        """
        Loads the characters for the RelationshipOutlineManager.
        
        :param data: The data dictionary. Empty.
        :type data: dict

        :rtype: None
        """ 
        characters = self.character_repo.get_all_characters()
        character_nodes =self.relationship_repo.get_all_node_positions()

        # Mapping Character_ID -> Node Data
        node_map = {node['Character_ID']: node for node in character_nodes}

        # 3. Merge node data into the character dictionaries
        merged_characters = []
        for char in characters:
            char_id = char.get('ID')
            # Merge character dict with node dict if it exists
            # This uses the | operator (Python 3.9+) to merge dictionaries
            combined_data = char | node_map.get(char_id, {})
            merged_characters.append(combined_data)

        bus.publish(Events.REL_CHAR_DATA_RETURN, data={
            'entity_type': self.current_entity_type,
            'characters': merged_characters
        })

    @receiver(Events.ITEM_SELECTED)
    def load_item(self, data: dict) -> None:
        """
        Called when an item in the OutlineManager is selected and
        the data is needed to load that item.
        
        :param data: The data dictionary containng {'entity_type': EntityType,
            'ID': int (item_id)}
        :type data: dict

        :rtype: None
        """
        entity_type = data.get('entity_type')
        item_id = data.get('ID')
        self.current_item_id = item_id

        return_data = {'entity_type': entity_type}

        if entity_type == EntityType.CHAPTER:
            content = self.chapter_repo.get_chapter_content(chapter_id=item_id)
            if content is None: content = ""
            tags_data = self.tag_repo.get_tags_for_chapter(chapter_id=item_id)
            tag_names = [name for _, name in tags_data] if tags_data else []
            return_data['ID'] = item_id
            return_data['content'] = content
            return_data['tags'] = tag_names

        elif entity_type == EntityType.LORE:
            lore = self.lore_repo.get_lore_entry_details(lore_id=item_id)
            tags_data = self.tag_repo.get_tags_for_lore_entry(item_id)
            tag_names = [name for _, name in tags_data] if tags_data else []
            return_data['ID'] = item_id
            return_data |= lore
            return_data['tags'] = tag_names

        elif entity_type == EntityType.CHARACTER:
            return_data |= self.character_repo.get_character_details(char_id=item_id)

        elif entity_type == EntityType.NOTE:
            content = self.note_repo.get_note_content(note_id=item_id)
            tags_data = self.tag_repo.get_tags_for_note(item_id)
            tag_names = [name for _, name in tags_data] if tags_data else []
            return_data['ID'] = item_id
            return_data['content'] = content
            return_data['tags'] = tag_names

        bus.publish(Events.DATA_LOADED, data=return_data)

    # --- Creating New Items ---

    @receiver(Events.NEW_ITEM_REQUESTED)
    def _check_save_before_new_item(self, data: dict) -> None:
        """
        Recieves NEW_ITEM_REQUESTED Event and emits PRE_ITEM_CHANGE
        to ensure data is saved or not before creating the new item.
        
        :param data: The data needed.
        :type data: dict

        :rtype: None
        """
        bus.publish(Events.PRE_ITEM_CHANGE, data={
            'entity_type': self.current_entity_type, 'ID': self.current_item_id
        })

        self._new_item_created(data=data)

    def _new_item_created(self, data: dict) -> None:
        """
        Called when a new item is created.
        
        :param data: The data needed to create the new item. Containing
            {type: EntityType, *Needed Item Creation Data*}
        :type data: dict

        :rtype: None
        """
        entity_type = data.pop('entity_type')
        if not entity_type:
            return
                
        match entity_type:
            case EntityType.CHAPTER:
                id = self.chapter_repo.create_chapter(data.get('title'), data.get('sort_order'))

            case EntityType.LORE:
                id = self.lore_repo.create_lore_entry(data.get('title'))

            case EntityType.CHARACTER:
                id = self.character_repo.create_character(data.get('title'))

            case EntityType.NOTE:
                id = self.note_repo.create_note(data.get('title'), data.get('sort_order'))

            case EntityType.RELATIONSHIP:
                id = self.relationship_repo.create_relationship_type(**data)

        map = {EntityType.CHAPTER: ViewType.CHAPTER_EDITOR, EntityType.LORE: ViewType.LORE_EDITOR,
                EntityType.CHARACTER: ViewType.CHARACTER_EDITOR, EntityType.NOTE: ViewType.NOTE_EDITOR}

        bus.publish(Events.VIEW_SWITCH_REQUESTED, data={'view_type': map.get(entity_type)})
        bus.publish(Events.NEW_ITEM_CREATED, data={'entity_type': entity_type, 'ID': id})

    # --- Deleting Items ---

    @receiver(Events.ITEM_DELETE_REQUESTED)
    def _delete_item(self, data: dict) -> None:
        """
        Recieves the ITEM_DELETE_REQUESTED Event and deletes said
        item.
        
        :param data: The data needed containing {type: EntityType, ID: item id (int),
        parent: Widget}
        :type data: dict

        :rtype: None
        """
        entity_type = data.get('entity_type')
        id = data.get('ID')

        check = self.check_and_save_dirty(data=data)
        if check:
            match entity_type:
                case EntityType.CHAPTER:
                    self.chapter_repo.delete_chapter(id)

                case EntityType.LORE:
                    self.lore_repo.delete_lore_entry(id)

                case EntityType.CHARACTER:
                    self.character_repo.delete_character(id)

                case EntityType.NOTE:
                    self.note_repo.delete_note(id)

                case EntityType.RELATIONSHIP:
                    self.relationship_repo.delete_relationship_type(id)

        bus.publish(Events.OUTLINE_LOAD_REQUESTED, data={'entity_type': entity_type})

    # --- Searching Items ---

    @receiver(Events.OUTLINE_SEARCH_REQUESTED)
    def _search_outline(self, data: dict) -> None:
        """
        Handles the OUTLINE_SEARCH_REQUESTED Event by gathering the data
        from the search query and emitting the OUTLINE_SEARCH_RETURN event.
        
        :param data: The needed data containing {'entity_type': EntityType,
            'query': str}
        :type data: dict
        """
        entity_type = data.get('entity_type', '')
        query = data.get('query')

        results = {}
        results_name = ''

        match entity_type:
            case EntityType.LORE:
                results = self.lore_repo.search_lore_entries(query)
                results_name = 'lore_entries'

            case EntityType.CHARACTER:
                results = self.character_repo.search_characters(query)
                results_name = 'characters'

            case EntityType.NOTE:
                results = self.note_repo.search_notes(query)
                results_name = 'notes'

        bus.publish(Events.OUTLINE_SEARCH_RETURN, data={
            'entity_type': entity_type, results_name: results
        })

    # --- Updating Parent ID / Reordering ---

    @receiver(Events.OUTLINE_PARENT_UPDATE)
    def update_outline_parent_id(self, data: dict) -> None:
        """
        Updates the parent ID of the outline item.
        
        :param data: The data needed to update the new parent ID containing
            {'entity_type': EntityType, 'ID': int, 'new_parent_id': int}
        :type data: dict

        :rtype: None
        """
        entity_type = data.get('entity_type')
        id = data.get('ID')
        new_parent_id = data.get('new_parent_id')
        if not entity_type or not id:
            return

        match entity_type:
            case EntityType.LORE:
                self.lore_repo.update_lore_entry_parent_id(lore_id=id, new_parent_id=new_parent_id)

            case EntityType.NOTE:
                self.note_repo.update_note_parent_id(note_id=id, new_parent_id=new_parent_id)

        bus.publish(Events.OUTLINE_LOAD_REQUESTED, data={'entity_type': entity_type})

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
    
    @receiver(Events.LORE_CATEGORIES_REFRESH)
    def refresh_lore_categories(self, data: dict) -> None:
        """
        Fetches unique categories and notifies the Lore Editor.
        
        :rtype: None
        """
        categories = self.lore_repo.get_unique_categories()
        bus.publish(Events.LORE_CATEGORIES_CHANGED, data={'categories': categories})

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
    
    @receiver(Events.OUTLINE_REORDER)
    def reordering_item(self, data: dict) -> None:
        """
        Recieves the OUTLINE_REORDER Event and updates the reordering.
        
        :param data: The data neeeded to reorder. Carries {editor: 'BaseEditor',
            view: ViewType, updates: list[tuple[int, int]]}
        :type data: dict

        :rtype: None
        """
        view, updates = data.get('view'), data.get('updates')
        if not view and not updates:
            return
        
        match view:
            case ViewType.CHAPTER_EDITOR:
                success = self.chapter_repo.reorder_chapters(updates)

        if not success:
            QMessageBox.critical(data.get('editor'), "Reordering Error", "Database update failed.")
            self.load_outline(data=data)

    
    # --- Relationship Graph Methods ---

    @receiver(Events.GRAPH_LOAD_REQUESTED)
    def load_relationship_graph_data(self, data: dict = None) -> None:
        """
        Fetches all character nodes, relationship edges, and relationship types 
        required for the graph editor.

        Emits :py:attr:`.graph_data_loaded`.
        
        :rtype: None
        """
        # Update Coordinator State
        self.current_item_id = 0

        self.load_outline(data={'entity_type': EntityType.RELATIONSHIP})

        # Fetch all components
        relationships = self.relationship_repo.get_all_relationships_for_graph() or []
        node_positons = self.relationship_repo.get_all_node_positions() or []
        relationship_types = self.relationship_repo.get_all_relationship_types() or []

        # Process data into a standard graph dictionary structure
        graph_data = self._process_graph_data(relationships, node_positons, relationship_types)

        # Emit signal to the RelationshipEditor
        bus.publish(Events.GRAPH_DATA_LOADED, data=graph_data)

    @receiver(Events.REL_DETAILS_REQUESTED)
    def get_rel_details(self, data: dict) -> None:
        """
        Retrieves all the details for a relationship
        and calls the event REL_DETAILS_RETURN.
        
        :param data: Description
        :type data: dict

        :rtype: None
        """
        return_data = data
        return_data |= self.relationship_repo.get_relationship_details(data.get('ID'))
        bus.publish(Events.REL_DETAILS_RETURN, data=return_data)

    @receiver(Events.REL_TYPE_DETAILS_REQUESTED)
    def get_rel_types_details(self, data: dict) -> None:
        """
        Retrieves the relationship details for a relationship
        type and calls the event REL_TYPE_DETAILS_RETURN.
        
        :param data: Description
        :type data: dict
        """
        data |= self.relationship_repo.get_relationship_type_details(data.get('ID'))
        bus.publish(Events.REL_TYPE_DETAILS_RETURN, data=data)
        
    @receiver(Events.REL_DELETE_REQUESTED)
    def handle_relationship_deletion(self, data: dict) -> None:
        """
        handles the deletion of a relationshipo
        
        :param data: Dictionary containing {ID: int}

        :rtype: None
        """
        self.relationship_repo.delete_relationship(data.get('ID'))
        self.load_relationship_graph_data()


    def _process_graph_data(self, relationships: list[dict], node_positions: list[dict], relationship_types: list[dict]) -> dict:
        """
        Proceess all the graph data.
        
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

            print(pos_data, char.get('Name'))

            nodes.append({
                'id': char_id,
                'name': char['Name'],
                'x': pos_data.get('X_Position', 0),    # Default to 0,0
                'y': pos_data.get('Y_Position', 0),
                'color': pos_data.get('Node_Color', '#60A5FA'), # Default color
                'shape': pos_data.get('Node_Shape', 'Circle'), # Default shape
                'is_hidden': pos_data.get('Is_Hidden', 0),
                'is_locked': pos_data.get('Is_Locked', 0)
            })

        # --- Edge Processing ---
        edges = []
        type_map = {rt['ID']: rt for rt in relationship_types}

        for rel in relationships:
            rel_type = type_map.get(rel['Type_ID'], {})
            
            edges.append({
                'id': rel['Relationship_ID'],
                'type_id': rel_type.get('ID'),
                'source': rel['Character_A_ID'],
                'target': rel['Character_B_ID'],
                'label': rel_type.get('Short_Label', 'Rel.'),
                'color': rel_type.get('Default_Color', '#000000'),
                'style': rel_type.get('Line_Style', 'Solid'),
                'intensity': rel.get('Intensity', 5),
                'is_directed': rel_type.get('Is_Directed', 0),
                'description': rel.get('Description'),
                'is_visible': True
            })
        return {'nodes': nodes, 'edges': edges}

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

    @receiver(Events.LOOKUP_REQUESTED)
    def lookup_entity_content_by_name(self, data: dict) -> tuple[str, str, str] | None:
        """
        Sequentially looks up an entity by name/title across all relevant repositories.
        
        The lookup order (Character -> Lore -> Chapter) is strategic: characters and 
        lore entries are usually more unique and concise than chapter titles.

        :param name: The highlighted text string (e.g., "Sir Kaelan").
        :type name: str

        :returns: A tuple (EntityType, Title, Content) or None if not found.
        :rtype: tuple[str, str, str]
        """

        name = data['selected_text'].strip()
        if not name: return

        # Start Searching For Characters
        if hasattr(self, 'character_repo'):
            char_data = self.character_repo.get_content_by_name(name=name)
            if char_data and char_data.get('Description'): # Check if match exists
                bus.publish(Events.LOOKUP_RESULT, data={
                    'entity_type': EntityType.CHARACTER,
                    'title': char_data.get('Name', name),
                    'content': char_data.get('Description', '')
                })
                return
            
        # Search Through Lore Entries
        if hasattr(self, 'lore_repo'):
            lore_data = self.lore_repo.get_content_by_title(title=name)
            if lore_data and lore_data.get('Content'):
                bus.publish(Events.LOOKUP_RESULT, data={
                    'entity_type': EntityType.LORE,
                    'title': lore_data.get('Title', name),
                    'content': lore_data.get('Content', '')
                })
                return
            
        return
            
    
    # --- Project Stats ---
    
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