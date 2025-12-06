# src/python/ui/tag_widget.py

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, 
    QPushButton, QLabel, QSizePolicy
)
from PyQt6.QtCore import QSize, pyqtSignal

from .flow_layout import QFlowLayout
    
class TagLabel(QWidget):
    """
    A small, removable pill-style widget for displaying a single tag.
    
    This widget consists of a :py:class:`~PyQt6.QtWidgets.QLabel` for the tag name 
    and a :py:class:`~PyQt6.QtWidgets.QPushButton` for removal.
    It emits a signal when the remove button is clicked.
    """
    
    tag_removed = pyqtSignal(str)
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (str): Emitted when the tag is removed carrying the tag's name.
    """

    def __init__(self, tag_name: str, parent=None) -> None:
        """
        Initializes the TagLabel.
        
        :param tag_name: The text content of the tag.
        :type tag_name: :py:class:`str`
        :param parent: The parent widget. Defaults to ``None``.
        :type parent: :py:class:`~PyQt6.QtWidgets.QWidget`, optional

        :rtype: None
        """
        super().__init__(parent)
        self.tag_name = tag_name
        
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # Internal layout
        self.h_layout = QHBoxLayout(self)
        self.h_layout.setContentsMargins(6, 2, 6, 2)
        self.h_layout.setSpacing(4)
        
        # Label for the tag text
        self.label = QLabel(self.tag_name)
        # Use a slightly smaller font for the tag text
        font = self.label.font()
        font.setPointSize(font.pointSize() - 1)
        self.label.setFont(font)
        
        # Button for removal (using a common symbol/style)
        self.remove_button = QPushButton("×") 
        self.remove_button.setFlat(True) # Make it look like part of the tag
        self.remove_button.setFixedSize(QSize(20, 20)) # Small fixed size
        self.remove_button.setStyleSheet("""
            QPushButton {
                padding: 0px; 
                margin: 0px; 
                border: none;
                font-weight: bold;
                color: #a80f0f;
            }
            QPushButton:hover {
                color: #A00000;
            }
        """)
        
        # Connect the remove button to emit the signal
        self.remove_button.clicked.connect(lambda: self.tag_removed.emit(self.tag_name))

        self.h_layout.addWidget(self.label)
        self.h_layout.addWidget(self.remove_button)

        # Apply basic pill-style CSS
        self.setStyleSheet("""
            TagLabel {
                background-color: #E0E0E0; 
                border-radius: 10px; 
                border: 1px solid #CCCCCC;
            }
        """)

class TagManagerWidget(QWidget):
    """
    A complete :py:class:`~PyQt6.QtWidgets.QWidget` for managing a list of tags. 
    
    It provides a :py:class:`~PyQt6.QtWidgets.QLineEdit` for input and displays 
    the current tags using a :py:class:`.QFlowLayout`, allowing them to wrap dynamically. 
    Tags are stored as a unique set (case-insensitive, converted to lowercase).
    """

    tags_changed = pyqtSignal(list)
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal`: Emitted when the list of tags has been modified.
    """

    def __init__(self, initial_tags: list[str] = None, parent=None) -> None:
        """
        Initializes the TagManagerWidget.
        
        :param initial_tags: A list of tag strings to initialize the widget with.
        :type initial_tags: :py:obj:`list[str]`, optional
        :param parent: The parent widget. Defaults to ``None``.
        :type parent: :py:class:`~PyQt6.QtWidgets.QWidget`, optional

        :rtype: None
        """
        super().__init__(parent)
        self.tags = set() # Use a set for quick lookups and uniqueness

        self._is_dirty = False
        
        # --- UI Setup ---
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(6)
        
        # 1. Tag Input Field (QLineEdit)
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Add tags (e.g., fantasy, action) and press Enter...")
        # Connect Enter key press to the tag addition logic
        self.tag_input.returnPressed.connect(self._add_tag_from_input)

        # 2. Flow Layout Container for Tags
        # This wrapper ensures the flow layout works inside the QVBoxLayout
        self.tag_container = QWidget()
        self.tag_flow_layout = QFlowLayout(self.tag_container, margin=0, spacing=6)
        
        self.main_layout.addWidget(self.tag_input)
        self.main_layout.addWidget(self.tag_container)
        
        # --- Initialization ---
        if initial_tags:
            self.set_tags(initial_tags)

    def is_dirty(self) -> bool:
        """
        Checks if the tags have unsaved changes since the last mark_saved call.
        
        :return: True if tags have been modified, False otherwise.
        :rtype: bool
        """
        return self._is_dirty
    
    def mark_saved(self) -> None:
        """
        Marks the current state of the tags as clean (saved).
        
        :rtype: None
        """
        self._is_dirty = False
        
    def _set_dirty(self) -> None:
        """
        Sets the dirty flag to True and emits the tags_changed signal if 
        the state transitioned from clean to dirty.

        :rtype: None
        """
        if not self._is_dirty:
            self._is_dirty = True
            # The signal is emitted here, which will be handled by MainWindow
            self.tags_changed.emit(self.get_tags())

    def _add_tag_from_input(self) -> None:
        """
        Processes the text in the input line. 
        
        It splits by comma or semicolon and adds all valid, unique, non-empty tags. 
        The input line is cleared after processing.

        :rtype: None
        """
        input_text = self.tag_input.text().strip()
        if not input_text:
            return

        # Split input by commas or semicolons
        raw_tags = input_text.replace(';', ',').split(',')
        
        new_tags_added = False
        for tag in raw_tags:
            clean_tag = tag.strip().lower()
            if clean_tag and clean_tag not in self.tags:
                self.tags.add(clean_tag)
                self._create_tag_label(clean_tag)
                new_tags_added = True

        if new_tags_added:
            self.tags_changed.emit(self.get_tags())
        
        if clean_tag and clean_tag not in self.tags:
            self.tags.add(clean_tag)
            self._create_tag_label(clean_tag)
            self.tag_input.clear()
            self._set_dirty()
        
    def _create_tag_label(self, tag_name: str) -> None:
        """
        Instantiates a new TagLabel and adds it to the flow layout.
        
        :param tag_name: The tag string for the label.
        :type tag_name: str

        :rtype: None
        """
        tag_label = TagLabel(tag_name)
        # Connect the custom signal for removal
        tag_label.tag_removed.connect(self._remove_tag)
        self.tag_flow_layout.addWidget(tag_label)

    def _remove_tag(self, tag_name: str) -> None:
        """
        Removes a tag from the set and its corresponding widget from the layout.
        
        This method is connected to the TagLabel's tag_removed signal.
        
        :param tag_name: The name of the tag to remove.
        :type tag_name: str
        :rtype: :py:obj:`None`
        """
        if tag_name in self.tags:
            self.tags.remove(tag_name)
            
            # Find the widget and remove it from the layout
            for i in range(self.tag_flow_layout.count()):
                item = self.tag_flow_layout.itemAt(i)
                widget = item.widget()
                if isinstance(widget, TagLabel) and widget.tag_name == tag_name:
                    self.tag_flow_layout.takeAt(i) # Remove from layout
                    widget.deleteLater()          # Delete the widget
                    break
            
            self.tags_changed.emit(self.get_tags())

    def get_tags(self) -> list[str]:
        """
        Returns the current list of tags.
        
        :return: A list of unique tags, sorted alphabetically.
        :rtype: list[str]
        """
        # Convert the set back to a list for a stable, user-friendly order
        return sorted(list(self.tags))

    def set_tags(self, tag_names: list[str]) -> None:
        """
        Sets the tags to a new list, clearing any existing tags. 
        
        :param tag_names: The list of tag strings to set.
        :type tag_names: list[str]

        :rtype: None
        """
        # This prevents the initial loading process from firing the tags_changed signal.
        self.blockSignals(True) 

        # Clear existing tags and widgets
        while self.tag_flow_layout.count():
            item = self.tag_flow_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        self.tags.clear()
        
        # Add new tags
        for tag_name in tag_names:
            clean_tag = tag_name.strip().lower()
            
            # Check to make sure we're not adding empty tags
            if clean_tag == "": continue 

            if clean_tag and clean_tag not in self.tags:
                self.tags.add(clean_tag)
                self._create_tag_label(clean_tag)
        
        # Restore signals and explicitly mark clean ---
        self.blockSignals(False) 
        self.mark_saved()