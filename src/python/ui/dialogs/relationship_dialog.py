# src/python/ui/widgets/relationship_dialog.py

from PySide6.QtWidgets import (
    QDialog, QFormLayout, QComboBox, QLineEdit, QSpinBox, QDialogButtonBox, QLabel
)
from PySide6.QtCore import Qt

class RelationshipCreationDialog(QDialog):
    """
    A Dialog to gather details for a new relationship.
    
    Presents fields for Relationship Type, Description, and Intensity.
    """
    def __init__(self, relationship_types: list[dict], char_a_name: str, char_b_name: str, 
                 description: str = "", intensity: int = 5, parent=None) -> None:
        """
        Initializes :py:class:`.RelationshipCreationDialog`.
        
        :param relationship_types: A list of all the existing Relationship Types (dicts containing 
            'ID' and 'Type_Name').
        :type relationship_types: list[dict]
        :param char_a_name: The name of the first Character.
        :type char_a_name: str
        :param char_b_name: The name of the second Charcter.
        :type char_b_name: str
        :param parent: The parent object.
        :type parent: :py:class:`~PySide6.QtWidgets.QWidget`

        :rtype: None
        """
        super().__init__(parent)
        self.setWindowTitle(f"Create Relationship: {char_a_name} ↔ {char_b_name}")
        
        self.type_data = {t['ID']: t['Type_Name'] for t in relationship_types}
        
        layout = QFormLayout(self)
        
        # Display the characters being connected
        layout.addRow(QLabel(f"Connecting: {char_a_name} to {char_b_name}"))
        
        # Relationship Type selection
        self.type_combo = QComboBox()
        for type_id, type_name in self.type_data.items():
            # Store ID as UserRole data
            self.type_combo.addItem(type_name, type_id) 
        layout.addRow("Type:", self.type_combo)
        
        # Description
        self.description_input = QLineEdit()
        self.description_input.setText(description)
        layout.addRow("Description:", self.description_input)
        
        # Intensity (e.g., a simple 1-10 scale)
        self.intensity_input = QSpinBox()
        self.intensity_input.setRange(1, 10) # Intensity is on Simple 1-10 Scale
        self.intensity_input.setValue(intensity)
        layout.addRow("Intensity (0-10):", self.intensity_input)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                      QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def get_relationship_data(self) -> tuple[int, str, int]:
        """
        Retrieves the data entered by the user in the dialog controls.
        
        :returns: A tuple containing the selected Relationship Type ID, Description, and Intensity.
        :rtype: tuple[int, str, int]
        """
        # Retrieve the type ID from the stored UserRole data
        type_id = self.type_combo.currentData(Qt.ItemDataRole.UserRole) 
        description = self.description_input.text()
        intensity = self.intensity_input.value()
        return type_id, description, intensity
