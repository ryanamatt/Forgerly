# Main Application Window: src/python/main_window.py

from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QMessageBox, QFileDialog, QDialog,
    QWidget, QVBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent, QAction, QTextDocument, QIcon
import os
import ctypes

from ui.views.chapter_outline_manager import ChapterOutlineManager
from ui.views.chapter_editor import ChapterEditor
from ui.views.lore_outline_manager import LoreOutlineManager
from ui.views.lore_editor import LoreEditor
from ui.dialogs.settings_dialog import SettingsDialog

from db_connector import DBConnector

from services.settings_manager import SettingsManager
from services.app_coordinator import AppCoordinator
from services.story_exporter import StoryExporter

from utils._version import __version__
from utils.theme_utils import apply_theme
from utils.constants import ViewType

class MainWindow(QMainWindow):
    """
    The Main Window for The Narrative Forge application.
    Sets up the core layout: Outline Manager on the left, Editor on the right.
    Uses a stack-like approach for view management and delegates business logic 
    to the AppCoordinator.
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
            self.db_connector.initialize_schema() 
            print("Application database setup verified.")
        else:
            print("FATAL: Could not connect to database.")

        # --- Initialize Coordinator & Repositories ---
        # Coordinator now manages all repositories and business logic
        self.coordinator = AppCoordinator(self.db_connector) 

        self.story_exporter = StoryExporter(self.coordinator)

        # --- Settings and Theme Management ---
        self.settings_manager = SettingsManager()
        self.current_settings = self.settings_manager.load_settings()
        if (apply_theme(self, self.current_settings)):
            self.current_settings['theme'] = self.current_settings.get("theme", "Dark")

        # State tracking now primarily managed by Coordinator, but keep a pointer to the ID for convenience
        self.current_item_id = 0 
        self.current_view = ViewType.CHAPTER

        self._create_view_shortcut()

        self._setup_ui()
        
        # NEW: Link editors to the coordinator using a dictionary map for scalability
        editor_map = {
            ViewType.CHAPTER: self.chapter_editor_panel,
            ViewType.LORE: self.lore_editor_panel
        }
        self.coordinator.set_editors(editor_map)

        self._setup_menu_bar()

        self._connect_components()

        # Initially set the view to Chapters
        self._switch_to_view(ViewType.CHAPTER)

    # -------------------------------------------------------------------------
    # System Events
    # -------------------------------------------------------------------------

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handles closing the database connection when the application exits."""

        if not self.coordinator.check_and_save_dirty(parent=self):
            event.ignore()
            return

        if self.db_connector:
            self.db_connector.close()
        super().closeEvent(event)

    # -------------------------------------------------------------------------
    # View Management
    # -------------------------------------------------------------------------

    def _create_view_shortcut(self) -> None:
        """Creates a shortcut to toggle between Chapter and Lore view (Ctrl+Tab)."""
        toggle_action = QAction("Toggle View", self)
        toggle_action.setShortcut("Ctrl+Tab")
        toggle_action.triggered.connect(self._toggle_view)
        self.addAction(toggle_action)

    def _toggle_view(self) -> None:
        """Toggles between the Chapter and Lore view."""
        new_view = ViewType.LORE if self.current_view == ViewType.CHAPTER else ViewType.CHAPTER
        self._switch_to_view(new_view)

    def _switch_to_view(self, view: ViewType) -> None:
        """Switches between the Chapter and Lore View"""
        if not self.coordinator.check_and_save_dirty(parent=self):
            return
        
        # Inform the Coordinator of the view change
        self.coordinator.set_current_view(view)
        
        # Update MainWindow State (for local use)
        self.current_view = view
        
        match self.current_view:
            case ViewType.CHAPTER:
                self.chapter_outline_manager.show()
                self.chapter_editor_panel.show()
                self.lore_outline_manager.hide()
                self.lore_editor_panel.hide()

            case ViewType.LORE:
                self.chapter_outline_manager.hide()
                self.chapter_editor_panel.hide()
                self.lore_outline_manager.show()
                self.lore_editor_panel.show()
        
        # 4. Disable the newly visible editor until an item is selected
        editor = self.coordinator.get_current_editor()
        if editor:
            editor.set_enabled(False)

    # -------------------------------------------------------------------------
    # UI Setup
    # -------------------------------------------------------------------------

    def _setup_ui(self) -> None:
        """Sets up the main application layout and components."""
        
        # 1. Instantiate Repositories (Outline Managers still need a repo to handle CUD)
        # Note: Outline Managers now only handle C/U/D, the Coordinator handles R/Update.
        self.chapter_repo = self.coordinator.chapter_repo
        self.lore_repo = self.coordinator.lore_repo
        
        # 2. Instantiate Main Components
        self.chapter_outline_manager = ChapterOutlineManager(chapter_repository=self.chapter_repo)
        self.chapter_editor_panel = ChapterEditor()
        self.lore_outline_manager = LoreOutlineManager(lore_repository=self.lore_repo)
        self.lore_editor_panel = LoreEditor()

        # 3. Left Panel: Outline Stack
        self.outline_stack = QWidget()
        outline_layout = QVBoxLayout(self.outline_stack)
        outline_layout.setContentsMargins(0, 0, 0, 0)
        outline_layout.addWidget(self.chapter_outline_manager)
        outline_layout.addWidget(self.lore_outline_manager)
        
        # 4. Right Panel: Editor Stack
        self.editor_stack = QWidget()
        editor_layout = QVBoxLayout(self.editor_stack)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.addWidget(self.chapter_editor_panel)
        editor_layout.addWidget(self.lore_editor_panel)

        # 5. Main Splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.addWidget(self.outline_stack)
        self.main_splitter.addWidget(self.editor_stack)
        self.main_splitter.setSizes([300, 900])  # Initial width distribution
        self.main_splitter.setStretchFactor(1, 1) # Editor side stretches

        self.setCentralWidget(self.main_splitter)
        
        # 6. Load Initial Data
        self.chapter_outline_manager.load_outline()
        self.lore_outline_manager.load_outline()

    def _setup_menu_bar(self) -> None:
        """Sets up the File, View, and Help menus."""
        menu_bar = self.menuBar()

        # --- File Menu ---
        file_menu = menu_bar.addMenu("&File")

        new_chapter_action = QAction("New Chapter", self)
        new_chapter_action.triggered.connect(self.chapter_repo.create_chapter)
        file_menu.addAction(new_chapter_action)

        new_lore_action = QAction("New Lore Entry", self)
        new_lore_action.triggered.connect(self.lore_repo.create_lore_entry)
        file_menu.addAction(new_lore_action)
        
        file_menu.addSeparator()

        save_action = QAction("&Save Content", self)
        save_action.setShortcut("Ctrl+S")
        # UPDATED: Connect save action to the new wrapper method
        save_action.triggered.connect(self._save_current_item_wrapper) 
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        export_action = QAction("&Export Story...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._export_story)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()

        settings_action = QAction("&Settings", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._open_settings_dialog)
        file_menu.addAction(settings_action)

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # --- View Menu ---
        view_menu = menu_bar.addMenu("&View")

        view_chapter_action = QAction("Chapter Outline", self)
        view_chapter_action.setCheckable(True)
        view_chapter_action.setChecked(self.current_view == ViewType.CHAPTER)
        view_chapter_action.triggered.connect(lambda: self._switch_to_view(ViewType.CHAPTER))
        view_menu.addAction(view_chapter_action)

        view_lore_action = QAction("Lore Outline", self)
        view_lore_action.setCheckable(True)
        view_lore_action.setChecked(self.current_view == ViewType.LORE)
        view_lore_action.triggered.connect(lambda: self._switch_to_view(ViewType.LORE))
        view_menu.addAction(view_lore_action)

        # --- Help Menu ---
        help_menu = menu_bar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def _show_about_dialog(self) -> None:
        """Displays the application's About dialog."""
        QMessageBox.about(
            self,
            f"About The Narrative Forge v{__version__}",
            f"<h2>The Narrative Forge</h2>"
            f"<p>Version: {__version__}</p>"
            f"<p>A writing application designed for worldbuilders and novel writers.</p>"
            f"<p>Built with Python and PyQt6.</p>"
        )

    # -------------------------------------------------------------------------
    # Signal Connections
    # -------------------------------------------------------------------------

    def _connect_components(self) -> None:
        """Connects signals from custom widgets to slots in the main window and coordinator."""
        
        # --- Outline Managers (UI signal OUT -> Coordinator slot IN) ---
        # The outline manager now signals the coordinator to load data
        self.chapter_outline_manager.chapter_selected.connect(self.coordinator.load_chapter)
        self.lore_outline_manager.lore_selected.connect(self.coordinator.load_lore)
        
        # Pre-change signal now checks for dirty state via the coordinator
        # The outlines emit pre_change, and the main window delegates the action
        self.chapter_outline_manager.pre_chapter_change.connect(self._check_save_before_change)
        self.lore_outline_manager.pre_lore_change.connect(self._check_save_before_change)
        
        # --- Coordinator (Coordinator signal OUT -> Editor/UI slot IN) ---
        # The coordinator signals the editors when data is ready
        self.coordinator.chapter_loaded.connect(self._handle_chapter_loaded)
        self.coordinator.lore_loaded.connect(self._handle_lore_loaded)
        
        # The coordinator signals the outline to update title (relaying editor signal)
        self.coordinator.lore_title_updated_in_outline.connect(self._update_lore_outline_title)

    # -------------------------------------------------------------------------
    # Logic Delegation / NEW Handlers
    # -------------------------------------------------------------------------

    def _check_save_before_change(self) -> bool:
        """
        Prompts the user to save if the active editor is dirty via the Coordinator.
        Returns True if safe to proceed (saved or discarded), False otherwise.
        """
        return self.coordinator.check_and_save_dirty(parent=self)

    def _save_current_item_wrapper(self):
        """Wrapper to call coordinator's save method and update status bar."""
        item_id = self.coordinator.current_item_id
        view = self.coordinator.current_view
        
        if self.coordinator.save_current_item(item_id, view, parent=self):
            item_type = 'Chapter' if view == ViewType.CHAPTER else 'Lore Entry'
            self.statusBar().showMessage(f"{item_type} ID {item_id} saved successfully.", 3000)
        # Note: Error messages are handled by the Coordinator via QMessageBox.

    def _handle_chapter_loaded(self, chapter_id: int, content: str, tag_names: list) -> None:
        """Receives loaded chapter data from coordinator and updates the editor/status."""
        self.current_item_id = chapter_id # Update local ID cache
        
        if "Error Loading Chapter" in content:
            self.chapter_editor_panel.set_html_content(content)
            self.chapter_editor_panel.set_enabled(False)
            self.statusBar().showMessage(f"Error loading Chapter ID {chapter_id}.")
        else:
            self.chapter_editor_panel.set_html_content(content)
            self.chapter_editor_panel.set_tags(tag_names)
            self.chapter_editor_panel.set_enabled(True)
            self.chapter_editor_panel.mark_saved() # Reset dirtiness after load
            self.statusBar().showMessage(f"Chapter ID {chapter_id} selected and loaded.")

    def _handle_lore_loaded(self, lore_id: int, title: str, category: str, content: str, tag_names: list) -> None:
        """Receives loaded lore data from coordinator and updates the editor/status."""
        self.current_item_id = lore_id # Update local ID cache
        
        if not title: # Check if loading failed
            self.lore_editor_panel.set_enabled(False)
            self.statusBar().showMessage(f"Error loading Lore ID {lore_id}.")
            return
            
        # The LoreEditor handles setting its internal state (title, category, etc.)
        self.lore_editor_panel.load_lore(lore_id, title, category, content, tag_names)
        self.lore_editor_panel.set_enabled(True)
        self.lore_editor_panel.mark_saved()
        self.statusBar().showMessage(f"Lore Entry ID {lore_id} selected and loaded.")

    def _update_lore_outline_title(self, lore_id: int, new_title: str) -> None:
        """Updates the title in the LoreOutlineManager when the editor title changes (relayed by coordinator)."""
        if self.current_view == ViewType.LORE:
            # Note: Outline Manager must have a helper method to find the item by ID
            item = self.lore_outline_manager.find_lore_item_by_id(lore_id)
            if item and item.text(0) != new_title:
                # Block signals to prevent _handle_item_renamed from firing back to the repo
                self.lore_outline_manager.blockSignals(True)
                item.setText(0, new_title)
                self.lore_outline_manager.blockSignals(False)
    
    # -------------------------------------------------------------------------
    # I/O Handlers (Export/Settings)
    # -------------------------------------------------------------------------

    def _export_story(self) -> None:
        """
        Handles the export action by delegating the entire process to the 
        StoryExporter after checking for unsaved changes.
        """
        # 1. Check for unsaved changes before exporting
        if not self.coordinator.check_and_save_dirty(parent=self):
            return
        
        # 2. Pass control to the StoryExporter
        if self.story_exporter.export_story(parent=self):
            self.statusBar().showMessage("Story exported successfully.", 5000)
        

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
            
            # Check if theme application was successful
            if apply_theme(self, self.current_settings):
                self.current_settings['theme'] = new_settings.get("theme", "Light")
            
            self.statusBar().showMessage(f"Settings saved and applied. Theme: {self.current_settings['theme']}.", 5000)