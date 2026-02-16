# src/python/ui/dialogs/update_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QCheckBox, QFrame
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFont
from ...utils.logger import get_logger

logger = get_logger(__name__)

class UpdateDialog(QDialog):
    """
    A dialog that notifies the user about available application updates.
    
    Displays version information, release notes, and provides options to 
    download the update or skip it.
    """
    def __init__(self, release_info: dict, current_version: str, parent=None) -> None:
        """
        Initializes the UpdateDialog with release information.
        
        :param release_info: Dictionary containing release details 
                            (version, url, body, etc.).
        :type release_info: dict
        :param current_version: The current version of the application.
        :type current_version: str
        :param parent: The parent widget (typically MainWindow).
        :type parent: QWidget
        :rtype: None
        """
        super().__init__(parent)
        
        self.release_info = release_info
        self.current_version = current_version
        self.skip_this_version = False
        
        self.setWindowTitle("Update Available")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self._setup_ui()
        
        logger.debug(f"UpdateDialog opened for version {release_info.get('version')}")

    def _setup_ui(self) -> None:
        """
        Sets up the dialog's user interface components.
        
        :rtype: None
        """
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header section
        header_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("🎉 A new version of Forgerly is available!")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        # Version comparison
        version_text = (
            f"Current version: <b>v{self.current_version}</b><br>"
            f"Latest version: <b>v{self.release_info.get('version')}</b>"
        )
        version_label = QLabel(version_text)
        header_layout.addWidget(version_label)
        
        layout.addLayout(header_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Release notes section
        notes_label = QLabel("Release Notes:")
        notes_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(notes_label)
        
        # Release notes text area
        self.notes_text = QTextEdit()
        self.notes_text.setReadOnly(True)
        self.notes_text.setPlainText(
            self.release_info.get('body') or "No release notes available."
        )
        layout.addWidget(self.notes_text, 1)  # Stretch factor of 1
        
        # Checkbox to skip this version
        self.skip_checkbox = QCheckBox("Don't remind me about this version again")
        layout.addWidget(self.skip_checkbox)
        
        # Button section
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Remind me later button
        self.later_button = QPushButton("Remind Me Later")
        self.later_button.clicked.connect(self._on_later_clicked)
        button_layout.addWidget(self.later_button)
        
        # Download button (primary action)
        self.download_button = QPushButton("Download Update")
        self.download_button.setDefault(True)
        self.download_button.clicked.connect(self._on_download_clicked)
        self.download_button.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
        """)
        button_layout.addWidget(self.download_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _on_download_clicked(self) -> None:
        """
        Handles the Download Update button click.
        Opens the release download URL in the default browser.
        
        :rtype: None
        """
        download_url = self.release_info.get('download_url') or self.release_info.get('url')
        
        if download_url:
            logger.info(f"Opening download URL: {download_url}")
            print(download_url)
            # QDesktopServices.openUrl(QUrl(download_url))
        else:
            logger.warning("No download URL available in release info.")
        
        self.skip_this_version = self.skip_checkbox.isChecked()
        self.accept()
    
    def _on_later_clicked(self) -> None:
        """
        Handles the Remind Me Later button click.
        Closes the dialog without taking action.
        
        :rtype: None
        """
        logger.debug("User chose to be reminded later about the update.")
        self.skip_this_version = self.skip_checkbox.isChecked()
        self.reject()
    
    def should_skip_version(self) -> bool:
        """
        Returns whether the user chose to skip this version.
        
        :returns: True if the user checked "Don't remind me again", False otherwise.
        :rtype: bool
        """
        return self.skip_this_version