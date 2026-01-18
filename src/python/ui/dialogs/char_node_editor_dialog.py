# src\python\ui\dialogs\char_node_editor_dialog.py

from PySide6.QtWidgets import (
    QPushButton, QColorDialog, QLineEdit, QDialog, QFormLayout, 
    QComboBox, QDialogButtonBox, QCheckBox
)
from PySide6.QtGui import QColor

class CharNodeEditorDialog(QDialog):
    """
    A Dialog for editing the Character Node Details in the Relationship Graph.
    """
    def __init__(self, details: dict, parent=None) -> None:
        """
        Instantiates the CharNodeEditorDialog
        
        :param details: The details needed containing {
            (Node_Color: str, Node_Shape: str, Is_Hidden: bool, Is_Locked: bool)}
        :param parent: The parent.
        :type parent: QWidget
        :rtype: None
        """
        super().__init__(parent)
        self.setWindowTitle("Edit Character Node Properties")
        self.setMinimumWidth(350)
        
        layout = QFormLayout(self)
        details = details or {}

        self.name_edit = QLineEdit(details.get('Name', ''))
        self.name_edit.setReadOnly(True)
        
        # 2. Node Color
        self.current_color = details.get('Node_Color', '#3498db') # Default blue-ish
        self.color_button = QPushButton(self.current_color)
        self.color_button.setStyleSheet(f"background-color: {self.current_color}; color: white;")
        self.color_button.clicked.connect(self._pick_color)

        # 3. Node Shape
        self.shape_combo = QComboBox()
        # Common graph shapes
        self.shape_combo.addItems(['Circle', 'Box', 'Diamond', 'Triangle', 'Star'])
        self.shape_combo.setCurrentText(details.get('Node_Shape', 'Circle'))

        # 4. Binary States (Hidden/Locked)
        self.hidden_check = QCheckBox("Hide from Graph")
        self.hidden_check.setChecked(bool(details.get('Is_Hidden', 0)))
        
        self.locked_check = QCheckBox("Lock Position")
        self.locked_check.setChecked(bool(details.get('Is_Locked', 0)))

        # Add to layout
        layout.addRow("Character Name:", self.name_edit)
        layout.addRow("Node Color:", self.color_button)
        layout.addRow("Node Shape:", self.shape_combo)
        layout.addRow("Visibility:", self.hidden_check)
        layout.addRow("Physics:", self.locked_check)

        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)

    def _pick_color(self) -> None:
        """
        A Color Dialog to choose the color of the Character Node.

        :rtype: None
        """
        color = QColorDialog.getColor(QColor(self.current_color), self)
        if color.isValid():
            self.current_color = color.name()
            self.color_button.setText(self.current_color)
            self.color_button.setStyleSheet(f"background-color: {self.current_color}; color: white;")

    def get_values(self) -> dict:
        """
        Returns the values of the boxes.
        
        :rtype: dict
        """
        return {
            "name": self.name_edit.text().strip(),
            "node_color": self.current_color,
            "node_shape": self.shape_combo.currentText(),
            "is_hidden": 1 if self.hidden_check.isChecked() else 0,
            "is_locked": 1 if self.locked_check.isChecked() else 0
        }