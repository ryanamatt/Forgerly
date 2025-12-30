# src/python/ui/views/character_editor.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, 
    QLineEdit, QComboBox, QHBoxLayout, QSpinBox
)
from PySide6.QtCore import Qt, Signal
from typing import Any

from .base_editor import BaseEditor
from ...ui.widgets.basic_text_editor import BasicTextEditor
from ...utils.constants import ViewType, EntityType
from ...utils.events import Events
from ...utils.event_bus import bus, receiver

class CharacterEditor(BaseEditor):
    """
    A composite :py:class:`~PyQt6.QtWidgets.QWidget` for editing a Character's details 
    (Name, Status, Description).
    
    This is a pure UI component designed to be managed by an external controller 
    (like the :py:class:`.MainWindow`). It handles data loading, state 
    management (dirty checks), and local validation, but does not interact 
    with repositories directly.
    """

    # State tracking for unsaved changes
    _initial_name: str = ""
    _initial_status: str = ""
    _initial_age: int = -1
    _initial_dob: str = ""
    _initial_occupation: str = ""
    _initial_physical: str = ""

    current_char_id: int | None = None
    """The database ID of the character currently loaded in the editor, or :py:obj:`None`."""

    def __init__(self, parent=None) -> None:
        """
        Initializes the :py:class:`.CharacterEditor` widget.
        
        :param parent: The parent widget. Defaults to ``None``.
        :type parent: :py:class:`~PyQt6.QtWidgets.QWidget`, optional

        :rtype: None
        """
        super().__init__(parent)

        bus.register_instance(self)

        self._dirty = False

        # --- 1. Sub-components ---
        self.description_editor = BasicTextEditor()
        self.text_editor = BasicTextEditor()  # Moved up for clarity
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter Character Name")
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Alive", "Deceased", "Unknown", "Retired/Removed"])

        self.age_spin = QSpinBox()
        self.age_spin.setRange(-1, 1000)
        self.dob_input = QLineEdit()
        self.occupation_input = QLineEdit()

        # --- 2. Layout Setup ---
        
        # Header Group (Name & Status)
        header_group = QWidget()
        header_layout = QHBoxLayout(header_group)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(QLabel("Name:"))
        header_layout.addWidget(self.name_input, 3)
        header_layout.addWidget(QLabel("Status:"))
        header_layout.addWidget(self.status_combo, 1)
        header_layout.addStretch(1)

        # Personal Details Group
        details_group = QGroupBox("Personal Details")
        details_group.setAlignment(Qt.AlignmentFlag.AlignCenter)
        details_layout = QHBoxLayout(details_group)
        details_layout.addWidget(QLabel("Age:"))
        details_layout.addWidget(self.age_spin)
        details_layout.addWidget(QLabel("Date of Birth:"))
        details_layout.addWidget(self.dob_input)
        details_layout.addWidget(QLabel("Occupation:"))
        details_layout.addWidget(self.occupation_input)

        # --- SIDE-BY-SIDE EDITORS (The Change) ---
        
        # Bottom Container
        editors_container = QWidget()
        editors_layout = QHBoxLayout(editors_container)
        editors_layout.setContentsMargins(0, 0, 0, 0)
        editors_layout.setSpacing(10)

        # Left: Description Group
        description_group = QGroupBox("Description")
        description_group.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description_layout = QVBoxLayout(description_group)
        description_layout.addWidget(self.description_editor)
        
        # Right: Physical Description Group
        physical_group = QGroupBox("Physical Description")
        physical_group.setAlignment(Qt.AlignmentFlag.AlignCenter)
        physical_layout = QVBoxLayout(physical_group)
        physical_layout.addWidget(self.text_editor)

        # Add groups to the horizontal layout
        editors_layout.addWidget(description_group, 1) # Equal stretch
        editors_layout.addWidget(physical_group, 1)    # Equal stretch

        # --- 3. Overall Layout (Vertical) ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        main_layout.addWidget(header_group)
        main_layout.addWidget(details_group)
        main_layout.addWidget(editors_container) # Add the side-by-side editors
        
        # --- Connections ---
        self.name_input.textChanged.connect(self._set_dirty)
        self.status_combo.currentTextChanged.connect(self._set_dirty)
        self.age_spin.valueChanged.connect(self._set_dirty)
        self.dob_input.textChanged.connect(self._set_dirty)
        self.occupation_input.textChanged.connect(self._set_dirty)
        
        self.name_input.editingFinished.connect(self._emit_name_change)
        
        self.setEnabled(False)

    # =========================================================================
    # PUBLIC INTERFACE (Data/State Management)
    # =========================================================================

    def load_character(self, char_id: int, name: str, description: str, status: str,
                       age: int, dob: str, occupation: str, physical: str) -> None:
        """
        Loads character data into the editor fields.
        
        This method updates the name, status, and description fields, and 
        calls :py:meth:`.mark_saved` to reset the dirty state. This method
        also fills the tag fields.
        
        :param name: The title of the new character.
        :type name: str
        :param description: The description of the character
        :type status: str
        :param status: The status of the character (Dead, Alive, etc.)
        :param age: The age of the character.
        :type age: int
        :param dob: The characters date of birth.
        :type dob: str
        :param occupation: The characters Occupation/Schooling
        :type occupation: str
        :param physical: The characters physical description.
        :type physical: str
        
        :rtype: None
        """
        self.current_char_id = char_id
        
        self.name_input.setText(name)
        
        # Temporarily block signals to prevent triggering _set_dirty when setting new text
        self.status_combo.blockSignals(True)
        # Find the status string in the combo box, fall back to 'Unknown' if not found
        index = self.status_combo.findText(status, Qt.MatchFlag.MatchExactly)
        if index == -1:
            index = self.status_combo.findText("Unknown", Qt.MatchFlag.MatchExactly)
        self.status_combo.setCurrentIndex(index)
        self.status_combo.blockSignals(False)

        self.description_editor.set_html_content(description)
        self.age_spin.setValue(age)
        self.dob_input.setText(dob)
        self.occupation_input.setText(occupation)
        self.text_editor.set_html_content(physical)
        
        self.mark_saved()
        self.setEnabled(True)

    def get_data(self) -> dict[str, Any]:
        """
        Returns the current state of all editable fields for MainWindow to save.

        This method returns the data in the edittor fields as a dictionary.
        
        :rtype dict[str, Any]
        """
        return {
            'name': self.get_name(),
            'status': self.get_status(),
            'description': self.get_description_content(),
            'age': self.age_spin.value(),
            'date_of_birth': self.dob_input.text().strip(),
            'occupation_school': self.occupation_input.text().strip(),
            'physical_description': self.text_editor.get_html_content()
        }
    
    def is_dirty(self) -> bool:
        """
        Checks if the content in the editor has unsaved changes compared to 
        the last loaded or saved state.
        
        This dynamically compares the current state of inputs (Name, Status, 
        and Description content) with their initial values.
        
        :returns: True if changes are detected, False otherwise.
        :rtype: bool
        """
        if self.current_char_id is None:
            return False
        
        return self._dirty or super().is_dirty() or self.description_editor.is_dirty()
    
    def _set_dirty(self) -> None:
        """
        Handler for UI input. 
        
        This method is connected to signals from various input widgets (like 
        :py:class:`~PyQt6.QtWidgets.QLineEdit` and :py:class:`~PyQt6.QtWidgets.QComboBox`) 
        to track when user interaction occurs.
        
        :rtype: None
        """
        if not self.current_char_id:
            return False

        self._dirty = True 

    @receiver(Events.MARK_SAVED)
    def mark_saved_connection(self, data: dict) -> None:
        """
        A connection for the mark saved Event.
        
        :param data: Data dictionary, Empty as function doesn't need it.
        :type data: dict

        :rtype: None
        """
        if data.get('entity_type') != EntityType.CHARACTER:
            return
        
        self.mark_saved()

    def mark_saved(self) -> None:
        """
        Updates the internal initial state trackers to match the current content, 
        effectively marking the editor as "clean" (saved).
        
        :rtype: None
        """

        super().mark_saved()

        self.description_editor.mark_saved()

        self._dirty = False
        
    def set_enabled(self, enabled: bool) -> None:
        """
        Enables or disables all interactive elements within the editor panel.
        
        :param enabled: If True, enables the panel; otherwise, disables it.
        :type enabled: bool

        :rtype: None
        """
        # self.text_editor and self.tag_manager
        super().set_enabled(enabled)

        self.name_input.setEnabled(enabled)
        self.status_combo.setEnabled(enabled)
        self.age_spin.setEnabled(enabled)
        self.dob_input.setEnabled(enabled)
        self.occupation_input.setEnabled(enabled)
        self.description_editor.setEnabled(enabled)
        
    # --- Data Retrieval Methods ---
    
    def get_name(self) -> str:
        """
        Returns the current character name from the input field.
        
        :returns: The character's name, trimmed of whitespace.
        :rtype: str
        """
        return self.name_input.text().strip()
    
    def get_status(self) -> str:
        """
        Returns the current character status from the combo box.
        
        :returns: The selected character status.
        :rtype: str
        """
        return self.status_combo.currentText().strip()

    def get_description_content(self) -> str:
        """
        Returns the rich text description content as HTML string.
        
        :returns: The description content in HTML format.
        :rtype: str
        """
        return self.description_editor.get_html_content()

    def _emit_name_change(self) -> None:
        """
        Emits the :py:attr:`.char_name_changed` signal after the user finishes 
        editing the name (e.g., focus leaves the :py:class:`~PyQt6.QtWidgets.QLineEdit`).
        
        :rtype: None
        """
        if self.current_char_id is not None:
            bus.publish(Events.OUTLINE_NAME_CHANGE, data={
                'editor': self,
                'ID': self.current_char_id,
                'title': self.name_input.text().strip(),
                'view': ViewType.CHARACTER_EDITOR
            })

    def get_save_data(self) -> dict:
        """
        Returns all the current saved data.
        
        :returns: A dictionary of the current character data.
        :rtype: dict
        """
        return {
            "name": self.name_input.text(),
            "description": self.description_editor.get_html_content(),
            "status": self.status_combo.currentText(),
            "age": self.age_spin.value(),
            "date_of_birth": self.dob_input.text(),
            "occupation_school": self.occupation_input.text(),
            "physical_description": self.text_editor.get_html_content(),
            "tags": self.get_tags()
        }
    
    @receiver(Events.SAVE_REQUESTED)
    def provide_data_for_save(self, data: dict):
        """
        If this editor is dirty, it sends its current content back to the coordinator.

        :param data: The data of the save data.
        :type data: dict

        :rtype: None
        """
        if not self.is_dirty():
            return
        
        if data.get('entity_type') != EntityType.CHARACTER:
            return

        save_data = self.get_save_data()
        data |= save_data
        data.update({'parent': self})

        bus.publish(Events.SAVE_DATA_PROVIDED, data=data)
    
    @receiver(Events.DATA_LOADED)
    def load_entity(self, data: dict) -> None:
        """
        Loads all the information into the editor
        
        :param data: A dictionary with all Character data.
        :type data: dict

        :rtype: None
        """
        if data.get('entity_type') != EntityType.CHARACTER:
            return

        id, name, description = data['ID'], data['Name'], data['Description']
        status, age, dob = data['Status'], data['Age'], data['Date_of_Birth']
        occupation, physical = data['Occupation_School'], data['Physical_Description']

        self.current_char_id = id

        # Update UI Components
        self.name_input.setText(name)
        self.description_editor.set_html_content(description)
        self.status_combo.setCurrentText(status)
        self.age_spin.setValue(int(age))
        self.dob_input.setText(dob)
        self.occupation_input.setText(occupation)
        self.text_editor.set_html_content(physical)

        self.mark_saved()
        self.set_enabled(True)
