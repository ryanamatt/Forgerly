# src/python/ui/diaglogs/exporter_dialog.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QComboBox, 
    QLabel, QDialogButtonBox, QHBoxLayout, QPushButton,
    QMessageBox
)

from ...services.story_exporter import StoryExporter
from ...utils.theme_utils import get_available_themes

class ExporterDialog(QDialog):
    """A small dialog window to manager exporting parts of the project"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Exporter")
        self.setGeometry(200, 200, 600, 400)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Sets up the UI for the ExporterDialog"""
        main_layout = QVBoxLayout()

        