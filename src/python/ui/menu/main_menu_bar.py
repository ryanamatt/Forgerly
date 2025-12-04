# src/python/ui/menu/main_menu_bar.py

from PyQt6.QtWidgets import QMenuBar, QMessageBox
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QIcon, QAction
import sys
from ...utils.constants import ViewType

class MainMenuBar(QMenuBar):
    """
    Handles the creation and signal emission for the application's main menu bar.
    It separates UI presentation (menu items) from business logic (what happens 
    when an item is clicked, which is handled by MainWindow/Coordinator).
    """
    # --- Signals for the MainWindow to connect to ---
    save_requested = pyqtSignal()
    export_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    
    new_chapter_requested = pyqtSignal()
    new_lore_requested = pyqtSignal()
    new_character_requested = pyqtSignal()

    view_switch_requested = pyqtSignal(int)

    def __init__(self, current_view: ViewType, app_version: str, is_macos: bool, parent=None) -> None:
        super().__init__(parent=parent)
        self.current_view = current_view
        self.app_version = app_version

        self._mod_key = "Meta" if is_macos else "Ctrl"

        self._setup_menus()

    def _setup_menus(self) -> None:
        """Sets up the File, View, and Help menus."""
        self._setup_file_menu()
        self._setup_view_menu()
        self._setup_help_menu()

    def _setup_file_menu(self) -> None:
        file_menu = self.addMenu("&File")

        # New Actions (connects directly to repository via MainWindow/Coordinator)
        new_chapter_action = QAction("New Chapter", self)
        new_chapter_action.triggered.connect(self.new_chapter_requested.emit)
        file_menu.addAction(new_chapter_action)

        new_lore_action = QAction("New Lore Entry", self)
        new_lore_action.triggered.connect(self.new_lore_requested.emit)
        file_menu.addAction(new_lore_action)

        new_character_action = QAction("New Character", self)
        new_character_action.triggered.connect(self.new_character_requested.emit)
        file_menu.addAction(new_character_action)
        
        file_menu.addSeparator()

        # Save Action
        save_action = QAction("&Save Content", self)
        save_action.setShortcut(f"{self._mod_key}+S")
        save_action.triggered.connect(self.save_requested.emit) 
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        # Export Action
        export_action = QAction("&Export...", self)
        export_action.setShortcut(f"{self._mod_key}+E")
        export_action.triggered.connect(self.export_requested.emit)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()

        # Settings Action
        settings_action = QAction("&Settings", self)
        settings_action.setShortcut(f"{self._mod_key}+,")
        settings_action.triggered.connect(self.settings_requested.emit)
        file_menu.addAction(settings_action)

        # Exit Action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(f"{self._mod_key}+Q")
        exit_action.triggered.connect(self.parent().close) # Use parent() close for convenience
        file_menu.addAction(exit_action)

    def _setup_view_menu(self) -> None:
        """Sets up actions for switching between different application views."""
        self.view_menu = self.addMenu("&View")

        # Chapter Outline View Action
        self.view_chapter_action = QAction("Chapter Outline", self)
        self.view_chapter_action.setCheckable(True)
        self.view_chapter_action.setChecked(self.current_view == ViewType.CHAPTER_EDITOR)
        self.view_chapter_action.triggered.connect(lambda: self.view_switch_requested.emit(ViewType.CHAPTER_EDITOR))
        self.view_menu.addAction(self.view_chapter_action)

        # Lore Outline View Action
        self.view_lore_action = QAction("Lore Outline", self)
        self.view_lore_action.setCheckable(True)
        self.view_lore_action.setChecked(self.current_view == ViewType.LORE_EDITOR)
        self.view_lore_action.triggered.connect(lambda: self.view_switch_requested.emit(ViewType.LORE_EDITOR))
        self.view_menu.addAction(self.view_lore_action)

        # Character Outline View Action
        self.view_character_action = QAction("Character Outline", self)
        self.view_character_action.setCheckable(True)
        self.view_character_action.setChecked(self.current_view == ViewType.CHARACTER_EDITOR)
        self.view_character_action.triggered.connect(lambda: self.view_switch_requested.emit(ViewType.CHARACTER_EDITOR))
        self.view_menu.addAction(self.view_character_action)

        self.view_menu.addSeparator()

        # Relationship Graph View Action
        self.view_relationship_action = QAction("Relationship Graph", self)
        self.view_relationship_action.setCheckable(True)
        self.view_relationship_action.setChecked(self.current_view == ViewType.RELATIONSHIP_GRAPH)
        self.view_relationship_action.triggered.connect(lambda: self.view_switch_requested.emit(ViewType.RELATIONSHIP_GRAPH))
        self.view_menu.addAction(self.view_relationship_action)

    def _setup_help_menu(self) -> None:
        """Sets up the Help menu."""
        help_menu = self.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def _show_about_dialog(self) -> None:
        """Displays the application's About dialog."""
        QMessageBox.about(
            self,
            f"About The Narrative Forge v{self.app_version}",
            f"<h2>The Narrative Forge</h2>"
            f"<p>Version: {self.app_version}</p>"
            f"<p>A writing application designed for worldbuilders and novel writers.</p>"
            f"<p>Built with Python and PyQt6.</p>"
        )

    def update_view_checkmarks(self, current_view: ViewType) -> None:
        """
        Updates the checked state of the view menu actions.
        
        Args:
            current_view: The current view ViewType
        """
        self.view_chapter_action.setChecked(current_view == ViewType.CHAPTER_EDITOR)
        self.view_lore_action.setChecked(current_view == ViewType.LORE_EDITOR)
        self.view_character_action.setChecked(current_view == ViewType.CHARACTER_EDITOR)
        self.view_relationship_action.setChecked(current_view == ViewType.RELATIONSHIP_GRAPH)