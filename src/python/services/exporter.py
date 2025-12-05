# src/python/services/exporter.py

from PyQt6.QtWidgets import QWidget
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app_coordinator import AppCoordinator

class Exporter(ABC):
    """
    An **Abstract Base Class (ABC)** defining the interface for all project exporters.
    
    Each concrete subclass (e.g., :py:class:`.StoryExporter`, :py:class:`.CharacterExporter`) 
    will implement the core logic for selecting a file destination, fetching content, 
    and writing that content to a file in a specific format (e.g., DOCX, Markdown).
    """
    def __init__(self, coordinator: AppCoordinator, project_title: str) -> None:
        """
        Initializes the base exporter.

        :param coordinator: The application coordinator, used to access repositories and services.
        :type coordinator: :py:class:`~app.services.app_coordinator.AppCoordinator`
        :param project_title: The current project's title, often used as the default export filename.
        :type project_title: str
        
        :rtype: None
        """
        self.coordinator = coordinator
        self.project_title = project_title

    @abstractmethod
    def export(self, parent: QWidget, selected_ids: list[int] = []) -> bool:
        """
        The main entry point for the export process.
        
        This method should handle opening a file dialog for the user to select the 
        output location, fetching the necessary data using the provided IDs, and 
        calling :py:meth:`._write_file`.

        :param parent: The parent Qt widget, used for modal dialogs like :py:class:`~PyQt6.QtWidgets.QFileDialog`.
        :type parent: :py:class:`~PyQt6.QtWidgets.QWidget`
        :param selected_ids: A list of unique IDs (e.g., chapter IDs, lore item IDs) 
            to be included in the export. Defaults to an empty list, meaning all 
            relevant items should be included if not specified.
        :type selected_ids: list[int]
        
        :returns: True if the export was successful, False otherwise.
        :rtype: bool
        """
        return
    
    @abstractmethod
    def _write_file(self) -> bool:
        """
        Abstract method responsible for the final stage of writing the fetched 
        content to the specified file path.
        
        The implementation must handle the actual file I/O and formatting logic.

        :returns: True if the file write operation succeeded, False otherwise.
        :rtype: bool
        """
        return