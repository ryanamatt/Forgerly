import sys
import os
from PyQt6.QtWidgets import QApplication

from .services.settings_manager import SettingsManager
from .db_connector import DBConnector
from .main_window import MainWindow
from .start_menu_window import StartMenuWindow

class ApplicationFlowManager:
    """
    Manages the application flow, switching between the start menu and main window.
    """
    def __init__(self, app: QApplication) -> None:
        """
        Docstring for __init__
        
        :param app: Description
        :type app: :py:class:`~PyQt6.QtWidgets.QApplication`

        :rtype: None
        """
        self.app = app
        
        # 1. Instantiate Application-wide Service
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.load_settings()
        last_project_path = self.settings['last_project_path']

        # 2. Hold references to the windows
        self.start_menu = None
        self.main_window = None

        # 3. Start the application with the initial window
        if last_project_path == "":
            self.show_start_menu()
        else:
            self.show_main_window(last_project_path)

    def show_start_menu(self) -> None:
        """
        Initializes and shows the StartMenuWindow.
        
        :rtype: None"""
        # Clean up any open windows
        if self.main_window:
            self.main_window.close()
            self.main_window = None

        self.start_menu = StartMenuWindow(settings_manager=self.settings_manager)
        
        # 4. Connect the signal that tells us a project is ready to open
        self.start_menu.project_opened.connect(self.show_main_window)
        
        self.start_menu.show()

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
        
        # --- DBConnector Logic ---
        # 2. Construct the project-specific database file path
        # Project structure: [ProjectName]/[ProjectName].db
        project_name = os.path.basename(project_path)
        db_file_path = os.path.join(project_path, f"{project_name}.db")
        
        # 3. Instantiate and connect the DBConnector for the new project
        db_connector = DBConnector(db_path=db_file_path) 
        db_connector.connect() # Assuming DBConnector has a connect method

        # 4. Initialize and show the Main Window
        self.main_window = MainWindow(
            project_path=project_path,
            settings_manager=self.settings_manager,
            db_connector=db_connector
        )
        self.main_window.show()


def main() -> None:
    """
    The entry point of the Narrative Forge application.
    
    :rtype: None
    """
    app = QApplication(sys.argv)

    # Start the application flow
    manager = ApplicationFlowManager(app)

    sys.exit(app.exec())

if __name__ == '__main__':
    main()