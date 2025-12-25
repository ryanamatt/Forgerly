# src/python/utils/error_handler.py

import sys
import traceback
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QCoreApplication

from .logger import get_logger

logger = get_logger(__name__)

def handle_uncaught_exception(exc_type, exc_value, exc_traceback) -> None:
    """
    Dedicated handler for all uncaught Python exceptions.
    Logs the error, shows a user-friendly message, and safely exits.
    
    :param exc_type: The type.
    :param exc_value: The value
    :param exc_traceback: The traceback

    :rtype: None
    """
    log_message = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logger.critical(f"UNCAUGHT EXCEPTION DETECTED:\n{log_message}")

    error_title = "Critical Application Error"
    error_message = (
        "An unexpected and critical error has occurred. The application "
        "must close to prevent data corruption.\n\n"
        "A detailed error report has been saved to 'application.log'."
    )

    # We check for a running QApplication instance before trying to show a dialog
    if QCoreApplication.instance() is not None:
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Icon.Critical)
        error_box.setWindowTitle(error_title)
        error_box.setText(error_message)
        error_box.setDetailedText(log_message) # Optional: Show traceback in details section
        error_box.setStandardButtons(QMessageBox.StandardButton.Close)
        error_box.exec()
        
    # Terminate the application with an error code
    sys.exit(1)

def install_system_exception_hook() -> None:
    """
    Installs the custom exception handler as the system-wide handler.
    
    :rtype: None
    """
    sys.excepthook = handle_uncaught_exception
    logger.debug("System exception hook installed for application-wide crash handling.")
