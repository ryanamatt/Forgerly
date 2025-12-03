# src/python/services/exporter.py

from PyQt6.QtWidgets import QWidget
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app_coordinator import AppCoordinator

class Exporter(ABC):
    """
    A generic Exporter class for exporting features of a Project.
    """
    def __init__(self, coordinator: AppCoordinator, project_title: str) -> None:
        self.coordinator = coordinator
        self.project_title = project_title

    @abstractmethod
    def export(self, parent: QWidget, selected_ids: list[int] = []) -> bool:
        return
    
    @abstractmethod
    def _write_file(self) -> bool:
        return