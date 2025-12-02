# src/python/services/story_exporter.py

from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget
from PyQt6.QtGui import QTextDocument

from ..services.exporter import Exporter

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..services.app_coordinator import AppCoordinator

class StoryExporter(Exporter):
    """
    Handles the presentation and file writing logic for exporting the entire story.
    It fetches data from the AppCoordinator but operates independently of the main UI.
    """
    def __init__(self, coordinator: AppCoordinator) -> None:
        self.coordinator = coordinator

    def export(self, parent: QWidget) -> bool:
        """
        Main export method. Prompts user for location, fetches data, and writes the file.
        
        Args:
            parent: The QWidget parent (MainWindow) for centering dialogs.
        
        Returns:
            True if export was successful, False otherwise.
        """
        
        # 1. Prompt user for file path and format
        file_filter = "HTML (*.html);;Markdown (*.md);;Plain Text (*.txt)"
        file_path, selected_filter = QFileDialog.getSaveFileName(
            parent, "Export Story", "Story.html", file_filter
        )
        
        if not file_path:
            return False

        # Determine the export format
        if "HTML" in selected_filter:
            file_format = "html"
        elif "Markdown" in selected_filter:
            file_format = "markdown"
        else:
            file_format = "text"

        try:
            # 2. Fetch all required data from the coordinator
            all_chapters_data = self.coordinator.get_chapter_data_for_export()
            
            # 3. Write content to file
            self._write_file(file_path, file_format, all_chapters_data, parent)

            # Success message is handled by MainWindow/calling context
            return True
            
        except Exception as e:
            QMessageBox.critical(parent, "Export Error", f"Failed to export story: {e}")
            return False

    def _write_file(self, file_path: str, file_format: str, chapters_data: list[dict], parent) -> None:
        """Handles the actual file writing based on the selected format."""
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                
                # --- HTML Header ---
                if file_format == "html":
                    f.write("<!DOCTYPE html><html><head><title>Exported Story</title>")
                    f.write("<meta charset='UTF-8'>")
                    f.write("<style>body{font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 40px auto;} h1{color: #333; border-bottom: 2px solid #ccc; padding-bottom: 5px;} h2{color: #555;}</style>")
                    f.write("</head><body>\n")

                for chapter in chapters_data:
                    title = chapter.get('Title', 'Untitled Chapter')
                    content = chapter.get('Text_Content', '')
                    
                    # Use QTextDocument to convert HTML to plain text/markdown approximation
                    doc = QTextDocument()
                    doc.setHtml(content)

                    if file_format == "html":
                        f.write(f'<h1>{title}</h1>\n')
                        f.write(content) # Content is already HTML
                        f.write('\n\n')

                    elif file_format == "markdown":
                        f.write(f'# {title}\n\n')
                        # QTextDocument's toPlainText() loses a lot of structure, but is a safe fallback
                        f.write(doc.toPlainText())
                        f.write("\n\n")

                    elif file_format == "text":
                        f.write(f'{title}\n')
                        f.write('=' * len(title) + '\n\n')
                        f.write(doc.toPlainText())
                        f.write("\n\n")
                        
                # --- HTML Footer ---
                if file_format == "html":
                    f.write("</body></html>")

            return True
        
        except FileNotFoundError:
            QMessageBox.critical(parent, "Export Error", f"Failed to find the desired file.")
            return False
        
        except Exception as e:
            QMessageBox.critical(parent, "Export Error", f"Failed to write the data to the desired file: {e}")
            return False