# src/python/ui/view_manager.py

from PyQt6.QtWidgets import QStackedWidget
from PyQt6.QtCore import QObject, pyqtSignal
from ..utils.constants import ViewType
from ..utils.logger import get_logger

# Type checking imports to avoid circular dependencies
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..services.app_coordinator import AppCoordinator
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
    """

    view_changed = pyqtSignal(int)
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (ViewType). Emitted When the View changes
    carrying the new ViewType.
    """

    def __init__(self, outline_stack: QStackedWidget, editor_stack: QStackedWidget, coordinator: 'AppCoordinator') -> None:
        """
        Creates the ViewManager Object.
        
        :param outline_stack: The Stack of OutlineManagers
        :type outline_stack: QStackedWidget
        :param editor_stack: The Stack of Editors
        :type editor_stack: QStackedWidget
        :param coordinator: The AppCoordinator
        :type coordinator: 'AppCoordinator'

        :rtype: None
        """
        super().__init__()
        self.outline_stack = outline_stack
        self.editor_stack = editor_stack
        self.coordinator = coordinator

        # Map ViewType to Stack Index
        self._view_indices = {
            ViewType.CHAPTER_EDITOR: 0,
            ViewType.LORE_EDITOR: 1,
            ViewType.CHARACTER_EDITOR: 2,
            ViewType.NOTE_EDITOR: 3,
            ViewType.RELATIONSHIP_GRAPH: 4
        }

    def switch_to_view(self, view: ViewType) -> None:
        """
        Changes the current visible panels and performs view-specific setup logic.
        
        :param view: The view to switch to.
        :type view: ViewType

        :rtype: None
        """
        index = self._view_indices.get(view)

        if index is None:
            logger.error(f"ViewManager: No stack index defined for {view}")
            return

        logger.info(f"ViewManager: Switching stacks to index {index} for {view}")

        self.outline_stack.setCurrentIndex(index)
        self.editor_stack.setCurrentIndex(index)

        self.coordinator.set_current_view(view)
        self._perform_view_entry_logic(view)

        self.view_changed.emit(view)

    def _perform_view_entry_logic(self, view: ViewType) -> None:
        """
        Executes specific setup tasks required when a view becomes active.
        
        :param view: The view to perform on.
        :type view: ViewType
        """
        editor = self.coordinator.get_current_editor()

        if view == ViewType.RELATIONSHIP_GRAPH:
            # Relationships usually load all data immediately
            if hasattr(editor, 'request_load_data'):
                editor.request_load_data.emit()
            editor.set_enabled(True)
            
        elif view == ViewType.LORE_EDITOR:
            # Refresh category dropdowns for the lore editor
            self.coordinator.refresh_lore_categories()
            editor.set_enabled(False)
            
        else:
            # Default behavior: Editors are disabled until an item is clicked in the outline
            if editor:
                editor.set_enabled(False)
                logger.debug(f"ViewManager: Disabled {view} editor awaiting selection.")

    def get_view_index(self, view: ViewType) -> int:
        """
        Gets the Index of the view.
        
        :param view: The view to get the index for.
        :type view: ViewType
        :return: The index of the view. Returns -1 if not found.
        :rtype: int
        """
        return self._view_indices.get(view, -1)