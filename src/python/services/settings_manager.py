# src/python/settings_manager.py

import json
import os
from typing import Any

class SettingsManager:
    """
    Handles loading, saving, and managing application settings from JSON files.
    Ensures that default settings are always available as a fallback.
    """

    # Define files paths
    _CONFIG_DIR = 'config'
    _DEFAULT_FILE = os.path.join(_CONFIG_DIR, 'default_settings.json')
    _USER_FILE = os.path.join(_CONFIG_DIR, 'user_settings.json')

    def __init__(self) -> None:
        os.makedirs(self._CONFIG_DIR, exist_ok=True)
        self._ensure_default_settings()

    def _ensure_default_settings(self) -> None:
        """
        Ensures the default settings file exists. If not, creates it 
        with the basic structure to prevent FileNotFoundError.
        """
        if not os.path.exists(self._DEFAULT_FILE):
            # If Default file is missing create it
            default_data = {
                "theme": "Dark",
                "window_size": "1200x800",
                "autosave_interval_minutes": 5,
                "outline_width_pixels": 300,
                "window_width": 1200,
                "window_height": 800,
                "window_pos_x": 100,
                "window_pos_y": 100
            }
            try:
                with open(self._DEFAULT_FILE,'w') as f:
                    json.dump(default_data, f, indent=4)
            except IOError as e:
                print(f"FATAL: could not create default settings file: {e}")

    def load_settings(self) -> dict[str, Any]:
        """
        Loads the default settings and then overwrites them with user settings.
        """
        settings = self._load_json(self._DEFAULT_FILE)

        # Load user settings and update the defaults
        if os.path.exists(self._USER_FILE):
            user_settings = self._load_json(self._USER_FILE)
            settings.update(user_settings)
            
        return settings
    
    def save_settings(self, settings: dict[str, Any]) -> bool:
        """
        Saves the current settings dictionary to the user file.
        """
        # Load defaults to only save *changes* in the user file
        defaults = self.get_default_settings()
        user_changes = {k: v for k, v in settings.items() if v != defaults.get(k)}
        
        try:
            with open(self._USER_FILE, 'w') as f:
                json.dump(user_changes, f, indent=4)
            return True
        except IOError as e:
            print(f"Error saving user settings: {e}")
            return False

    def get_default_settings(self) -> dict[str, Any]:
        """
        Directly loads and returns only the default settings.
        """
        return self._load_json(self._DEFAULT_FILE)

    def revert_to_defaults(self) -> dict[str, Any]:
        """
        Deletes the user settings file and returns the default settings.
        """
        if os.path.exists(self._USER_FILE):
            try:
                os.remove(self._USER_FILE)
            except Exception as e:
                print(f"Error deleting user settings file: {e}")
                
        # Return a fresh copy of the defaults
        return self.get_default_settings()

    def _load_json(self, file_path: str) -> dict[str, Any]:
        """Internal helper to load a JSON file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return {}