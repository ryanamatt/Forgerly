# src/python/utils/constants.py

# Enum-Like class for view state clarity (Used by both MainWindow and AppCoordinator)
class ViewType:
    CHAPTER_EDITOR = 1
    LORE_EDITOR = 2
    CHARACTER_EDITOR = 3
    RELATIONSHIP_GRAPH = 4

# All Types of content that can be exported
class ExportType:
    STORY = "Story (All Chapters)"
    CHAPTERS = "Selected Chapters"
    LORE = "Selected Lore Entries"
    CHARACTERS = "Selected Characters"

# A set of supported file extensions
class FileFormats:
    """Defines the supported file formats for Import/Export operations."""

    # Text/Reading Formats
    HTML = ".html"
    MARKDOWN = ".md"
    PLAIN_TEXT = ".txt"
    EPUB = ".epub"
    PDF = ".pdf"

    # Structured Data/Backup Formats
    JSON = ".json"
    YAML = ".yaml"

    # List of all Structured Formats
    STRUCTURED_FORMATS = [JSON, YAML]

    # List of all human-readable/presentation formats
    PRESENTATION_FORMATS = [HTML, MARKDOWN, PLAIN_TEXT, EPUB, PDF]

    # List of all Suppored Formats
    ALL = PRESENTATION_FORMATS + STRUCTURED_FORMATS

# Helper function for generating PyQt file filter strings
def generate_file_filter(formats: list[str]) -> str:
    """Generates a QFileDialog filter string from a list of extensions."""
    filters = []
    for ext in formats:
        # Example: "HTML Documents (*.html)"
        name = ext.strip('.').upper()
        filters.append(f"{name} Documents (*{ext})")
    
    return ";;".join(filters)