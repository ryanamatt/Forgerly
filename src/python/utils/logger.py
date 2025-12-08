# src/python/utils/logger.py

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = 'logs'
LOG_FILE = os.path.join(LOG_DIR, 'application.log')
LOG_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
LOG_BACKUP_COUNT = 5

def _clear_log_file() -> None:
    """Deletes the existing log file to start a fresh log on startup."""
    try:
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
    except Exception as e:
        pass

def setup_logger(debug_mode: bool | None = None) -> logging.Logger:
    """
    Configures and returns the application's central logger based on debug_mode.

    :param debug_mode: If True, sets console logging to DEBUG. Defaults to INFO.
    :type debug_mode: bool or None

    :returns: The configured root logger instance.
    :rtype: :py:class:`~logging.Logger`
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    _clear_log_file()

    log_level = logging.DEBUG if debug_mode is True else logging.INFO

    logger = logging.getLogger()
    logger.setLevel(log_level)

    if logger.hasHandlers():
        return logger
    
    # Detailed formatter for the persistent log file (includes function and module)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s'
    )
    # Simple formatter for the console output
    console_formatter = logging.Formatter(
        '[%(levelname)s] %(message)s'
    )

    # File Handler: for detailed, persistent logging
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    # The file should always capture INFO and above for post-crash analysis
    file_handler.setLevel(log_level) 
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console Handler: for immediate, visible feedback
    # console_handler = logging.StreamHandler()
    # console_handler.setLevel(log_level) # Uses the determined level (DEBUG or INFO)
    # console_handler.setFormatter(console_formatter)
    # logger.addHandler(console_handler)

    return logger

def get_logger(name: str | None = None) -> logging.Logger:
    """
    Retrieves a named logger. If no name is given, returns the root logger.
    
    :param name: The name of the logger (e.g., __name__).
    :type name: str or None

    :returns: The logger instance.
    :rtype: :py:class:`~logging.Logger`
    """
    return logging.getLogger(name)