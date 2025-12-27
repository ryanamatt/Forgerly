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
    
    # Save/Load Events
    SAVE_REQUESTED = "save.requested"
    LOAD_REQUESTED = "load.requested"
    CHECK_SAVE = "save.check"
    DATA_LOADED = "data.loaded"
    
    # Item Creation Events
    NEW_CHAPTER_REQUESTED = "chapter.new_requested"
    NEW_LORE_REQUESTED = "lore.new_requested"
    NEW_CHARACTER_REQUESTED = "character.new_requested"
    NEW_NOTE_REQUESTED = "note.new_requested"
    NEW_ITEM_CREATED = "item.new_created"
    
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
    NODE_SAVE_REQUESTED = "graph.node_save"
    REL_TYPES_REQUESTED = "graph.rel_types_requested"
    REL_TYPES_RECEIVED = "graph.rel_types_received"
    REL_CREATE_REQUESTED = "graph.rel_create"
    REL_DELETE_REQUESTED = "graph.rel_delete"
    
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