# src/python/main_window.py

from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QMessageBox, QDialog, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent, QResizeEvent, QMoveEvent, QIcon
import os
import sys
import ctypes
from typing import Any

from .ui.menu.main_menu_bar import MainMenuBar
from .ui.views.chapter_outline_manager import ChapterOutlineManager
from .ui.views.chapter_editor import ChapterEditor
from .ui.views.lore_outline_manager import LoreOutlineManager
from .ui.views.lore_editor import LoreEditor
from .ui.views.character_outline_manager import CharacterOutlineManager
from .ui.views.character_editor import CharacterEditor
from .ui.views.relationship_outline_manager import RelationshipOutlineManager
from .ui.views.relationship_editor import RelationshipEditor
from .ui.dialogs.settings_dialog import SettingsDialog
from .ui.dialogs.exporter_dialog import ExporterDialog

from .db_connector import DBConnector

from .services.settings_manager import SettingsManager
from .services.app_coordinator import AppCoordinator
from .services.story_exporter import StoryExporter
from .services.character_exporter import CharacterExporter
from .services.lore_exporter import LoreExporter

from .utils._version import __version__
from .utils.theme_utils import apply_theme
from .utils.constants import ViewType, ExportType

class MainWindow(QMainWindow):
    """
    The main window of the Narrative Forge application.
    
    It is responsible for:
    
    1. **Initialization:** Setting up the database, settings, and central application coordinator.
    2. **Layout Management:** Arranging the outline panel, editor panel, and menu bar.
    3. **View Switching:** Managing which content editor (Chapter, Lore, Character, Relationship) 
       is currently visible via a :py:class:`~PyQt6.QtWidgets.QStackedWidget`.
    4. **Event Handling:** Intercepting window close events to check for unsaved changes.
    5. **Settings/Theming:** Loading and saving window geometry and applying the current theme.
    """

    project_close_and_open_requested = pyqtSignal(bool) 
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (bool): Emitted when the user selects 
    'New Project' or 'Open Project' from the file menu. 
    The boolean payload is True for 'New Project', False for 'Open Project'.
    """

    def __init__(self, project_settings: dict[str, Any], settings_manager: SettingsManager, db_connector: DBConnector,
                 parent=None) -> None:
        """
        Initializes the main window, connecting to the database and setting up 
        all sub-components and services.
        
        :param project_path: The path to the narrative forge project.
        :type project_path: str
        :param settings_manager: The settings manager class to manage all settings.
        :type settings_manager: :py:class:'~services.SettingsManager`
        :param settings_manager: The database connector to connect to the database.
        :type settings_manager: :py:class:'~DBConnectorr`

        :rtype: None
        """
        super().__init__(parent)
        self.project_settings = project_settings
        self.project_path = self.project_settings['project_path']

        # need to know if macOS for differences
        self.is_macos = sys.platform == 'darwin'

        # This is a workaround to allow the taskbar to have the same icon as the window icon on windows
        if sys.platform.startswith('win'):
            try:
                appID = f"narrative-forge.{__version__}"
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appID)
            except AttributeError:
                pass

        # Temporary Project Title will need to be changed to actual users project title
        self.project_title = project_settings['project_name'] if project_settings['project_name'] != "" else "Project Title"

        self.setWindowTitle(f"The Narrative Forge v{__version__}")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon(os.path.join('resources', 'logo.ico')))
        
        # Initialize DB Connector
        self.db_connector = db_connector
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
        self.settings_manager = settings_manager
        self.current_settings = self.settings_manager.load_settings()
        self._apply_settings(self.current_settings)

        # State tracking now primarily managed by Coordinator, but keep a pointer to the ID for convenience
        self.current_view = ViewType.CHAPTER_EDITOR

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

        self.main_menu_bar = MainMenuBar(
            current_view=self.current_view,
            app_version=__version__,
            is_macos=self.is_macos,
            parent=self
        )
        self.setMenuBar(self.main_menu_bar)

        self._connect_components()

        # Initially set the view to Chapters
        self._switch_to_view(ViewType.CHAPTER_EDITOR)

    # -------------------------------------------------------------------------
    # System Events
    # -------------------------------------------------------------------------

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Overrides the standard window close event.

        Checks with the :py:class:`.AppCoordinator` if there are unsaved changes. 
        If so, it prompts the user to save, discard, or cancel the exit.
        
        :param event: The QCloseEvent object.
        :type event: :py:class:`~PyQt6.QtGui.QCloseEvent`
        
        :rtype: None
        """

        if not self.coordinator.check_and_save_dirty(parent=self):
            event.ignore()
            return
        
        self._save_geometry_to_settings()

        if self.main_splitter:
            current_sizes = self.main_splitter.sizes()
            outline_width = current_sizes[0]
            self.current_settings['outline_width_pixels'] = outline_width
            self.current_settings['last_project_path'] = self.project_path
            self.settings_manager.save_settings(self.current_settings)

        if self.db_connector:
            self.db_connector.close()
        super().closeEvent(event)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Overrides the standard window resize event to automatically save the 
        new window dimensions to settings.
        
        :param event: The QResizeEvent object.
        :type event: :py:class:`~PyQt6.QtGui.QResizeEvent`
        
        :rtype: None
        """
        super().resizeEvent(event)
        self._save_geometry_to_settings()

    def moveEvent(self, event: QMoveEvent) -> None:
        """
        Overrides the standard window move event to automatically save the 
        new window position to settings.
        
        :param event: The QMoveEvent object.
        :type event: :py:class:`~PyQt6.QtGui.QMoveEvent`
        
        :rtype: None
        """
        super().moveEvent(event)
        self._save_geometry_to_settings()

    # -------------------------------------------------------------------------
    # View Management
    # -------------------------------------------------------------------------

    def _switch_to_view(self, view: ViewType) -> None:
        """
        Switches between all the different views.
        
        :param view: The view that will be changed to.
        :type view: :py:class:`~app.utils.types.ViewType`

        :rtype: None
        """
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

        self.main_menu_bar.update_view_checkmarks(self.current_view)
        
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
        """
        Creates the main window structure, including the menu bar, the central 
        splitter, and the stacked widgets for outlines and editors.
        
        :rtype: None
        """
        
        # 1. Instantiate Repositories (Outline Managers still need a repo to handle CUD)
        # Note: Outline Managers now only handle C/U/D, the Coordinator handles R/Update.
        self.chapter_repo = self.coordinator.chapter_repo
        self.lore_repo = self.coordinator.lore_repo
        self.char_repo = self.coordinator.character_repo
        self.relationship_repo = self.coordinator.relationship_repo
        
        # 2. Instantiate Main Components
        self.chapter_outline_manager = ChapterOutlineManager(project_title=self.project_title, chapter_repository=self.chapter_repo)
        self.chapter_editor_panel = ChapterEditor(self.current_settings, self.coordinator)
        self.lore_outline_manager = LoreOutlineManager(lore_repository=self.lore_repo, coordinator=self.coordinator)
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

    # -------------------------------------------------------------------------
    # Signal Connections
    # -------------------------------------------------------------------------

    def _connect_components(self) -> None:
        """
        Connects signals from custom widgets to slots in the main window and coordinator.
        
        :rtype: None
        """
        
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

        # --- MainMenuBar Connections (Menu signal OUT -> MainWindow slot IN) ---
        self.main_menu_bar.new_chapter_requested.connect(self.chapter_repo.create_chapter)
        self.main_menu_bar.new_lore_requested.connect(self.lore_repo.create_lore_entry)
        self.main_menu_bar.new_character_requested.connect(self.char_repo.create_character)

        self.main_menu_bar.save_requested.connect(self._save_current_item_wrapper)
        self.main_menu_bar.export_requested.connect(self._export)
        self.main_menu_bar.settings_requested.connect(self._open_settings_dialog)

        # Connections for MainMenuBar Projects
        self.main_menu_bar.new_project_requested.connect(lambda: self._request_project_switch(is_new=True))
        self.main_menu_bar.open_project_requested.connect(lambda: self._request_project_switch(is_new=False))

        # Connect the view switching signal from the menu bar
        self.main_menu_bar.view_switch_requested.connect(self._switch_to_view)
        
        # --- Coordinator (Coordinator signal OUT -> Editor/UI slot IN) ---
        # The coordinator signals the editors when data is ready
        self.coordinator.chapter_loaded.connect(self._handle_chapter_loaded)
        self.coordinator.lore_loaded.connect(self._handle_lore_loaded)
        self.coordinator.char_loaded.connect(self._handle_character_loaded)
        self.coordinator.graph_data_loaded.connect(self.relationship_editor_panel.load_graph)
        
        self.relationship_outline_manager.relationship_types_updated.connect(self.coordinator.reload_relationship_graph_data)

    # --- For Creating/Opening other Projects ---

    def _request_project_switch(self, is_new: bool) -> None:
        """
        Handles the request to switch to a new project or open an existing one.
        
        First, checks for unsaved changes. If safe to proceed, emits a signal 
        to the ApplicationFlowManager to handle the window switch.
        
        :param is_new: True if 'New Project' was requested, False if 'Open Project'.
        :type is_new: bool

        :rtype: None
        """
        # 1. Check for and save unsaved changes before switching
        if not self.coordinator.check_and_save_dirty(parent=self):
            return # User cancelled save dialog

        # 2. Emit the signal to the ApplicationFlowManager
        self.project_close_and_open_requested.emit(is_new)

    # -------------------------------------------------------------------------
    # Logic Delegation / Handlers
    # -------------------------------------------------------------------------

    def _check_save_before_change(self) -> bool:
        """
        Prompts the user to save if the active editor is dirty via the Coordinator.

        :returns: Returns True if safe to proceed (saved or discarded), False otherwise.
        :rtype: bool
        """
        return self.coordinator.check_and_save_dirty(parent=self)

    def _save_current_item_wrapper(self) -> None:
        """
        Wrapper to call coordinator's save method and update status bar.
        
        :rtype: None
        """
        item_id = self.coordinator.current_item_id
        view = self.coordinator.current_view
        
        if self.coordinator.save_current_item(item_id, view, parent=self):
            item_type = 'Chapter' if view == ViewType.CHAPTER_EDITOR else 'Lore Entry'
            self.statusBar().showMessage(f"{item_type} ID {item_id} saved successfully.", 3000)
        # Note: Error messages are handled by the Coordinator via QMessageBox.

    def _handle_chapter_loaded(self, chapter_id: int, content: str, tag_names: list[str]) -> None:
        """
        Receives loaded chapter data from coordinator and updates the editor/status.
        
        :param chapter_id: The ID of the chapter.
        :type chapter: int
        :param content: The content of the chapter.
        :type content: str
        :param tag_names: A list of all the tag names for the chapter.
        :type tag_names: list[str]

        :rtype: None
        """

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

    def _handle_lore_loaded(self, lore_id: int, title: str, category: str, content: str, tag_names: list[str]) -> None:
        """
        Receives loaded lore data from coordinator and updates the editor/status.
        
        :param lore_id: The ID of the lore entry.
        :type lore_id: int
        :param title: The title of the lore entry.
        :type title: str
        :param category: The category of the lore entry.
        :type category: str
        :param content: The content of the lore entry.
        :type content: str
        :param tag_names: A list of all the tag names that the lore entry has.
        :type tag_names: list[str]

        :rtype: None
        """
        
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
        """
        Updates the title in the LoreOutlineManager when the editor title changes (relayed by coordinator).
        
        :param lore_id: The ID of the lore entry.
        :type lore_id: int
        :param new_title: The new title of the lore entry.
        :type new_title: str

        :rtype: None
        """
        if self.current_view == ViewType.LORE_EDITOR:
            # Note: Outline Manager must have a helper method to find the item by ID
            item = self.lore_outline_manager.find_lore_item_by_id(lore_id)
            if item:
                # Block signals to prevent _handle_item_renamed from firing back to the repo
                self.lore_outline_manager.blockSignals(True)
                item.setText(0, new_title)
                self.lore_outline_manager.blockSignals(False)

    def _handle_character_loaded(self, char_id: int, name: str, description: str, status: str) -> None:
        """
        Receives loaded character data from coordinator and updates the editor/status.
        
        :param char_id: The Character ID to load.
        :type char_id: int
        :param name: The name of the character.
        :type name: str
        :param description: The description of the character.
        :type descriptionL str
        :param status: The status of the character.
        :type status: str

        :rtype: None
        """

        if not name:
            self.character_editor_panel.set_enabled(False)
            self.statusBar().showMessage(f"Error loading Character ID {char_id}.")
            return
        
        self.character_editor_panel.load_character(char_id, name, description, status)
        self.character_editor_panel.set_enabled(True)
        self.character_editor_panel.mark_saved()
        self.statusBar().showMessage(f"Character ID {char_id} selected and loaded.")

    def _update_character_outline_name(self, char_id: int, new_name: str) -> None:
        """
        Updates the name in the CharacterOutlineManager when the editor name changes (relayed by coordinator).
        
        :param char_id: The ID of the Character.
        :type char_id: int
        :param new_name: The new name to set the Character to.
        :type new_name: str

        :rtype: None
        """
        if self.current_view == ViewType.CHARACTER_EDITOR:
            item = self.character_outline_manager.find_character_item_by_id(char_id)
            if item:
                # Block signals to prevent _handle_item_renamed from firing back to the repo
                self.character_outline_manager.blockSignals(True)
                item.setText(0, new_name)
                self.character_outline_manager.blockSignals(False)
    
    # -------------------------------------------------------------------------
    # I/O Handlers (Export/Settings)
    # -------------------------------------------------------------------------

    def _export(self) -> None:
        """
        Opens the :py:class:`~app.ui.dialogs.ExporterDialog`. 
        
        If accepted, it delegates the export logic to the appropriate exporter 
        class (:py:class:`~app.services.story_exporter.StoryExporter`, etc.).
        
        :rtype: None
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
        
        :param export_type: The type of content to export (e.g., 'Story (All Chapters)').
        :type export_type: str
        :param selected_ids: A list of integer IDs for selected items (empty for full story).
        :type selected_ids: int

        :rtype: int
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
                    QMessageBox.warning(self, "Export Error", "No Lore Entries were selected for export.")

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
        """
        Opens the :py:class:`~app.ui.dialogs.SettingsDialog`. 
        
        If accepted, it saves the new settings and applies the new theme and geometry.
        
        :rtype: None
        """

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

        :param new_settings: A dictionary of the new settings e.g {window_size: 800x600}
        :type new_settings: dict

        :rtype: None
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
        to the internal settings dictionary.
        
        Note: This only updates the internal state; the settings are saved 
        to disk upon application close or when explicitly requested via the 
        Settings Dialog.
        
        :rtype: None
        """
        # Get the geometry of the non-frame window (content area)
        rect = self.geometry()

        self.current_settings['window_width'] = rect.width()
        self.current_settings['window_height'] = rect.height()
        self.current_settings['window_pos_x'] = rect.x()
        self.current_settings['window_pos_y'] = rect.y()

        # Persist the updated settings immediately
        self.settings_manager.save_settings(self.current_settings)