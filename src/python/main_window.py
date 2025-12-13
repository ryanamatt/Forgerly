# src/python/main_window.py

from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QMessageBox, QDialog, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QCloseEvent, QResizeEvent, QIcon
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
from .ui.dialogs.project_stats_dialog import ProjectStatsDialog

from .db_connector import DBConnector

from .services.settings_manager import SettingsManager
from .services.app_coordinator import AppCoordinator
from .services.story_exporter import StoryExporter
from .services.character_exporter import CharacterExporter
from .services.lore_exporter import LoreExporter

from .utils._version import __version__
from .utils.theme_utils import apply_theme
from .utils.constants import ViewType, ExportType
from .utils.exceptions import ConfigurationError, EditorContentError
from .utils.logger import get_logger

logger = get_logger(__name__)

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

    project_open_requested = pyqtSignal() 
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (bool): Emitted when the user selects 
    'Open Project' from the file menu. 
    """
    project_new_requested = pyqtSignal()
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (bool): Emitted when the user selects 
    'New Project' from the file menu. 
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
        logger.debug("MainWindow initialization started.")

        self.project_settings = project_settings
        self.project_path = self.project_settings['project_path']

        # need to know if macOS for differences with Ctrl or Cmd Key
        self.is_macos = sys.platform == 'darwin'
        logger.debug(f"Platform detected: {'macOS' if self.is_macos else sys.platform}.")

        # This is a workaround to allow the taskbar to have the same icon as the window icon on windows
        if sys.platform.startswith('win'):
            try:
                # We use an application ID to group windows under the correct icon on the taskbar
                appID = f"narrative-forge.{__version__}"
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appID)
                logger.info(f"Windows AppUserModelID set to '{appID}'.")
            except AttributeError:
                logger.warning("Failed to set Windows AppUserModelID (ctypes.windll.shell32 not available or AttributeError).")
                pass

        # Temporary Project Title will need to be changed to actual users project title
        self.project_title = project_settings['project_name'] if project_settings['project_name'] != "" else "Project Title"

        self.setWindowTitle(f"The Narrative Forge v{__version__}")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon(os.path.join('resources', 'logo.ico')))

        # Flag to prevent geometry saving during initialization
        self._is_ready_to_save_geometry = False
        
        # Initialize DB Connector
        self.db_connector = db_connector
        try:
            if self.db_connector.connect():
                self.db_connector.initialize_schema() 
                logger.info(f"Project database setup verified for: {self.project_title}.db.")
            else:
                # If connect() fails, raise a specific error to halt execution
                raise ConfigurationError(f"Database connection failed for project: {self.project_title}")
        except Exception as e:
            logger.critical(f"FATAL: Failed to connect or initialize database schema at {self.db_connector.db_path}.", exc_info=True)
            # Assuming ConfigurationError is a suitable application-level error wrapper
            raise ConfigurationError("A critical error occurred while setting up the project database. See log for details.") from e

        # --- Initialize Coordinator & Repositories ---
        # Coordinator now manages all repositories and business logic
        self.coordinator = AppCoordinator(self.db_connector)
        logger.debug("AppCoordinator initialized.")

        self.story_exporter = StoryExporter(self.coordinator, self.project_title)
        self.character_exporter = CharacterExporter(self.coordinator, self.project_title)
        self.lore_exporter = LoreExporter(self.coordinator, self.project_title)
        logger.debug("Exporters initialized.")

        # --- Settings and Theme Management ---
        self.settings_manager = settings_manager
        self.current_settings = self.settings_manager.load_settings()
        self._apply_settings(self.current_settings)
        logger.info(f"Current theme applied: {self.current_settings.get('theme', 'N/A')}.")

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
        logger.debug("Editors linked to Coordinator and signals connected.")

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

        # Enable geometry saving after initial setup is complete
        self._is_ready_to_save_geometry = True

        logger.info("MainWindow initialized and default view set to Chapter Editor.")

        # Geomtry Save Timer
        self._geometry_save_timer = QTimer(self)
        self._geometry_save_timer.setSingleShot(True)
        # Connect the timer's timeout signal to the save method
        self._geometry_save_timer.timeout.connect(self._save_geometry_to_settings)

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

        # If check_and_save_dirty returns False, the user canceled the exit.
        if not self.coordinator.check_and_save_dirty(parent=self):
            logger.debug("Close event ignored: User canceled due to unsaved changes.")
            event.ignore()
            return
        
        try:
            self._save_geometry_to_settings()

            if hasattr(self, 'main_splitter') and self.main_splitter:
                current_sizes = self.main_splitter.sizes()
                if current_sizes:
                    outline_width = current_sizes[0]
                    self.current_settings['outline_width_pixels'] = outline_width
                    logger.debug(f"Saved main splitter width: {outline_width} pixels.")

            self.current_settings['last_project_path'] = self.project_path
            self.settings_manager.save_settings(self.current_settings)
            logger.info("Application settings (geometry, splitter size, last project) saved successfully.")

        except Exception as e:
            logger.error(f"Failed to save application settings during close. Proceeding with shutdown. Error: {e}", exc_info=True)


        # Close the database connection
        if self.db_connector:
            try:
                self.db_connector.close()
                logger.info("Project database connection closed.")
            except Exception as e:
                # Log the error but continue to allow the window to close
                logger.error(f"Error closing database connection: {e}", exc_info=True)

        # Accept the close event
        logger.info("MainWindow successfully closed.")
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
        # If a new resize event arrives before the 500ms timeout, the timer 
        # is reset, and the save operation is deferred.
        if hasattr(self, '_geometry_save_timer'):
            self._geometry_save_timer.start(500) 
            logger.debug("Resize event received. Debouncing geometry save.")

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
        logger.info(f"Requested view switch to: {view}")

        if not self.coordinator.check_and_save_dirty(parent=self):
            logger.debug("View switch canceled by user due to unsaved changes.")
            return
        
        if self.current_view == view:
            logger.debug(f"View is already set to {view}. Aborting switch.")
            return
        
        # Update the view and notify coordinator
        self.current_view = view
        self.coordinator.set_current_view(view)
        logger.debug(f"MainWindow state updated to {view}.")
        
        
        # Define a mapping from ViewType to the internal index property name for cleaner access
        view_map = {
            ViewType.CHAPTER_EDITOR: self._chapter_index,
            ViewType.LORE_EDITOR: self._lore_index,
            ViewType.CHARACTER_EDITOR: self._character_index,
            ViewType.RELATIONSHIP_GRAPH: self._relationship_index,
        }
    
        # Use .get() with a default value to handle unexpected or unhandled views safely
        view_index = view_map.get(self.current_view, -1)
            
        # Switch the QStackedWidgets to the correct panel index
        if view_index != -1:
            self.outline_stack.setCurrentIndex(view_index)
            self.editor_stack.setCurrentIndex(view_index)
            logger.debug(f"Switched outline and editor stacks to index {view_index}.")
        else:
            logger.error(f"Failed to find a stack index for ViewType: {self.current_view}")
        
        # 4. Disable the newly visible editor until an item is selected
        editor = self.coordinator.get_current_editor()
        if not editor:
            # This shouldn't happen if coordinator is set up correctly, but is a good safety check
            logger.warning(f"Coordinator returned no editor for view: {self.current_view}")
            return

        if self.current_view == ViewType.RELATIONSHIP_GRAPH:
            # The relationship editor typically manages its own loading logic
            # and should remain enabled to show the graph.
            self.relationship_editor_panel.request_load_data.emit()
            # Ensure it is explicitly enabled (if it was disabled by a previous logic path)
            editor.set_enabled(True) 
            logger.debug("Requested data load for Relationship Graph and ensured it is enabled.")
        else:
            # Standard editors (Chapter, Lore, Character) should be disabled 
            # until a specific item is selected from the outline.
            editor.set_enabled(False)
            logger.debug(f"{self.current_view} editor disabled (awaiting item selection).")

        self.main_menu_bar.update_view_checkmarks(current_view=self.current_view)

    # -------------------------------------------------------------------------
    # UI Setup
    # -------------------------------------------------------------------------

    def _setup_ui(self) -> None:
        """
        Creates the main window structure, including the menu bar, the central 
        splitter, and the stacked widgets for outlines and editors.
        
        :rtype: None
        """
        logger.info("Initializing main application UI structure.")
        
        # 2. Instantiate Main Components
        self.chapter_outline_manager = ChapterOutlineManager(project_title=self.project_title, chapter_repository=self.coordinator.chapter_repo)
        self.chapter_editor_panel = ChapterEditor(self.current_settings, self.coordinator)
        self.lore_outline_manager = LoreOutlineManager(lore_repository=self.coordinator.lore_repo, coordinator=self.coordinator)
        self.lore_editor_panel = LoreEditor()
        self.character_outline_manager = CharacterOutlineManager(character_repository=self.coordinator.character_repo)
        self.character_editor_panel = CharacterEditor()
        self.relationship_outline_manager = RelationshipOutlineManager(relationship_repository=self.coordinator.relationship_repo)
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
        logger.debug(f"UI Stack Indices: Chapter={self._chapter_index}, Lore={self._lore_index}, Character={self._character_index}, Relationship={self._relationship_index}")

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

        logger.info("UI setup finalized.")

    # -------------------------------------------------------------------------
    # Signal Connections
    # -------------------------------------------------------------------------

    def _connect_components(self) -> None:
        """
        Connects signals from custom widgets to slots in the main window and coordinator.
        
        :rtype: None
        """
        logger.info("Connecting all application UI and data components.")

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
        self.main_menu_bar.new_chapter_requested.connect(self.coordinator.chapter_repo.create_chapter)
        self.main_menu_bar.new_lore_requested.connect(self.coordinator.lore_repo.create_lore_entry)
        self.main_menu_bar.new_character_requested.connect(self.coordinator.character_repo.create_character)

        self.main_menu_bar.save_requested.connect(self._save_current_item_wrapper)
        self.main_menu_bar.export_requested.connect(self._export)
        self.main_menu_bar.settings_requested.connect(self._open_settings_dialog)

        # Connections for MainMenuBar Projects
        self.main_menu_bar.new_project_requested.connect(lambda: self._request_project_switch(is_new=True))
        self.main_menu_bar.open_project_requested.connect(lambda: self._request_project_switch(is_new=False))

        # Connect the view switching signal from the menu bar
        self.main_menu_bar.view_switch_requested.connect(self._switch_to_view)
        
        # Connect Main Menu Project Stats Dialog Openm
        self.main_menu_bar.project_stats_requested.connect(self._open_project_stats_dialog)
        
        # --- Coordinator (Coordinator signal OUT -> Editor/UI slot IN) ---
        # The coordinator signals the editors when data is ready
        self.coordinator.chapter_loaded.connect(self._handle_chapter_loaded)
        self.coordinator.lore_loaded.connect(self._handle_lore_loaded)
        self.coordinator.char_loaded.connect(self._handle_character_loaded)
        self.coordinator.graph_data_loaded.connect(self.relationship_editor_panel.load_graph)
        
        self.relationship_outline_manager.relationship_types_updated.connect(self.coordinator.reload_relationship_graph_data)

        logger.info("Component signal connections complete.")

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
        action = "New Project" if is_new else "Open Existing Project"
        logger.info(f"Project switch requested: {action}. Initiating dirty state check.")

        # Check for and save unsaved changes before switching
        # The coordinator handles the QMessageBox logic and returns False if the user cancels.
        if not self.coordinator.check_and_save_dirty(parent=self):
            logger.info(f"User cancelled {action} action during save prompt. Aborting switch.")
            return

        logger.debug(f"Dirty check passed. Emitting project close and open signal for: {action}.")

        # Emit the signal to the ApplicationFlowManager (slot: _handle_project_switch_request in main.py)
        if is_new:
            self.project_new_requested.emit()
        if is_new ==False:
            self.project_open_requested.emit()

        logger.debug(f"Signal emitted to ApplicationFlowManager. Current MainWindow is now closing.")

    # -------------------------------------------------------------------------
    # Logic Delegation / Handlers
    # -------------------------------------------------------------------------

    def _check_save_before_change(self) -> bool:
        """
        Prompts the user to save if the active editor is dirty via the Coordinator.

        :returns: Returns True if safe to proceed (saved or discarded), False otherwise.
        :rtype: bool
        """
        logger.info("Checking for unsaved changes before selection change...")
        # The coordinator handles the prompt and returns the result of the user's action
        is_safe_to_proceed = self.coordinator.check_and_save_dirty(parent=self)
        
        if is_safe_to_proceed:
            logger.debug("Dirty check passed. Safe to proceed with item change.")
        else:
            logger.info("Dirty check failed. Item change was cancelled by user.")
            
        return is_safe_to_proceed

    def _save_current_item_wrapper(self) -> None:
        """
        Wrapper to call coordinator's save method and update status bar.
        
        :rtype: None
        """

        #________
        # NOTE THIS FUNCTION FAILS TO SAVE TAGS  (TAGS)
        # TREAT THEM AS VIEWS

        item_id = self.coordinator.current_item_id
        view = self.coordinator.current_view
        
        # Check if there is an active item to save before proceeding
        if item_id is None:
            self.statusBar().showMessage("No active item selected or loaded to save.", 3000)
            logger.warning("Save requested, but no active item (ID is None). Operation aborted.")
            return

        logger.info(f"Save requested for item ID: {item_id} in view: {view}")
        
        # Delegate the save logic to the coordinator
        if self.coordinator.save_current_item(item_id, view, parent=self):
            # Determine the user-friendly name for the item type
            if view == ViewType.CHAPTER_EDITOR:
                item_type = 'Chapter'
            elif view == ViewType.LORE_EDITOR:
                item_type = 'Lore Entry'
            elif view == ViewType.CHARACTER_EDITOR:
                item_type = 'Character'
            else:
                item_type = 'Item' # Fallback for other views
                
            # Success message in status bar
            message = f"{item_type} ID {item_id} saved successfully."
            self.statusBar().showMessage(message, 3000)
            logger.info(message)
        else:
            # Saving failed (e.g., database error). 
            # Note: QMessageBox errors are handled by the Coordinator, so we just log here.
            logger.error(f"Failed to save item ID: {item_id} in view: {view}. Check coordinator logs for details.")
            self.statusBar().showMessage("Error: Failed to save the current item. See logs.", 5000)

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
        logger.info(f"Chapter load attempt for ID: {chapter_id}.")

        # --- Coordinator-Reported Error Check ---
        # This check relies on the coordinator embedding a specific error string on failure.
        if "Error Loading Chapter" in content:
            logger.warning(f"Coordinator signaled a load error for Chapter ID {chapter_id}.")
            # Use the error content to display the issue directly to the user
            self.chapter_editor_panel.set_html_content(content)
            self.chapter_editor_panel.set_enabled(False)
            self.statusBar().showMessage(f"Error loading Chapter ID {chapter_id}. See editor for details.", 5000)
            return

        # --- Successful Load & UI Update ---
        try:
            self.chapter_editor_panel.set_html_content(content)
            self.chapter_editor_panel.set_tags(tag_names)
            self.chapter_editor_panel.set_enabled(True)
            self.chapter_editor_panel.mark_saved() # Important: Reset dirtiness after load

            # Success update
            self.statusBar().showMessage(f"Chapter ID {chapter_id} selected and loaded.", 3000)
            logger.info(f"Chapter ID {chapter_id} successfully loaded into the editor (tags: {len(tag_names)}).")

        except EditorContentError as e:
            # --- Critical UI/Editor Error ---
            # Catches failures that happen *within* the editor widget itself (e.g., malformed HTML)
            error_message = f"FATAL UI Error loading Chapter ID {chapter_id}: Editor failed to render content."
            logger.critical(error_message, exc_info=True)
            
            QMessageBox.critical(
                self, 
                "Editor Load Error", 
                f"The editor failed to display content for Chapter ID {chapter_id} due to an internal UI issue. Please check the application log for details."
            )
            # Ensure the editor is disabled to prevent further interaction after a critical failure
            self.chapter_editor_panel.set_enabled(False)

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
        logger.info(f"Lore load attempt for ID: {lore_id}. Title: '{title}'.")

        # Check for Coordinator-Reported Failure (e.g., item not found)
        if not title: 
            logger.warning(f"Coordinator signaled a load error for Lore ID {lore_id}. Title was empty.")
            
            # Disable the editor panel and report the failure
            self.lore_editor_panel.set_enabled(False)
            self.statusBar().showMessage(f"Error: Lore Entry ID {lore_id} could not be loaded.", 5000)
            return
            
        # Successful Load & UI Update
        try:
            # The LoreEditor handles setting its internal state (title, category, content, tags)
            self.lore_editor_panel.load_lore(lore_id, title, category, content, tag_names)
            
            self.lore_editor_panel.set_enabled(True)
            self.lore_editor_panel.mark_saved() # Reset dirtiness after load

            # Success update
            self.statusBar().showMessage(f"Lore Entry '{title}' (ID {lore_id}) selected and loaded.", 3000)
            logger.info(f"Lore Entry ID {lore_id} ('{title}') successfully loaded.")
            
        except EditorContentError as e:
            # Critical UI/Editor Error Handling
            # Catches failures that happen *within* the editor widget itself (e.g., malformed HTML/UI issue)
            error_message = f"FATAL UI Error loading Lore ID {lore_id} ('{title}'): Editor failed to render content."
            logger.critical(error_message, exc_info=True)
            
            # Notify user with a critical message box
            QMessageBox.critical(
                self, 
                "Editor Load Error", 
                f"The editor failed to display content for Lore Entry ID {lore_id} due to an internal UI issue. Please check the application log for details."
            )
            # Ensure the editor is disabled to prevent further interaction
            self.lore_editor_panel.set_enabled(False)

    def _update_lore_outline_title(self, lore_id: int, new_title: str) -> None:
        """
        Updates the title in the LoreOutlineManager when the editor title changes (relayed by coordinator).
        
        :param lore_id: The ID of the lore entry.
        :type lore_id: int
        :param new_title: The new title of the lore entry.
        :type new_title: str

        :rtype: None
        """
        display_title = new_title.strip()
    
        if not display_title:
            display_title = f"Untitled Lore Entry (ID {lore_id})"
            logger.warning(f"Lore ID {lore_id} saved with an empty title. Using placeholder: '{display_title}'.")

        logger.debug(f"Attempting to update outline title for Lore ID {lore_id} to '{display_title}'.")

        # The outline update only needs to happen if the Lore panel is currently active.
        # If the user is on the Lore view stack, the outline manager should be updated.
        if self.current_view == ViewType.LORE_EDITOR: 
            try:
                item = self.lore_outline_manager.find_lore_item_by_id(lore_id)
                
                if item:
                    # Block signals to prevent the outline's itemChanged signal from firing 
                    # back to the coordinator/repository, causing a recursive update.
                    self.lore_outline_manager.blockSignals(True)
                    item.setText(0, display_title)
                    self.lore_outline_manager.blockSignals(False)
                    
                    logger.info(f"Successfully synchronized Lore Outline title for ID {lore_id}.")
                else:
                    logger.warning(f"Lore Outline item not found for ID {lore_id}. Cannot update title.")
            
            except Exception as e:
                # Catch any unexpected low-level GUI error during the update
                logger.error(f"Critical error during Lore Outline title synchronization for ID {lore_id}.", exc_info=True)

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

        logger.info(f"Character load attempt for ID: {char_id}. Name: '{name}'.")

        # 1. Check for Coordinator-Reported Failure (e.g., item not found)
        if not name:
            logger.warning(f"Coordinator signaled a load error for Character ID {char_id}. Name was empty.")
            self.character_editor_panel.set_enabled(False)
            self.statusBar().showMessage(f"Error: Character ID {char_id} could not be loaded.", 5000)
            return
            
        # 2. Successful Load & UI Update
        try:
            # Delegate the actual setting of data (including rich-text description) to the panel
            self.character_editor_panel.load_character(char_id, name, description, status)
            
            self.character_editor_panel.set_enabled(True)
            self.character_editor_panel.mark_saved() # Reset dirtiness after load
            
            # Success update
            self.statusBar().showMessage(f"Character '{name}' (ID {char_id}) selected and loaded.", 3000)
            logger.info(f"Character ID {char_id} ('{name}') successfully loaded into the editor.")

        except EditorContentError as e:
            # 3. Critical UI/Editor Error Handling
            # Catches failures that happen *within* the editor widget itself
            error_message = f"FATAL UI Error loading Character ID {char_id} ('{name}'): Editor failed to render content."
            logger.critical(error_message, exc_info=True)
            
            QMessageBox.critical(
                self, 
                "Editor Load Error", 
                f"The editor failed to display content for Character '{name}' (ID {char_id}) due to an internal UI issue. Please check the application log for details."
            )
            # Ensure the editor is disabled to prevent further interaction
            self.character_editor_panel.set_enabled(False)

    def _update_character_outline_name(self, char_id: int, new_name: str) -> None:
        """
        Updates the name in the CharacterOutlineManager when the editor name changes (relayed by coordinator).
        
        :param char_id: The ID of the Character.
        :type char_id: int
        :param new_name: The new name to set the Character to.
        :type new_name: str

        :rtype: None
        """
        display_name = new_name.strip()
    
        if not display_name:
            display_name = f"Untitled Character (ID {char_id})"
            logger.warning(f"Character ID {char_id} saved with an empty name. Using placeholder: '{display_name}'.")

        logger.debug(f"Attempting to update outline name for Character ID {char_id} to '{display_name}'.")

        if self.current_view == ViewType.CHARACTER_EDITOR:
            try:
                item = self.character_outline_manager.find_character_item_by_id(char_id)
                
                if item:
                    # Block signals to prevent the outline's itemChanged signal from firing 
                    # back to the coordinator/repository, causing a recursive update loop.
                    self.character_outline_manager.blockSignals(True)
                    item.setText(0, display_name)
                    self.character_outline_manager.blockSignals(False)
                    
                    logger.info(f"Successfully synchronized Character Outline name for ID {char_id}.")
                else:
                    logger.warning(f"Character Outline item not found for ID {char_id}. Cannot update name.")
            
            except Exception as e:
                # Catch any unexpected low-level GUI error during the update
                logger.error(f"Critical error during Character Outline name synchronization for ID {char_id}.", exc_info=True)
    
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
        logger.info("Export process initiated.")
        
        # 1. Check for unsaved changes before exporting. 
        # If check_and_save_dirty returns False, the user canceled the operation.
        if not self.coordinator.check_and_save_dirty(parent=self):
            logger.info("Export canceled by user during unsaved changes check.")
            self.statusBar().showMessage("Export canceled.", 3000)
            return
        
        logger.debug("All data is saved or discarded. Proceeding to ExporterDialog.")
            
        # 2. Open the new ExporterDialog
        try:
            dialog = ExporterDialog(coordinator=self.coordinator, parent=self)
            
            # Connect the signal from the dialog to a slot in the main window.
            # This slot (e.g., `_perform_export`) will execute the export logic 
            # when the user clicks 'Export' and the dialog closes with QDialog.Accepted.
            dialog.export_requested.connect(self._perform_export)

            # Execute the dialog modally. Control flow blocks until the user closes the dialog.
            dialog.exec()
            # The result (accepted/rejected) is handled by the connected signal and its slot.

        except Exception as e:
            # Catch critical errors during dialog creation or execution
            logger.critical("FATAL UI Error: Failed to open or run ExporterDialog.", exc_info=True)
            
            # Notify the user that the setup failed
            QMessageBox.critical(
                self, 
                "Export Setup Error", 
                "The export dialogue failed to open due to an internal application error. Check the application log for details."
            )
        
    def _perform_export(self, export_type: str, selected_ids: list) -> None:
        """
        Delegates the export task based on the type selected in the dialog.
        
        :param export_type: The type of content to export (e.g., 'Story (All Chapters)').
        :type export_type: str
        :param selected_ids: A list of integer IDs for selected items (empty for full story).
        :type selected_ids: int

        :rtype: int
        """
        logger.info(f"Export delegation started: Type='{export_type}', Items selected: {len(selected_ids)}.")
        success = False

        try:
            match export_type:
                case ExportType.STORY | ExportType.CHAPTERS:
                    if export_type == ExportType.STORY:
                        logger.debug("Initiating full story export via StoryExporter.")
                        success = self.story_exporter.export(parent=self)

                    else:  # ExportType.CHAPTERS
                        if selected_ids:
                            logger.debug(f"Initiating chapter export for IDs: {selected_ids}.")
                            success = self.story_exporter.export(parent=self, selected_ids=selected_ids)

                        else:
                            logger.warning("Chapter export requested, but no chapters were selected.")
                            QMessageBox.warning(self, "Export Error", "No chapters were selected for export.")

                case ExportType.LORE:
                    if selected_ids:
                        logger.debug(f"Initiating lore export for IDs: {selected_ids}.")
                        success = self.lore_exporter.export(parent=self, selected_ids=selected_ids)

                    else:
                        logger.warning("Lore export requested, but no entries were selected.")
                        QMessageBox.warning(self, "Export Error", "No Lore Entries were selected for export.")

                case ExportType.CHARACTERS:
                    if selected_ids:
                        logger.debug(f"Initiating character export for IDs: {selected_ids}.")
                        success = self.character_exporter.export(parent=self, selected_ids=selected_ids)

                    else:
                        logger.warning("Character export requested, but no characters were selected.")
                        QMessageBox.warning(self, "Export Error", "No Characters were selected for export.")

                case _:
                    logger.error(f"Unknown export type received: {export_type}")
                    QMessageBox.critical(self, "Export Error", f"Unknown export type: {export_type}")
                    
        except Exception as e:
            # Catch unexpected errors during the exporter service execution (e.g., I/O, database failure)
            logger.critical(f"CRITICAL ERROR during export of type '{export_type}'.", exc_info=True)
            QMessageBox.critical(
                self, 
                "Export Failed", 
                f"A critical error occurred while exporting '{export_type}'. Check the application log for details."
            )
            success = False # Ensure failure state

        # Report final status to the user
        if success is True:
            logger.info(f"Export of type '{export_type}' completed successfully.")
            self.statusBar().showMessage(f"{export_type} exported successfully.", 5000)
        elif success is False:
            # If success is False, it was either due to a critical error (already shown to user) 
            # or a benign cancellation (e.g., closing the file dialog) or a handled error (shown as QMessageBox).
            logger.debug(f"Export of '{export_type}' was canceled or failed gracefully.")

    def _open_settings_dialog(self) -> None:
        """
        Opens the :py:class:`~app.ui.dialogs.SettingsDialog`. 
        
        If accepted, it saves the new settings and applies the new theme and geometry.
        
        :rtype: None
        """

        logger.info("Settings dialog opened.")

        try:
            # 1. Initialize the dialog with current settings
            dialog = SettingsDialog(
                current_settings=self.current_settings,
                settings_manager=self.settings_manager,
                parent=self
            )

            # 2. Execute the dialog and check the result
            if dialog.exec() == QDialog.DialogCode.Accepted:
                
                new_settings = dialog.get_new_settings()
                
                # Log the change before committing
                old_theme = self.current_settings.get('theme', 'N/A')
                new_theme = new_settings.get('theme', 'N/A')
                logger.info(f"Settings accepted by user. Theme change: {old_theme} -> {new_theme}.")
                
                # 3. Save new settings to disk and update internal reference
                self.settings_manager.save_settings(new_settings)
                
                # CRITICAL: Update the internal reference (`self.current_settings`) 
                # to point to the saved and returned dictionary, ensuring the main window 
                # uses the latest values immediately.
                self.current_settings = new_settings 
                
                # 4. Apply non-geometry settings (theme, etc.)
                self._apply_settings(new_settings)
                
                # 5. Provide user feedback
                self.statusBar().showMessage(f"Settings saved and applied. Theme: {self.current_settings['theme']}.", 5000)
                
            else:
                logger.info("Settings dialog closed without saving (rejected or cancelled).")

        except Exception as e:
            # Catch unexpected errors during dialog creation or settings processing
            logger.critical("FATAL ERROR: Failed to process SettingsDialog results.", exc_info=True)
            QMessageBox.critical(
                self, 
                "Settings Error", 
                "A critical error occurred while saving or applying settings. Changes may be lost. Check the application log."
            )

    def _apply_settings(self, new_settings: dict) -> None:
        """
        Applies the loaded or newly changed settings to the application window

        :param new_settings: A dictionary of the new settings e.g {window_size: 800x600}
        :type new_settings: dict

        :rtype: None
        """
        logger.info("Applying new application settings.")
    
        # 1. Apply component-specific settings (e.g., Words Per Minute)
        old_wpm = self.current_settings.get('words_per_minute', 250)
        new_wpm = new_settings.get('words_per_minute', 250)

        if old_wpm != new_wpm:
            logger.debug(f"WPM setting changed: {old_wpm} -> {new_wpm}. Updating ChapterEditor.")
            self.chapter_editor_panel.set_wpm(new_wpm)

        # CRITICAL: Update the main window's internal state to the new settings dictionary
        self.current_settings = new_settings

        # 2. Apply Theme
        current_theme = self.current_settings.get('theme', 'Dark')
        try:
            # apply_theme utility function handles the heavy lifting
            if apply_theme(self, self.current_settings):
                logger.info(f"Theme '{current_theme}' applied successfully.")
            else:
                logger.warning(f"Failed to apply theme '{current_theme}'. Check theme utility/files.")
            
        except Exception as e:
            logger.error(f"Critical error during theme application for '{current_theme}'.", exc_info=True)

        # 3. Apply Window Geometry (Size and Position)
        window_pos_x = self.current_settings.get('window_pos_x', 100) 
        window_pos_y = self.current_settings.get('window_pos_y', 100) 

        try:
            window_width = self.current_settings.get('window_width')
            window_height = self.current_settings.get('window_height')
            
            target_width, target_height = None, None

            if window_width and window_height:
                # Use the dynamically saved geometry (from manual resize/move)
                target_width = window_width
                target_height = window_height
            else:
                # Fallback to the preset size string (e.g., '1200x800')
                window_size_str = self.current_settings.get('window_size', '1200x800')
                
                # This is the vulnerable line for ValueError
                w, h = map(int, window_size_str.split('x'))
                target_width = w
                target_height = h
                
            if target_width and target_height:
                self.setGeometry(window_pos_x, window_pos_y, target_width, target_height)
                logger.debug(f"Window geometry applied: {target_width}x{target_height} at ({window_pos_x}, {window_pos_y}).")

        except ValueError:
            # Catch errors if 'window_size' string is malformed (e.g., '1200_800' or missing 'x')
            logger.error(f"Configuration Error: Window size format is malformed. Setting position only to ({window_pos_x}, {window_pos_y}).", exc_info=True)
            self.move(window_pos_x, window_pos_y)
        except Exception as e:
            logger.critical("Unexpected error occurred while applying window geometry.", exc_info=True)

    def _save_geometry_to_settings(self):
        """
        Helper method to save the current window dimensions and position
        to the internal settings dictionary.
        
        Note: This only updates the internal state; the settings are saved 
        to disk upon application close or when explicitly requested via the 
        Settings Dialog.
        
        :rtype: None
        """
        # Defensive check: Ensure the window is fully initialized before trying to save geometry.
        if not self._is_ready_to_save_geometry:
            logger.debug("Attempted to save geometry before window was ready. Operation skipped.")
            return

        # Get the geometry of the non-frame window (content area)
        rect = self.geometry()
        
        new_width = rect.width()
        new_height = rect.height()
        new_pos_x = rect.x()
        new_pos_y = rect.y()

        # Log the update for traceability (using DEBUG level as this happens frequently)
        logger.debug(
            f"Updating internal geometry state: WxH={new_width}x{new_height}, "
            f"Pos=({new_pos_x}, {new_pos_y})."
        )

        # Update the internal settings dictionary
        self.current_settings['window_width'] = new_width
        self.current_settings['window_height'] = new_height
        self.current_settings['window_pos_x'] = new_pos_x
        self.current_settings['window_pos_y'] = new_pos_y

    def _open_project_stats_dialog(self) -> None:
        """
        Opens the :py:class:`~app.ui.dialogs.ProjectStatsDialog`. 
                
        :rtype: None
        """
        stats_dialog = ProjectStatsDialog(coordinator=self.coordinator, wpm = self.current_settings['words_per_minute'], parent=self)

        stats_dialog.exec()
