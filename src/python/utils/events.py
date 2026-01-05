# src/python/utils/event_bus.py

from enum import Enum

class Events(str, Enum):
    """
    Centralized registry of all application event topics.
    Using string enum provides both type safety and string compatibility.
    """
    
    # View/Navigation Events
    VIEW_SWITCH_REQUESTED = "view.switch_requested"
    VIEW_CHANGED = "view.changed"

    # Content/Selection
    CONTENT_CHANGED = "editor.content_changed"
    SELECTION_CHANGED = "editor.selection_changed"
    
    # Save/Load Events
    SAVE_REQUESTED = "save.requested"
    SAVE_DATA_PROVIDED = "save.data_provided"
    NO_CHECK_SAVE_DATA_PROVIDED = "save.no_check_save_data_provided"
    LOAD_REQUESTED = "load.requested"
    CHECK_SAVE = "save.check"
    DATA_LOADED = "data.loaded"
    MARK_SAVED = "save.mark_saved"

    # OutlineManager
    OUTLINE_NAME_CHANGE = "outline.name_change"
    OUTLINE_LOAD_REQUESTED = "outline.load_requested"
    OUTLINE_DATA_LOADED = "outline.data_loaded"
    OUTLINE_REORDER = "outline.reorder"
    OUTLINE_SEARCH_REQUESTED = "outline.search_request"
    OUTLINE_SEARCH_RETURN= "outline.search_recturn"
    OUTLINE_PARENT_UPDATE = "outline.parent_update"
    
    # Item Creation Events
    NEW_ITEM_REQUESTED = "item.new_requested"
    NEW_ITEM_CREATED = "item.new_created"
    
    NEW_CHAPTER_REQUESTED = "item.chapter_new_requested"
    NEW_LORE_REQUESTED = "item.lore_new_requested"
    NEW_CHARACTER_REQUESTED = "item.character_new_requested"
    NEW_NOTE_REQUESTED = "item.note_new_requested"

    # Item Deletion
    ITEM_DELETE_REQUESTED = "item.delete_requested"
    
    # Item Selection Events
    ITEM_SELECTED = "item.selected"
    PRE_ITEM_CHANGE = "item.pre_change"
    
    # Lookup Events
    LOOKUP_REQUESTED = "lookup.requested"
    LOOKUP_RESULT = "lookup.result"
    
    # Lore Category Events
    LORE_CATEGORIES_CHANGED = "lore.categories_changed"
    LORE_CATEGORIES_REFRESH = "lore.categories_refresh"
    
    # Relationship Graph Events
    GRAPH_LOAD_REQUESTED = "graph.load_requested"
    GRAPH_DATA_LOADED = "graph.data_loaded"
    GRAPH_EDGE_VISIBILITY_CHANGED = "graph.edge_visibility_changed"
    GRAPH_NODE_VISIBILTY_CHANGED = "graph.node_visibility_changed"
    GRAPH_NODE_LOCKED_CHANGED = "graph.node_locked_changed"
    GRAPH_NODE_LOCKED_BULK_CHANGED = "graph.node_locked_bulk_changed"

    NODE_SAVE_REQUESTED = "graph.node_save"
    REL_TYPES_REQUESTED = "graph.rel_types_requested"
    REL_TYPES_RECEIVED = "graph.rel_types_received"
    REL_TYPE_DETAILS_REQUESTED = "graph.rel_type_details_requested"
    REL_TYPE_DETAILS_RETURN = "graph.rel_types_details_return"
    REL_CHAR_DATA_REQUESTED = "graph.rel_char_data_requested"
    REL_CHAR_DATA_RETURN = "graph.rel_char_data_return"

    REL_CREATE_REQUESTED = "graph.rel_create"
    REL_UPDATE_REQUESTED = "graph.rel_update"
    REL_DELETE_REQUESTED = "graph.rel_delete"
    REL_DETAILS_REQUESTED = "graph.rel_details_requested"
    REL_DETAILS_RETURN = "graph._rel_details_return"
    
    # Export Events
    EXPORT_REQUESTED = "export.requested"
    
    # Settings Events
    SETTINGS_REQUESTED = "settings.requested"
    SETTINGS_CHANGED = "settings.changed"
    WPM_CHANGED = "settings.wpm_changed"
    
    # Project Events
    PROJECT_NEW_REQUESTED = "project.new_requested"
    PROJECT_OPEN_REQUESTED = "project.open_requested"
    PROJECT_STATS_REQUESTED = "project.stats_requested"