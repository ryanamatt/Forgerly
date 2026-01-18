# src\python\ui\dialogs\relationship_type_editor_dialog.py

from PySide6.QtWidgets import (
    QPushButton, QColorDialog, QLineEdit, QDialog, QFormLayout, QComboBox, QDialogButtonBox
)
from PySide6.QtGui import QColor

class RelationshipTypeEditorDialog(QDialog):
    """
    A Dialog to edit the Relationship Type Attributes.
    """
    def __init__(self, details: dict, parent=None):
        """
        Instantiates the RelationshipTypeEditorDialog
        
        :param details: The details needed containing {
            (Name: str, Short_Label: str, color: str, style: str, is_directed: bool)}
        :param parent: The parent.
        :type parent: QWidget
        :rtype: None
        """
        super().__init__(parent)
        self.setWindowTitle("Edit Relationship Type")
        self.setMinimumWidth(350)
        
        layout = QFormLayout(self)

        # Inputs
        self.name_edit = QLineEdit(details.get('Type_Name', ''))
        self.short_label_edit = QLineEdit(details.get('Short_Label', ''))
        
        # Color - Storing the hex string
        self.color_button = QPushButton(details.get('Default_Color', '#000000'))
        self.color_button.setStyleSheet(f"background-color: {self.color_button.text()}; color: white;")
        self.color_button.clicked.connect(self._pick_color)
        self.current_color = details.get('Default_Color', '#000000')

        # Line Style
        self.style_combo = QComboBox()
        self.style_combo.addItems(['Solid', 'Dash', 'Dot', 'DashDot'])
        self.style_combo.setCurrentText(details.get('Line_Style', 'Solid'))

        # Directionality
        self.direction_combo = QComboBox()
        self.direction_combo.addItem("Undirected (A <-> B)", 0)
        self.direction_combo.addItem("Directed (A -> B)", 1)
        self.direction_combo.setCurrentIndex(1 if details.get('Is_Directed', 0) else 0)

        # Add to layout
        layout.addRow("Type Name:", self.name_edit)
        layout.addRow("Short Label:", self.short_label_edit)
        layout.addRow("Default Color:", self.color_button)
        layout.addRow("Line Style:", self.style_combo)
        layout.addRow("Directionality:", self.direction_combo)

        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self.current_color), self)
        if color.isValid():
            self.current_color = color.name()
            self.color_button.setText(self.current_color)
            self.color_button.setStyleSheet(f"background-color: {self.current_color};")

    def get_values(self):
        return {
            "name": self.name_edit.text().strip(),
            "short_label": self.short_label_edit.text().strip(),
            "color": self.current_color,
            "style": self.style_combo.currentText(),
            "is_directed": self.direction_combo.currentData()
        }