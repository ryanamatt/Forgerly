# Main Application Window: src/python/main_window.py

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QSplitter,
    QMenuBar, QToolBar, QTextEdit, QListWidget
)
from PyQt6.QtCore import Qt

from outline_manager import OutlineManager
from rich_text_editor import RichTextEditor
from db_connector import DBConnector

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

        self._setup_ui()

        self._setup_menu_bar()

        self._connect_components()

        # State tracking for the currently loaded chapter (ID 0 means nothing loaded)
        self.current_chapter_id = 0

    def closeEvent(self, event) -> None:
        """Handles closing the database connection when the application exits."""
        if self.db_connector:
            self.db_connector.close()
        super().closeEvent(event)

    def _setup_ui(self):
        """Setsup the central widget and the main split layout"""

        # 1. Create a QSplitter for the main content area (Outline | Editor)
        # This allows the user to resize the sections horizontally.
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- Left Panel: Outline Manager
        self.outline_manager = OutlineManager(db_connector=self.db_connector)

        # --- Right Panel: Editor ---
        self.editor_panel = RichTextEditor()

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
        # Placeholder connection:
        new_chapter_action.triggered.connect(lambda: print("Action: New Chapter triggered"))
        
        file_menu.addSeparator()
        file_menu.addAction("Save")
        file_menu.addAction("Save All")
        
        # Action: Exit
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        
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

    def _load_chapter_content(self, chapter_id: int):
        """
        Placeholder slot: Called when a chapter is selected in the outline.
        (Story 2.6 will implement the actual database lookup and text loading).
        """
        # Update the state of the currently loaded chapter
        self.current_chapter_id = chapter_id
        
        print(f"MainWindow received selection for Chapter ID: {chapter_id}. Loading content...")
        
        # Use the RichTextEditor's set_html_content method
        self.editor_panel.set_html_content(
            f"<h1>Chapter ID: {chapter_id}</h1>"
            f"<p>This is the newly implemented **Rich Text Editor**. You can now use <b>Bold</b>, <i>Italic</i>, and <u>Underline</u>, as well as bulleted and numbered lists!</p>"
            f"<ul><li>List Item 1</li><li>List Item 2</li></ul>"
        )
        self.statusBar().showMessage(f"Chapter ID {chapter_id} selected.")

if __name__ == '__main__':
    # Initialize the QApplication
    app = QApplication(sys.argv)
    
    # Create the main window instance
    window = MainWindow()
    
    # Show the window
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())