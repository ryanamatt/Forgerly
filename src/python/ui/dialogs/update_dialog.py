# src/python/ui/dialogs/update_dialog.py

import os
import sys
import subprocess
import zipfile
import tempfile
import platform
import requests
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QCheckBox, QFrame
)
from PySide6.QtGui import QFont
from ...utils.logger import get_logger

import markdown
from PySide6.QtWidgets import QTextBrowser

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
        self.notes_text = QTextBrowser()
        self.notes_text.setReadOnly(True)
        raw_markdown = self.release_info.get('body') or "No release notes available."
        html_notes = markdown.markdown(raw_markdown)
        self.notes_text.setHtml(html_notes)
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
        
        if not download_url:
            logger.warning("No download URL available in release info.")
            return
        
        try:
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "update.zip")

            response = requests.get(download_url)
            with open(zip_path, 'wb') as f:
                f.write(response.content)

            stage_dir = os.path.join(temp_dir, "staged")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(stage_dir)

            # Trigger the swap
            self.execute_swap_and_restart(stage_dir)
            
        except Exception as e:
            logger.error(f"Update failed: {e}")
            self.reject()

    def execute_swap_and_restart(self, stage_dir: str):
        app_dir = os.getcwd()  # Root of Forgerly
        
        if platform.system() == "Windows":
            # We use a 'ping' trick to create a delay, then move files, then restart
            # This runs in a hidden cmd window after Forgerly exits
            cmd = (
                f'timeout /t 2 /nobreak > NUL && '  # Wait for process to die
                f'xcopy "{stage_dir}\\*" "{app_dir}" /s /e /y && ' # Overwrite
                f'start "" "{sys.executable}" "{os.path.join(app_dir, "run_app.py")}"' # Restart
            )
            subprocess.Popen(cmd, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
        
        else:
            # Linux/macOS equivalent
            cmd = f'sleep 2 && cp -rf "{stage_dir}/"* "{app_dir}" && python3 "{app_dir}/run_app.py" &'
            subprocess.Popen(cmd, shell=True)

        sys.exit(0)
    
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