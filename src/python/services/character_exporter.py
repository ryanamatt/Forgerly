# src/python/services/character_exporter.py

from xhtml2pdf import pisa
import json
import yaml

from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget
from PySide6.QtGui import QTextDocument

from ..services.exporter import Exporter
from ..utils.constants import FileFormats, generate_file_filter

from typing import TextIO
from ..services.app_coordinator import AppCoordinator

class CharacterExporter(Exporter):
    """
    Handles the presentation and file writing logic for exporting the entire characters 
    and selected characters.
    
    It is a concrete implementation of :py:class:`~app.services.exporter.Exporter` 
    and supports exporting to multiple formats including html, md, txt, PDF, JSON, and YAML.
    """
    def __init__(self, coordinator: AppCoordinator, project_title: str) -> None:
        """
        Initializes the :py:class:`.CharacterExporter`.

        :param coordinator: The application coordinator, used to access the character repository.
        :type coordinator: :py:class:`~app.services.app_coordinator.AppCoordinator`
        :param project_title: The current project's title, used for file naming and document metadata.
        :type project_title: str
        
        :rtype: None
        """
        super().__init__(coordinator=coordinator, project_title=project_title)

    def export(self, parent: QWidget, selected_ids: list[int] = []) -> bool:
        """
        The main public method to initiate the character export process.
        
        It guides the user through selecting a file path and format, fetches the 
        character data, and calls the private file writing method.

        :param parent: The parent Qt widget, used for modal dialogs like :py:class:`~PySide6.QtWidgets.QFileDialog`.
        :type parent: :py:class:`~PySide6.QtWidgets.QWidget`
        :param selected_ids: A list of character IDs to export. If empty, all characters are exported.
        :type selected_ids: list[int]
        
        :returns: True if the export was successful, False otherwise.
        :rtype: bool
        """
        
        # 1. Prompt user for file path and format
        formats = FileFormats.ALL
        formats.remove(FileFormats.EPUB)
        file_filter = generate_file_filter(formats)
        file_path, selected_filter = QFileDialog.getSaveFileName(
            parent, "Export Characters", "Characters.html", file_filter
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
                all_characters_data = self.coordinator.get_character_data_for_export(character_ids=selected_ids)
            else:
                all_characters_data = self.coordinator.get_character_data_for_export()
            
            # 3. Write content to file
            self._write_file(file_path, file_format, all_characters_data, parent)

            # Success message is handled by MainWindow/calling context
            return True
            
        except Exception as e:
            QMessageBox.critical(parent, "Export Error", f"Failed to export story: {e}")
            return False

    def _write_file(self, file_path: str, file_format: str, characters_data: list[dict], parent) -> None:
        """
        Implementation of the abstract method from :py:class:`~app.services.exporter.Exporter`.

        Based on the :py:attr:`.output_format` determined in :py:meth:`.export`, 
        this method calls the appropriate format-specific writer method to save the 
        :py:attr:`.characters_data` to :py:attr:`.output_path`.
        
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
                writer_function(f, characters_data)

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
    
    def _generate_full_html_document(self, character_data: list[dict]) -> str:
        """
        Generates a complete HTML string representing the entire characters_data, 
        suitable for conversion to PDF.
        
        :param character_data: A list of dictionaries containing character data.
        :type character_data: list[dict]
        
        :returns: The complete HTML document string.
        :rtype: str
        """
        # Simple, print-friendly CSS style for PDF
        css_style = """
        @page { size: A4; margin: 1in; }
        body { font-family: sans-serif; line-height: 1.6; }
        h1 { color: #333; border-bottom: 2px solid #ccc; padding-bottom: 5px; }
        h2 { page-break-before: always; color: #555; }
        .character-info { margin-bottom: 2em; }
        .data-point { margin-left: 20px; }
        """

        body_content = f"<h1>{self.project_title} Character Library</h1>"

        for i, character in enumerate(character_data):
            name = character.get("Name", "Unnamed Character")
            description = character.get("Description", "No Description")
            # Extracting other fields (assuming they exist as per _write_html)
            status = character.get("Status", "")
            age = character.get("Age", "")
            date_of_birth = character.get("Date_Of_Birth", "")
            pronouns = character.get("Pronouns", "")
            sex_orient = character.get("Sexual_Orientation", "")
            gen_ident = character.get("Gender_Identity", "")
            ethn_back = character.get("Ethnicity_Background", "")
            occu_school = character.get("Occupation_School", "")
            home_city = character.get("Hometown_City", "")
            phys_desc = character.get("Physical_Description", "")

            # Add a page break before each character (except the first) for a clean PDF
            page_break = "style='page-break-before: always;'" if i > 0 else ""

            body_content += f'<h2 {page_break}>{name}</h2>\n'
            body_content += f'<div class="character-info">\n'
            body_content += f'<p><strong>Description:</strong> {description}</p>\n'
            if status: body_content += f'<p class="data-point"><strong>Status:</strong> {status}</p>\n'
            if age: body_content += f'<p class="data-point"><strong>Age:</strong> {age}</p>\n'
            if date_of_birth: 
                body_content += f'<p class="data-point"><strong>Date of Birth:</strong> {date_of_birth}</p>\n'
            if pronouns: 
                body_content += f'<p class="data-point"><strong>Pronouns:</strong> {pronouns}</p>\n'
            if occu_school: 
                body_content += f'<p class="data-point"><strong>Occupation/School:</strong> {occu_school}</p>\n'
            if home_city: 
                body_content += f'<p class="data-point"><strong>Home City/Town:</strong> {home_city}</p>\n'
            if phys_desc: body_content += f'<p><strong>Physical Description:</strong> {phys_desc}</p>\n'

            body_content += '</div>\n'

        # Full HTML structure
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{self.project_title} Characters</title>
            <meta charset='UTF-8'>
            <style>{css_style}</style>
        </head>
        <body>
            {body_content}
        </body>
        </html>
        """
        return html
    
    def _write_html(self, f: TextIO, characters_data: list[dict]) -> None:
        """
        Writes the character data to the file object in html format.

        :param f: The open file object (:py:class:`~typing.TextIO` opened in text mode).
        :type f: :py:class:`~typing.TextIO`
        :param characters_data: A list of dictionaries containing character data.
        :type characters_data: list[dict]
        
        :rtype: None
        """

        # HTML Header/Preamble
        f.write(f"<!DOCTYPE html><html><head><title>{self.project_title} Character(s)</title>")
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

        for character in characters_data:
            name = character.get("Name", "Unnamed Character")
            description = character.get("Description", "No Description")
            status = character.get("Status", "")
            age = character.get("Age", "")
            date_of_birth = character.get("Date_Of_Birth", "")
            pronouns = character.get("Pronouns", "")
            sex_orient = character.get("Sexual_Orientation", "")
            gen_ident = character.get("Gender_Identity", "")
            ethn_back = character.get("Ethnicity_Background", "")
            occu_school = character.get("Occupation_School", "")
            home_city = character.get("Hometown_City", "")
            phys_desc = character.get("Physical_Description", "")
            
            f.write(f'<h1>{name}</h1>\n')
            f.write(f"Description: {description}\n")
            if status: f.write(f"Status: {status}\n")
            if age: f.write(f"Age: {age}\n")
            if date_of_birth: f.write(f"Date of Birth: {date_of_birth}\n")
            if pronouns: f.write(f"Pronouns: {pronouns}")
            if sex_orient: f.write(f"Sexual Orientation: {sex_orient}\n")
            if gen_ident: f.write(f"Gender Identity: {gen_ident}\n")
            if ethn_back: f.write(f"Ethnic Background: {ethn_back}\n")
            if occu_school: f.write(f"Occupation/School: {occu_school}\n")
            if home_city: f.write(f"Home City/Town: {home_city}\n")
            if phys_desc: f.write(f"Physical Description: {phys_desc}\n")

            f.write('\n\n')
            
        # HTML Footer
        f.write("</body></html>")

    def _write_markdown(self, f: TextIO, characters_data: list[dict]) -> None:
        """
        Writes the character data to the file object in markdown format.

        :param f: The open file object (:py:class:`~typing.TextIO` opened in text mode).
        :type f: :py:class:`~typing.TextIO`
        :param characters_data: A list of dictionaries containing character data.
        :type characters_data: list[dict]
        
        :rtype: None
        """
        f.write(f"# {self.project_title}")
        for character in characters_data:
            name = character.get("Name", "Unnamed Character")
            description = character.get("Description", "No Description")
            status = character.get("Status", "")
            age = character.get("Age", "")
            date_of_birth = character.get("Date_Of_Birth", "")
            pronouns = character.get("Pronouns", "")
            sex_orient = character.get("Sexual_Orientation", "")
            gen_ident = character.get("Gender_Identity", "")
            ethn_back = character.get("Ethnicity_Background", "")
            occu_school = character.get("Occupation_School", "")
            home_city = character.get("Hometown_City", "")
            phys_desc = character.get("Physical_Description", "")

            f.write("\n\n")
            
            f.write(f"## {name}\n")
            f.write(f"Description: {description}\n")
            if status: f.write(f"Status: {status}\n")
            if age: f.write(f"Age: {age}\n")
            if date_of_birth: f.write(f"Date of Birth: {date_of_birth}\n")
            if pronouns: f.write(f"Pronouns: {pronouns}")
            if sex_orient: f.write(f"Sexual Orientation: {sex_orient}\n")
            if gen_ident: f.write(f"Gender Identity: {gen_ident}\n")
            if ethn_back: f.write(f"Ethnic Background: {ethn_back}\n")
            if occu_school: f.write(f"Occupation/School: {occu_school}\n")
            if home_city: f.write(f"Home City/Town: {home_city}\n")
            if phys_desc: f.write(f"Physical Description: {phys_desc}\n")

        

    def _write_plain_text(self, f: TextIO, characters_data: list[dict]) -> None:
        """
        Writes the character data to the file object in text format.

        :param f: The open file object (:py:class:`~typing.TextIO` opened in text mode).
        :type f: :py:class:`~typing.TextIO`
        :param characters_data: A list of dictionaries containing character data.
        :type characters_data: list[dict]
        
        :rtype: None
        """
        f.write(f"# {self.project_title}\n\n")
        for character in characters_data:
            name = character.get("Name", "Unnamed Character")
            description = character.get("Description", "No Description")
            status = character.get("Status", "")
            age = character.get("Age", "")
            date_of_birth = character.get("Date_Of_Birth", "")
            pronouns = character.get("Pronouns", "")
            sex_orient = character.get("Sexual_Orientation", "")
            gen_ident = character.get("Gender_Identity", "")
            ethn_back = character.get("Ethnicity_Background", "")
            occu_school = character.get("Occupation_School", "")
            home_city = character.get("Hometown_City", "")
            phys_desc = character.get("Physical_Description", "")
            
            f.write(f"{name}\n")
            f.write(f"Description: {description}\n")
            if status: f.write(f"Status: {status}\n")
            if age: f.write(f"Age: {age}\n")
            if date_of_birth: f.write(f"Date of Birth: {date_of_birth}\n")
            if pronouns: f.write(f"Pronouns: {pronouns}")
            if sex_orient: f.write(f"Sexual Orientation: {sex_orient}\n")
            if gen_ident: f.write(f"Gender Identity: {gen_ident}\n")
            if ethn_back: f.write(f"Ethnic Background: {ethn_back}\n")
            if occu_school: f.write(f"Occupation/School: {occu_school}\n")
            if home_city: f.write(f"Home City/Town: {home_city}\n")
            if phys_desc: f.write(f"Physical Description: {phys_desc}\n")

            f.write("\n\n")

    def _write_pdf(self, f: TextIO, characters_data: list[dict]) -> None:
        """
        Writes the character data to the file object in PDF format.
        
        This method relies on the `xhtml2pdf` library (`pisa`) to convert 
        generated HTML content into a PDF document.

        :param f: The open file object (:py:class:`~typing.TextIO` opened in binary mode).
        :type f: :py:class:`~typing.TextIO`
        :param characters_data: A list of dictionaries containing character data.
        :type characters_data: list[dict]

        :raises IOError: If the PDF generation fails using `xhtml2pdf`.
        :rtype: None
        """
        html_string = self._generate_full_html_document(characters_data)

        pisa_status = pisa.CreatePDF(html_string, dest = f)

        if pisa_status.err:
            raise IOError("PDF Generation failed using xhtml2pdf")

    def _write_json(self, f: TextIO, characters_data: list[dict]) -> None:
        """
        Writes the character data to the file object in JSON format.
        
        The JSON structure includes the project title as the root key, containing 
        the list of character data.

        :param f: The open file object (:py:class:`~typing.TextIO` opened in text mode).
        :type f: :py:class:`~typing.TextIO`
        :param characters_data: A list of dictionaries containing character data.
        :type characters_data: list[dict]
        
        :rtype: None
        """
        characters = {self.project_title: characters_data}
        json.dump(characters, f, indent=4)

    def _write_yaml(self, f: TextIO, characters_data: list[dict]) -> None:
        """
        Writes the character data to the file object in YAML format.
        
        The YAML structure mirrors the JSON structure, using the project title as 
        the root key for the character list.

        :param f: The open file object (:py:class:`~typing.TextIO` opened in text mode).
        :type f: :py:class:`~typing.TextIO`
        :param characters_data: A list of dictionaries containing character data.
        :type characters_data: list[dict]
        
        :rtype: None
        """
        yaml_data = {
            "project_title": self.project_title,
            "characters": characters_data
        }
        yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)
