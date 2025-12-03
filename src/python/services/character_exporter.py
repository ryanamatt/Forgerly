# src/python/services/character_exporter.py

import json
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget
from PyQt6.QtGui import QTextDocument

from ..services.exporter import Exporter
from ..utils.constants import FileFormats, generate_file_filter

from typing import TYPE_CHECKING, TextIO
if TYPE_CHECKING:
    from ..services.app_coordinator import AppCoordinator

class CharacterExporter(Exporter):
    """
    Handles the presentation and file writing logic for exporting the entire characters library and characters parts.
    It fetches data from the AppCoordinator but operates independently of the main UI.
    """
    def __init__(self, coordinator: AppCoordinator, project_title: str) -> None:
        super().__init__(coordinator=coordinator, project_title=project_title)

    def export(self, parent: QWidget, selected_ids: list[int] = []) -> bool:
        """
        Main export method. Prompts user for location, fetches data, and writes the file.
        
        Args:
            parent: The QWidget parent (MainWindow) for centering dialogs.
            selected_ids: A list of character IDs to export. If empty, all characters are exported.
        
        Returns:
            True if export was successful, False otherwise.
        """
        # 1. Prompt user for file path and format
        self.file_formats = [FileFormats.HTML, FileFormats.MARKDOWN, FileFormats.PLAIN_TEXT, FileFormats.JSON]
        file_filter = generate_file_filter(self.file_formats)
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
        Handles the actual file writing based on the selected format.
        
        Args:
            file_path: A string that is the file_path to the desired file to write to
            file_format: The file format that is being written in
            characters_data: The characters data that is being written.
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
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
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
        
        Args:
            html_content: The string of HTML content being turned into regular text.

        Returns:
            The plain text.
        """
        doc = QTextDocument()
        doc.setHtml(html_content)
        return doc.toPlainText()
    
    def _write_html(self, f: TextIO, characters_data: list[dict]) -> None:
        """
        Writes the character data to the file object in HTML format.

        Args:
            f: The open file object (TextIO).
            characters_data: A list of dictionaries containing character data.
        """

        # HTML Header/Preamble
        f.write(f"<!DOCTYPE html><html><head><title>{self.project_title} Character(s)</title>")
        f.write("<meta charset='UTF-8'>")
        f.write("<style>body{font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 40px auto;} h1{color: #333; border-bottom: 2px solid #ccc; padding-bottom: 5px;} h2{color: #555;}</style>")
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

        Args:
            f: The open file object (TextIO).
            characters_data: A list of dictionaries containing character data.
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
        Writes the character data to the file object in Plain Text format.

        Args:
            f: The open file object (TextIO).
            characters_data: A list of dictionaries containing character data.
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

    def _write_epub(self, f: TextIO, characters_data: list[dict]) -> None:
        """
        Writes the character data to the file object in EPUB format.

        Args:
            f: The open file object (TextIO).
            characters_data: A list of dictionaries containing character data.
        """

    def _write_pdf(self, f: TextIO, characters_data: list[dict]) -> None:
        """
        Writes the character data to the file object in PDF format.

        Args:
            f: The open file object (TextIO).
            characters_data: A list of dictionaries containing character data.
        """

    def _write_json(self, f: TextIO, characters_data: list[dict]) -> None:
        """
        Writes the character data to the file object in JSON format.

        Args:
            f: The open file object (TextIO).
            characters_data: A list of dictionaries containing character data.
        """
        characters = {self.project_title: characters_data}
        json.dump(characters, f, indent=4)

    def _write_yaml(self, f: TextIO, characters_data: list[dict]) -> None:
        """
        Writes the character data to the file object in YAML format.

        Args:
            f: The open file object (TextIO).
            characters_data: A list of dictionaries containing character data.
        """