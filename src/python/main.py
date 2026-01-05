import sys
import os
import json
from PySide6.QtWidgets import QApplication

from .services.settings_manager import SettingsManager
from .db_connector import DBConnector
from .main_window import MainWindow
from .start_menu_window import StartMenuWindow
from .utils.logger import setup_logger, get_logger
from .utils.exceptions import ConfigurationError
from .utils.error_handler import install_system_exception_hook
from .utils.events import Events
from .utils.event_bus import bus, receiver

logger = get_logger(__name__)

class ApplicationFlowManager:
    """
    Manages the application flow, switching between the start menu and main window.
    """
    def __init__(self, app: QApplication, settings_manager: SettingsManager) -> None:
        """
        Instatiates the ApplicationFlowManager Class.
        
        :param app: Description
        :type app: :py:class:`~PySide6.QtWidgets.QApplication`

        :rtype: None
        """ 

        bus.register_instance(self)

        self.app = app
        
        # 1. Instantiate Application-wide Service
        self.settings_manager = settings_manager
        self.settings = self.settings_manager.load_settings()
        last_project_path = self.settings['last_project_path']

        # 2. Hold references to the windows
        self.start_menu = None
        self.main_window = None

        # 3. Start the application with the initial window
        if last_project_path == "":
            self.show_start_menu()
        else:
            try:
                self.show_main_window(last_project_path)
            except Exception:
                self.show_start_menu()

    def show_start_menu(self, is_new_project: bool = False) -> None:
        """
        Initializes and shows the StartMenuWindow.

        :param is_new_project: If True, immediately trigger the new project dialog 
                               upon showing the start menu.
        :type is_new_project: bool
        
        :rtype: None
        """
        # Clean up any open windows
        if self.main_window:
            self.main_window.close()
            self.main_window = None

        self.start_menu = StartMenuWindow(settings_manager=self.settings_manager)
        
        # 4. Connect the signal that tells us a project is ready to open
        self.start_menu.project_opened.connect(self.show_main_window)
        
        self.start_menu.show()

        if is_new_project:
            self.start_menu.new_project_button.click()

    def show_main_window(self, project_path: str) -> None:
        """
        Slot to switch from the Start Menu to the Main Window.
        
        This method is responsible for connecting to the project-specific database
        and passing it to the main application window.

        :param project_path: The path to the project.
        :type project_path: str

        :rtype: None
        """
        # 1. Close the Start Menu
        self.start_menu.close() if self.start_menu else None
        self.start_menu = None

        self.settings ['last_project_path'] = project_path
        self.settings_manager.save_settings(self.settings)
        
        # --- Project Configuration (NEW DICT APPROACH) ---
        project_name_from_path = os.path.basename(project_path)
        project_settings_file = os.path.join(project_path, "config", "Project_Settings.nfp")
        
        project_config = {}
        
        try:
            with open(project_settings_file, 'r', encoding='utf-8') as f:
                project_config = json.load(f)
        except FileNotFoundError as e:
            pass

        # Construct the project settings dictionary
        db_file_name = project_config.get('database_file', f"{project_name_from_path}.db")
        
        db_file_path = os.path.join(project_path, db_file_name)

        project_config['project_path'] = project_path
        project_config['db_file_path'] = db_file_path

        project_title = project_config.get('project_name')
        
        # --- DBConnector Logic ---
        # Instantiate and connect the DBConnector for the new project
        db_connector = DBConnector(db_path=project_config['db_file_path']) 
        try:
            if db_connector.connect():
                db_connector.initialize_schema() 
                logger.info(f"Project database setup verified for: {project_title}.db.")
            else:
                # If connect() fails, raise a specific error to halt execution
                raise ConfigurationError(f"Database connection failed for project: {project_title}")
        except Exception as e:
            logger.critical(f"FATAL: Failed to connect or initialize database schema at "
                            f"{db_connector.db_path}.", exc_info=True)
            # Assuming ConfigurationError is a suitable application-level error wrapper
            raise ConfigurationError("A critical error occurred while setting up the project \
                                     database. See log for details.") from e

        # Initialize and show the Main Window
        self.main_window = MainWindow(
            project_settings=project_config,
            settings_manager=self.settings_manager,
            db_connector=db_connector
        )

        self.main_window.show()

    @receiver(Events.PROJECT_NEW_REQUESTED)
    def handle_new_project_request(self, data: dict = None) -> None:
        """
        Handles event to switch to Start Menu for a new project.
        
        :param data: Empty Dict, No needed parameters.
        :type data: dict

        :rtype: None
        """
        if self.main_window and not self.main_window.save_helper():
            return  # User cancelled due to unsaved changes
        self.show_start_menu(is_new_project=True)

    @receiver(Events.PROJECT_OPEN_REQUESTED)
    def handle_open_project_request(self, data: dict = None) -> None:
        """
        Handles event to switch to Start Menu to open an existing project.
        
        :param data: Empty Dict, No needed parameters.
        :type data: dict

        :rtype: None
        """
        if self.main_window and not self.main_window.save_helper():
            return
        self.show_start_menu(is_new_project=False)

def main() -> None:
    """
    The entry point of the Narrative Forge application.
    
    :rtype: None
    """

    settings_manager = SettingsManager()
    app_settings = settings_manager.load_settings()
    DEBUG_MODE = app_settings.get("debug_mode", False)

    setup_logger(debug_mode=DEBUG_MODE)
    logger = get_logger(__name__)
    install_system_exception_hook()

    logger.info("Narrative Forge application is starting up.")
    if DEBUG_MODE:
        logger.debug(f"Debug Mode is active. Logging level set to DEBUG.")

    app = QApplication(sys.argv)

    # Start the application flow
    appFlowManager = ApplicationFlowManager(app, settings_manager=settings_manager)

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
