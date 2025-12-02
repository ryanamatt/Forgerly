# src/python/services/story_exporter.py

import json
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget
from PyQt6.QtGui import QTextDocument

from ..services.exporter import Exporter
from ..utils.constants import FileFormats, generate_file_filter

from typing import TYPE_CHECKING, TextIO
if TYPE_CHECKING:
    from ..services.app_coordinator import AppCoordinator

class StoryExporter(Exporter):
    """
    Handles the presentation and file writing logic for exporting the entire story.
    It fetches data from the AppCoordinator but operates independently of the main UI.
    """
    def __init__(self, coordinator: AppCoordinator) -> None:
        self.coordinator = coordinator

        self.chapters_export_formats = [
            '.html',
            '.md',
            '.txt'
        ]

    def export(self, parent: QWidget, selected_ids: list[int] = []) -> bool:
        """
        Main export method. Prompts user for location, fetches data, and writes the file.
        
        Args:
            parent: The QWidget parent (MainWindow) for centering dialogs.
            selected_ids: A list of chapter IDs to export. If empty, all chapters are exported.
        
        Returns:
            True if export was successful, False otherwise.
        """
        
        # 1. Prompt user for file path and format
        self.file_formats = [FileFormats.HTML, FileFormats.MARKDOWN, FileFormats.PLAIN_TEXT, FileFormats.JSON]
        file_filter = generate_file_filter(self.file_formats)
        file_path, selected_filter = QFileDialog.getSaveFileName(
            parent, "Export Story", "Story.html", file_filter
        )
        
        if not file_path:
            return False

        # Determine the export format
        if "html" in selected_filter.lower():
            file_format = "html"
        elif "md" in selected_filter.lower():
            file_format = "markdown"
        elif 'txt' in selected_filter.lower():
            file_format = 'txt'
        elif 'json' in selected_filter.lower():
            file_format = 'json'
        else: # Default is html
            file_format = "html"

        try:
            # 2. Fetch all required data from the coordinator
            if selected_ids:
                all_chapters_data = self.coordinator.get_chapter_data_for_export(chapter_ids=selected_ids)
            else:
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
        
        writer_map = {
            "html": self._write_html,
            "markdown": self._write_markdown,
            "text": self._write_plain_text,
            'json': self._write_json
        }

        writer_function = writer_map.get(file_format)

        if not writer_function:
            raise ValueError(f"Unsupported file format: {file_format}")
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                writer_function(f, chapters_data)

        except FileNotFoundError:
            QMessageBox.critical(parent, "Export Error", f"Failed to find the desired file.")
            return False
        
        except Exception as e:
            QMessageBox.critical(parent, "Export Error", f"Failed to write the data to the desired file: {e}")
            return False
        
    def _get_document_text(self, html_content: str) -> str:
        """Helper to safely convert HTML content to plain text"""
        doc = QTextDocument()
        doc.setHtml(html_content)
        return doc.toPlainText()
    
    def _write_html(self, f: TextIO, chapters_data: list[dict]) -> None:
        """
        Writes the story data to the file object in HTML format.

        Args:
            f: The open file object (TextIO).
            chapters_data: A list of dictionaries containing chapter data.
        """
        
        # HTML Header/Preamble
        f.write("<!DOCTYPE html><html><head><title>Exported Story</title>")
        f.write("<meta charset='UTF-8'>")
        f.write("<style>body{font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 40px auto;} h1{color: #333; border-bottom: 2px solid #ccc; padding-bottom: 5px;} h2{color: #555;}</style>")
        f.write("</head><body>\n")
        
        # Content Loop
        for chapter in chapters_data:
            title = chapter.get('Title', 'Untitled Chapter')
            content = chapter.get('Text_Content', '')
            
            f.write(f'<h1>{title}</h1>\n')
            f.write(content) # Content is already HTML
            f.write('\n\n')
            
        # HTML Footer
        f.write("</body></html>")

    def _write_markdown(self, f: TextIO, chapters_data: list[dict]) -> None:
        """
        Writes the story data to the file object in Markdown format.

        Args:
            f: The open file object (TextIO).
            chapters_data: A list of dictionaries containing chapter data.
        """
        for chapter in chapters_data:
            title = chapter.get('Title', 'Untitled Chapter')
            content = chapter.get('Text_Content', '')
            
            f.write(f'## {title}\n\n')
            f.write(self._get_document_text(content))
            f.write("\n\n")

    def _write_plain_text(self, f: TextIO, chapters_data: list[dict]) -> None:
        """
        Writes the story data to the file object in Plain Text format.

        Args:
            f: The open file object (TextIO).
            chapters_data: A list of dictionaries containing chapter data.
        """
        for chapter in chapters_data:
            title = chapter.get('Title', 'Untitled Chapter')
            content = chapter.get('Text_Content', '')

            f.write(f'{title}\n')
            f.write(self._get_document_text(content))
            f.write('\n\n')

    def _write_json(self, f: TextIO, chapters_data: list[dict]) -> None:
        """
        Writes the story data to the file object in JSON format.

        Args:
            f: The open file object (TextIO).
            chapters_data: A list of dictionaries containing chapter data.
        """
        export_data = {
            "export_type": "story",
            "format_version": 1,
            "chapters": chapters_data
        }

        json.dump(export_data, f, indent=4)