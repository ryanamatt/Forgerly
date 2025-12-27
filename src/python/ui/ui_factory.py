# src/python/ui/ui_factory.py

from PySide6.QtWidgets import QStackedWidget

from .views.chapter_outline_manager import ChapterOutlineManager
from .views.chapter_editor import ChapterEditor
from .views.lore_outline_manager import LoreOutlineManager
from .views.lore_editor import LoreEditor
from .views.character_outline_manager import CharacterOutlineManager
from .views.character_editor import CharacterEditor
from .views.note_outline_manager import NoteOutlineManager
from .views.note_editor import NoteEditor
from .views.relationship_outline_manager import RelationshipOutlineManager
from .views.relationship_editor import RelationshipEditor

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..services.app_coordinator import AppCoordinator

class UIFactory:
    """
    Handles the instantiation of all major UI components for MainWindow.
    """
    @staticmethod
    def create_components(project_title: str, coordinator: 'AppCoordinator', settings: dict) -> dict:
        """
        Instantiates all editors and outlines.
        
        :param project_title: The title of the project
        :type: project_title: str
        :param coordinator: The AppCoordinator
        :type coordinator: 'AppCoordinator'
        :param settings: The dictionary of settings
        :type settings: dict

        :returns: a dictionary containing the stacks and the individual editors.
        :rtype: dict
        """
        # Instantiate Managers and Editors
        components = {
            'chapter_outline': ChapterOutlineManager(project_title=project_title),
            'chapter_editor': ChapterEditor(settings),
            
            'lore_outline': LoreOutlineManager(project_title=project_title),
            'lore_editor': LoreEditor(),
            
            'character_outline': CharacterOutlineManager(project_title=project_title),
            'character_editor': CharacterEditor(),
            
            'note_outline': NoteOutlineManager(project_title=project_title),
            'note_editor': NoteEditor(settings),

            'relationship_outline': RelationshipOutlineManager(relationship_repository=coordinator.relationship_repo),
            'relationship_editor': RelationshipEditor()
        }

        # Create and Populate Stacks
        outline_stack = QStackedWidget()
        outline_stack.addWidget(components['chapter_outline'])
        outline_stack.addWidget(components['lore_outline'])
        outline_stack.addWidget(components['character_outline'])
        outline_stack.addWidget(components['note_outline'])
        outline_stack.addWidget(components['relationship_outline'])

        editor_stack = QStackedWidget()
        editor_stack.addWidget(components['chapter_editor'])
        editor_stack.addWidget(components['lore_editor'])
        editor_stack.addWidget(components['character_editor'])
        editor_stack.addWidget(components['note_editor'])
        editor_stack.addWidget(components['relationship_editor'])

        return outline_stack, editor_stack
