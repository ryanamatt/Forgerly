# Main Application Window: src/python/main_window.py

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QSplitter, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent, QAction

from outline_manager import OutlineManager
from ui.chapter_editor import ChapterEditor
from db_connector import DBConnector
from chapter_repository import ChapterRepository
from tag_repository import TagRepository

class MainWindow(QMainWindow):
    """
    The Main Window for The Narrative Forge application.
    Sets up the core layout: Outline Manager on the left, Editor on the right
    """
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("The Narrative Forge")
        self.setGeometry(100, 100, 1200, 800)

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
        save_action.triggered.connect(self._save_chapter)
        file_menu.addAction(save_action)
        
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
        content_saved = self.chapter_repo.set_chapter_content(chapter_id, content)

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


if __name__ == '__main__':
    # Initialize the QApplication
    app = QApplication(sys.argv)
    
    # Create the main window instance
    window = MainWindow()
    
    # Show the window
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())