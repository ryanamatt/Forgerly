# src/python/services/app_coordinator.py

import os
import sys
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMessageBox

from ..db_connector import DBConnector
from ..repository.chapter_repository import ChapterRepository
from ..repository.lore_repository import LoreRepository
from ..repository.tag_repository import TagRepository
from ..repository.character_repository import CharacterRepository
from ..repository.note_repository import NoteRepository
from ..repository.relationship_repository import RelationshipRepository

from ..utils.text_stats import calculate_read_time
from ..utils.spell_checker import get_spell_checker
from ..utils.resource_path import get_resource_path
from ..utils.constants import ViewType, EntityType, ExportType
from ..utils.logger import get_logger
from ..utils.events import Events
from ..utils.event_bus import bus, receiver

logger = get_logger(__name__)

class AppCoordinator(QObject):
    """
    Coordinates the data logic from the repository classes.
    
    This class acts as the central hub for all application events that involve 
    data retrieval or persistence, ensuring that UI components only interact 
    with each other via event bus, and interact with the database only via this coordinator.
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

        # Initialize Spell Checker
        self.spell_checker = get_spell_checker()
        self._initialize_spell_checker()

        # State Tracking
        self.current_item_id: int = 0
        self.current_entity_type: EntityType = EntityType.CHAPTER

    @receiver(Events.APP_SHUTDOWN_INITIATED)
    def disconnect_from_bus(self, data: dict) -> None:
        """
        Unregisters this instance from the event bus to prevent zombie calls.
        
        :param data: An Empty dict, not needed for this function.
        :type data: dict
        :rtype: None
        """
        bus.unregister_instance(self)
        logger.info("AppCoordinator unregistered from Event Bus.")

    @receiver(Events.DATA_LOADED)
    def set_state_tracking(self, data: dict) -> None:
        """
        Sets the current state of ID and EntityType.
        
        :param data: The data needed to set the state variables containing
            {'entity_type': EntityType, 'ID': int}
        :type data: dict
        :rtype: None
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
        
        :param data: Handles the PRE_ITEM_CHANGE event by asking for a save
            of the current items by calling SAVE_REQUESTED event.
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
        
        :param data: The data needed to help save including {'ID': int, 'parent': QWidget=None,
            'entity_type': EntityType, 'tags': list[str]}
        :type data: dict
        :rtype: None
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
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | 
            QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Save
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
        :returns: Returns the True if successfully created and saved new relationship.
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
        
    @receiver(Events.REL_CHAR_DETAILS_SAVE)
    def save_character_node_detials(self, data: dict) -> None:
        """
        Saves the Character Node Details to the database.
        
        :param data: dict containing {'ID': int, 'Node_Color': str, 'Node_Shape': str, 
            'Is_Hidden': bool, 'Is_Locked', bool}
        :type data: dict
        :rtype: None
        """
        id = data.pop('ID')
        self.relationship_repo.save_node_details(character_id=id, **data)
    
    @receiver(Events.GRAPH_NODE_VISIBILTY_CHANGED)
    def save_character_node_is_hidden(self, data: dict) -> None:
        """
        Saves the status of a change is_hidden attribute.
        
        :param data: A dictionary of the data containing {'ID': int,
            'is_hidden': bool}
        :type data: dict
        :rtype: None
        """
        self.relationship_repo.update_node_is_hidden(char_id=data.get('ID'), 
                                                     is_hidden=data.get('is_hidden'))

    @receiver(Events.GRAPH_NODE_LOCKED_CHANGED)
    def save_character_node_is_locked(self, data: dict) -> None:
        """
        Saves the status of a change is_locked attribute.
        
        :param data: A dictionary of the data containing {'ID': int,
            'is_locked': bool}
        :type data: dict
        :rtype: None
        """
        self.relationship_repo.update_node_is_locked(char_id=data.get('ID'), 
                                                     is_locked=data.get('is_locked'))
        
    @receiver(Events.GRAPH_NODE_LOCKED_BULK_CHANGED)
    def save_character_node_bulk_is_locked(self, data: dict) -> None:
        """
        Saves the status of a change is_locked attribute.
        
        :param data: A dictionary of the data containing {'ID': int,
            'is_locked': bool}
        :type data: dict
        :rtype: None
        """
        self.relationship_repo.update_node_bulk_is_locked(**data)

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
        character_nodes = self.relationship_repo.get_all_node_positions()

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
                title = self.lore_repo.get_lore_entry_title(lore_id=id)
                self._add_custom_word(title)

            case EntityType.CHARACTER:
                id = self.character_repo.create_character(data.get('title'))
                name = self.character_repo.get_character_name(char_id=id)
                self._add_custom_word(name)

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
                    title = self.lore_repo.get_lore_entry_title(lore_id=id)
                    self._remove_custom_word(word=title)
                    self.lore_repo.delete_lore_entry(id)

                case EntityType.CHARACTER:
                    name = self.character_repo.get_character_name(char_id=id)
                    self._remove_custom_word(word=name)
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
        :rtype: None
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
    
    @receiver(Events.LORE_CATEGORIES_REFRESH)
    def refresh_lore_categories(self, data: dict) -> None:
        """
        Fetches unique categories and notifies the Lore Editor.

        :param data: An empty dict. Not needed for this function but for when recieving event bus event.
        :type data: dict
        :rtype: None
        """
        categories = self.lore_repo.get_unique_categories()
        bus.publish(Events.LORE_CATEGORIES_CHANGED, data={'categories': categories})
    
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
        required for the graph editor. At the end calls GRAPH_DATA_LOADED event with
        the graph data.

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
        
        :param data: The data needed containing the relationship id with Key ID.
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
        
        :param data: The data needed containing the relationship type ID with key 'ID'.
        :type data: dict
        :rtype: None
        """
        data |= self.relationship_repo.get_relationship_type_details(data.get('ID'))
        bus.publish(Events.REL_TYPE_DETAILS_RETURN, data=data)
        
    @receiver(Events.REL_DELETE_REQUESTED)
    def handle_relationship_deletion(self, data: dict) -> None:
        """
        Handles the deletion of a relationship from the database.
        
        :param data: Dictionary containing {ID: int}
        :type data: dict
        :rtype: None
        """
        self.relationship_repo.delete_relationship(data.get('ID'))
        self.load_relationship_graph_data()

    @receiver(Events.REL_CHAR_DETAILS_REQUESTED)
    def hande_char_node_details(self, data: dict) -> None:
        """
        Retrieves the character Node details and calls the event REL_CHAR_DETAILS_RETURN.
        
        :param data: The data needed to update containing the character ID: {'ID': int}
        :type data: dict
        :rtype: None
        """
        id = data.get('ID')
        data |= self.relationship_repo.get_node_details(char_id=id)
        data.update({'Name': self.character_repo.get_character_name(char_id=id)})
        bus.publish(Events.REL_CHAR_DETAILS_RETURN, data=data)

    def _process_graph_data(self, relationships: list[dict], node_positions: list[dict], 
                            relationship_types: list[dict]) -> dict:
        """
        Proceess all the graph data. It takes in the relationships, node_positions, relationship_types
        and creates the nodes data and edges data to be returned as a dict.
        
        :param relationships: A list of relationships with the relationship attributes a dict.
        :type relationships: list[dict]
        :param node_positions: The postition of the nodes (characters)
        :type node_positions: list[dict]
        :param relationship_types: A list of the types of relationships with the relationship_types
            attributes as dict.
        :type relationship_types: list[dict]
        :return: Returns a dict of nodes and edges. {'nodes': nodes, 'edges': edges}
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

    # --- Export Logic ---

    @receiver(Events.EXPORT_DATA_REQUESTED)
    def get_data_for_export(self, data: dict) -> None:
        """
        Gets all the Data for the export and emits the EXPORT_DATA_RETURN event with the
            export data.
        
        :param data: The data needed containg {'export_type: ExportType, selected_ids: list[int]}
        :type data: dict
        :rtype: None
        """
        export_type = data.get('export_type')
        selected_ids = data.pop('selected_ids', None)

        match export_type:
            case ExportType.CHAPTERS:
                return_data = self.chapter_repo.get_all_chapters_for_export(selected_ids)
                results_name = 'chapters'
            case ExportType.LORE:
                return_data = self.lore_repo.get_lore_entries_for_export(selected_ids)
                results_name = 'lore_entries'
            case ExportType.CHARACTERS:
                return_data = self.character_repo.get_all_characters_for_export(selected_ids)
                results_name = 'characters'
        
        data.update({results_name: return_data})
        
        bus.publish(Events.EXPORT_DATA_RETURN, data=data)

    @receiver(Events.EXPORT_LIST_REQUESTED)
    def get_export_list(self, data: dict) -> None:
        """
        Gets the exports needed to list what to export.
        
        :param data: The data needed containing {'entity_type': EntityType}
        :type data: dict
        :rtype: None
        """
        export_type = data.get('export_type')

        match export_type:
            case ExportType.CHAPTERS:
                return_data = self.chapter_repo.get_all_chapters()
                results_name = 'chapters'
            case ExportType.LORE:
                return_data = self.lore_repo.get_all_lore_entries()
                results_name = 'lore_entries'
            case ExportType.CHARACTERS:
                return_data = self.character_repo.get_all_characters()
                results_name = 'characters'

        bus.publish(Events.EXPORT_LIST_RETURN, data = {
            'export_type': export_type, results_name: return_data
        })
    
    # -----------------------------------
    # Entity Lookup Methods
    #------------------------------------

    @receiver(Events.PERFORM_DATABASE_LOOKUP)
    def lookup_entity_content_by_name(self, data: dict) -> tuple[str, str, str] | None:
        """
        Sequentially looks up an entity by name/title across all relevant repositories.
        
        The lookup order (Character -> Lore -> Chapter) is strategic: characters and 
        lore entries are usually more unique and concise than chapter titles.

        :param data: A dict carrying {'selected text': str} 
            The highlighted text string (e.g., "Sir Kaelan").
        :type name: dict
        :returns: A tuple (EntityType, Title, Content) or None if not found.
        :rtype: tuple[str, str, str]
        """
        text = data.get('selected_text')
        if not text: return
            
        char_data = self.character_repo.get_content_by_name(name=text)
        lore_data = self.lore_repo.get_content_by_title(title=text)

        data = {}
        data.update({'char_data': char_data, 'lore_data': lore_data})
        bus.publish(Events.LOOKUP_RESULT, data=data)
            
    # --- Project Stats ---
    
    def get_project_stats(self, wpm: int) -> dict[str, str]:
        """
        A function to retrive the project stats from each of the repositories.
    
        :param wpm: The words per minute setting
        :type wpm: int
        :returns: A dictionary of the project statistics. {"total_word_count": str,
            "char_count_no_spaces": str, "read_time": str, "chapter_count": str,
            "lore_count": str, "character_count": str} 
        :rtype: dict[str,str]
        """
        chapter_stats = self.chapter_repo.get_all_chapters_stats()

        total_word_count, char_count_no_spaces = 0, 0
        for chapter in chapter_stats:
            total_word_count += chapter.get('word_count', 0)
            char_count_no_spaces += chapter.get('char_count_no_spaces', 0)

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
    
    # --- Spell Checker ---

    def _load_custom_dict_words(self) -> list[str]:
        """
        Gets the Name of Characters and Lore Entries from
        their respective repos and returns them to add to
        the custom Trie for spelling suggestions.
        
        :return: A list of the custom words to add to the custom Spell Checking Trie.
        :rtype: list[str]
        """
        results = []
        char_data = self.character_repo.get_all_character_names()
        lore_data = self.lore_repo.get_all_lore_entry_titles()

        results.extend(char_data)
        results.extend(lore_data)

        return results
    
    def _add_custom_word(self, word: str) -> None:
        """
        Adds a custom word into the Custom dictionary Trie.
        
        :param word: The word to add to the custom Trie.
        :type word: str
        :rtype: None
        """
        checker = get_spell_checker()
        checker.add_custom_word(word=word)

    def _remove_custom_word(self, word: str) -> None:
        """
        Removes a custom word from the Custom dictionary Trie.
        
        :param word: The word to remove from the custom Trie.
        :type word: str
        :rtype: None
        """
        checker = get_spell_checker()
        checker.remove_custom_word(word=word)

    def _initialize_spell_checker(self) -> None:
        """
        Loads the default dictionary file.
        
        :rtype: None
        """
        try:
            dict_path = get_resource_path(os.path.join('dictionaries', 'en_US.txt'))
            
            # Get the checker and load
            checker = get_spell_checker()
            words_loaded = checker.load_dictionary_from_file(dict_path)

            custom_words = self._load_custom_dict_words()
            checker.load_custom_words(custom_words)
            
            logger.info(f"Spell checker initialized with {words_loaded} words from {dict_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize spell checker: {e}", exc_info=True)
            # We don't raise here to allow the app to function without spellcheck