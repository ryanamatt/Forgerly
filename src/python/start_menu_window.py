# src/python/start_menu_window.py

import os
import json 
import shutil 
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QFileDialog, QSizePolicy, QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

from .services.settings_manager import SettingsManager

from .utils._version import __version__
from .utils.exceptions import ConfigurationError
from .utils.logger import get_logger

logger = get_logger(__name__)

class StartMenuWindow(QMainWindow):
    """
    A QMainWindow subclass to serve as the initial start menu for the application.

    This window allows the user to create a new project, open an existing project,
    or shows a list of recent projects.
    """

    project_opened = Signal(str)
    """:py:class:`~PyQt6.QtCore.Signal` Emitted when a project path is successfully selected.
                          It carries the string path of the selected project folder.
    """

    def __init__(self, settings_manager: SettingsManager, parent=None) -> None:
        """
        Initializes the StartMenuWindow.

        :param settings_manager: An instance of the SettingsManager to handle
                                 recent project list and other user settings.
        :type settings_manager: settings_manager.SettingsManager
        :param parent: The parent widget, defaults to None.
        :type parent: QWidget, optional

        rtype: None
        """
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setWindowTitle(f"Narrative Forge - Start Menu - {__version__}")
        self.setFixedSize(650, 450)

        self._create_widgets()
        self._create_layouts()
        self._create_signals()

        logger.debug("Start Menu window initialized.")

    def _create_widgets(self) -> None:
        """
        Creates and configures the core widgets for the start menu.
        
        :rtype: None
        """
        # Main Title
        self.title_label = QLabel("Narrative Forge")
        self.title_label.setObjectName("StartMenuTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.title_label.font()
        font.setPointSize(24)
        font.setBold(True)
        self.title_label.setFont(font)

        # Buttons
        self.new_project_button = QPushButton("Create New Project...")
        self.new_project_button.setMinimumHeight(40)
        self.new_project_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.open_project_button = QPushButton("Open Existing Project...")
        self.open_project_button.setMinimumHeight(40)
        self.open_project_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Recent Projects List
        self.recent_label = QLabel("Recent Projects (Not Implemented Yet)")
        self.recent_label.setObjectName("RecentProjectsHeader")

    def _create_layouts(self) -> None:
        """
        Organizes the widgets into layouts.
        
        rtype: None
        """
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(20)

        # Title
        main_layout.addWidget(self.title_label)

        # Action Buttons Layout
        actions_layout = QVBoxLayout()
        actions_layout.addWidget(self.new_project_button)
        actions_layout.addWidget(self.open_project_button)

        # Grouping the main actions for better spacing/alignment
        action_group_widget = QWidget()
        action_group_widget.setLayout(actions_layout)
        action_group_widget.setMaximumWidth(400) # Constrain width for a central look

        # Add a flexible spacer to push everything up slightly
        main_layout.addStretch(1)

        # Add the action group to the main layout
        main_layout.addWidget(action_group_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        # Recent Projects section
        main_layout.addWidget(self.recent_label, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addStretch(2) # Extra stretch at the bottom

    def _create_signals(self):
        """
        Connects widget signals to their respective slots/methods.
        
        :rtype: None
        """
        self.new_project_button.clicked.connect(self._create_new_project)
        self.open_project_button.clicked.connect(self._open_existing_project)

    def _scaffold_project(self, project_path: Path, project_name: str) -> bool:
        """
        Creates the standard Narrative Forge project folder structure and initial files.

        The structure should be:
        [ProjectName]/
        ├── [ProjectName].db
        ├── config/
        |   └── Project_Settings.nfp
        ├── assets/
        ├── exports/

        :param project_path: The full path to the new project's root directory.
        :type project_path: pathlib.Path
        :param project_name: The name of the project, used for files like the database.
        :type project_name: str
        :return: True if scaffolding was successful, False otherwise.
        :rtype: bool
        """
        try:
            # 1. Create subdirectories
            (project_path / "config").mkdir(parents=True, exist_ok=True)
            (project_path / "assets").mkdir(parents=True, exist_ok=True)
            (project_path / "exports").mkdir(parents=True, exist_ok=True)
            logger.debug("Subdirectories created.")

            # 2. Create database file (empty placeholder for now)
            db_path = project_path / f"{project_name}.db"
            db_path.touch()
            logger.debug(f"Database file created at '{db_path}'.")

            # 3. Create config file (JSON with .nfp extension)
            config_path = project_path / "config" / "Project_Settings.nfp"
            initial_config = {
                "project_name": project_name,
                "version": f"{__version__}",
                "database_file": f"{project_name}.db"
            }
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(initial_config, f, indent=4)
            logger.debug(f"Configuration file created at '{config_path}'.")

            return True

        except Exception as e:
            logger.error(f"Failed to scaffold project files for '{project_name}' at '{project_path}'", exc_info=True)
            
            if project_path.is_dir():
                logger.warning(f"Attempting to clean up partially created directory: {project_path}")
                shutil.rmtree(project_path, ignore_errors=True) 
                logger.warning("Cleanup complete (or ignored errors).")
                
            raise ConfigurationError(
                message="Failed to create project files (database, config, or subfolders). Check permissions or disk space.",
                original_exception=e
            )

    def _create_new_project(self) -> None:
        """
        Opens a directory dialog for the user to select the location for a new project,
        prompts for a project name, and creates the project structure.
        
        :rtype: None
        """
        logger.info("New project creation initiated.")

        try:
            # Get the parent folder where the new project folder will be created.
            parent_dir_str = QFileDialog.getExistingDirectory(
                self,
                "Select Parent Location for New Project Folder",
                os.path.expanduser("projects") # Starting directory
            )

            if not parent_dir_str:
                logger.info("New project creation cancelled during directory selection.")
                return # User cancelled directory selection

            # Prompt for the new project name
            project_name, ok = QInputDialog.getText(
                self,
                "New Project Name",
                "Enter the name for your new project:",
                echo=QLineEdit.EchoMode.Normal,
            )

            if not ok or not project_name:
                logger.info("New project creation cancelled during name input.")
                return # User cancelled or entered empty name

            # Basic sanitization for directory name (replace spaces with underscores)
            folder_name = project_name.strip().replace(" ", "_").replace("\\", "").replace("/", "")
            
            if not folder_name:
                logger.warning(f"Project name '{project_name}' resulted in an invalid folder name.")
                QMessageBox.warning(self, "Invalid Name", "The project name resulted in an invalid folder name.")
                return

            # Define the final project path
            project_path = Path(parent_dir_str) / folder_name
            logger.debug(f"Target project path: {project_path}")
            
            # Check if folder already exists
            if project_path.exists():
                logger.warning(f"Target folder already exists: {project_path}")
                QMessageBox.warning(
                    self, 
                    "Project Exists", 
                    f"A folder named '{folder_name}' already exists in the selected location. Please choose a different name or location."
                )
                return

            # Create the root project folder
            project_path.mkdir(parents=True, exist_ok=False)
            logger.info(f"Project root folder created: {project_path}")

            # Scaffold the internal structure
            self._scaffold_project(project_path, project_name)

            # Emit the signal with the path to the newly created project folder
            logger.info(f"Successfully created and opening new project: {project_path}")
            self.project_opened.emit(str(project_path))
        
        except ConfigurationError as ce:
            # Catch ConfigurationError specifically from _scaffold_project
            QMessageBox.critical(
                self,
                "Project Creation Error",
                ce.user_message
            )
        except Exception as e:
            # Catch I/O, permissions, or disk errors during root folder creation
            logger.error(f"Failed to create project folder or structure at '{project_path}'", exc_info=True)
            QMessageBox.critical(
                self,
                "Folder Creation Error",
                f"Could not create the project folder at '{project_path}'.\nDetails: Please check write permissions and disk space."
            )

    def _open_existing_project(self):
        """
        Opens a file dialog for the user to select the project's configuration file.
        
        :rtype: None
        """
        logger.info("Open existing project initiated.")
        project_path = QFileDialog.getExistingDirectory(
            self,
            "Select Existing Project Folder",
            os.path.expanduser("projects")
        )

        if project_path:
            logger.info(f"Existing project folder selected: {project_path}")
            # The AppCoordinator will handle validating the path and opening the project.
            self.project_opened.emit(project_path)
        else:
            logger.info("Open existing project cancelled.")
