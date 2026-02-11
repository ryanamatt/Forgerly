# src/ptyhon/ui/dialogs/user_guide_dialog.py

from PySide6.QtWidgets import QDialog, QTextBrowser, QVBoxLayout
from PySide6.QtGui import QIcon
from PySide6.QtCore import QFile, QTextStream, QIODevice, Qt, QUrl

from ...utils.resource_path import get_resource_path
from ...utils.logger import get_logger

logger = get_logger(__name__)

class UserGuideDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowIcon(QIcon(get_resource_path('resources/logo.ico')))
        self.setWindowTitle("Forgerly User Guide")

        layout = QVBoxLayout()
        self.browser = QTextBrowser()
        
        self.apply_styles()
        
        layout.addWidget(self.browser)
        self.setLayout(layout)

        self.setWindowFlags(
            Qt.WindowType.Window | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        self.setMinimumSize(800, 600)
        self.load_markdown(get_resource_path('docs/user/GUIDE.md'))

    def apply_styles(self):
        """Adds CSS to improve readability and constrain image sizes."""
        css = """
            body { 
                line-height: 1.6; 
                font-family: 'Segoe UI', sans-serif; 
                margin: 25px; 
                color: #202124;
            }
            h1, h2, h3 { 
                color: #1a73e8; 
                margin-top: 1.5em; 
                margin-bottom: 0.5em; 
            }
            li { margin-bottom: 8px; }
            
            /* Constrain images to the width of the dialog */
            img { 
                display: block;
                margin-left: auto;
                margin-right: auto;
            }
        """
        self.browser.document().setDefaultStyleSheet(css)

    def load_markdown(self, file_path):
        # Set the search path for images relative to the markdown file
        image_dir = get_resource_path("docs/user/")
        self.browser.setSearchPaths([image_dir])

        
        try:
            file = QFile(file_path)
            if file.open(QIODevice.ReadOnly | QIODevice.Text):
                stream = QTextStream(file)
                markdown_text = stream.readAll()
                
                self.browser.setMarkdown(markdown_text)

                self.browser.document().setPageSize(self.browser.size())

                file.close()
                logger.debug("Opened User Guide Dialog")
        except Exception as e:
            logger.error(f"Failed to open User Guide Dialog: {e}")