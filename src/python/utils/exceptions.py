# src/python/utils/exceptions.py

class ApplicationError(Exception):
    """
    Base class for all custom exceptions in Narrative Forge.

    All specific exceptions should inherit from this class.
    """
    def __init__(self, message: str, original_exception: Exception = None) -> None:
        """
        Initializes the custom error.

        :param message: The user-friendly error message.
        :type message: str
        :param original_exception: The underlying system exception (optional).
        :type original_exception: Exception

        :rtype: None
        """
        super().__init__(message)
        self.original_exception = original_exception
        self.user_message = message

class DatabaseError(ApplicationError):
    """
    Raised for general issues with database operations, such as connection 
    failures, SQL execution errors, or transaction failures.
    """
    pass

class EditorContentError(ApplicationError):
    """
    Raised when there is an issue setting, parsing, or retrieving
    content from a text editor (BasicTextEditor/RichTextEditor).
    """
    pass

class ConfigurationError(ApplicationError):
    """
    Raised when there is an issue loading, saving, or parsing
    application settings (e.g., malformed JSON, file permissions, I/O errors).
    """
    pass