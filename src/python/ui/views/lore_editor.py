# src/python/ui/lore_editor.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QSplitter, 
    QLineEdit, QComboBox, QHBoxLayout, QLabel
)
from PySide6.QtCore import Qt
from typing import Any

from .base_editor import BaseEditor
from ...ui.widgets.basic_text_editor import BasicTextEditor
from ...utils.constants import ViewType, EntityType
from ...utils.events import Events
from ...utils.event_bus import bus, receiver

class LoreEditor(BaseEditor):
    """
    A composite :py:class:`~PySide6.QtWidgets.QWidget` for editing a Lore Entry's details 
    (Title, Content, Category).
    
    This is a pure UI component designed to be managed by an external controller 
    (like the :py:class:`.MainWindow`). It handles data loading, state 
    management (dirty checks), and local validation, but does not interact 
    with repositories directly.
    """

    current_lore_id: int | None = None
    """The database ID of the Lore Entry currently loaded in the editor, or :py:obj:`None`."""
    
    def __init__(self, current_settings: dict, parent=None) -> None:
        """
        Initializes the :py:class:`.LoreEditor` widget.
        
        :param current_settings: A dictionary containing initial application settings.
        :type current_settings: dict
        :param parent: The parent widget.
        :type parent: :py:class:`~PySide6.QtWidgets.QWidget`, optional

        :rtype: None
        """
        super().__init__(parent)

        bus.register_instance(self)

        self._dirty = False

        is_spell_checking = current_settings.get('is_spell_checking')
        
        # --- Sub-components ---
        self.text_editor = BasicTextEditor(is_spell_checking)

        # --- Layout Setup ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Lore-Specific Components (Title and Category) ---

        # Title
        title_group = QWidget()
        title_layout = QHBoxLayout(title_group)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter Lore Entry Title (e.g., 'The Sunken City of K'tal')")
        title_label = QLabel("Title:")
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_input)
        main_layout.addWidget(title_group)

        # Category Group Box
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True) 

        cat_group = QGroupBox("Lore Type")
        cat_layout = QHBoxLayout(cat_group)
        cat_layout.addWidget(QLabel("Category:"))
        cat_layout.addWidget(self.category_combo)
        
        # Tagging Group Box
        tag_group = QGroupBox("Lore Tags")
        tag_layout = QVBoxLayout(tag_group)
        tag_layout.setContentsMargins(10, 15, 10, 10)
        tag_layout.addWidget(self.tag_manager)

        # Vertical Splitter for Metadata (Category/Tags) and Content
        content_splitter = QSplitter(Qt.Orientation.Vertical)
        
        metadata_container = QWidget()
        metadata_layout = QVBoxLayout(metadata_container)
        metadata_layout.setContentsMargins(0, 0, 0, 0)
        metadata_layout.addWidget(cat_group)
        metadata_layout.addWidget(tag_group)
        
        content_splitter.addWidget(metadata_container)
        content_splitter.addWidget(self.text_editor)
        
        content_splitter.setSizes([200, 800]) 
        main_layout.addWidget(content_splitter)
        
        # --- Connections: All changes trigger a dirtiness state check ---
        self.title_input.textChanged.connect(self._set_dirty)
        self.category_combo.currentIndexChanged.connect(self._set_dirty)
        
        # Emit signal when title edit is finished (for Outline update)
        self.title_input.editingFinished.connect(self._emit_title_change)
        
        self.set_enabled(False)
        self.mark_saved()

    def load_lore(self, lore_id: int, title: str, category: str, content: str, tag_names: list[str]) -> None:
        """
        Loads Lore Entry data into the editor fields.
        
        This method updates the Title, Category, and Content fields, and 
        calls :py:meth:`.mark_saved` to reset the dirty state. 
        
        :param lore_id: The ID of the Lore Entry
        :type lore_id: int
        :param title: The title of the Lore Entry
        :type title: str
        :param category: The category of the Lore Entry
        :type category: str
        :param content: The content of the Lore Entry
        :type content: str
        :param tag_names: A list of the names of all tags applied to the Lore Entry
        :type tag_names: list[str]

        :rtype: None
        """
        self.set_enabled(False)
        self.current_lore_id = lore_id

        self.title_input.setText(title)
        
        # Handle Category: Add if it doesn't exist, then set current index
        index = self.category_combo.findText(category)
        if index == -1:
            self.category_combo.insertItem(0, category)
            self.category_combo.setCurrentIndex(0)
        else:
            self.category_combo.setCurrentIndex(index)
            
        self.text_editor.set_html_content(content)
        self.tag_manager.set_tags(tag_names)
        
        # Store initial state for dirtiness check
        self._initial_title = title
        self._initial_category = category
        self.mark_saved()
        self.set_enabled(True)

    @receiver(Events.LORE_CATEGORIES_CHANGED)
    def set_available_categories(self, data: dict) -> None:
        """
        Updates the category combo box with existing categories from the DB.

        :param categories: The list of unique categories.
        :type categories: list[str]

        :rtype: None
        """
        categories = data.get('categories')
        if not categories: return

        current_text = self.category_combo.currentText()
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItems(categories)
        self.category_combo.setCurrentText(current_text)
        self.category_combo.blockSignals(False)

    def get_data(self) -> dict[str, Any]:
        """
        Returns the current state of all editable fields for MainWindow to save.

        This method returns the data in the edittor fields as a dictionary.
        
        :rtype dict[str, Any]
        """
        return {
            'id': self.current_lore_id,
            'title': self.title_input.text().strip(),
            'category': self.category_combo.currentText().strip(),
            'content': self.text_editor.get_html_content(),
            'tags': self.tag_manager.get_tags()
        }
        
    def is_dirty(self) -> bool:
        """
        Returns the dirty flag to see if the editor is dirty.
        
        :returns: True if changes are detected, False otherwise.
        :rtype: bool
        """
        return self._dirty or super().is_dirty()
    
    def _set_dirty(self) -> None:
        """
        Sets the dirty flag to be True.
        
        :rtype: None
        """
        if not self.current_lore_id:
            return False
        
        self._dirty = True

    @receiver(Events.MARK_SAVED)
    def mark_saved_connection(self, data: dict) -> None:
        """
        A connection for the mark saved Event.
        
        :param data: Data dictionary, Empty as function doesn't need it.
        :type data: dict

        :rtype: None
        """
        if data.get('entity_type') != EntityType.LORE:
            return
        
        self.mark_saved()

    def mark_saved(self) -> None:
        """
        Marks all nested components as clean.
        
        :rtype: None
        """
        # # self.text_editor and self.tag_manager
        super().mark_saved()

        self._dirty = False
        
        
    def set_enabled(self, enabled: bool) -> None:
        """
        Enables/disables the entire editor panel.
        
        :param enabled: True if want to enable editor panel, otherwise False
        :type enabled: bool
        
        :rtype: None
        """
        # self.text_editor and self.tag_manager
        super().set_enabled(enabled)

        self.title_input.setEnabled(enabled)
        self.category_combo.setEnabled(enabled)

    def _emit_title_change(self) -> None:
        """
        Emits the signal to update the outline after the user finishes editing the title.
        
        :rtype: None
        """
        if self.current_lore_id is not None:
            bus.publish(Events.OUTLINE_NAME_CHANGE, data={
                'entity_type': EntityType.LORE,
                'ID': self.current_lore_id,
                'new_title': self.title_input.text().strip(),
            })

    def get_save_data(self) -> dict:
        """
        Returns all the current saved data.
        
        :returns: A dictionary of the current lore entry data.
        :rtype: dict
        """
        return {
            'title': self.title_input.text().strip(),
            'content': self.text_editor.get_html_content(),
            'category': self.category_combo.currentText().strip(),
            'tags': self.tag_manager.get_tags()
        }
    
    @receiver(Events.SAVE_REQUESTED)
    def provide_data_for_save(self, data: dict):
        """
        If this editor is dirty, it sends its current content back to the coordinator.

        :param data: The data of the save data.
        :type data: dict

        :rtype: None
        """
        if not self.is_dirty():
            return
        
        if data.get('entity_type') != EntityType.LORE:
            return

        save_data = self.get_save_data()
        data |= save_data
        data.update({'parent': self})

        bus.publish(Events.SAVE_DATA_PROVIDED, data=data)
    
    @receiver(Events.DATA_LOADED)
    def load_entity(self, data: dict) -> None:
        """
        Loads all the information into the editor
        
        :param data: A dict with all Lore Data.
        :type data: dict

        :rtype: None
        """
        if data.get('entity_type') != EntityType.LORE:
            return

        id, title, content = data['ID'], data['Title'], data['Content']
        category, tags = data['Category'], data['tags']

        self.current_lore_id = id

        self.title_input.setText(title)
        self.text_editor.set_html_content(content)
        self.category_combo.setCurrentText(category)
        self.tag_manager.set_tags(tags)

        self.mark_saved()
        self.set_enabled(True)
