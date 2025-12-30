# src/python/ui/menu/main_menu_bar.py

from PySide6.QtWidgets import QMenuBar, QMessageBox
from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QActionGroup, QIcon

from ...resources_rc import *
from ...utils.constants import ViewType, EntityType
from ...utils.logger import get_logger
from ...utils.events import Events
from ...utils.event_bus import bus, receiver

logger = get_logger(__name__)

class MainMenuBar(QMenuBar):
    """
    Handles the creation and signal emission for the application's main menu bar.
    
    It separates UI presentation (menu items) from business logic (what happens 
    when an item is clicked, which is handled by :py:class:`~app.ui.main_window.MainWindow` 
    or :py:class:`~app.services.app_coordinator.AppCoordinator`).
    """

    settings_requested = Signal()
    """
    :py:class:`~PyQt6.QtCore.Signal`: Emitted when the 'Settings' action is triggered.
    """

    def __init__(self, app_version: str, is_macos: bool, parent=None) -> None:
        """
        Initializes the main menu bar.

        :param app_version: The application's version string, used for the About dialog.
        :type app_version: str
        :param is_macos: Flag indicating if the application is running on macOS to set the correct modifier key (Cmd vs Ctrl).
        :type is_macos: bool
        :param parent: The parent Qt widget.
        :type parent: :py:class:`~PyQt6.QtWidgets.QWidget` or None

        :rtype: None
        """
        super().__init__(parent=parent)

        bus.register_instance(self)

        self.app_version = app_version

        self._mod_key = "Meta" if is_macos else "Ctrl"

        self._setup_menus()

        logger.debug("Main Menu Bar initialized.")

    def _setup_menus(self) -> None:
        """
        Sets up the File, View, and Help menus by calling their respective setup methods.
        
        :rtype: None
        """
        self._setup_file_menu()
        self._setup_view_menu()
        self._setup_help_menu()

    def _setup_file_menu(self) -> None:
        """
        Sets up the 'File' menu containing actions like Save, Export, and Settings.
        
        :rtype: None
        """
        file_menu = self.addMenu("&File")

        # Project Actions
        new_project_action = QAction("New Project", self)
        new_project_action.setIcon(QIcon(":icons/project-add.svg"))
        new_project_action.triggered.connect(lambda: bus.publish(Events.PROJECT_NEW_REQUESTED))
        file_menu.addAction(new_project_action)

        open_project_action = QAction("Open Project", self)
        open_project_action.setIcon(QIcon(":icons/project-open.svg"))
        open_project_action.triggered.connect(lambda: bus.publish(Events.PROJECT_OPEN_REQUESTED))
        file_menu.addAction(open_project_action)
        
        file_menu.addSeparator()

        # New Actions (connects directly to repository via MainWindow/Coordinator)
        new_chapter_action = QAction("New Chapter", self)
        new_chapter_action.setIcon(QIcon(":icons/chapter.svg"))
        new_chapter_action.triggered.connect(lambda: bus.publish(Events.NEW_CHAPTER_REQUESTED))
        file_menu.addAction(new_chapter_action)

        new_lore_action = QAction("New Lore Entry", self)
        new_lore_action.setIcon(QIcon(":icons/lore-entry.svg"))
        new_lore_action.triggered.connect(lambda: bus.publish(Events.NEW_LORE_REQUESTED))
        file_menu.addAction(new_lore_action)

        new_character_action = QAction("New Character", self)
        new_character_action.setIcon(QIcon(":icons/character.svg"))
        new_character_action.triggered.connect(lambda: bus.publish(Events.NEW_CHARACTER_REQUESTED))
        file_menu.addAction(new_character_action)
        
        file_menu.addSeparator()

        # Save Action
        save_action = QAction("&Save Content", self)
        save_action.setIcon(QIcon(":icons/save.svg"))
        save_action.setShortcut(f"{self._mod_key}+S")
        save_action.triggered.connect(lambda: bus.publish(Events.PRE_ITEM_CHANGE, data={'skip_check': True}))
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        # Export Action
        export_action = QAction("&Export...", self)
        export_action.setIcon(QIcon(":icons/download.svg"))
        export_action.setShortcut(f"{self._mod_key}+E")
        export_action.triggered.connect(lambda: bus.publish(Events.EXPORT_REQUESTED))
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()

        # Settings Action
        settings_action = QAction("&Settings", self)
        settings_action.setIcon(QIcon(":icons/settings.svg"))
        settings_action.setShortcut(f"{self._mod_key}+,")
        settings_action.triggered.connect(lambda: bus.publish(Events.SETTINGS_REQUESTED))
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        # Exit Action
        exit_action = QAction("E&xit", self)
        exit_action.setIcon(QIcon(":icons/exit.svg"))
        exit_action.setShortcut(f"{self._mod_key}+Q")
        exit_action.triggered.connect(self.parent().close) # Use parent() close for convenience
        file_menu.addAction(exit_action)

        logger.debug("All QActions created and connected.")

    def _setup_view_menu(self) -> None:
        """
        Sets up the 'View' menu which allows switching between the main application panels.
        
        Each view action is a toggle action, displaying a checkmark next to the active view.
        
        :rtype: None
        """
        self.view_menu = self.addMenu("&View")

        self.view_group = QActionGroup(self)
        self.view_group.setExclusive(True)

        # Helper to create and add actions to the menu and group
        def add_view_action(text, icon_path, view_type):
            action = QAction(text, self)
            action.setIcon(QIcon(icon_path))
            action.setCheckable(True)
            
            action.triggered.connect(lambda: bus.publish(Events.VIEW_SWITCH_REQUESTED, data={'view_type': view_type}))
            
            self.view_group.addAction(action)
            self.view_menu.addAction(action)
            return action

        self.view_chapter_action = add_view_action("Chapter Outline", ":icons/chapter.svg", ViewType.CHAPTER_EDITOR)
        self.view_lore_action = add_view_action("Lore Outline", ":icons/lore-entry.svg", ViewType.LORE_EDITOR)
        self.view_character_action = add_view_action("Character Outline", ":icons/character.svg", ViewType.CHARACTER_EDITOR)
        self.view_note_action = add_view_action("Note Outline", ":icons/note.svg", ViewType.NOTE_EDITOR)
        
        self.view_menu.addSeparator()
        
        self.view_relationship_action = add_view_action("Relationship Graph", ":icons/node-tree.svg", ViewType.RELATIONSHIP_GRAPH)

        self.view_menu.addSeparator()

        # Project Statistics (Not part of the group as it's a pop-up, not a toggle view)
        self.project_stats_action = QAction("&Project Statistics", self)
        self.project_stats_action.setIcon(QIcon(":icons/line-chart-line.svg"))
        self.project_stats_action.triggered.connect(lambda: bus.publish(Events.PROJECT_STATS_REQUESTED))
        self.view_menu.addAction(self.project_stats_action)

    def _setup_help_menu(self) -> None:
        """
        Sets up the 'Help' menu, containing the About dialog action.
        
        :rtype: None
        """
        help_menu = self.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.setIcon(QIcon(":icons/information.svg"))
        about_action.setShortcut(f"{self._mod_key}+H")
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def _show_about_dialog(self) -> None:
        """
        Displays the application's About dialog using :py:class:`~PyQt6.QtWidgets.QMessageBox.about`.
        
        It presents the application name, version number, and a brief description.
        
        :rtype: None
        """
        logger.info("Displaying About Dialog.")
        QMessageBox.about(
            self,
            f"About The Narrative Forge v{self.app_version}",
            f"<h2>The Narrative Forge</h2>"
            f"<p>Version: {self.app_version}</p>"
            f"<p>A writing application designed for worldbuilders and novel writers.</p>"
            f"<p>Built with Python and PyQt6.</p>"
        )

    @receiver(Events.VIEW_CHANGED)
    def update_view_checkmarks(self, data: dict) -> None:
        """
        Updates the checked state of the view menu actions based on the current active view.
        
        This visually indicates to the user which panel is currently displayed. If not checked
        the icons is replaced by its icon.

        :param current_view: The current active view type.
        :type current_view: :py:class:`~app.utils.constants.ViewType`
        
        :rtype: None
        """
        current_view = data.get('current_view')
        logger.debug(f"Updating view checkmarks to: {current_view}")
        actions = {
            ViewType.CHAPTER_EDITOR: self.view_chapter_action,
            ViewType.LORE_EDITOR: self.view_lore_action,
            ViewType.CHARACTER_EDITOR: self.view_character_action,
            ViewType.NOTE_EDITOR: self.view_note_action,
            ViewType.RELATIONSHIP_GRAPH: self.view_relationship_action
        }

        for view_type, action in actions.items():
            is_active = (current_view == view_type)
            # setChecked handles unchecking the others via QActionGroup
            if is_active:
                action.setChecked(True)
            
            # Ensure the checkmark has space by hiding the icon on the active item
            action.setIconVisibleInMenu(not is_active)
