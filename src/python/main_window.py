# Main Application Window: src/python/main_window.py

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QSplitter, QMessageBox, QFileDialog, QDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent, QAction, QTextDocument, QIcon
import os
import ctypes

from ui.outline_manager import OutlineManager
from ui.chapter_editor import ChapterEditor
from ui.settings_dialog import SettingsDialog

from db_connector import DBConnector
from chapter_repository import ChapterRepository
from tag_repository import TagRepository
from settings_manager import SettingsManager

from _version import __version__

class MainWindow(QMainWindow):
    """
    The Main Window for The Narrative Forge application.
    Sets up the core layout: Outline Manager on the left, Editor on the right
    """
    def __init__(self) -> None:
        super().__init__()

        # This is a workaround to allow the taskbar to have the same icon as the window icon
        appID = "narrative-forge.0.1.0"
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
        self.tag_repo = TagRepository(self.db_connector)

        # --- Settings and Theme Management ---
        self.settings_manager = SettingsManager()
        self.current_settings = self.settings_manager.load_settings()
        self._apply_theme(self.current_settings)

        # State tracking for the currently loaded chapter
        self.current_chapter_id = 0

        self._setup_ui()

        self._setup_menu_bar()

        self._connect_components()

        # Initially disable editor panel until chapter is selected
        self.editor_panel.setEnabled(False)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handles closing the database connection when the application exits."""

        # Check for unsaved changes before allowing app to close
        if self.editor_panel.is_dirty():
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
                # Attempt to save the current chapter
                if not self._save_chapter(self.current_chapter_id):
                    QMessageBox.critical(self, "Save Failed", "Failed to save the current chapter. Aborting exit.")
                    event.ignore()
                    return

        if self.db_connector:
            self.db_connector.close()
        super().closeEvent(event)

    def _setup_ui(self):
        """Setsup the central widget and the main split layout"""

        # 1. Create a QSplitter for the main content area (Outline | Editor)
        # This allows the user to resize the sections horizontally.
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- Left Panel: Outline Manager
        self.outline_manager = OutlineManager(chapter_repo=self.chapter_repo)

        # --- Right Panel: Editor ---
        self.editor_panel = ChapterEditor()

        # Add the panels to the splitter
        main_splitter.addWidget(self.outline_manager)
        main_splitter.addWidget(self.editor_panel)

        # Set the initial ratio of the splitter (e.g., 1:3 ratio)
        main_splitter.setSizes([300, 900]) 

        # Set the splitter as the central widget
        self.setCentralWidget(main_splitter)
        
        # Add a placeholder status bar
        self.statusBar().showMessage("Ready to forge your narrative.")

    def _setup_menu_bar(self):
        """Creates the basic menu bar with placeholder items (File, Edit, Help)."""
        
        menu_bar = self.menuBar()
        
        # --- File Menu ---
        file_menu = menu_bar.addMenu("&File")
        
        # Action: New Chapter (Will be implemented in Story 2.4)
        new_chapter_action = file_menu.addAction("New Chapter...")
        new_chapter_action.setStatusTip("Create a new chapter document")
        new_chapter_action.triggered.connect(self.outline_manager.prompt_and_add_chapter)
        
        file_menu.addSeparator()

        # Action: Save Current Chapter
        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.setStatusTip("Save the current chapter content to the database")
        save_action.triggered.connect(lambda: self._save_chapter(self.current_chapter_id))
        file_menu.addAction(save_action)

        # Action Export Story
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
        # Connect the chapter selection signal from the OutlineManager to a handler
        self.outline_manager.chapter_selected.connect(self._load_chapter_content)
        # Connect the pre-change signal to ensure content is saved if necessary
        self.outline_manager.pre_chapter_change.connect(self._check_save_before_change)

    def _check_save_before_change(self) -> bool:
        """
        Prompts the user to save if the editor is dirty.
        Returns True if safe to proceed (saved or discarded), False otherwise.
        """
        if self.current_chapter_id != 0 and self.editor_panel.is_dirty():
            save_reply = QMessageBox.question(
                self, 
                "Unsaved Changes",
                "The current chapter has unsaved changes. Do you want to save before continuing?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            
            if save_reply == QMessageBox.StandardButton.Cancel:
                # User cancels the operation (e.g., changing chapter/deleting)
                return False
            
            if save_reply == QMessageBox.StandardButton.Save:
                # Attempt to save
                return self._save_chapter(self.current_chapter_id) # Returns True/False based on save success
            
            # If Discard, return True (safe to proceed)
            return True
        
        # No chapter loaded or editor is clean
        return True
    
    def _save_chapter(self, chapter_id: int) -> bool:
        """Saves the current content and tags to the database."""
        if chapter_id <= 0:
            return False # Nothing is loaded

        content = self.editor_panel.get_html_content()
        tags = self.editor_panel.get_tags()

        # 1. Save Content (using ChapterRepository)
        content_saved = self.chapter_repo.update_chapter_content(chapter_id, content)

        # 2. Save Tags (using TagRepository)
        tags_saved = self.tag_repo.set_tags_for_chapter(chapter_id, tags)
        
        if content_saved and tags_saved:
            self.editor_panel.mark_saved()
            self.statusBar().showMessage(f"Chapter ID {chapter_id} saved successfully.", 3000)
            return True
        else:
            self.statusBar().showMessage(f"ERROR: Failed to save Chapter ID {chapter_id}!", 5000)
            return False

    def _load_chapter_content(self, chapter_id: int) -> None:
        """
        Slot: Called when a chapter is selected in the outline.
        Loads content from the database and updates the editor.
        """
        # Ensure the pre-change save check passed before proceeding with load
        # Note: OutlineManager ensures this, but a safety check is good practice
        
        self.current_chapter_id = chapter_id
        
        print(f"MainWindow loading content for Chapter ID: {chapter_id}...")
        
        # 1. Load Content (Handles content persistence / new chapter initialization)
        content = self.chapter_repo.get_chapter_content(chapter_id)
        
        if content is None:
            # This should not happen if the ID is valid, but handle it anyway
            content = "<h1>Error Loading Chapter</h1><p>Content could not be retrieved from the database.</p>"
            self.editor_panel.set_html_content(content)
            self.editor_panel.setEnabled(False)
            self.statusBar().showMessage(f"Error loading Chapter ID {chapter_id}.")
        else:
            self.editor_panel.set_html_content(content)
            self.editor_panel.setEnabled(True)
            self.statusBar().showMessage(f"Chapter ID {chapter_id} selected and loaded.")

        # 2. Load Tags
        tags_data = self.tag_repo.get_tags_for_chapter(chapter_id)
        tag_names = [name for _, name in tags_data] if tags_data else []

        self.editor_panel.set_tags(tag_names)

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