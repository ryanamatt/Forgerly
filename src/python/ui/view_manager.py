# src/python/ui/view_manager.py

from PySide6.QtWidgets import QStackedWidget
from PySide6.QtCore import QObject, Signal

from ..utils.constants import ViewType, EntityType
from ..utils.events import Events
from ..utils.event_bus import bus, receiver
from ..utils.logger import get_logger

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .views.base_editor import BaseEditor
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

logger = get_logger(__name__)

class ViewManager(QObject):
    """
    Orchestrates the switching of UI panels within MainWindow.
    Manages the synchronization between the Outline Stack and the Editor Stack.

    Connects the OutlineManager, Editor signals.
    """

    view_changed = Signal(int)
    """
    :py:class:`~PySide6.QtCore.Signal` (ViewType). Emitted When the View changes
    carrying the new ViewType.
    """

    def __init__(self, outline_stack: QStackedWidget, editor_stack: QStackedWidget) -> None:
        """
        Creates the ViewManager Object.
        
        :param outline_stack: The Stack of OutlineManagers
        :type outline_stack: QStackedWidget
        :param editor_stack: The Stack of Editors
        :type editor_stack: QStackedWidget

        :rtype: None
        """
        super().__init__()

        bus.register_instance(self)

        self.outline_stack = outline_stack
        self.editor_stack = editor_stack

        # Default View is Chapter Editor when first launching
        self.current_view = ViewType.CHAPTER_EDITOR

        # Map ViewType to Stack Index
        self._view_indices = {
            ViewType.CHAPTER_EDITOR: 0,
            ViewType.LORE_EDITOR: 1,
            ViewType.CHARACTER_EDITOR: 2,
            ViewType.NOTE_EDITOR: 3,
            ViewType.RELATIONSHIP_GRAPH: 4
        }

        self._connect_view_signals()

    def _connect_view_signals(self) -> None:
        """
        Connects navigation and view-state signals internally.
        
        :rtype: None
        """

        chapter_editor: ChapterEditor = self.editor_stack.widget(0) # ChapterEditor
        lore_editor: LoreEditor = self.editor_stack.widget(1)    # LoreEditor
        char_editor: CharacterEditor = self.editor_stack.widget(2)    # ChapterEditor
        note_editor: NoteEditor = self.editor_stack.widget(3) # NoteEditor
        rel_editor: RelationshipEditor = self.editor_stack.widget(4) # RelationshipEditor

        chapter_outline: ChapterOutlineManager = self.outline_stack.widget(0) # ChapterOutlineManager
        lore_outline: LoreOutlineManager = self.outline_stack.widget(1)    # LoreOutlineManager
        char_outline: CharacterOutlineManager = self.outline_stack.widget(2)    # CharacterOutlineManager
        note_outline: NoteOutlineManager = self.outline_stack.widget(3) # NoteOutlineManager
        rel_outline: RelationshipOutlineManager = self.outline_stack.widget(4) #RelationshipOutlineManager

        # Connect the internal relay signals to the specific widgets - MainMenuBar
        # self.new_chapter_requested.connect(chapter_outline.prompt_and_add_chapter)
        # self.new_lore_requested.connect(lore_outline.prompt_and_add_lore)
        # self.new_character_requested.connect(char_outline.prompt_and_add_character)

    def get_current_editor(self) -> 'BaseEditor':
        """
        Gets the current Editor
        
        :return: The current Editors
        :rtype: BaseEditor
        """
        return self.editor_stack.currentWidget()
    
    def get_current_view(self) -> ViewType:
        """
        Gets the current view
        
        :return: The current View
        :rtype: ViewType
        """
        return self.current_view

    # @receiver(Events.VIEW_SWITCH_REQUESTED)
    # def _switch_view(self, data: dict):
    #     """
    #     TEMPORARY HELPER for event bus to switch view.
    #     """
    #     self.switch_to_view(view=data.get('view_type'))

    @receiver(Events.VIEW_SWITCH_REQUESTED)
    def switch_to_view(self, data: dict) -> None:
        """
        Changes the current visible panels and performs view-specific setup logic.
        
        :param data: Carrying the dict of a data containing {'view_type': ViewType}
        :type data: dict

        :rtype: None
        """
        view = data.get('view_type')
        index = self._view_indices.get(view, -1)

        if index == -1:
            logger.error(f"ViewManager: No stack index defined for {view}")
            return

        logger.info(f"ViewManager: Switching stacks to index {index} for {view}")

        self.current_view = view
        self.outline_stack.setCurrentIndex(index)
        self.editor_stack.setCurrentIndex(index)

        self._perform_view_entry_logic(view)

        # self.view_changed.emit(view)
        bus.publish(Events.VIEW_CHANGED, data={'current_view': self.current_view})

    def _perform_view_entry_logic(self, view: ViewType) -> None:
        """
        Executes specific setup tasks required when a view becomes active.
        
        :param view: The view to perform on.
        :type view: ViewType
        """
        editor: BaseEditor = self.get_current_editor()

        if view == ViewType.RELATIONSHIP_GRAPH:
            bus.publish(Events.GRAPH_LOAD_REQUESTED)
            entity_type = EntityType.RELATIONSHIP

        elif view == ViewType.CHAPTER_EDITOR:
            entity_type = EntityType.CHAPTER
            
        elif view == ViewType.LORE_EDITOR:
            # Refresh category dropdowns for the lore editor
            bus.publish(Events.LORE_CATEGORIES_REFRESH)
            entity_type = EntityType.LORE

        elif view == ViewType.CHARACTER_EDITOR:
            entity_type = EntityType.CHARACTER

        elif view == ViewType.NOTE_EDITOR:
            entity_type = EntityType.NOTE
            
        else:
            # Default behavior: Editors are disabled until an item is clicked in the outline
            if editor:
                editor.set_enabled(False)
                logger.debug(f"ViewManager: Disabled {view} editor awaiting selection.")

        bus.publish(Events.OUTLINE_LOAD_REQUESTED, data={
                'entity_type': entity_type
            })

    def set_wpm(self, wpm: int) -> None:
        """
        Sets the WPM in ChapterEditor
        
        :param wpm: The new WPM
        :type wpm: int
        """
        self.editor_stack.widget(0).set_wpm(wpm)
