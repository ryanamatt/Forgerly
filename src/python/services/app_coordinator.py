# src/python/services/app_coordinator.py

from PyQt6.QtCore import QObject, pyqtSignal, QCoreApplication
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QTextDocument

from db_connector import DBConnector
from repository.chapter_repository import ChapterRepository
from repository.lore_repository import LoreRepository
from repository.tag_repository import TagRepository
from utils.constants import ViewType

from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from ui.views.chapter_editor import ChapterEditor
    from ui.views.lore_editor import LoreEditor

class AppCoordinator(QObject):
    """
    Coordinates data flow between the UI components (Outline/Editor) and the 
    database repositories. Centralizes save/load/dirty checking logic.
    """
    # --- Signals for Editor Panel Updates (Data OUT) ---
    chapter_loaded = pyqtSignal(int, str, list)      # id, content_html, tags
    lore_loaded = pyqtSignal(int, str, str, str, list) # id, title, category, content_html, tags
    
    # --- Signals for Outline Manager Updates (UI IN) ---
    lore_title_updated_in_outline = pyqtSignal(int, str)

    def __init__(self, db_connector: DBConnector) -> None:
        super().__init__()

        self.db = db_connector

        # Create Repositorys
        self.chapter_repo = ChapterRepository(self.db)
        self.lore_repo = LoreRepository(self.db)
        self.tag_repo = TagRepository(self.db)

        # State Tracking
        self.current_item_id = 0
        self.current_view = ViewType.CHAPTER

        # References to the active Outline/Editor panels (set by MainWindow)
        self.editors = {}
        # Keep for signal
        self.lore_editor = None

    # --- Save / Dirty Check Logic (Core Business Logic) ---

    def set_editors(self, editor_map: dict[ViewType, Any]) -> None:
        """
        Sets all editor references using a dictionary map where keys are ViewType constants.
        Example: {ViewType.CHAPTER: chapter_editor, ViewType.LORE: lore_editor}
        """
        self.editors = editor_map
        
        # Handle specific editor connections separately (like title change signals)
        if ViewType.LORE in self.editors:
            self.lore_editor: LoreEditor = self.editors[ViewType.LORE]
            # Connect the specific signal
            self.lore_editor.lore_title_changed.connect(self.lore_title_updated_in_outline)

    def set_current_view(self, view_type: ViewType) -> None:
        """Called by MainWindow when the view is explicitly switched."""
        self.current_view = view_type
        self.current_item_id = 0 # Reset current item id

    # --- Save / Dirty Check Logic (Core Business Logic) ---

    def get_current_editor(self):
        """Helper to get the currently visible editor panel"""
        return self.editors.get(self.current_view)

    def check_and_save_dirty(self, parent=None) -> bool:
        """
        Prompts the user to save if the active editor is dirty.
        Returns True if safe to proceed (saved or discarded), False otherwise (canceled).
        """
        if self.current_item_id == 0:
            return True # No item loeaded
        
        editor_panel = self.get_current_editor()
        if not editor_panel or not editor_panel.is_dirty():
            return True # Editor is clean
        
        item_type = 'Chapter' if self.current_view == ViewType.CHAPTER else 'Lore Entry'
        save_reply = QMessageBox.question(
            parent, # Use parent for dialog centering
            "Unsaved Changes",
            f"The current {item_type} has unsaved changes. Do you want to save before continuing?",
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
        if item_id <= 0:
            return False
        
        match view:
            case ViewType.CHAPTER:
                return self._save_chapter_content(item_id, parent)
            
            case ViewType.LORE:
                return self._save_lore_entry_content(item_id, parent)
            
            case _:
                return False
            
    def _save_chapter_content(self, chapter_id: int, parent) -> bool:
        """Saves the current chapter content and tags to the database"""
        editor: ChapterEditor = self.editors[ViewType.CHAPTER]
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

    def _save_lore_entry_content(self, lore_id: int, parent) -> bool:
        """Saves the current lore content and tags to the database"""
        editor: LoreEditor = self.lore_editor
        data = editor.get_data()
        
        title = data['title']
        category = data['category']
        content = data['content']
        tags = data['tags']

        content_saved = self.lore_repo.update_lore_entry(lore_id, title, category, content)
        tags_saved = self.tag_repo.set_tags_for_lore_entry(lore_id, tags)

        if content_saved and tags_saved:
            # Reload to reset the editor's internal state (dirtiness tracking)
            editor.load_lore(lore_id, title, category, content, tags) 
            editor.mark_saved()
            return True
        else:
            QMessageBox.critical(parent, "Save Failed", f"Failed to save Lore Entry ID {lore_id}.")
            return False
        
    # --- Load Content Logic (Called by Outline Managers) ---

    def load_chapter(self, chapter_id: int) -> None:
        """Loads chapter data and emits a signal to update the editor."""
        
        # 1. Update Coordinator State
        self.current_item_id = chapter_id
        self.current_view = ViewType.CHAPTER

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
        self.current_view = ViewType.LORE

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

    # --- Cross-Update Logic ---

    def update_lore_outline_title(self, lore_id: int, new_title: str) -> None:
        """
        Receives title change from LoreEditor and relays it to the LoreOutlineManager.
        Note: The editor is responsible for setting the item as dirty,
        and the save logic handles persisting the new title to the DB.
        """
        self.lore_title_updated_in_outline.emit(lore_id, new_title)

    # --- Export Logic Helper (For use by the new StoryExporter class) ---
    
    def get_chapter_data_for_export(self):
        """Fetches all chapter data needed for export."""
        return self.chapter_repo.get_all_chapters_with_content()