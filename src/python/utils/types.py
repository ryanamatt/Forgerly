# src/python/utils/types.py

from typing import TypedDict, List, Tuple, Dict, Any

# Type Alias for a list of generic dictionary results (used frequently for SELECT * or partial data)
DBRow = Dict[str, Any]
DBRowList = List[DBRow]

# --- Chapter Repository Types ---

# TypedDict for the full details of a Chapter
class ChapterContentDict(TypedDict):
    """Represents a full chapter row from the Database"""
    ID: int
    Title: str
    Text_Content: str
    Sort_Order: int
    Precursor_Chapter_ID: int | None

# TypedDict for basic chapter info (Used by get_all_chapters)
class ChapterBasicDict(TypedDict):
    """Represents a basic chapter row from the DB."""
    ID: int
    Title: str
    Sort_Order: int
    Precursor_Chapter_ID: int | None

# --- Lore Repository Types ---

# TypedDict for the full details of a Lore Entry (Used by get_lore_entry_details)
class LoreEntryDict(TypedDict):
    """Represents a full Lore_Entry row from the DB."""
    ID: int
    Title: str
    Content: str
    Category: str
    Parent_Lore_ID: int | None

# TypedDict for a lore search result (Used by search_lore_entries)
class LoreSearchResultDict(TypedDict):
    """Represents a single row from a Lore search result."""
    ID: int
    Title: str
    Category: str
    final_rank: int

# --- Character Repository Types ---

# TypedDict for the full details of a Character (Used by get_character_details)
class CharacterDetailsDict(TypedDict):
    """Represents a full Character row from the DB."""
    ID: int
    Name: str
    Description: str # Assuming this is a rich text or long text field
    Status: str      # e.g., 'Main', 'Supporting', 'Deceased'
    
# TypedDict for a character outline list item (Used by get_all_characters)
class CharacterBasicDict(TypedDict):
    """Represents a basic character row from the DB."""
    ID: int
    Name: str
    Status: str # Status might be useful for icon/sorting in the outline

# --- Tag Repository Types ---

# Type Alias for the (ID, Name) tuple returned by tag repository methods
TagTuple = Tuple[int, str]
TagTupleList = List[TagTuple]