# src/python/utils/theme_utils.py

import os
from PyQt6.QtWidgets import QWidget
from typing import TYPE_CHECKING, Dict, Any, List

if TYPE_CHECKING:
    HasStyleSheet = QWidget
else:
    HasStyleSheet = object

# Define the directory where style files are stored
STYLES_DIR = 'styles'

def get_available_themes() -> List[str]:
    """
    Scans the styles directory for .qss files and returns a list of theme names.
    The theme name is derived from the filename (e.g., 'dark.qss' -> 'Dark').
    If the directory does not exist, it returns a default list.
    """
    themes = []
    
    if not os.path.exists(STYLES_DIR):
        print(f"Warning: Styles directory not found at {STYLES_DIR}. Using default themes.")
        return ["Light", "Dark"] # Fallback to hardcoded names

    for filename in os.listdir(STYLES_DIR):
        # Check if the file ends with the .qss extension
        if filename.endswith('.qss'):
            # Remove the .qss extension
            theme_name = os.path.splitext(filename)[0]
            # Capitalize the first letter (e.g., 'dark' -> 'Dark')
            themes.append(theme_name.capitalize())
            
    # Ensure there's a fallback if the directory is empty but exists
    if not themes:
        themes = ["Light", "Dark"]

    # Sort the themes alphabetically for the UI
    return sorted(list(set(themes)))

def apply_theme(app_window: HasStyleSheet, settings: dict[str, Any]) -> bool:
    """
    Loads and applies the QSS file for the selected theme to the given window/widget.

    Args:
        app_window: The QMainWindow or QWidget instance to apply the stylesheet to.
        settings: The application settings dictionary containing the 'theme' key.

    Returns:
        True if the theme was applied successfully, False otherwise.
    """
    theme_name = settings.get("theme", "Light") # Default to 'Light' if key is missing
    theme_file = os.path.join('styles', f"{theme_name.lower()}.qss")

    if os.path.exists(theme_file):
        try:
            with open(theme_file, 'r') as f:
                # Apply the stylesheet to the QMainWindow
                app_window.setStyleSheet(f.read())
            
            print(f"Theme applied: {theme_name}")
            return True

        except Exception as e:
            print(f"Error loading theme file {theme_file}: {e}")
            return False
    else:
        print(f"Theme file not found: {theme_file}")
        return False