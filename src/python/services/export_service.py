# src/python/services/export_service.py

from ..utils.constants import ExportType
from .story_exporter import StoryExporter
from .character_exporter import CharacterExporter
from .lore_exporter import LoreExporter
from ..utils.logger import get_logger
from ..utils.event_bus import bus, receiver
from ..utils.events import Events

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .exporter import Exporter

logger = get_logger(__name__)

class ExportService:
    """
    A service to help export the user wanted stuff.
    """
    def __init__(self, project_title: str) -> None:
        """
        Docstring for __init__
        
        :param project_title: The Title of the project.
        :type: project_title: str
        :rtype: None
        """
        bus.register_instance(self)

        self.project_title = project_title
        
        # Initialize the concrete exporters
        story_exporter = StoryExporter(project_title=project_title)
        self.exporters = {
            ExportType.STORY: story_exporter,
            ExportType.CHAPTERS: story_exporter,
            ExportType.CHARACTERS: CharacterExporter(project_title),
            ExportType.LORE: LoreExporter(project_title)
        }

    @receiver(Events.EXPORT_PERFORM)
    def handle_export_request(self, data: dict):
        export_type = data.get('export_type')
        selected_ids = data.get('selected_ids', [])
        parent_widget = data.get('parent') # Pass parent for dialogs

        exporter: Exporter = self.exporters.get(export_type)
        if exporter:
            success = exporter.export(parent=parent_widget, selected_ids=selected_ids)
            if success:
                logger.info(f"Successfully exported {export_type}")
