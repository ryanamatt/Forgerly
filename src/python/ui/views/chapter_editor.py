# src/python/ui/chapter_editor.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QSplitter, QHBoxLayout
)
from PyQt6.QtCore import Qt

from ...ui.widgets.tag_widget import TagManagerWidget
from ...ui.widgets.rich_text_editor import RichTextEditor

def calculate_word_count(text: str) -> int:
    """Calculates the word count of the plain text content."""
    # Use split() without arguments to handle various whitespace separators
    words = text.split()
    return len(words)

def calculate_character_count(text: str, include_spaces: bool = True) -> int:
    """Calculates the character count."""
    if include_spaces:
        return len(text)
    else:
        return len("".join(text.split())) # Counts characters excluding all whitespace

def calculate_read_time(word_count: int, wpm: int = 250) -> str:
    """Calculates the estimated read time and formats it as 'X min'."""
    if wpm <= 0 or word_count == 0:
        return "0 min"
    
    # Calculate time in minutes (round up to nearest whole minute)
    minutes = (word_count + wpm - 1) // wpm # Integer division equivalent of ceil(word_count / wpm)
    
    # Handle hours/minutes if needed, but for simplicity, stick to minutes
    if minutes == 0:
        # If words > 0 but time is less than 1 min, show '<1 min'
        return "<1 min" if word_count > 0 else "0 min"
    
    return f"{minutes} min"

class ChapterEditor(QWidget):
    """
    A composite QWidget that serves as the main editing panel for a chapter.
    It combines the RichTextEditor for content and the TagManagerWidget for metadata.
    
    This component manages the state and provides a single interface for the 
    MainWindow to load and save all chapter data (content and tags).
    """
    
    def __init__(self, current_settings, parent=None) -> None:
        super().__init__(parent)
        self.wpm = current_settings['words_per_minute']

        # --- Sub-components ---
        self.rich_text_editor = RichTextEditor()
        self.tag_manager = TagManagerWidget()
        
        # --- Statistics Labels (New Components) ---
        self.word_count_label = QLabel("Words: 0")
        self.char_count_label = QLabel("Chars: 0")
        self.read_time_label = QLabel(f"Read Time: 0 min (WPM: {self.wpm})")

        # --- Layout ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 1. Tagging Group Box (Existing Code)
        tag_group = QGroupBox("Chapter Tags (Genres, Themes, POVs)")
        tag_layout = QVBoxLayout(tag_group)
        tag_layout.setContentsMargins(10, 20, 10, 10)
        tag_layout.addWidget(self.tag_manager)
        
        # 2. Editor and Stats (Modified Layout)
        
        # Statistics Bar at the bottom of the editor
        stats_bar = QWidget()
        stats_layout = QHBoxLayout(stats_bar)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.addWidget(self.word_count_label)
        stats_layout.addWidget(self.char_count_label)
        stats_layout.addWidget(self.read_time_label)
        stats_layout.addStretch() # Push stats to the left
        
        # Combine the editor and the stats bar
        editor_group = QWidget()
        editor_vbox = QVBoxLayout(editor_group)
        editor_vbox.setContentsMargins(0, 0, 0, 0)
        editor_vbox.addWidget(stats_bar)
        editor_vbox.addWidget(self.rich_text_editor)
        
        editor_splitter = QSplitter(Qt.Orientation.Vertical)
        editor_splitter.addWidget(tag_group) # Use the new group containing stats bar
        editor_splitter.addWidget(editor_group)
        editor_splitter.setSizes([100, 900]) 

        # Add the splitter to the main layout
        main_layout.addWidget(editor_splitter)

        # --- Signal Connections ---
        self.rich_text_editor.content_changed.connect(self._update_stats_display)
        self.rich_text_editor.selection_changed.connect(self._update_stats_display)

    def _update_stats_display(self) -> None:
        """
        Calculates and updates the real-time statistics labels based on 
        the selected text or the full content if no text is selected.
        """
        # 1. Check for selected text first
        selected_text = self.rich_text_editor.get_selected_text()
        
        if selected_text:
            # Stats for SELECTED text
            source_text = selected_text
            label_prefix = "Selected"
        else:
            # Stats for FULL document
            source_text = self.rich_text_editor.get_plain_text()
            label_prefix = "Total"

        # 2. Calculate statistics
        word_count = calculate_word_count(source_text)
        char_count_with_spaces = calculate_character_count(source_text, include_spaces=True)
        read_time_str = calculate_read_time(word_count, self.wpm)

        # 3. Update UI Labels with dynamic prefix
        self.word_count_label.setText(f"{label_prefix} Words: {word_count:,}")
        self.char_count_label.setText(f"{label_prefix} Chars: {char_count_with_spaces:,}")
        self.read_time_label.setText(f"Read Time: {read_time_str} (WPM: {self.wpm})")

    def set_wpm(self, new_wpm: int) -> None:
        """Updates the WPM setting and recalculates the statistics display.
        
        Args:
            new_wpm: The new wpm int number to set wpm to.
        """
        if new_wpm <= 0:
            new_wpm = 250
        self.wpm = new_wpm
        self._update_stats_display

    def _handle_tag_change(self):
        """Sets the rich text editor's dirty flag when tags are modified."""
        self.rich_text_editor._set_dirty()
        
    # --- Content Passthrough Methods (RichTextEditor) ---
    
    def is_dirty(self) -> bool:
        """Checks if the content or the tags have unsaved changes."""
        return self.rich_text_editor.is_dirty() or self.tag_manager.is_dirty()

    def mark_saved(self) -> None:
        """Marks both content and tags as clean."""
        self.rich_text_editor.mark_saved()
        self.tag_manager.mark_saved()
        
    def set_enabled(self, enabled: bool) -> None:
        """Enables/disables the entire chapter editor panel."""
        self.rich_text_editor.setEnabled(enabled)
        self.tag_manager.setEnabled(enabled)

    def get_html_content(self) -> str:
        """Returns the current rich text content."""
        return self.rich_text_editor.get_html_content()

    def set_html_content(self, html_content: str) -> None:
        """Sets the rich text content."""
        self.rich_text_editor.set_html_content(html_content)
        self._update_stats_display()

    # --- Tagging Passthrough Methods (TagManagerWidget) ---
    
    def get_tags(self) -> list[str]:
        """Returns the current list of tag names."""
        return self.tag_manager.get_tags()

    def set_tags(self, tag_names: list[str]) -> None:
        """Sets the tags when a chapter is loaded."""
        # This function also clears the tag manager's dirty state internally
        self.tag_manager.set_tags(tag_names)

