# src/python/ui/view_manager.py

from PySide6.QtWidgets import QStackedWidget
from PySide6.QtCore import QObject, Signal

from ..utils.constants import ViewType
from ..utils.logger import get_logger

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

    view_changed = Signal(int)
    """
    :py:class:`~PyQt6.QtCore.Signal` (ViewType). Emitted When the View changes
    carrying the new ViewType.
    """

    save_requested = Signal(object, int) # (editor_instance, ViewType)
    """
    :py:class:`~PyQt6.QtCore.Signal` (editor ,ViewType). Emitted When a save is requested
    carrying the Editor, View
    """

    load_requested = Signal(int, int)    # (item_id, ViewType)
    """
    :py:class:`~PySide6.QtCore.Signal` (editor ,ViewType). Emitted When a load is requested
    carrying the item_id, View
    """

    relay_lookup_requested = Signal(str)
    """
    :py:class:`~PySide6.QtCore.Signal` (str). Emitted When a lookup is requested carrying
    the text to lookup.
    """

    relay_return_lookup_requested = Signal(str, str, str)
    """
    :py:class:`~PySide6.QtCore.Signal` (str, str, str) Emitted when returning a lookup. 
    Carries the (EntityType, Name of Entity, Description of Entity)
    """

    item_selected = Signal(int, int)

    check_save = Signal(int, object)


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
        self.main_menu_bar.save_requested.connect(
            lambda: self.coordinator.save_current_item(
                view=self.get_current_view(), editor=self.get_current_editor()
            ))

        self.main_menu_bar.view_switch_requested.connect(self.switch_to_view)
        self.view_changed.connect(self.main_menu_bar.update_view_checkmarks)

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

        # New Item Created Connect to Switch View
        chapter_outline.new_item_created.connect(lambda: self.switch_to_view(ViewType.CHAPTER_EDITOR))
        lore_outline.new_item_created.connect(lambda: self.switch_to_view(ViewType.LORE_EDITOR))
        char_outline.new_item_created.connect(lambda: self.switch_to_view(ViewType.CHARACTER_EDITOR))
        note_outline.new_item_created.connect(lambda: self.switch_to_view(ViewType.NOTE_EDITOR))

        # Pre Item Change Connect to AppCoordinator.check_save_before_change
        chapter_outline.pre_item_change.connect(
            lambda: self.check_save.emit(
                self.get_current_view(), self.get_current_editor()
            ))
        lore_outline.pre_item_change.connect(
            lambda: self.check_save.emit(
                self.get_current_view(), self.get_current_editor()
            ))
        char_outline.pre_item_change.connect(
            lambda: self.check_save.emit(
                self.get_current_view(), self.get_current_editor()
            ))
        note_outline.pre_item_change.connect(
            lambda: self.check_save.emit(
                self.get_current_view(), self.get_current_editor()
            ))

        # Outline Item Select -> AppCoordinator.load_item(item_id, ViewType)
        chapter_outline.item_selected.connect(
            lambda item_id: self.load_requested.emit(item_id, ViewType.CHAPTER_EDITOR)
        )
        lore_outline.item_selected.connect(
            lambda item_id: self.load_requested.emit(item_id, ViewType.LORE_EDITOR)
        )
        char_outline.item_selected.connect(
            lambda item_id: self.load_requested.emit(item_id, ViewType.CHARACTER_EDITOR)
        )
        note_outline.item_selected.connect(
            lambda item_id: self.load_requested.emit(item_id, ViewType.NOTE_EDITOR)
        )

        # MainMenuBar New Item Connect to outline.prompt_and_add_*item*
        self.main_menu_bar.new_chapter_requested.connect(chapter_outline.prompt_and_add_chapter)
        self.main_menu_bar.new_lore_requested.connect(lore_outline.prompt_and_add_lore)
        self.main_menu_bar.new_character_requested.connect(char_outline.prompt_and_add_character)

        # Editor Lookup Signals
        chapter_editor.lookup_requested.connect(self.relay_lookup_requested.emit)
        self.relay_return_lookup_requested.connect(chapter_editor.display_lookup_result)

        # Load & Reload Graph Data
        self.coordinator.graph_data_loaded.connect(rel_editor.load_graph)
        rel_outline.relationship_types_updated.connect(self.coordinator.load_relationship_graph_data)
        rel_editor.request_load_data.connect(self.coordinator.load_relationship_graph_data)
        rel_editor.save_node_attributes.connect(self.coordinator.save_node_position)
        rel_editor.request_load_rel_types.connect(
            self.coordinator.load_relationship_types_for_editor
        )
        self.coordinator.relationship_types_available.connect(
            rel_editor.set_available_relationship_types
        )

        # Relationship Editor -> Coordinator
        rel_editor.relationship_created.connect(self.coordinator.save_new_relationship)
        rel_editor.relationship_deleted.connect(self.coordinator.handle_relationship_deletion)

        # Lore Categories
        self.coordinator.lore_categories_changed.connect(lore_editor.set_available_categories)

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

        self.current_view = view
        self.outline_stack.setCurrentIndex(index)
        self.editor_stack.setCurrentIndex(index)

        # self.coordinator.set_current_view(view)
        self._perform_view_entry_logic(view)

        self.view_changed.emit(view)


    def _perform_view_entry_logic(self, view: ViewType) -> None:
        """
        Executes specific setup tasks required when a view becomes active.
        
        :param view: The view to perform on.
        :type view: ViewType
        """
        editor: BaseEditor = self.get_current_editor()

        if view == ViewType.RELATIONSHIP_GRAPH:
            # Relationships usually load all data immediately
            if hasattr(editor, 'request_load_data'):
                editor: RelationshipEditor = editor
                editor.request_load_data.emit()
            if hasattr(editor, 'request_load_rel_types'):
                editor.request_load_rel_types.emit()
            
        elif view == ViewType.LORE_EDITOR:
            # Refresh category dropdowns for the lore editor
            self.coordinator.refresh_lore_categories()
            
        else:
            # Default behavior: Editors are disabled until an item is clicked in the outline
            if editor:
                editor.set_enabled(False)
                logger.debug(f"ViewManager: Disabled {view} editor awaiting selection.")

    def set_wpm(self, wpm: int) -> None:
        """
        Sets the WPM in ChapterEditor
        
        :param wpm: The new WPM
        :type wpm: int
        """
        print(f"ViewManager.set_wpm() {wpm}")
        self.editor_stack['chapter_editor'].set_wpm(wpm)
