# src/python/settings_manager.py

import json
import os
from typing import Any

class SettingsManager:
    """
    Handles loading, saving, and managing application settings from JSON files.
    
    Settings are stored in two files:
    1. A permanent **default settings** file.
    2. A **user settings** file which only stores values that override the defaults.
    This ensures that default settings are always available as a fallback.
    """

    # Define files paths
    _CONFIG_DIR = 'config'
    _DEFAULT_FILE = os.path.join(_CONFIG_DIR, 'default_settings.json')
    _USER_FILE = os.path.join(_CONFIG_DIR, 'user_settings.json')

    def __init__(self) -> None:
        """
        Initializes the :py:class:`.SettingsManager`.

        It ensures the configuration directory exists and validates the presence 
        of the default settings file.
        
        :rtype: None
        """
        os.makedirs(self._CONFIG_DIR, exist_ok=True)
        self._ensure_default_settings()

    def _ensure_default_settings(self) -> None:
        """
        Ensures the default settings file exists. 
        
        If it does not exist, it creates it with a basic, hardcoded 
        structure to prevent :py:class:`FileNotFoundError` on startup.
        
        :rtype: None
        """
        if not os.path.exists(self._DEFAULT_FILE):
            # If Default file is missing create it
            default_data = {
                "theme": "Dark",
                "window_size": "1200x800",
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
        Loads the application settings by merging default and user-specific settings.

        The method prioritizes values from the user file, using defaults as a fallback.
        
        :returns: A dictionary containing the complete, merged application settings.
        :rtype: dict[str, Any]
        """
        settings = self._load_json(self._DEFAULT_FILE)

        # Load user settings and update the defaults
        if os.path.exists(self._USER_FILE):
            user_settings = self._load_json(self._USER_FILE)
            settings.update(user_settings)
            
        return settings
    
    def save_settings(self, settings: dict[str, Any]) -> bool:
        """
        Saves the current application settings to the user settings file.

        Only settings that differ from the default values are written to 
        the user file to keep it clean.
        
        :param settings: The complete dictionary of settings to save.
        :type settings: dict[str, Any]
        
        :returns: True if the save operation was successful, False otherwise.
        :rtype: bool
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
        Directly loads and returns only the default settings from the default file.
        
        :returns: A dictionary containing only the default application settings.
        :rtype: dict[str, Any]
        """
        return self._load_json(self._DEFAULT_FILE)

    def revert_to_defaults(self) -> dict[str, Any]:
        """
        Reverts the application settings to factory defaults.

        This method deletes the user settings file and returns a fresh copy 
        of the default settings.
        
        :returns: A dictionary containing the default application settings.
        :rtype: dict[str, Any]
        """
        if os.path.exists(self._USER_FILE):
            try:
                os.remove(self._USER_FILE)
            except Exception as e:
                print(f"Error deleting user settings file: {e}")
                
        # Return a fresh copy of the defaults
        return self.get_default_settings()

    def _load_json(self, file_path: str) -> dict[str, Any]:
        """
        Internal helper to safely load and return the content of a JSON file.

        If the file does not exist or is malformed, it returns an empty dictionary.
        
        :param file_path: The full path to the JSON file.
        :type file_path: str
        
        :returns: A dictionary containing the file's content, or an empty dict on error.
        :rtype: dict[str, Any]
        """
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return {}