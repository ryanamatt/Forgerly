# src/python/utils/constants.py

from enum import IntEnum

class ViewType(IntEnum):
    """
    Defines integer constants representing the primary views or editors in the application.
    
    This is used for state tracking, menu toggling, and switching between panels.
    """
    CHAPTER_EDITOR = 1
    """The main text editor for Chapter content."""
    LORE_EDITOR = 2
    """The editor panel for Lore Entry details."""
    CHARACTER_EDITOR = 3
    """The editor panel for Character details."""
    NOTE_EDITOR = 4
    """The editor panel for Note Content"""
    RELATIONSHIP_GRAPH = 5
    """The graphical view for character relationships."""

class EntityType:
    """
    Defines string constants for the data entities that can be looked up or linked.
    """
    CHAPTER = "Chapter"
    """The Chapter Entity"""
    
    LORE = "Lore Entry"
    """The Lore Entry Entity"""

    CHARACTER = "Character"
    """The Character Entity"""

    Note = "Note"
    """The Note Entity"""

    RELATIONSHIP = "Relationship"
    """The Relationship Entity"""

class ExportType:
    """
    Defines string constants for the categories of content that can be exported 
    via the :py:class:`~app.ui.dialogs.ExporterDialog`.
    """
    STORY = "Story (All Chapters)"
    """Export the entire story, including all chapters."""
    CHAPTERS = "Selected Chapters"
    """Export a user-selected subset of chapters."""
    LORE = "Selected Lore Entries"
    """Export a user-selected subset of lore items."""
    CHARACTERS = "Selected Characters"
    """Export a user-selected subset of characters."""

class FileFormats:
    """Defines the supported file extensions for Import/Export operations."""

    HTML = ".html"
    """HyperText Markup Language format."""
    MARKDOWN = ".md"
    """Markdown text format."""
    PLAIN_TEXT = ".txt"
    """Simple plain text format."""
    EPUB = ".epub"
    """Electronic Publication format (standard e-book format)."""
    PDF = ".pdf"
    """Portable Document Format."""

    JSON = ".json"
    """JavaScript Object Notation format."""
    YAML = ".yaml"
    """YAML Ain't Markup Language format."""

    STRUCTURED_FORMATS = [JSON, YAML]
    """A list of all supported structured data/backup formats."""

    PRESENTATION_FORMATS = [HTML, MARKDOWN, PLAIN_TEXT, EPUB, PDF]
    """A list of all supported human-readable/presentation export formats."""

    ALL = PRESENTATION_FORMATS + STRUCTURED_FORMATS
    """A comprehensive list of all supported import/export formats."""

# Helper function for generating PyQt file filter strings
def generate_file_filter(formats: list[str]) -> str:
    """
    Generates a file filter string suitable for use with PyQt's :py:class:`~PyQt6.QtWidgets.QFileDialog`.
    
    Example output for ['.md', '.txt'] is 'Markdown (*.md);;Plain Text (*.txt)'.

    :param formats: A list of file extension strings (e.g., ['.json', '.yaml']).
    :type formats: list[str]
    
    :returns: A PyQt-compatible file filter string.
    :rtype: str
    """
    filters = []
    for ext in formats:
        # Example: "HTML Documents (*.html)"
        name = ext.strip('.').upper()
        filters.append(f"{name} Documents (*{ext})")
    
    return ";;".join(filters)