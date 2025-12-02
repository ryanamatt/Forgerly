# src/python/settings_dialog.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QComboBox, 
    QLabel, QDialogButtonBox, QHBoxLayout, QPushButton,
    QMessageBox
)

from ...services.settings_manager import SettingsManager
from ...utils.theme_utils import get_available_themes

class SettingsDialog(QDialog):
    """A dialog window for managing application settings"""

    def __init__(self, current_settings: dict, settings_manager: SettingsManager, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Application Settings")
        self.setGeometry(200, 200, 600, 400)

        self.settings_manager = settings_manager
        self._new_settings = current_settings.copy()

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Window Group Box ---
        window_group = QGroupBox("Window Settings")
        window_layout = QVBoxLayout(window_group)

        window_size_label = QLabel("Select Window Size")
        self.window_size_combo = QComboBox()

        available_sizes = ['1200x800', '800x600']
        self.window_size_combo.addItems(available_sizes)

        current_window_size = self._new_settings.get('window_size', '1200x800')
        index = self.window_size_combo.findText(current_window_size)
        if index != -1:
            self.window_size_combo.setCurrentIndex(index)
        else:
            self.window_size_combo.setCurrentIndex(0)

        window_layout.addWidget(window_size_label)
        window_layout.addWidget(self.window_size_combo)

        # Set the combo box to the current theme
        index = self.window_size_combo.findText(current_window_size)
        if index != -1:
            self.window_size_combo.setCurrentIndex(index)
        else:
            self.window_size_combo.setCurrentIndex(0)

        main_layout.addWidget(window_group)

        # --- Appearance Group Box (Themes) ---
        appearance_group = QGroupBox("Appearance")
        themes_layout = QVBoxLayout(appearance_group)

        # Theme Selection
        theme_label = QLabel("Select Theme:")
        self.theme_combo = QComboBox()
        
        available_themes = get_available_themes()
        self.theme_combo.addItems(available_themes)

        current_theme_name = self._new_settings.get('theme', 'Light')
        
        # Set the combo box to the current theme
        index = self.theme_combo.findText(current_theme_name)
        if index != -1:
            self.theme_combo.setCurrentIndex(index)
        else:
            self.theme_combo.setCurrentIndex(0)

        themes_layout.addWidget(theme_label)
        themes_layout.addWidget(self.theme_combo)

        main_layout.addWidget(appearance_group)

        # --- Standard OK/Cancel Buttons and Revert ---
        
        # 1. Revert Button
        revert_button = QPushButton("Revert to Defaults")
        revert_button.clicked.connect(self._revert_to_defaults)
        
        # 2. OK/Cancel Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        
        # Layout for the button box (Revert on left, OK/Cancel on right)
        h_layout = QHBoxLayout()
        h_layout.addWidget(revert_button)
        h_layout.addStretch(1)
        h_layout.addWidget(button_box)
        
        main_layout.addLayout(h_layout)

    def _on_accept(self):
        """Called when the OK button is pressed. Saves the selected settings."""
        self.selected_window_size = self.window_size_combo.currentText()
        self.selected_theme = self.theme_combo.currentText()
        self.accept()

    def _revert_to_defaults(self):
        """Reverts settings by deleting the user file and updating the dialog UI."""
        reply = QMessageBox.question(
            self,
            "Confirm Revert",
            "Are you sure you want to revert ALL settings to their factory defaults? This will erase your saved preferences.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 1. Delete user file and get defaults from manager
            default_settings = self.settings_manager.revert_to_defaults()
            
            # 2. Update the internal state
            self._new_settings = default_settings.copy()
            
            # 3. Update the UI controls
            new_theme = default_settings.get('theme', 'Light')
            index = self.theme_combo.findText(new_theme)
            if index != -1:
                self.theme_combo.setCurrentIndex(index)
                
            QMessageBox.information(self, "Reverted", "Settings reverted to defaults. Click OK to apply these changes.")
            
    def _on_accept(self):
        """Called when the OK button is pressed. Saves the selected settings to internal state."""
        # Update the internal settings dictionary with current UI values
        self._new_settings['theme'] = self.theme_combo.currentText()
        self._new_settings['window_size'] = self.window_size_combo.currentText()
        
        self.accept()

    def get_new_settings(self) -> dict:
        """Returns the settings dictionary intended to be saved and applied."""
        return self._new_settings