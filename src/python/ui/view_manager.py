# src/python/ui/view_manager.py

from PyQt6.QtWidgets import QStackedWidget
from PyQt6.QtCore import QObject, pyqtSignal

from ..utils.constants import ViewType
from ..utils.logger import get_logger

# Type checking imports to avoid circular dependencies
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..services.app_coordinator import AppCoordinator
    from .menu.main_menu_bar import MainMenuBar
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

    Connects the OutlineManager, Editor signals to the coordinator.
    """

    view_changed = pyqtSignal(int)
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (ViewType). Emitted When the View changes
    carrying the new ViewType.
    """

    def __init__(self, outline_stack: QStackedWidget, editor_stack: QStackedWidget, 
                 coordinator: 'AppCoordinator', main_menu_bar: 'MainMenuBar') -> None:
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
        self.main_menu_bar = main_menu_bar

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
        self.main_menu_bar.save_requested.connect(self.coordinator.save_current_item)

        self.main_menu_bar.view_switch_requested.connect(self.switch_to_view)
        self.view_changed.connect(self.main_menu_bar.update_view_checkmarks)

        chapter_editor: ChapterEditor = self.editor_stack.widget(0) # ChapterEditor
        lore_editor: LoreEditor = self.editor_stack.widget(1)    # LoreEditor
        char_editor: CharacterEditor = self.editor_stack.widget(2)    # ChapterEditor
        note_editor: NoteEditor = self.editor_stack.widget(3) # NoteEditor
        rel_editor: RelationshipEditor = self.editor_stack.widget(4)

        chapter_outline: ChapterOutlineManager = self.outline_stack.widget(0) # ChapterOutlineManager
        lore_outline: LoreOutlineManager = self.outline_stack.widget(1)    # LoreOutlineManager
        char_outline: CharacterOutlineManager = self.outline_stack.widget(2)    # CharacterOutlineManager
        note_outline: NoteOutlineManager = self.outline_stack.widget(3) # NoteOutlineManager
        rel_outline: RelationshipOutlineManager = self.outline_stack.widget(4)

        # New Item Created Connect to Switch View
        chapter_outline.new_item_created.connect(lambda: self.switch_to_view(ViewType.CHAPTER_EDITOR))
        lore_outline.new_item_created.connect(lambda: self.switch_to_view(ViewType.LORE_EDITOR))
        char_outline.new_item_created.connect(lambda: self.switch_to_view(ViewType.CHARACTER_EDITOR))
        note_outline.new_item_created.connect(lambda: self.switch_to_view(ViewType.NOTE_EDITOR))

        # Pre Item Change Connect to AppCoordinator.check_save_before_change
        chapter_outline.pre_item_change.connect(self.coordinator.check_and_save_dirty)
        lore_outline.pre_item_change.connect(self.coordinator.check_and_save_dirty)
        char_outline.pre_item_change.connect(self.coordinator.check_and_save_dirty)
        note_outline.pre_item_change.connect(self.coordinator.check_and_save_dirty)

        # Outline Item Select -> AppCoordinator.load_item(item_id, ViewType)
        chapter_outline.item_selected.connect(
            lambda item_id: self.coordinator.load_item(item_id, ViewType.CHAPTER_EDITOR)
        )
        lore_outline.item_selected.connect(
            lambda item_id: self.coordinator.load_item(item_id, ViewType.LORE_EDITOR)
        )
        char_outline.item_selected.connect(
            lambda item_id: self.coordinator.load_item(item_id, ViewType.CHARACTER_EDITOR)
        )
        note_outline.item_selected.connect(
            lambda item_id: self.coordinator.load_item(item_id, ViewType.NOTE_EDITOR)
        )

        # MainMenuBar New Item Connect to outline.prompt_and_add_*item*
        self.main_menu_bar.new_chapter_requested.connect(chapter_outline.prompt_and_add_chapter)
        self.main_menu_bar.new_lore_requested.connect(lore_outline.prompt_and_add_lore)
        self.main_menu_bar.new_character_requested.connect(char_outline.prompt_and_add_character)

        # Item Selected to Coordinator.load_item(item_id, ViewType.Editor)
        self.coordinator.chapter_loaded.connect(chapter_editor.load_entity)
        self.coordinator.lore_loaded.connect(lore_editor.load_entity)
        self.coordinator.char_loaded.connect(char_editor.load_entity)
        self.coordinator.note_loaded.connect(note_editor.load_entity)

        # Load & Reload Graph Data
        self.coordinator.graph_data_loaded.connect(rel_editor.load_graph)
        rel_outline.relationship_types_updated.connect(self.coordinator.reload_relationship_graph_data)
        rel_editor.request_load_data.connect(self.coordinator.load_relationship_graph_data)

        # Lore Categories
        self.coordinator.lore_categories_changed.connect(lore_editor.set_available_categories)


    def switch_to_view(self, view: ViewType) -> None:
        """
        Changes the current visible panels and performs view-specific setup logic.
        
        :param view: The view to switch to.
        :type view: ViewType

        :rtype: None
        """
        index = self._view_indices.get(view, -1)

        if index == -1:
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
        editor: BaseEditor = self.coordinator.get_current_editor()

        if view == ViewType.RELATIONSHIP_GRAPH:
            # Relationships usually load all data immediately
            if isinstance(editor, RelationshipEditor):
                editor.request_load_data.emit()
            editor.set_enabled(True)
            
        elif view == ViewType.LORE_EDITOR:
            # Refresh category dropdowns for the lore editor
            self.coordinator.refresh_lore_categories()
            
        else:
            # Default behavior: Editors are disabled until an item is clicked in the outline
            if editor:
                editor.set_enabled(False)
                logger.debug(f"ViewManager: Disabled {view} editor awaiting selection.")
