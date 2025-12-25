# tools/qss_previewer.py
#
# A helpful tool to view what a qss file might look like on the full application

import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTextEdit, QTreeWidget,
    QMenuBar, QMainWindow, QToolBar, QSplitter,
    QTreeWidgetItem, QCheckBox, QGroupBox, QRadioButton,
    QLabel
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
import sys
import os
from pathlib import Path

class ThemePreviewWindow(QMainWindow):
    def __init__(self, qss_path):
        super().__init__()
        self.setWindowTitle("QSS Theme Previewer")
        self.setGeometry(100, 100, 800, 600)
        
        self.apply_qss(qss_path)
        self.setup_ui()

    def apply_qss(self, qss_path):
        """Reads the QSS file and applies it to the application."""
        try:
            with open(qss_path, 'r') as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print(f"Error: QSS file not found at {qss_path}")

    def setup_ui(self):
        """Creates and organizes the test widgets."""
        
        # --- 1. Central Widget and Layout ---
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # --- 2. Menu Bar (to test QMenuBar and QMenu::item:selected) ---
        menu_bar = QMenuBar()
        file_menu = menu_bar.addMenu("File")
        file_menu.addAction("New")
        file_menu.addAction("Open")
        self.setMenuBar(menu_bar)

        # --- 3. Toolbar (to test QToolBar) ---
        toolbar = QToolBar("Main Toolbar")
        toolbar.addAction(QIcon.fromTheme("document-new"), "New")
        toolbar.addAction(QIcon.fromTheme("document-save"), "Save")
        self.addToolBar(toolbar)

        # --- 4. Main Content Area (Widgets and Splitters) ---
        
        # Section A: Input Widgets (Testing QLineEdit, QPushButton)
        input_group = QGroupBox("Input Widgets")
        input_layout = QHBoxLayout(input_group)
        input_layout.addWidget(QLineEdit("QLineEdit"))
        
        # Testing QPushButton and QPushButton:hover
        button_layout = QVBoxLayout()
        button_layout.addWidget(QPushButton("Normal Button"))
        button_layout.addWidget(QPushButton("Hover Me"))
        input_layout.addLayout(button_layout)
        
        # Testing CheckBoxes and Radio Buttons
        choice_layout = QVBoxLayout()
        choice_layout.addWidget(QCheckBox("QCheckBox"))
        choice_layout.addWidget(QRadioButton("QRadioButton"))
        input_layout.addLayout(choice_layout)
        
        main_layout.addWidget(input_group)

        # Section B: Multi-line and Complex Widgets
        splitter = QSplitter(Qt.Orientation.Horizontal) # Testing QSplitter
        
        # Testing QTextEdit (background-color, border, font-size)
        text_edit = QTextEdit()
        text_edit.setPlainText("QTextEdit\nThis text field tests the QTextEdit style.")
        splitter.addWidget(text_edit)
        
        # Testing QTreeWidget (background-color, alternate-background-color, selection-background-color)
        tree_widget = QTreeWidget()
        tree_widget.setHeaderLabels(["Key", "Value"])
        
        root = QTreeWidgetItem(tree_widget, ["Root Item", "Data"])
        QTreeWidgetItem(root, ["Child 1", "More Data"])
        QTreeWidgetItem(root, ["Child 2 (Alternate)", "Other Data"])
        
        splitter.addWidget(tree_widget)
        
        splitter.setSizes([400, 400]) # Equal split
        main_layout.addWidget(splitter)
        
        # --- 5. Status Bar (optional, for completeness) ---
        self.statusBar().showMessage("QSS Preview Loaded Successfully.")

        self.setCentralWidget(main_widget)
        

if __name__ == '__main__':
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    
    QSS_FILE = os.path.join(PROJECT_ROOT, 'styles', 'dark.qss')
    
    app = QApplication(sys.argv)
    
    # Check for argument overrides for flexibility
    if len(sys.argv) > 1:
        QSS_FILE = sys.argv[1]
    
    # The application itself (QMainWindow) is the main window
    window = ThemePreviewWindow(QSS_FILE)
    window.show()
    sys.exit(app.exec())
    