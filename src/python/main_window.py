# Main Application Window: src/python/main_window.py

from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QMessageBox, QFileDialog, QDialog,
    QWidget, QVBoxLayout, QStackedWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent, QAction, QResizeEvent, QMoveEvent, QIcon
import os
import ctypes

from .ui.views.chapter_outline_manager import ChapterOutlineManager
from .ui.views.chapter_editor import ChapterEditor
from .ui.views.lore_outline_manager import LoreOutlineManager
from .ui.views.lore_editor import LoreEditor
from .ui.views.character_outline_manager import CharacterOutlineManager
from .ui.views.character_editor import CharacterEditor
from .ui.views.relationship_outline_manager import RelationshipOutlineManager
from .ui.views.relationship_editor import RelationshipEditor
from .ui.dialogs.settings_dialog import SettingsDialog
from .ui.dialogs.exporter_dialog import ExporterDialog, ExportType

from .db_connector import DBConnector

from .services.settings_manager import SettingsManager
from .services.app_coordinator import AppCoordinator
from .services.story_exporter import StoryExporter
from .services.character_exporter import CharacterExporter
from .services.lore_exporter import LoreExporter

from .utils._version import __version__
from .utils.theme_utils import apply_theme
from .utils.constants import ViewType

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

        # Temporary Project Title will need to be changed to actual users project title
        self.project_title = "Project Title"

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

        self.story_exporter = StoryExporter(self.coordinator, self.project_title)
        self.character_exporter = CharacterExporter(self.coordinator, self.project_title)
        self.lore_exporter = LoreExporter(self.coordinator, self.project_title)

        # --- Settings and Theme Management ---
        self.settings_manager = SettingsManager()
        self.current_settings = self.settings_manager.load_settings()
        self._apply_settings(self.current_settings)

        # State tracking now primarily managed by Coordinator, but keep a pointer to the ID for convenience
        self.current_item_id = 0 
        self.current_view = ViewType.CHAPTER_EDITOR

        self._create_view_shortcut()

        self._setup_ui()
        
        # NEW: Link editors to the coordinator using a dictionary map for scalability
        editor_map = {
            ViewType.CHAPTER_EDITOR: self.chapter_editor_panel,
            ViewType.LORE_EDITOR: self.lore_editor_panel,
            ViewType.CHARACTER_EDITOR: self.character_editor_panel,
            ViewType.RELATIONSHIP_GRAPH: self.relationship_editor_panel
        }
        self.coordinator.set_editors(editor_map)
        self.coordinator.connect_signals()

        self._setup_menu_bar()

        self._connect_components()

        # Initially set the view to Chapters
        self._switch_to_view(ViewType.CHAPTER_EDITOR)

    # -------------------------------------------------------------------------
    # System Events
    # -------------------------------------------------------------------------

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handles closing the database connection when the application exits."""

        if not self.coordinator.check_and_save_dirty(parent=self):
            event.ignore()
            return
        
        self._save_geometry_to_settings()

        if self.main_splitter:
            current_sizes = self.main_splitter.sizes()
            outline_width = current_sizes[0]
            self.current_settings['outline_width_pixels'] = outline_width
            self.settings_manager.save_settings(self.current_settings)

        if self.db_connector:
            self.db_connector.close()
        super().closeEvent(event)

    def resizeEvent(self, event: QResizeEvent):
        """Called when the window is resized. Saves new dimensions."""
        super().resizeEvent(event)
        self._save_geometry_to_settings()

    def moveEvent(self, event: QMoveEvent):
        """Called when the window is moved. Saves new position."""
        super().moveEvent(event)
        self._save_geometry_to_settings()

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
        new_view = ViewType.LORE_EDITOR if self.current_view == ViewType.CHAPTER_EDITOR else ViewType.CHAPTER_EDITOR
        self._switch_to_view(new_view)

    def _switch_to_view(self, view: ViewType) -> None:
        """Switches between the Chapter and Lore View"""
        if not self.coordinator.check_and_save_dirty(parent=self):
            return
        
        # Inform the Coordinator of the view change
        self.coordinator.set_current_view(view)
        
        # Update MainWindow State (for local use)
        self.current_view = view
        
        # Determine the index for the QStackedWidgets
        view_index = -1
        match self.current_view:
            case ViewType.CHAPTER_EDITOR:
                view_index = self._chapter_index # Should be 0
            case ViewType.LORE_EDITOR:
                view_index = self._lore_index    # Should be 1
            case ViewType.CHARACTER_EDITOR:
                view_index = self._character_index # Should be 2
            case ViewType.RELATIONSHIP_GRAPH:
                view_index = self._relationship_index # Should be 3
        
        # Switch the QStackedWidgets to the correct panel index
        if view_index != -1:
            self.outline_stack.setCurrentIndex(view_index)
            self.editor_stack.setCurrentIndex(view_index)

        self.view_lore_action.setChecked(ViewType.LORE_EDITOR == self.current_view)
        self.view_chapter_action.setChecked(ViewType.CHAPTER_EDITOR == self.current_view)
        self.view_character_action.setChecked(ViewType.CHARACTER_EDITOR == self.current_view)
        self.view_relationship_action.setChecked(ViewType.RELATIONSHIP_GRAPH == self.current_view)
        
        # 4. Disable the newly visible editor until an item is selected
        editor = self.coordinator.get_current_editor()
        if editor:
            # We don't disable the relationship editor, as it loads its own content
            if self.current_view != ViewType.RELATIONSHIP_GRAPH:
                editor.set_enabled(False)
            # If it's the graph view, trigger a load (also handled in set_current_view)
            else:
                self.relationship_editor_panel.request_load_data.emit()

    # -------------------------------------------------------------------------
    # UI Setup
    # -------------------------------------------------------------------------

    def _setup_ui(self) -> None:
        """Sets up the main application layout and components."""
        
        # 1. Instantiate Repositories (Outline Managers still need a repo to handle CUD)
        # Note: Outline Managers now only handle C/U/D, the Coordinator handles R/Update.
        self.chapter_repo = self.coordinator.chapter_repo
        self.lore_repo = self.coordinator.lore_repo
        self.char_repo = self.coordinator.character_repo
        self.relationship_repo = self.coordinator.relationship_repo
        
        # 2. Instantiate Main Components
        self.chapter_outline_manager = ChapterOutlineManager(chapter_repository=self.chapter_repo)
        self.chapter_editor_panel = ChapterEditor(self.current_settings)
        self.lore_outline_manager = LoreOutlineManager(lore_repository=self.lore_repo)
        self.lore_editor_panel = LoreEditor()
        self.character_outline_manager = CharacterOutlineManager(character_repository=self.char_repo)
        self.character_editor_panel = CharacterEditor()
        self.relationship_outline_manager = RelationshipOutlineManager(relationship_repository=self.relationship_repo)
        self.relationship_editor_panel = RelationshipEditor(coordinator=self.coordinator)

        # 3. Left Panel: Outline Stack
        self.outline_stack = QStackedWidget()
        self.outline_stack.addWidget(self.chapter_outline_manager)
        self.outline_stack.addWidget(self.lore_outline_manager)
        self.outline_stack.addWidget(self.character_outline_manager)
        self.outline_stack.addWidget(self.relationship_outline_manager)
        
        # 4. Right Panel: Editor Stack
        self.editor_stack = QStackedWidget()
        self.editor_stack.addWidget(self.chapter_editor_panel)
        self.editor_stack.addWidget(self.lore_editor_panel)
        self.editor_stack.addWidget(self.character_editor_panel)
        self.editor_stack.addWidget(self.relationship_editor_panel)

        # Store the indices for the new QStackedWidget
        self._chapter_index = 0
        self._lore_index = 1
        self._character_index = 2
        self._relationship_index = 3

        # 5. Main Splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.addWidget(self.outline_stack)
        self.main_splitter.addWidget(self.editor_stack)

        outline_width = self.current_settings.get('outline_width_pixels', 300)
        self.main_splitter.setSizes([outline_width, self.width() - outline_width])  # Initial width distribution
        self.main_splitter.setStretchFactor(1, 1) # Editor side stretches

        self.setCentralWidget(self.main_splitter)
        
        # 6. Load Initial Data
        self.chapter_outline_manager.load_outline()
        self.lore_outline_manager.load_outline()
        self.character_outline_manager.load_outline()

        # Initialize relationship editor's signals
        self.relationship_editor_panel.set_coordinator_signals(self.coordinator)

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

        new_character_action = QAction("New Character", self)
        new_character_action.triggered.connect(self.char_repo.create_character)
        file_menu.addAction(new_character_action)
        
        file_menu.addSeparator()

        save_action = QAction("&Save Content", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_current_item_wrapper) 
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        export_action = QAction("&Export...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._export)
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

        # Chapter Outline View Action
        self.view_chapter_action = QAction("Chapter Outline", self)
        self.view_chapter_action.setCheckable(True)
        self.view_chapter_action.setChecked(self.current_view == ViewType.CHAPTER_EDITOR)
        self.view_chapter_action.triggered.connect(lambda: self._switch_to_view(ViewType.CHAPTER_EDITOR))
        view_menu.addAction(self.view_chapter_action)

        # Lore Outline View Action
        self.view_lore_action = QAction("Lore Outline", self)
        self.view_lore_action.setCheckable(True)
        self.view_lore_action.setChecked(self.current_view == ViewType.LORE_EDITOR)
        self.view_lore_action.triggered.connect(lambda: self._switch_to_view(ViewType.LORE_EDITOR))
        view_menu.addAction(self.view_lore_action)

        # Character Outline View Action
        self.view_character_action = QAction("Character Outline", self)
        self.view_character_action.setCheckable(True)
        self.view_character_action.setChecked(self.current_view == ViewType.CHARACTER_EDITOR)
        self.view_character_action.triggered.connect(lambda: self._switch_to_view(ViewType.CHARACTER_EDITOR))
        view_menu.addAction(self.view_character_action)

        view_menu.addSeparator()

        # Relationship Graph View Action
        self.view_relationship_action = QAction("Relationship Graph", self)
        self.view_relationship_action.setCheckable(True)
        self.view_relationship_action.setChecked(self.current_view == ViewType.RELATIONSHIP_GRAPH)
        self.view_relationship_action.triggered.connect(lambda: self._switch_to_view(ViewType.RELATIONSHIP_GRAPH))
        view_menu.addAction(self.view_relationship_action)

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
        self.character_outline_manager.char_selected.connect(self.coordinator.load_character)
        
        # Pre-change signal now checks for dirty state via the coordinator
        # The outlines emit pre_change, and the main window delegates the action
        self.chapter_outline_manager.pre_chapter_change.connect(self._check_save_before_change)
        self.lore_outline_manager.pre_lore_change.connect(self._check_save_before_change)
        self.character_outline_manager.pre_char_change.connect(self._check_save_before_change)
        
        # --- Coordinator (Coordinator signal OUT -> Editor/UI slot IN) ---
        # The coordinator signals the editors when data is ready
        self.coordinator.chapter_loaded.connect(self._handle_chapter_loaded)
        self.coordinator.lore_loaded.connect(self._handle_lore_loaded)
        self.coordinator.char_loaded.connect(self._handle_character_loaded)
        self.coordinator.graph_data_loaded.connect(self.relationship_editor_panel.load_graph)
        
        # The coordinator signals the outline to update title (relaying editor signal)
        self.coordinator.lore_title_updated_in_outline.connect(self._update_lore_outline_title)
        self.coordinator.char_name_updated_in_ouline.connect(self._update_character_outline_name)

        self.relationship_outline_manager.relationship_types_updated.connect(self.coordinator.reload_relationship_graph_data)

    # -------------------------------------------------------------------------
    # Logic Delegation / Handlers
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
            item_type = 'Chapter' if view == ViewType.CHAPTER_EDITOR else 'Lore Entry'
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
        if self.current_view == ViewType.LORE_EDITOR:
            # Note: Outline Manager must have a helper method to find the item by ID
            item = self.lore_outline_manager.find_lore_item_by_id(lore_id)
            if item and item.text(0) != new_title:
                # Block signals to prevent _handle_item_renamed from firing back to the repo
                self.lore_outline_manager.blockSignals(True)
                item.setText(0, new_title)
                self.lore_outline_manager.blockSignals(False)

    def _handle_character_loaded(self, char_id: int, name: str, description: str, status: str) -> None:
        """Receives loaded character data from coordinator and updates the editor/status."""
        self.current_item_id = char_id

        if not name:
            self.character_editor_panel.set_enabled(False)
            self.statusBar().showMessage(f"Error loading Character ID {char_id}.")
            return
        
        self.character_editor_panel.load_character(char_id, name, description, status)
        self.character_editor_panel.set_enabled(True)
        self.character_editor_panel.mark_saved()
        self.statusBar().showMessage(f"Lore Entry ID {char_id} selected and loaded.")

    def _update_character_outline_name(self, char_id: int, new_name: str) -> None:
        """Updates the name in the CharacterOutlineManager when the editor name changes (relayed by coordinator)."""
        if self.current_view == ViewType.CHARACTER_EDITOR:
            # Note: Outline Manager must have a helper method to find the item by ID
            item = self.character_outline_manager.find_character_item_by_id(char_id)
            if item and item.text(0) != new_name:
                # Block signals to prevent _handle_item_renamed from firing back to the repo
                self.character_outline_manager.blockSignals(True)
                item.setText(0, new_name)
                self.character_outline_manager.blockSignals(False)
    
    # -------------------------------------------------------------------------
    # I/O Handlers (Export/Settings)
    # -------------------------------------------------------------------------

    def _export(self) -> None:
        """
        Handles the export action by opening the ExporterDialog to let the user 
        choose what to export and then delegating the process.
        """
        # 1. Check for unsaved changes before exporting
        if not self.coordinator.check_and_save_dirty(parent=self):
            return
        
        # 2. Open the new ExporterDialog
        dialog = ExporterDialog(coordinator=self.coordinator, parent=self)
        
        # Connect the signal from the dialog to a slot in the main window
        dialog.export_requested.connect(self._perform_export)

        dialog.exec()
        # Dialog is closed and the signal is handled by _perform_export if accepted
        
    def _perform_export(self, export_type: str, selected_ids: list) -> None:
        """
        Delegates the export task based on the type selected in the dialog.
        
        Args:
            export_type (str): The type of content to export (e.g., 'Story (All Chapters)').
            selected_ids (list): A list of integer IDs for selected items (empty for full story).
        """
        success = False
        
        # You will expand this logic when you introduce other specific exporters
        match export_type:
            case ExportType.STORY | ExportType.CHAPTERS:
                if export_type == ExportType.STORY:
                    success = self.story_exporter.export(parent=self)
                else:
                    if selected_ids:
                        success = self.story_exporter.export(parent=self, selected_ids=selected_ids)
                    else:
                        QMessageBox.warning(self, "Export Error", "No chapters were selected for export.")
            
            case ExportType.LORE:
                if selected_ids:
                    success = self.lore_exporter.export(parent=self, selected_ids=selected_ids)
                else:
                    QMessageBox.warning(self, "Export Error", "No Characters were selected for export.")

            case ExportType.CHARACTERS:
                if selected_ids:
                    success = self.character_exporter.export(parent=self, selected_ids=selected_ids)
                else:
                        QMessageBox.warning(self, "Export Error", "No Characters were selected for export.")

            case _:
                QMessageBox.critical(self, "Export Error", f"Unknown export type: {export_type}")
                
        
        if success:
            self.statusBar().showMessage(f"{export_type} exported successfully.", 5000)

    def _open_settings_dialog(self) -> None:
        """Handles opening the settings dialog and applying changes."""

        dialog = SettingsDialog(
            current_settings=self.current_settings,
            settings_manager=self.settings_manager,
            parent=self
            )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_settings = dialog.get_new_settings()
            
            self.settings_manager.save_settings(new_settings)
            
            self._apply_settings(new_settings)
            
            self.statusBar().showMessage(f"Settings saved and applied. Theme: {self.current_settings['theme']}.", 5000)

    def _apply_settings(self, new_settings: dict) -> None:
        """
        Applies the loaded or newly changed settings to the application window

        Args:
            A dictionary of the new settings e.g {window_size: 800x600}
        """
        old_wpm = self.current_settings.get('words_per_minute', 250)
        new_wpm = new_settings.get('words_per_minute', 250)

        if old_wpm != new_wpm:
            # Update the ChapterEditor with the new WPM setting
            self.chapter_editor_panel.set_wpm(new_wpm)

        self.current_settings = new_settings

        # Check if theme application was successful
        if apply_theme(self, self.current_settings):
            self.current_settings['theme'] = self.current_settings.get("theme", "Dark") 

        window_width = self.current_settings.get('window_width')
        window_height = self.current_settings.get('window_height')
        window_pos_x = self.current_settings.get('window_pos_x', 100) # Use saved position, fallback to 100
        window_pos_y = self.current_settings.get('window_pos_y', 100) # Use saved position, fallback to 100

        if window_width and window_height:
            # Use the dynamically saved geometry (from manual resize/move)
            self.setGeometry(window_pos_x, window_pos_y, window_width, window_height)
        else:
            # Fallback to the preset size string (e.g., '1200x800')
            window_size_str = self.current_settings['window_size']
            w, h = map(int, window_size_str.split('x'))
            self.setGeometry(window_pos_x, window_pos_y, w, h)

    def _save_geometry_to_settings(self):
        """
        Helper method to save the current window dimensions and position
        to the settings manager.
        """
        # Get the geometry of the non-frame window (content area)
        rect = self.geometry()

        self.current_settings['window_width'] = rect.width()
        self.current_settings['window_height'] = rect.height()
        self.current_settings['window_pos_x'] = rect.x()
        self.current_settings['window_pos_y'] = rect.y()

        # Persist the updated settings immediately
        self.settings_manager.save_settings(self.current_settings)