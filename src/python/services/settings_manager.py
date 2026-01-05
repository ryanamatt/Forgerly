# src/python/settings_manager.py

import json
import os
from typing import Any
from ..utils.logger import get_logger
from ..utils.exceptions import ConfigurationError

logger = get_logger(__name__)

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
        try:
            os.makedirs(self._CONFIG_DIR, exist_ok=True)

        except Exception as e:
            logger.critical(f"FATAL: Failed to create config directory '{self._CONFIG_DIR}'. "
                            "Check permissions.", exc_info=True)
            raise ConfigurationError(f"Cannot initialize settings manager. Failed to create "
                                     f"directory: {self._CONFIG_DIR}") from e

        self._ensure_default_settings()
        logger.debug("SettingsManager initialized successfully.")

    def _ensure_default_settings(self) -> None:
        """
        Ensures the default settings file exists. 
        
        If it does not exist, it creates it with a basic, hardcoded 
        structure to prevent :py:class:`FileNotFoundError` on startup.
        
        :rtype: None
        """
        if not os.path.exists(self._DEFAULT_FILE):
            logger.warning(f"Default settings file not found at {self._DEFAULT_FILE}. "
                           "Creating minimal default file.")
            try:
                default_data = {
                    "last_project_path": "",
                    "theme": "Dark",
                    "window_size": "1200x800",
                    "outline_width_pixels": 300,
                    "window_width": 1200,
                    "window_height": 800,
                    "window_pos_x": 100,
                    "window_pos_y": 100
                }

                with open(self._DEFAULT_FILE,'w') as f:
                    json.dump(default_data, f, indent=4)

                logger.info(f"Created new default settings file at {self._DEFAULT_FILE}.")

            except Exception as e:
                logger.critical(f"FATAL: Failed to create a new default settings file.", exc_info=True)
                raise ConfigurationError("A critical application file is missing and cannot be created.") from e

    def load_settings(self) -> dict[str, Any]:
        """
        Loads the application settings by merging default and user-specific settings.

        The method prioritizes values from the user file, using defaults as a fallback.
        
        :returns: A dictionary containing the complete, merged application settings.
        :rtype: dict[str, Any]
        """
        logger.debug("Attempting to load settings.")
        
        # 1. Load Defaults (must exist and be valid)
        default_settings = self.get_default_settings() 
        
        # 2. Load User Overrides (may not exist, handled by _load_json returning {})
        user_settings = self._load_json(self._USER_FILE)
        
        # 3. Merge: Start with a copy of defaults and update with user overrides
        merged_settings = default_settings.copy()
        merged_settings.update(user_settings)
        
        logger.info(f"Settings loaded and merged successfully. Keys: {len(merged_settings)}.")
        
        # CRITICAL FIX: The save_settings call is absent here.
        # This prevents the repetitive loading/saving loop.
        
        return merged_settings
    
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
        try:
            logger.info(f"Attempting to save {len(settings)} user-defined settings to {self._USER_FILE}.")
            with open(self._USER_FILE, 'w') as f:
                json.dump(settings, f, indent=4)
            logger.info("User settings saved successfully.")
        except Exception as e:
            logger.error(f"CRITICAL: Failed to save user settings to {self._USER_FILE}.", exc_info=True)
            raise ConfigurationError("Failed to save application settings. Changes may be lost.") from e
        
    def save_setting(self, key: str, value: Any) -> bool:
        """
        Saves a single setting key and saves the new user-level settings file.

        This function first loads the existing user settings, updates the single key, 
        then calls the main save_settings method to handle the comparison against defaults.
        
        :param key: The setting key to update (e.g., 'outline_width_pixels').
        :type key: str
        :param value: The new value for the setting.
        :type value: Any
        
        :returns: True if the save operation was successful, False otherwise.
        :rtype: bool
        """
        # Load the current merged settings
        current_settings = self.load_settings()
        
        # Update the single key in memory
        current_settings[key] = value
        
        # Use the existing save_settings logic to save only the change
        return self.save_settings(current_settings)

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
                logger.info(f"User settings file deleted: {self._USER_FILE}. Reverted to defaults.")
            except Exception as e:
                logger.error(f"Error deleting user settings file: {self._USER_FILE}. File may be "
                             "locked or permissions denied.", exc_info=True)
                raise ConfigurationError("Failed to reset user settings due to a file system error.") from e
                
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
                content = json.load(f)
                logger.debug(f"Successfully loaded JSON from: {file_path}. Data keys: {list(content.keys())}")
                return content
            
        except FileNotFoundError:
            if file_path == self._DEFAULT_FILE:
                # This should be caught by _ensure_default_settings, but acts as a final fail-safe
                logger.critical(f"FATAL: Default settings file is missing at startup: {file_path}")
                raise ConfigurationError("Critical default settings file is missing and cannot be loaded.")
            
            # User settings file missing is expected on first run, so it's logged as INFO
            logger.info(f"User settings file not found: {file_path}. Returning empty dict.") 
            return {}
        
        except json.JSONDecodeError as e:
            # CRITICAL: A configuration file is corrupt
            logger.critical(f"FATAL: JSON format error in file: {file_path}.", exc_info=True)
            raise ConfigurationError(f"Configuration file is corrupt: {file_path}") from e
        
        except Exception as e:
            # Catch all other I/O errors (e.g., permissions, disk full)
            logger.critical(f"FATAL: Failed to read file: {file_path}.", exc_info=True)
            raise ConfigurationError(f"Failed to access configuration file: {file_path}") from e
