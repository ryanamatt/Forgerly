# src/python/services/lore_exporter.py

from xhtml2pdf import pisa
import json
import yaml

from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget
from PyQt6.QtGui import QTextDocument

from ..services.exporter import Exporter
from ..utils.constants import FileFormats, generate_file_filter

from typing import TYPE_CHECKING, TextIO
if TYPE_CHECKING:
    from ..services.app_coordinator import AppCoordinator

class LoreExporter(Exporter):
    """
    Handles the presentation and file writing logic for exporting the entire lore
    library and individual lore entries.
    It fetches data from the AppCoordinator but operates independently of the main UI.
    The primary data source is the Lore_Entries table.
    """
    def __init__(self, coordinator: AppCoordinator, project_title: str) -> None:
        super().__init__(coordinator=coordinator, project_title=project_title)

    def export(self, parent: QWidget, selected_ids: list[int] = []) -> bool:
        """
        Main export method. Prompts user for location, fetches data, and writes the file.
        
        Args:
            parent: The QWidget parent (MainWindow) for centering dialogs.
            selected_ids: A list of Lore Entry IDs to export. If empty, all entries are exported.
        
        Returns:
            True if export was successful, False otherwise.
        """
        formats = FileFormats.ALL
        formats.remove(FileFormats.EPUB)
        file_filter = generate_file_filter(formats)
        file_path, selected_filter = QFileDialog.getSaveFileName(
            parent, "Export Lore Entries", "Lore.html", file_filter
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
                all_lore_data = self.coordinator.get_lore_data_for_export(lore_ids=selected_ids)
            else:
                all_lore_data = self.coordinator.get_lore_data_for_export()
            
            # 3. Write content to file
            self._write_file(file_path, file_format, all_lore_data, parent)

            # Success message is handled by MainWindow/calling context
            return True
            
        except Exception as e:
            QMessageBox.critical(parent, "Export Error", f"Failed to export lore: {e}")
            return False

    def _write_file(self, file_path: str, file_format: str, lore_data: list[dict], parent) -> None:
        """
        Handles the actual file writing based on the selected format.
        
        Args:
            file_path: A string that is the file_path to the desired file to write to
            file_format: The file format that is being written in
            lore_data: The lore data that is being written.
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
        
        Args:
            html_content: The string of HTML content being turned into regular text.

        Returns:
            The plain text.
        """
        doc = QTextDocument()
        doc.setHtml(html_content)
        return doc.toPlainText()
    
    # --- HTML/PDF Helper ---
    def _generate_lore_html_content(self, entry: dict) -> str:
        """
        Generates the HTML content snippet for a single lore entry.
        """
        title = entry.get('Title', 'Untitled Entry')
        category = entry.get('Category', 'Uncategorized')
        content = entry.get('Content', '') # Content is rich text (HTML)

        # Basic HTML structure for a single entry
        html_content = f'<h2>{title}</h2>\n'
        html_content += f'<p><strong>Category:</strong> {category}</p>\n'
        html_content += f'<div class="lore-content">{content}</div>\n'
        return html_content

    def _generate_full_html_document(self, lore_data: list[dict]) -> str:
        """
        Generates a full HTML document string for PDF generation.
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
    # --- End HTML/PDF Helper ---

    def _write_html(self, f: TextIO, lore_data: list[dict]) -> None:
        """
        Writes the lore data to the file object in HTML format.

        Args:
            f: The open file object (TextIO).
            lore_data: A list of dictionaries containing lore data.
        """
        
        # HTML Header/Preamble
        f.write(f"<!DOCTYPE html><html><head><title>{self.project_title} Lore</title>")
        f.write("<meta charset='UTF-8'>")
        f.write("<style>body{font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 40px auto;} h1{color: #333; border-bottom: 2px solid #ccc; padding-bottom: 5px;} h2{color: #555;}</style>")
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
        Writes the lore data to the file object in Markdown format.

        Args:
            f: The open file object (TextIO).
            lore_data: A list of dictionaries containing lore data.
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
        Writes the lore data to the file object in Plain Text format.

        Args:
            f: The open file object (TextIO).
            lore_data: A list of dictionaries containing lore data.
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
        Writes the lore data to the file object in PDF format.

        Args:
            f: The open file object (TextIO).
            lore_data: A list of dictionaries containing lore data.
        """
        html_string = self._generate_full_html_document(lore_data)

        pisa_status = pisa.CreatePDF(html_string, dest = f)

        if pisa_status.err:
            raise IOError("PDF Generation failed using xhtml2pdf")

    def _write_json(self, f: TextIO, lore_data: list[dict]) -> None:
        """
        Writes the lore data to the file object in JSON format.

        Args:
            f: The open file object (TextIO).
            lore_data: A list of dictionaries containing lore data.
        """
        # Structure the output for easy reading/parsing
        output_data = {
            "project_title": self.project_title,
            "lore_entries": lore_data
        }
        json.dump(output_data, f, indent=4)

    def _write_yaml(self, f: TextIO, lore_data: list[dict]) -> None:
        """
        Writes the lore data to the file object in YAML format.

        Args:
            f: The open file object (TextIO).
            lore_data: A list of dictionaries containing lore data.
        """
        yaml_data = {
            "project_title": self.project_title,
            "lore_entries": lore_data
        }
        yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)