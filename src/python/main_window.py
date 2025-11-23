# Main Application Window: src/python/main_window.py

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QSplitter, QMessageBox, QFileDialog, QDialog,
    QWidget, QVBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent, QAction, QTextDocument, QIcon
import os
import ctypes

from ui.chapter_outline_manager import ChapterOutlineManager
from ui.chapter_editor import ChapterEditor
from ui.lore_outline_manager import LoreOutlineManager
from ui.lore_editor import LoreEditor
from ui.settings_dialog import SettingsDialog

from db_connector import DBConnector

from repository.chapter_repository import ChapterRepository
from repository.lore_repository import LoreRepository
from repository.tag_repository import TagRepository

from settings_manager import SettingsManager

from _version import __version__

# Enum-Like class for view state clarity
class ViewType:
    CHAPTER = 1
    LORE = 2

class MainWindow(QMainWindow):
    """
    The Main Window for The Narrative Forge application.
    Sets up the core layout: Outline Manager on the left, Editor on the right.
    Uses a stack-like approach for view management.
    """
    def __init__(self) -> None:
        super().__init__()

        # This is a workaround to allow the taskbar to have the same icon as the window icon
        appID = f"narrative-forge.{__version__}"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appID)

        self.setWindowTitle(f"The Narrative Forge v{__version__}")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon(os.path.join('assets', 'logo.ico')))

        # Initialize DB Connector
        self.db_connector = DBConnector() 
        if self.db_connector.connect():
            # Ensure the database is initialized on app startup
            self.db_connector.initialize_schema() 
            print("Application database setup verified.")
        else:
            print("FATAL: Could not connect to database.")

        # --- Initialize Repositories ---
        self.chapter_repo = ChapterRepository(self.db_connector)
        self.lore_repo = LoreRepository(self.db_connector)
        self.tag_repo = TagRepository(self.db_connector)

        # --- Settings and Theme Management ---
        self.settings_manager = SettingsManager()
        self.current_settings = self.settings_manager.load_settings()
        self._apply_theme(self.current_settings)

        # State tracking for the currently loaded item (Chapter or Lore)
        self.current_item_id = 0
        self.current_view = ViewType.CHAPTER

        self._setup_ui()

        self._setup_menu_bar()

        self._connect_components()

        # Initially set the view to Chapters
        self._switch_to_view(ViewType.CHAPTER)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handles closing the database connection when the application exits."""

        # Check for unsaved changes before allowing app to close
        # Use the appropriate editor panel based on the current view
        current_editor = self._get_current_editor()
        
        if current_editor and current_editor.is_dirty():
            save_reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save them before exiting?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )

            if save_reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            
            if save_reply == QMessageBox.StandardButton.Save:
                # Attempt to save the current item
                if not self._save_current_item(self.current_item_id, self.current_view):
                    QMessageBox.critical(self, "Save Failed", "Failed to save the current item. Aborting exit.")
                    event.ignore()
                    return

        if self.db_connector:
            self.db_connector.close()
        super().closeEvent(event)

    def _setup_ui(self):
        """Setsup the central widget and the main split layout"""

        # 1. Create a QSplitter for the main content area (Outline | Editor)
        # This allows the user to resize the sections horizontally.
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- Left Panel: Outline Manager
        self.chapter_outline_manager = ChapterOutlineManager(chapter_repository=self.chapter_repo)
        self.lore_outline_manager = LoreOutlineManager(lore_repository=self.lore_repo)

        # Container for the outline managers (will hide/whow as needed)
        self.outline_container = QWidget()
        self.outline_container_layout = QVBoxLayout(self.outline_container)
        self.outline_container_layout.setContentsMargins(0, 0, 0, 0)
        self.outline_container_layout.addWidget(self.chapter_outline_manager)
        self.outline_container_layout.addWidget(self.lore_outline_manager)

        # --- Right Panel: Editors (Only one is shown at a time) ---
        self.chapter_editor_panel = ChapterEditor()
        self.lore_editor_panel = LoreEditor()

        # Container for the editors (will hide/show as needed)
        self.editor_container = QWidget()
        self.editor_container_layout = QVBoxLayout(self.editor_container)
        self.editor_container_layout.setContentsMargins(0, 0, 0, 0)
        self.editor_container_layout.addWidget(self.chapter_editor_panel)
        self.editor_container_layout.addWidget(self.lore_editor_panel)

        # Add the containers to the splitter
        self.main_splitter.addWidget(self.outline_container)
        self.main_splitter.addWidget(self.editor_container)

        # Set the initial ratio of the splitter (e.g., 1:3 ratio)
        self.main_splitter.setSizes([300, 900]) 

        # Set the splitter as the central widget
        self.setCentralWidget(self.main_splitter)
        
        # Add a placeholder status bar
        self.statusBar().showMessage("Ready to forge your narrative.")

    def _setup_menu_bar(self):
        """Creates the basic menu bar with placeholder items (File, Edit, Help)."""
        
        menu_bar = self.menuBar()
        
        # --- File Menu ---
        file_menu = menu_bar.addMenu("&File")
        
        # Action: New Chapter
        new_chapter_action = file_menu.addAction("New Chapter...")
        new_chapter_action.setStatusTip("Create a new chapter document")
        new_chapter_action.triggered.connect(self.chapter_outline_manager.prompt_and_add_chapter)

        # Action: New Lore Entry
        new_lore_action = file_menu.addAction("New Lore Entry...")
        new_lore_action.setStatusTip("Create a new lore entry")
        new_lore_action.triggered.connect(self.lore_outline_manager.prompt_and_add_lore)
        
        file_menu.addSeparator()

        # Action: Save Current Chapter
        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.setStatusTip("Save the current chapter content to the database")
        save_action.triggered.connect(lambda: self._save_current_item(self.current_item_id, self.current_view))
        file_menu.addAction(save_action)

        # Action Export Story (Only For Chapters)
        export_action = QAction("Export Story...", self)
        export_action.setShortcut("Ctrl+O")
        export_action.setStatusTip("Export the entire story (all chapters) to a single file")
        export_action.triggered.connect(self._export_story)
        file_menu.addAction(export_action)

        # Action: Exit
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+E")
        exit_action.setStatusTip("Exit the Application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # --- View Menu ---
        view_menu = menu_bar.addMenu("&View")

        # Action: Switch to Chapter View
        chapter_view_action = QAction("Chapter View", self)
        chapter_view_action.setStatusTip("Switch to Chapter Outline and Editor")
        chapter_view_action.triggered.connect(lambda: self._switch_to_view(ViewType.CHAPTER))
        view_menu.addAction(chapter_view_action)

        # Action: Switch to Lore View
        lore_view_action = QAction("Lore View", self)
        lore_view_action.setStatusTip("Switch to Lore Outline and Editor")
        lore_view_action.triggered.connect(lambda: self._switch_to_view(ViewType.LORE))
        view_menu.addAction(lore_view_action)
        
        # --- Edit Menu ---
        edit_menu = menu_bar.addMenu("&Edit")
        edit_menu.addAction("Undo")
        edit_menu.addAction("Redo")

        # --- Settings Menu ----
        settings_menu = menu_bar.addMenu("&Settings")

        # Settings Action
        settings_action = QAction("Open Settings...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.setStatusTip("Open application settings, including themes.")
        settings_action.triggered.connect(self._open_settings_dialog)
        settings_menu.addAction(settings_action)
        
        # --- Help Menu ---
        help_menu = menu_bar.addMenu("&Help")
        help_menu.addAction("About The Narrative Forge")

    def _connect_components(self) -> None:
        """Connects signals from custom widgets to slots in the main window."""
        
        # --- Chapter View Connections ---
        self.chapter_outline_manager.chapter_selected.connect(self._load_chapter_content)
        # Connect the pre-change signal to ensure content is saved if necessary
        self.chapter_outline_manager.pre_chapter_change.connect(self._check_save_before_change)
        
        # --- Lore View Connections ---
        self.lore_outline_manager.lore_selected.connect(self._load_lore_content)
        self.lore_outline_manager.pre_lore_change.connect(self._check_save_before_change)
        
        # Connect the editor title change back to the outline (only needed for Lore for now)
        self.lore_editor_panel.lore_title_changed.connect(self._update_lore_outline_title)

    def _get_current_editor(self) -> None:
        """Helper to get the currently visible editor panel."""
        match self.current_view:
            case ViewType.CHAPTER: return self.chapter_editor_panel

            case ViewType.LORE: return self.lore_editor_panel

            case _: return None

    def _switch_to_view(self, view: ViewType) -> None:
        """Switches between the Chapter and Lore View"""
        # Check for unsaved changes
        if not self._check_save_before_change():
            return
        
        # Update State
        self.current_view = view
        self.current_item_id = 0 # Reset current item id

        # Toggle Visibility
        is_chapter_view = (view == ViewType.CHAPTER)

        # Outline Managers
        self.chapter_outline_manager.setVisible(is_chapter_view)
        self.lore_outline_manager.setVisible(not is_chapter_view)

        # Editor Panels
        self.chapter_editor_panel.setVisible(is_chapter_view)
        self.lore_editor_panel.setVisible(not is_chapter_view)
        
        # 4. Disable the newly visible editor until an item is selected
        editor = self._get_current_editor()
        if editor:
            editor.set_enabled(False)

        self.statusBar().showMessage(f"Switched to {'Chapter' if is_chapter_view else 'Lore'} View.")

    def _check_save_before_change(self) -> bool:
        """
        Prompts the user to save if the active editor is dirty.
        Returns True if safe to proceed (saved or discarded), False otherwise.
        """
        editor_panel = self._get_current_editor()

        if self.current_item_id != 0 and editor_panel.is_dirty():
            save_reply = QMessageBox.question(
                self, 
                "Unsaved Changes",
                f"The current {'Chapter' if self.current_view == ViewType.CHAPTER else 'Lore Entry'} has unsaved changes. Do you want to save before continuing?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            
            if save_reply == QMessageBox.StandardButton.Cancel:
                # User cancels the operation (e.g., changing item/deleting)
                return False
            
            if save_reply == QMessageBox.StandardButton.Save:
                # Attempt to save
                return self._save_current_item(self.current_item_id, self.current_view) # Returns True/False based on save success
            
            # If Discard, return True (safe to proceed)
            return True
        
        # No item loaded or editor is clean
        return True
    
    def _save_current_item(self, item_id: int, view: ViewType) -> bool:
        """General Method to save either chapter or a lore entry."""
        if item_id <= 0:
            return
        
        match view:
            case ViewType.CHAPTER: return self._save_chapter(item_id)

            case ViewType.LORE: return self._save_lore_entry(item_id)

            case _: return False
    
    def _save_chapter(self, chapter_id: int) -> bool:
        """Saves the current content and tags to the database."""
        editor = self.chapter_editor_panel
        content = editor.get_html_content()
        tags = editor.get_tags()

        content_saved = self.chapter_repo.update_chapter_content(chapter_id, content)
        tags_saved = self.tag_repo.set_tags_for_chapter(chapter_id, tags)

        if content_saved and tags_saved:
            editor.mark_saved()
            self.statusBar().showMessage(f"Chapter ID {chapter_id} saved successfully.", 3000)
            return True
        else:
            self.statusBar().showMessage(f"ERROR: Failed to save Chapter ID {chapter_id}!", 5000)
            return False
        
    def _save_lore_entry(self, lore_id: int) -> bool:
        """Saves the current lore entry's data and tags to the database."""
        editor = self.lore_editor_panel
        data = editor.get_data()
        
        title = data['title']
        category = data['category']
        content = data['content']
        tags = data['tags'] # List of tag names

        content_saved = self.lore_repo.update_lore_entry(lore_id, title, category, content)
        tags_saved = self.tag_repo.set_tags_for_lore_entry(lore_id, tags)

        if content_saved and tags_saved:
            # Update the initial state in the editor so is_dirty() works correctly
            editor.load_lore(lore_id, title, category, content, tags) # Reload to reset state
            editor.mark_saved()
            self.statusBar().showMessage(f"Lore Entry ID {lore_id} saved successfully.", 3000)
            return True
        else:
            self.statusBar().showMessage(f"ERROR: Failed to save Lore Entry ID {lore_id}!", 5000)
            return False

    def _load_chapter_content(self, chapter_id: int) -> None:
        """
        Slot: Called when a chapter is selected in the outline.
        Loads content from the database and updates the editor.
        """
        
        self.current_item_id = chapter_id
        
        print(f"MainWindow loading content for Chapter ID: {chapter_id}...")
        
        # 1. Load Content (Handles content persistence / new chapter initialization)
        content = self.chapter_repo.get_chapter_content(chapter_id)
        
        if content is None:
            content = "<h1>Error Loading Chapter</h1><p>Content could not be retrieved from the database.</p>"
            self.chapter_editor_panel.set_html_content(content)
            self.chapter_editor_panel.setEnabled(False)
            self.statusBar().showMessage(f"Error loading Chapter ID {chapter_id}.")
        else:
            self.chapter_editor_panel.set_html_content(content)
            self.chapter_editor_panel.setEnabled(True)
            self.statusBar().showMessage(f"Chapter ID {chapter_id} selected and loaded.")

        # 2. Load Tags
        tags_data = self.tag_repo.get_tags_for_chapter(chapter_id)
        tag_names = [name for _, name in tags_data] if tags_data else []

        self.chapter_editor_panel.set_tags(tag_names)
        self.chapter_editor_panel.mark_saved() # Reset dirtiness after load

    def _load_lore_content(self, lore_id: int) -> None:
        """
        Slot: Called when a lore entry is selected in the outline.
        Loads content from the database and updates the editor.
        """
        self.current_item_id = lore_id

        print(f"MainWindow loading content for Lore ID: {lore_id}...")
        
        # 1. Load Lore Details (Title, Content, Category)
        lore_details = self.lore_repo.get_lore_entry_details(lore_id)
        
        if lore_details is None:
            self.lore_editor_panel.set_enabled(False)
            self.statusBar().showMessage(f"Error loading Lore ID {lore_id}.")
            return
        
        title = lore_details['Title']
        category = lore_details['Category']
        content = lore_details['Content']

        # 2. Load Tags
        tags_data = self.tag_repo.get_tags_for_lore_entry(lore_id) # Assuming new method exists
        tag_names = [name for _, name in tags_data] if tags_data else []
        
        # 3. Load all into the editor
        self.lore_editor_panel.load_lore(lore_id, title, category, content, tag_names)
        self.lore_editor_panel.set_enabled(True)
        self.statusBar().showMessage(f"Lore Entry ID {lore_id} selected and loaded.")

    def _update_lore_outline_title(self, lore_id: int, new_title: str) -> None:
        """Updates the title in the LoreOutlineManager when the editor title changes."""
        
        # Note: This is a direct update to the UI. The editor's change also flags the item as dirty,
        # which will trigger a save to the DB via _save_lore_entry on the next state change/save action.
        # This keeps the UI responsive.
        
        if self.current_view == ViewType.LORE:
            # Find the item and set the text
            item = self.lore_outline_manager.find_lore_item_by_id(lore_id)
            if item and item.text(0) != new_title:
                # Block signals to prevent _handle_item_renamed from firing back to the repo
                self.lore_outline_manager.blockSignals(True)
                item.setText(0, new_title)
                self.lore_outline_manager.blockSignals(False)

    def _export_story(self) -> None:
        """Prompts the user for a save location and exports the entire story content."""

        # 1. Check for unsaved changes before exporting
        if not self._check_save_before_change():
            return
        
        file_filers = (
            "Markdown Files (*.md);;"
            "HTML Files (*.html);;"
            "Plain Text Files (*.txt);;"
            "All Files (*)"
        )

        # 2. Get file save location from the user
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Story",
            "narrative_forge_export.md",
            file_filers
        )

        if not file_path:
            return
        
        # Determine the selected export format
        if "(*.html)" in selected_filter:
            file_format = "html"
        elif "(*.txt)" in selected_filter:
            file_format = "text"
        else:
            # Default to markdown, which is the first filter and handles *.md
            file_format = "markdown"
        
        self.statusBar().showMessage("Exporting Story... Please wait.")
        QApplication.processEvents()

        try:
            all_chapters_data = self.chapter_repo.get_all_chapters_with_content()

            if not all_chapters_data:
                QMessageBox.warning(self, "Export Failed", "No chapters found to export.")
                self.statusBar().showMessage("Export cancelled: No chapters found.")
                return
            
            # 2. Format and write the content based on the selected format
            with open(file_path, 'w', encoding='utf-8') as f:
                
                # --- HTML Header/Footer (Optional but good practice) ---
                if file_format == "html":
                    f.write("<!DOCTYPE html><html><head><title>Narrative Forge Export</title></head><body>\n")
                    f.write("<h1>The Narrative Forge Export</h1>\n")

                # --- Write Chapter Content ---
                for chapter in all_chapters_data:
                    title = chapter['Title']
                    sort_order = chapter['Sort_Order']
                    content = chapter['Text_Content']
                    
                    if file_format == "markdown":
                        # Markdown format (uses raw content which is HTML, so it may need cleanup,
                        # but works well for simple rich text converted to MD)
                        f.write(f"## Chapter {sort_order}: {title}\n\n")
                        f.write(f"{content}\n\n---\n\n")
                        
                    elif file_format == "html":
                        # HTML format (uses the raw HTML content directly)
                        f.write(f'<section id="chapter-{sort_order}">\n')
                        f.write(f'  <h2>Chapter {sort_order}: {title}</h2>\n')
                        f.write(f'{content}\n') # Text_Content is stored as HTML
                        f.write('</section>\n\n')

                    elif file_format == "text":
                        # Plain Text format (simplest format, removes HTML tags)
                        f.write(f"--- Chapter {sort_order}: {title} ---\n\n")

                        doc = QTextDocument()
                        doc.setHtml(content)
                        f.write(doc.toPlainText())
                        f.write("\n\n")
                        
                # --- HTML Footer ---
                if file_format == "html":
                    f.write("</body></html>")


            self.statusBar().showMessage(f"Story exported successfully to: {file_path}", 5000)
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export story: {e}")
            self.statusBar().showMessage("Export failed.", 5000)

    def _open_settings_dialog(self) -> None:
        """Handles opening the settings dialog and applying changes."""

        dialog = SettingsDialog(
            current_settings=self.current_settings,
            settings_manager=self.settings_manager,
            parent=self
            )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_settings = dialog.get_new_settings()
            
            # 1. Save the new settings to the user file
            self.settings_manager.save_settings(new_settings)
            
            # 2. Apply the new settings
            self.current_settings = new_settings
            self._apply_theme(self.current_settings)
            
            self.statusBar().showMessage(f"Settings saved and applied. Theme: {new_settings['theme']}.", 5000)

    def _apply_theme(self, settings: dict) -> None:
        """Loads and applies the QSS file for the selected theme."""

        theme_name = settings.get("theme", "Light") # Use 'Dark' as a hardcoded fallback
        
        theme_file = os.path.join('styles', f"{theme_name.lower()}.qss")
        
        if os.path.exists(theme_file):
            try:
                with open(theme_file, 'r') as f:
                    # Apply the stylesheet to the entire application
                    self.setStyleSheet(f.read())

                self.current_settings['theme'] = theme_name
                print(f"Theme applied: {theme_name}")

            except Exception as e:
                print(f"Error loading theme file {theme_file}: {e}")
        else:
            print(f"Theme file not found: {theme_file}")