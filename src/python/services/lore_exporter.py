# src/python/services/lore_exporter.py

from xhtml2pdf import pisa
import json
import yaml
from typing import TextIO
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget
from PySide6.QtGui import QTextDocument

from ..services.exporter import Exporter
from ..utils.constants import FileFormats, generate_file_filter, ExportType
from ..utils.events import Events
from ..utils.event_bus import bus, receiver

class LoreExporter(Exporter):
    """
    Handles the presentation and file writing logic for exporting the entire lore entries 
    and selected lore entries.
    
    It is a concrete implementation of :py:class:`~app.services.exporter.Exporter` 
    and supports exporting to multiple formats including html, md, txt, PDF, JSON, and YAML.
    """
    def __init__(self, project_title: str) -> None:
        """
        Initializes the :py:class:`.LoreExporter`.

        :param project_title: The current project's title, used for file naming and document metadata.
        :type project_title: str
        
        :rtype: None
        """
        super().__init__(project_title=project_title)

        bus.register_instance(self)

    def export(self, parent: QWidget, selected_ids: list[int] = []) -> bool:
        """
        Publishes the event to get the export data.

        :param parent: The parent Qt widget, used for modal dialogs like :py:class:`~PySide6.QtWidgets.QFileDialog`.
        :type parent: :py:class:`~PySide6.QtWidgets.QWidget`
        :param selected_ids: A list of Lore Entry IDs to export. If empty, all Lore Entries are exported.
        :type selected_ids: list[int]
        
        :returns: True if the export was successful, False otherwise.
        :rtype: bool
        """
        bus.publish(Events.EXPORT_DATA_REQUESTED, data={
            'parent': parent, 'export_type': ExportType.LORE, 'selected_ids': selected_ids
        })

    @receiver(Events.EXPORT_DATA_RETURN)
    def _perform_export(self, data: dict) -> None:
        """
        Performs the Actual Export with the returning export data.
        
        :param data: The needed export data including {'export_type': ExportType.LORE,
            'parent': parent widget, 'lore_entries' list of all lore_entries to export}
        :type data: dict
        :rtype: None
        """
        if data.get('export_type') != ExportType.LORE:
            return
        
        parent = data.get('parent', self)
        lore_data = data.get('lore_entries')

        if not lore_data or not parent:
            return

        file_formats = FileFormats.ALL
        file_formats.remove(FileFormats.EPUB)
        file_filter = generate_file_filter(file_formats)
        file_path, selected_filter = QFileDialog.getSaveFileName(
            parent, "Export Lore_Entry(s)", "Lore_Entry.html", file_filter
        )
        
        if not file_path:
            return False

        match selected_filter.lower():
            case 'html': file_format = 'html'
            case 'md': file_format = 'markdown'
            case 'txt': file_format = 'txt'
            case 'pdf': file_format = 'pdf'
            case 'json': file_format = 'json'
            case 'yaml': file_format = 'yaml'
            case _: file_format = 'html'

        try:            
            self._write_file(file_path, file_format, lore_data, parent)
            
        except Exception as e:
            QMessageBox.critical(parent, "Export Error", f"Failed to export Lore Entry(s): {e}")

        return

    def _write_file(self, file_path: str, file_format: str, lore_data: list[dict], parent) -> None:
        """
        Implementation of the abstract method from :py:class:`~app.services.exporter.Exporter`.

        Based on the :py:attr:`.output_format` determined in :py:meth:`.export`, 
        this method calls the appropriate format-specific writer method to save the 
        :py:attr:`.lore_data` to :py:attr:`.output_path`.
        
        :returns: True if the file write operation succeeded, False otherwise.
        :rtype: bool
        """
        
        writer_map = {
            "html": self._write_html,
            "markdown": self._write_markdown,
            "txt": self._write_plain_text,
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
                writer_function(f, lore_data)

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

    def _generate_full_html_document(self, lore_data: list[dict]) -> str:
        """
        Generates a complete HTML string representing the entire lore_data, 
        suitable for conversion to PDF.
        
        :param lore_data: A list of dictionaries containing lore entry data.
        :type lore_data: list[dict]
        
        :returns: The complete HTML document string.
        :rtype: str
        """
        # Simple, print-friendly CSS style for PDF
        css_style = """
        @page { size: A4; margin: 1in; }
        body { font-family: sans-serif; line-height: 1.6; }
        h1 { color: #333; border-bottom: 2px solid #ccc; padding-bottom: 5px; }
        h2 { page-break-before: always; color: #555; }
        .lore-content { margin-top: 1em; }
        """

        body_content = f"<h1>{self.project_title} Lore Library</h1>"

        for i, entry in enumerate(lore_data):
            title = entry.get('Title', 'Untitled Entry')
            category = entry.get('Category', 'Uncategorized')
            content = entry.get('Content', '')
            
            # Add a page break before each entry (except the first) for a clean PDF
            page_break = "style='page-break-before: always;'" if i > 0 else ""
            
            body_content += f'<h2 {page_break}>{title}</h2>\n'
            body_content += f'<p><strong>Category:</strong> {category}</p>\n'
            body_content += f'<div class="lore-content">{content}</div>\n' # Content is already HTML
            
        # Full HTML structure
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{self.project_title} Lore</title>
            <meta charset='UTF-8'>
            <style>{css_style}</style>
        </head>
        <body>
            {body_content}
        </body>
        </html>
        """
        return html

    def _write_html(self, f: TextIO, lore_data: list[dict]) -> None:
        """
        Writes the lore entry data to the file object in html format.

        :param f: The open file object (:py:class:`~typing.TextIO` opened in text mode).
        :type f: :py:class:`~typing.TextIO`
        :param lore_data: A list of dictionaries containing lore entry data.
        :type lore_data: list[dict]
        
        :rtype: None
        """
        
        # HTML Header/Preamble
        f.write(f"<!DOCTYPE html><html><head><title>{self.project_title} Lore</title>")
        f.write("<meta charset='UTF-8'>")
        f.write("""
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    max-width: 800px;
                    margin: 40px auto;
                }
                h1 {
                    color: #333;
                    border-bottom: 2px solid #ccc;
                    padding-bottom: 5px;
                }
                h2 {
                    color: #555;
                }
            </style>
            """)
        f.write("</head><body>\n")
        f.write(f"<h1>{self.project_title} Lore Library</h1>\n\n")

        # Content Loop
        for entry in lore_data:
            title = entry.get('Title', 'Untitled Entry')
            category = entry.get('Category', 'Uncategorized')
            content = entry.get('Content', '')
            
            f.write(f'<h2>{title}</h2>\n')
            f.write(f'<p><strong>Category:</strong> {category}</p>\n')
            f.write(content) # Content is already HTML
            f.write('\n\n')
            
        # HTML Footer
        f.write("</body></html>")

    def _write_markdown(self, f: TextIO, lore_data: list[dict]) -> None:
        """
        Writes the lore entry data to the file object in markdown format.

        :param f: The open file object (:py:class:`~typing.TextIO` opened in text mode).
        :type f: :py:class:`~typing.TextIO`
        :param lore_data: A list of dictionaries containing lore entry data.
        :type lore_data: list[dict]
        
        :rtype: None
        """
        f.write(f"# {self.project_title} Lore Library\n\n")
        for entry in lore_data:
            title = entry.get('Title', 'Untitled Entry')
            category = entry.get('Category', 'Uncategorized')
            content = entry.get('Content', '')
            
            f.write(f'## {title}\n')
            f.write(f'**Category:** {category}\n\n')
            f.write(self._get_document_text(content))
            f.write("\n\n---\n\n") # Separator between entries

    def _write_plain_text(self, f: TextIO, lore_data: list[dict]) -> None:
        """
        Writes the lore entry data to the file object in text format.

        :param f: The open file object (:py:class:`~typing.TextIO` opened in text mode).
        :type f: :py:class:`~typing.TextIO`
        :param lore_data: A list of dictionaries containing lore entry data.
        :type lore_data: list[dict]
        
        :rtype: None
        """
        f.write(f"{self.project_title} Lore Library\n\n")
        f.write("=" * len(f"{self.project_title} Lore Library") + "\n\n")
        
        for entry in lore_data:
            title = entry.get('Title', 'Untitled Entry')
            category = entry.get('Category', 'Uncategorized')
            content = entry.get('Content', '')

            f.write(f'ENTRY: {title}\n')
            f.write(f'Category: {category}\n')
            f.write("-" * (len(title) + 7) + '\n')
            f.write(self._get_document_text(content))
            f.write('\n\n\n')

    def _write_pdf(self, f: TextIO, lore_data: list[dict]) -> None:
        """
        Writes the lore entry data to the file object in PDF format.
        
        This method relies on the `xhtml2pdf` library (`pisa`) to convert 
        generated HTML content into a PDF document.

        :param f: The open file object (:py:class:`~typing.TextIO` opened in binary mode).
        :type f: :py:class:`~typing.TextIO`
        :param lore_data: A list of dictionaries containing lore entry data.
        :type lore_data: list[dict]

        :raises IOError: If the PDF generation fails using `xhtml2pdf`.
        :rtype: None
        """
        html_string = self._generate_full_html_document(lore_data)

        pisa_status = pisa.CreatePDF(html_string, dest = f)

        if pisa_status.err:
            raise IOError("PDF Generation failed using xhtml2pdf")

    def _write_json(self, f: TextIO, lore_data: list[dict]) -> None:
        """
        Writes the lore entry data to the file object in JSON format.
        
        The JSON structure includes the project title as the root key, containing 
        the list of lore entry data.

        :param f: The open file object (:py:class:`~typing.TextIO` opened in text mode).
        :type f: :py:class:`~typing.TextIO`
        :param lore_data: A list of dictionaries containing lore entry data.
        :type lore_data: list[dict]
        
        :rtype: None
        """
        # Structure the output for easy reading/parsing
        output_data = {
            "project_title": self.project_title,
            "lore_entries": lore_data
        }
        json.dump(output_data, f, indent=4)

    def _write_yaml(self, f: TextIO, lore_data: list[dict]) -> None:
        """
        Writes the lore entry data to the file object in YAML format.
        
        The YAML structure mirrors the JSON structure, using the project title as 
        the root key for the lore entry list.

        :param f: The open file object (:py:class:`~typing.TextIO` opened in text mode).
        :type f: :py:class:`~typing.TextIO`
        :param lore_data: A list of dictionaries containing lore entry data.
        :type lore_data: list[dict]
        
        :rtype: None
        """
        yaml_data = {
            "project_title": self.project_title,
            "lore_entries": lore_data
        }
        yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)
