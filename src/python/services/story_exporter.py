# src/python/services/story_exporter.py

from ebooklib import epub
from xhtml2pdf import pisa
import json
import yaml

from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget
from PyQt6.QtGui import QTextDocument

from ..services.exporter import Exporter
from ..utils.constants import FileFormats, generate_file_filter

from typing import TextIO
from ..services.app_coordinator import AppCoordinator

class StoryExporter(Exporter):
    """
    Handles the presentation and file writing logic for exporting the entire story 
    and selected story parts (Chapters).
    
    It is a concrete implementation of :py:class:`~app.services.exporter.Exporter` 
    and supports exporting to multiple formats including html, md, txt, epub, PDF, JSON, and YAML.
    """
    def __init__(self, coordinator: AppCoordinator, project_title: str) -> None:
        """
        Initializes the :py:class:`.StoryExporter`.

        :param coordinator: The application coordinator, used to access the chapter repository.
        :type coordinator: :py:class:`~app.services.app_coordinator.AppCoordinator`
        :param project_title: The current project's title, used for file naming and document metadata.
        :type project_title: str
        
        :rtype: None
        """
        super().__init__(coordinator=coordinator, project_title=project_title)

    def export(self, parent: QWidget, selected_ids: list[int] = []) -> bool:
        """
        The main public method to initiate the story export process.
        
        It guides the user through selecting a file path and format, fetches the 
        chapter data, and calls the private file writing method.

        :param parent: The parent Qt widget, used for modal dialogs like :py:class:`~PyQt6.QtWidgets.QFileDialog`.
        :type parent: :py:class:`~PyQt6.QtWidgets.QWidget`
        :param selected_ids: A list of chapter IDs to export. If empty, all chapters are exported.
        :type selected_ids: list[int]
        
        :returns: True if the export was successful, False otherwise.
        :rtype: bool
        """
        
        # 1. Prompt user for file path and format
        file_filter = generate_file_filter(FileFormats.ALL)
        file_path, selected_filter = QFileDialog.getSaveFileName(
            parent, "Export Story", "Story.html", file_filter
        )
        
        if not file_path:
            return False

        # Determine the export format
        if 'html' in selected_filter.lower():
            file_format = "html"
        elif 'md' in selected_filter.lower():
            file_format = "markdown"
        elif 'txt' in selected_filter.lower():
            file_format = 'txt'
        elif 'epub' in selected_filter.lower():
            file_format = 'epub'
        elif 'pdf' in selected_filter.lower():
            file_format = 'pdf'
        elif 'json' in selected_filter.lower():
            file_format = 'json'
        elif 'yaml' in selected_filter.lower():
            file_format = 'yaml'
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
        """
        Implementation of the abstract method from :py:class:`~app.services.exporter.Exporter`.

        Based on the :py:attr:`.output_format` determined in :py:meth:`.export`, 
        this method calls the appropriate format-specific writer method to save the 
        :py:attr:`.chapters_data` to :py:attr:`.output_path`.
        
        :returns: True if the file write operation succeeded, False otherwise.
        :rtype: bool
        """
        
        writer_map = {
            "html": self._write_html,
            "markdown": self._write_markdown,
            "txt": self._write_plain_text,
            "epub": self._write_epub,
            "pdf": self._write_pdf,
            "json": self._write_json,
            "yaml": self._write_yaml
        }

        writer_function = writer_map.get(file_format)

        if not writer_function:
            raise ValueError(f"Unsupported file format: {file_format}")
        
        is_binary = file_format in ["epub", "pdf"]
        mode = 'wb' if is_binary else 'w'
        encoding = None if is_binary else 'utf-8'
        
        try:
            with open(file_path, mode, encoding=encoding) as f:
                writer_function(f, chapters_data)

        except FileNotFoundError:
            QMessageBox.critical(parent, "Export Error", f"Failed to find the desired file.")
            return False
        
        except Exception as e:
            QMessageBox.critical(parent, "Export Error", f"Failed to write the data to the desired file: {e}")
            return False
        
    def _get_document_text(self, html_content: str) -> str:
        """
        Helper to safely convert HTML content to plain text
        
        :param html_content: The html content to convert to plain text
        :type html_content: str

        :rtype: str
        """
        doc = QTextDocument()
        doc.setHtml(html_content)
        return doc.toPlainText()
    
    def _generate_full_html_document(title: str, chapters: list[dict]) -> str:
        """
        Generates a complete HTML string representing the entire book structure, 
        including chapter titles and content, suitable for conversion to PDF.
        
        :param chapters_data: A list of dictionaries containing chapter data (title, content).
        :type chapters_data: list[dict]
        
        :returns: The complete HTML document string.
        :rtype: str
        """
        # Simple, print-friendly CSS style
        css_style = """
        @page { size: A4; margin: 1in; }
        body { font-family: sans-serif; line-height: 1.6; }
        h1 { color: #333; border-bottom: 2px solid #ccc; padding-bottom: 5px; }
        h2 { page-break-before: always; color: #555; }
        .chapter-content { margin-bottom: 2em; }
        """

        body_content = f"<h1>{title}</h1>" # Project Title

        for i, chapter in enumerate(chapters):
            title = chapter.get('Title', 'Untitled Chapter')
            content = chapter.get('Text_Content', '')
            
            # Add a page break before each chapter (except the first) for a clean PDF
            page_break = "style='page-break-before: always;'" if i > 0 else ""
            
            body_content += f'<h2 {page_break}>{title}</h2>\n'
            body_content += f'<div class="chapter-content">{content}</div>\n'
            
        # Full HTML structure
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <meta charset='UTF-8'>
            <style>{css_style}</style>
        </head>
        <body>
            {body_content}
        </body>
        </html>
        """
        return html
    
    def _write_html(self, f: TextIO, chapters_data: list[dict]) -> None:
        """
        Writes the story data to the file object in html format.

        :param f: The open file object (:py:class:`~typing.TextIO` opened in text mode).
        :type f: :py:class:`~typing.TextIO`
        :param chapters_data: A list of dictionaries containing chapter data.
        :type chapters_data: list[dict]
        
        :rtype: None
        """
        
        # HTML Header/Preamble
        f.write(f"<!DOCTYPE html><html><head><title>{self.project_title}</title>")
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
        Writes the story data to the file object in markdown format.

        :param f: The open file object (:py:class:`~typing.TextIO` opened in text mode).
        :type f: :py:class:`~typing.TextIO`
        :param chapters_data: A list of dictionaries containing chapter data.
        :type chapters_data: list[dict]
        
        :rtype: None
        """
        f.write(f"# {self.project_title}\n\n")
        for chapter in chapters_data:
            title = chapter.get('Title', 'Untitled Chapter')
            content = chapter.get('Text_Content', '')
            
            f.write(f'## {title}\n\n')
            f.write(self._get_document_text(content))
            f.write("\n\n")

    def _write_plain_text(self, f: TextIO, chapters_data: list[dict]) -> None:
        """
        Writes the story data to the file object in text format.

        :param f: The open file object (:py:class:`~typing.TextIO` opened in text mode).
        :type f: :py:class:`~typing.TextIO`
        :param chapters_data: A list of dictionaries containing chapter data.
        :type chapters_data: list[dict]
        
        :rtype: None
        """
        f.write(f"{self.project_title}\n\n")
        for chapter in chapters_data:
            title = chapter.get('Title', 'Untitled Chapter')
            content = chapter.get('Text_Content', '')

            f.write(f'{title}\n')
            f.write(self._get_document_text(content))
            f.write('\n\n')

    def _write_epub(self, f: TextIO, chapters_data: list[dict]) -> None:
        """
        Writes the story data to the file object in EPUB format.
        
        This method relies on the `ebooklib` library to structure and write the EPUB file.

        :param f: The open file object (:py:class:`~typing.TextIO` opened in binary mode).
        :type f: :py:class:`~typing.TextIO`
        :param chapters_data: A list of dictionaries containing chapter data.
        :type chapters_data: list[dict]
        
        :rtype: None
        """
        book = epub.EpubBook()

        book.set_identifier(f'story-exporter-{self.project_title.replace(" ", "-")}')
        book.set_title(self.project_title)
        book.set_language('en')
        book.add_author("Story Exporter")

        # Create EPUB chapters and contents
        epub_chapters = []
        for i, chapter_data in enumerate(chapters_data):
            title = chapter_data.get('Title', f'Untitled Chapter {i+1}')
            html_content = chapter_data.get('Text_Content', '')
            
            # The EPUB content must be valid XHTML
            c = epub.EpubHtml(
                title=title, 
                file_name=f'chap_{i+1}.xhtml', 
                lang='en'
            )
            
            # Wrap content with standard body tags for valid EPUB content
            c.content = f'<h1>{title}</h1>{html_content}'
            
            book.add_item(c)
            epub_chapters.append(c)

        # Define table of contents (TOC) and Spine
        book.toc = tuple(epub_chapters)
        book.spine = ['nav'] + epub_chapters
        
        # Add default NCX (table of contents) and Nav files
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # Write the EPUB file to the binary stream 'f'
        epub.write_epub(f, book, {})

    def _write_pdf(self, f: TextIO, chapters_data: list[dict]) -> None:
        """
        Writes the story data to the file object in PDF format.
        
        This method relies on the `xhtml2pdf` library (`pisa`) to convert 
        generated HTML content into a PDF document.

        :param f: The open file object (:py:class:`~typing.TextIO` opened in binary mode).
        :type f: :py:class:`~typing.TextIO`
        :param chapters_data: A list of dictionaries containing chapter data.
        :type chapters_data: list[dict]

        :raises IOError: If the PDF generation fails using `xhtml2pdf`.
        :rtype: None
        """
        html_string = self._generate_full_html_document(chapters_data)

        pisa_status = pisa.CreatePDF(html_string, dest = f)

        if pisa_status.err:
            raise IOError("PDF Generation fialed using xhtml2pdf")

    def _write_json(self, f: TextIO, chapters_data: list[dict]) -> None:
        """
        Writes the story data to the file object in JSON format.
        
        The JSON structure includes the project title as the root key, containing 
        the list of chapter data.

        :param f: The open file object (:py:class:`~typing.TextIO` opened in text mode).
        :type f: :py:class:`~typing.TextIO`
        :param chapters_data: A list of dictionaries containing chapter data.
        :type chapters_data: list[dict]
        
        :rtype: None
        """
        chapters = {self.project_title: chapters_data}
        json.dump(chapters, f, indent=4)

    def _write_yaml(self, f: TextIO, chapters_data: list[dict]) -> None:
        """
        Writes the story data to the file object in YAML format.
        
        The YAML structure mirrors the JSON structure, using the project title as 
        the root key for the chapter list.

        :param f: The open file object (:py:class:`~typing.TextIO` opened in text mode).
        :type f: :py:class:`~typing.TextIO`
        :param chapters_data: A list of dictionaries containing chapter data.
        :type chapters_data: list[dict]
        
        :rtype: None
        """
        yaml_data = {
            "project_title": self.project_title,
            "chapters": chapters_data
        }
        yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)