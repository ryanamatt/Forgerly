# src/python/ui/views/base_editor.py

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QCloseEvent

from ...ui.widgets.tag_widget import TagManagerWidget
from ...utils.event_bus import bus

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..widgets.basic_text_editor import BasicTextEditor

class BaseEditor(QWidget):
    """
    Base class for all editor views, providing common state management
    and tag handling functionality.
    """
    def __init__(self, parent=None) -> None:
        """
        Instaniates the BaseEditor class.
        
        :param parent: Description
        :type parent: :py:class:`~PyQy6.QtWidgets.QWidget`

        :rtype: None
        """
        super().__init__(parent)

        bus.register_instance(self)

        self._dirty = False

        self.tag_manager = TagManagerWidget()
        # Common text editor reference (to be initialized by subclasses)
        self.text_editor: BasicTextEditor | None = None

    def __del__(self) -> None:
        """
        Deleting a BaseEditor.
        
        :rtype: None
        """
        try:
            bus.unregister_instance(self)
        except:
            pass

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Handling cleanup after closing the Widget.
        
        :param event: The closing event.
        :type event: QCloseEvent

        :rtype: None
        """
        super().closeEvent()

    def is_dirty(self) -> bool:
        """
        Checks if the content (BasicTextEditor) or the tags (TagManagerWidget) 
        have unsaved changes.

        :returns: True if content or tags are modified, ``False`` otherwise.
        :rtype: bool
        """
        return self.text_editor.is_dirty() or self.tag_manager.is_dirty() or self._dirty
    
    def set_dirty(self) -> None:
        """
        Sets the text_editor and tag_manager to be dirty.
        """
        self._dirty = True
    
    def mark_saved(self) -> None:
        """
        Resets dirty flags for sub-components.
        
        :rtype: None
        """
        if self.text_editor:
            self.text_editor.mark_saved()
        self.tag_manager.mark_saved()

        self._dirty = False

    def set_enabled(self, enabled: bool) -> None:
        """
        Enables or disables the entire editor panel by setting the 
        state of its main sub-components.

        :param enabled: True to enable, False to disable.
        :type enabled: bool

        :rtype: None
        """
        self.setEnabled(enabled)
        if self.text_editor:
            self.text_editor.setEnabled(enabled)
        self.tag_manager.setEnabled(enabled)

    # --- Tagging Passthrough Methods (TagManagerWidget) ---
    
    def get_tags(self) -> list[str]:
        """
        Returns the current list of tag names entered in the tag manager.

        :returns: A list of tag names (strings).
        :rtype: list[str]
        """
        return self.tag_manager.get_tags()

    def set_tags(self, tag_names: list[str]) -> None:
        """
        Sets the tags when a chapter is loaded.

        This function also clears the tag manager's dirty state internally.

        :param tag_names: A list of tag names (strings) to set.
        :type tag_names: list[str]

        :rtype: None
        """
        self.tag_manager.set_tags(tag_names)

    # --- Save and Load Data ---
    def get_save_data(self) -> dict:
        """Subclasses MUST override this to return a dict of their current UI state."""
        raise NotImplementedError("Subclasses must implement get_save_data")

    def load_entity(self, data: dict):
        """Subclasses MUST override this to populate UI and reset initial state."""
        raise NotImplementedError("Subclasses must implement load_entity")
