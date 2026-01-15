# src/python/utils/theme_utils.py

import os
import sys
from PySide6.QtWidgets import QWidget
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    HasStyleSheet = QWidget
else:
    HasStyleSheet = object

# Define the directory where style files are stored
STYLES_DIR = 'styles'
BASE_THEME_FILE = os.path.join(STYLES_DIR, 'dark.qss')

# Define accent colors for each theme
ACCENT_COLORS = {
    'Blue': '#005080',      # Default blue (from original dark.qss)
    'Green': '#307351',
    'Berry': '#963D5A',
    'Purple': '#624C6B',
    'Red': '#660000',
    'Violet': '#3B1F2B',
    'Teal': '#073B3A',
    'Orange': "#854803"
    }

def resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for dev and for PyInstaller 
    
    :param relative_path: The relative path to the file.
    :type relative_path: str
    :rtype: str
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Update these variables ---
STYLES_DIR = 'styles'
# Wrap the path with resource_path()
BASE_THEME_FILE = resource_path(os.path.join(STYLES_DIR, 'dark.qss'))

def get_available_themes() -> list[str]:
    """
    Returns a list of available theme names based on the ACCENT_COLORS dictionary.
    
    :returns: A sorted list of available theme names.
    :rtype: list[str]
    """
    return sorted(list(ACCENT_COLORS.keys()))

def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """
    Converts a hex color to rgba format with specified alpha.
    
    :param hex_color: Hex color code (e.g., '#0078d4')
    :type hex_color: str
    :param alpha: Alpha value between 0 and 1
    :type alpha: float
    :returns: rgba color string
    :rtype: str
    """
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"

def _generate_accent_stylesheet(accent_color: str) -> str:
    """
    Generates a QSS stylesheet snippet that applies the accent color
    to specific UI elements.
    
    :param accent_color: The hex color code for the accent (e.g., '#0078d4').
    :type accent_color: str
    :returns: A QSS string with accent color overrides.
    :rtype: str
    """
    
    # Generate color variations
    hover_light = _hex_to_rgba(accent_color, 0.2)  # 20% opacity for hover
    hover_medium = _hex_to_rgba(accent_color, 0.3)  # 30% opacity
    
    accent_qss = f"""
        /* ========== Accent Color Overrides ========== */
        
        /* Selection backgrounds */
        QTextEdit, QPlainTextEdit, QLineEdit {{
            selection-background-color: {accent_color};
        }}
        
        QTreeWidget, QTreeView {{
            selection-background-color: {accent_color};
        }}
        
        QTreeWidget::item:selected, QTreeView::item:selected {{
            background-color: {accent_color};
        }}
        
        QTableWidget::item:selected, QListWidget::item:selected {{
            background-color: {accent_color};
        }}
        
        /* Hover states with semi-transparent accent */
        QTableWidget::item:hover, QListWidget::item:hover {{
            background-color: {hover_light};
        }}
        
        QPushButton:hover {{
            background-color: #4d4d4d;
            border: 1px solid {accent_color};
        }}
        
        QPushButton:pressed {{
            background-color: {accent_color};
            border: 1px solid {accent_color};
        }}
        
        QToolButton:hover {{
            background-color: {hover_light};
            border: 1px solid {accent_color};
        }}
        
        QToolButton:pressed {{
            background-color: {accent_color};
        }}
        
        QMenuBar::item:pressed {{
            background-color: {accent_color};
        }}
        
        /* Focus borders */
        QLineEdit:focus {{
            border: 2px solid {accent_color};
        }}
        
        QTextEdit:focus, QPlainTextEdit:focus {{
            border: 2px solid {accent_color};
        }}
        
        QComboBox:focus {{
            border: 2px solid {accent_color};
        }}
        
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border: 2px solid {accent_color};
        }}
        
        /* Check boxes and radio buttons */
        QCheckBox::indicator:checked {{
            background-color: {accent_color};
            border: 1px solid {accent_color};
        }}
        
        QRadioButton::indicator:checked {{
            background-color: {accent_color};
            border: 1px solid {accent_color};
        }}
        
        /* Progress bar */
        QProgressBar::chunk {{
            background-color: {accent_color};
        }}
        
        /* Sliders */
        QSlider::handle:horizontal, QSlider::handle:vertical {{
            background: {accent_color};
        }}
        
        QSlider::sub-page:horizontal {{
            background-color: {accent_color};
        }}
        
        QSlider::sub-page:vertical {{
            background-color: {accent_color};
        }}
        
        /* Tabs */
        QTabBar::tab:selected {{
            background-color: {accent_color};
            border-bottom: 1px solid {accent_color};
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {hover_medium};
        }}
        
        /* Scrollbars */
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
            background: {accent_color};
        }}
        
        QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
            background-color: {accent_color};
            opacity: 0.8;
        }}
        
        /* ComboBox dropdown */
        QComboBox QAbstractItemView {{
            selection-background-color: {accent_color};
        }}
        
        /* Splitter */
        QSplitter::handle:pressed {{
            background-color: {accent_color};
        }}
        
        /* Toolbar separator */
        QToolBar::separator {{
            background-color: {accent_color};
            width: 2px;
            margin: 4px;
        }}
        
        /* ToolTips */
        QToolTip {{
            border: 1px solid {accent_color};
            background-color: #2a2a2a;
            color: #f0f0f0;
        }}
        
        /* Link colors */
        QLabel a {{
            color: {accent_color};
        }}
        """
    return accent_qss

def apply_theme(app_window: HasStyleSheet, settings: dict[str, Any]) -> bool:
    """
    Loads and applies the base dark theme plus accent color overrides.

    It reads the theme name from the provided ``settings`` dictionary under the 
    key ``'theme'`` and combines the base dark.qss with accent color styling.

    :param app_window: The QMainWindow or QWidget instance to apply the stylesheet to.
    :type app_window: HasStyleSheet
    :param settings: The application settings dictionary containing the ``'theme'`` key.
    :type settings: dict[str, Any]

    :returns: True if the theme was applied successfully, False otherwise.
    :rtype: bool
    """
    theme_name = settings.get("theme", "Blue")
    
    # Validate theme name
    if theme_name not in ACCENT_COLORS:
        theme_name = "Blue"
    
    # Load base Blue theme
    if not os.path.exists(BASE_THEME_FILE):
        return False
    
    try:
        with open(BASE_THEME_FILE, 'r') as f:
            base_stylesheet = f.read()
        
        # Get accent color and generate overrides
        accent_color = ACCENT_COLORS[theme_name]
        accent_stylesheet = _generate_accent_stylesheet(accent_color)
        
        # Combine base + accent
        combined_stylesheet = base_stylesheet + "\n" + accent_stylesheet
        
        # Apply to window
        app_window.setStyleSheet(combined_stylesheet)
        
        return True
        
    except Exception as e:
        return False