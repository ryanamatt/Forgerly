# src/python/ui/tag_widget.py

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QMessageBox, 
    QPushButton, QLabel, QSizePolicy, QLayoutItem
)
from PySide6.QtCore import QSize, Signal

from .flow_layout import QFlowLayout
from ...utils.logger import get_logger #

logger = get_logger(__name__)
    
class TagLabel(QWidget):
    """
    A small, removable pill-style widget for displaying a single tag.
    
    This widget consists of a :py:class:`~PySide6.QtWidgets.QLabel` for the tag name 
    and a :py:class:`~PySide6.QtWidgets.QPushButton` for removal.
    It emits a signal when the remove button is clicked.
    """
    
    tag_removed = Signal(str)
    """
    :py:class:`~PySide6.QtCore.Signal` (str): Emitted when the tag is removed carrying the tag's name.
    """

    def __init__(self, tag_name: str, parent=None) -> None:
        """
        Initializes the TagLabel.
        
        :param tag_name: The text content of the tag.
        :type tag_name: :py:class:`str`
        :param parent: The parent widget. Defaults to ``None``.
        :type parent: :py:class:`~PySide6.QtWidgets.QWidget`, optional

        :rtype: None
        """
        super().__init__(parent)
        self.tag_name = tag_name

        logger.debug(f"TagLabel initialized for tag: '{tag_name}'")
        
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
    A complete :py:class:`~PySide6.QtWidgets.QWidget` for managing a list of tags. 
    
    It provides a :py:class:`~PySide6.QtWidgets.QLineEdit` for input and displays 
    the current tags using a :py:class:`.QFlowLayout`, allowing them to wrap dynamically. 
    Tags are stored as a unique set (case-insensitive, converted to lowercase).
    """

    tags_changed = Signal(list)
    """
    :py:class:`~PySide6.QtCore.Signal`: Emitted when the list of tags has been modified.
    """

    def __init__(self, initial_tags: list[str] = None, parent=None) -> None:
        """
        Initializes the TagManagerWidget.
        
        :param initial_tags: A list of tag strings to initialize the widget with.
        :type initial_tags: :py:obj:`list[str]`, optional
        :param parent: The parent widget. Defaults to ``None``.
        :type parent: :py:class:`~PySide6.QtWidgets.QWidget`, optional

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

        logger.debug("TagManagerWidget initialized.")

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
        try:
            if self._is_dirty:
                self._is_dirty = False
                logger.info("TagWidget state set to clean (saved).")
            else:
                logger.debug("TagWidget state already clean, 'mark_saved' skipped.")
                
        except Exception as e:
            logger.error(f"Error occurred during mark_saved operation: {e}", exc_info=True)
        
    def _set_dirty(self) -> None:
        """
        Sets the dirty flag to True and emits the tags_changed signal if 
        the state transitioned from clean to dirty.

        :rtype: None
        """
        try:
            if not self._is_dirty:
                self._is_dirty = True
                
                self.tags_changed.emit(self.get_tags())
                logger.info("TagWidget state transitioned from clean to dirty. Signal emitted.")
            else:

                logger.debug("TagWidget state already dirty, no signal emitted.")
        
        except Exception as e:
            logger.error(f"Error occurred during _set_dirty operation: {e}", exc_info=True)

    def _add_tag_from_input(self) -> None:
        """
        Processes the text in the input line. 
        
        It splits by comma or semicolon and adds all valid, unique, non-empty tags. 
        The input line is cleared after processing.

        :rtype: None
        """
        input_text = self.tag_input.text().strip()
    
        logger.debug(f"Attempting to process tag input: '{input_text}'")

        if not input_text:
            logger.debug("Input is empty after stripping, skipping tag addition.")
            return

        # Split input by commas or semicolons
        raw_tags = input_text.replace(';', ',').split(',')
        
        new_tags_added = False
        
        try:
            for tag in raw_tags:
                clean_tag = tag.strip().lower()
                
                if not clean_tag:
                    logger.debug("Skipping empty tag from split result.")
                    continue

                if clean_tag in self.tags:
                    logger.debug(f"Tag '{clean_tag}' already exists, skipping.")
                    continue

                # Add tag and create UI element
                self.tags.add(clean_tag)
                # Assuming this private method creates the TagLabel and adds it to the layout.
                self._create_tag_label(clean_tag) 
                new_tags_added = True
                logger.info(f"Added new tag: '{clean_tag}'.")

        except Exception as e:
            logger.error(
                f"Error processing tag input '{input_text}'. Tag processing may be incomplete.", 
                exc_info=True
            )
            # Display a user-friendly error message
            QMessageBox.critical(
                self,
                "Tag Input Error",
                "An error occurred while trying to process the tags you entered. Please try again."
            )

        # Final actions after processing the input list
        self.tag_input.clear()
        logger.debug("Input line cleared.")
        
        if new_tags_added:
            self.tags_changed.emit(self.get_tags())
            # Assuming _set_dirty is intended to be called once upon successful addition
            self._set_dirty() 
            logger.info(f"Tags changed signal emitted. Total tags: {len(self.tags)}")
        else:
            logger.debug("No new unique tags were added.")
        
    def _create_tag_label(self, tag_name: str) -> None:
        """
        Instantiates a new TagLabel and adds it to the flow layout.
        
        :param tag_name: The tag string for the label.
        :type tag_name: str

        :rtype: None
        """
        logger.debug(f"Attempting to create TagLabel for: '{tag_name}'")
        try:
            tag_label = TagLabel(tag_name)
            
            tag_label.tag_removed.connect(self._remove_tag)
            
            self.tag_flow_layout.addWidget(tag_label)
            
            logger.info(f"Successfully created and added TagLabel for: '{tag_name}'.")
            
        except Exception as e:
            # Log the specific failure for this UI operation
            logger.error(
                f"Failed to create, connect, or add TagLabel for '{tag_name}'.", 
                exc_info=True
            )
            # Re-raise the exception to allow the calling method to handle the failure 
            # (e.g., rolling back the addition to self.tags).
            raise

    def _remove_tag(self, tag_name: str) -> None:
        """
        Removes a tag from the set and its corresponding widget from the layout.
        
        This method is connected to the TagLabel's tag_removed signal.
        
        :param tag_name: The name of the tag to remove.
        :type tag_name: str
        :rtype: :py:obj:`None`
        """
        logger.debug(f"Received signal to remove tag: '{tag_name}'")
        
        try:
            # 1. Remove from internal set
            if tag_name in self.tags:
                self.tags.remove(tag_name)
            else:
                logger.warning(f"Attempted to remove non-existent tag: '{tag_name}'. Ignoring "
                               "removal from set.")
            
            # 2. Remove the widget from the layout
            i = 0
            while i < self.tag_flow_layout.count():
                item: QLayoutItem | None = self.tag_flow_layout.itemAt(i)
                if item:
                    widget = item.widget()
                    if isinstance(widget, TagLabel) and widget.tag_name == tag_name:
                        # Remove the item from the layout and delete the widget
                        self.tag_flow_layout.takeAt(i)
                        widget.deleteLater() 
                        logger.debug(f"Removed widget for tag: '{tag_name}' at index {i}")
                        
                        # Notify of change and exit the loop
                        self.tags_changed.emit(self.get_tags())
                        logger.info(f"Tag '{tag_name}' successfully removed. Total tags: {len(self.tags)}")
                        return 
                i += 1
            
            logger.warning(f"Could not find widget for tag '{tag_name}' in the layout.")
            
        except Exception as e:
            logger.error(f"Error processing tag removal for '{tag_name}': {e}", exc_info=True)

    def get_tags(self) -> list[str]:
        """
        Returns the current list of tags.
        
        :return: A list of unique tags, sorted alphabetically.
        :rtype: list[str]
        """
        sorted_tags = sorted(list(self.tags))
        logger.debug(f"Returning {len(sorted_tags)} tags.")
        return sorted(sorted_tags)

    def set_tags(self, tag_names: list[str]) -> None:
        """
        Sets the tags to a new list, clearing any existing tags. 
        
        :param tag_names: The list of tag strings to set.
        :type tag_names: list[str]

        :rtype: None
        """
        logger.debug(f"Setting tags from list of size: {len(tag_names)}")
        
        # This prevents the change process from firing the tags_changed signal repeatedly.
        self.blockSignals(True) 
        
        try:
            # Clear existing tags and widgets
            while self.tag_flow_layout.count():
                item = self.tag_flow_layout.takeAt(0)
                if item:
                    widget = item.widget()
                    if widget:
                        widget.deleteLater() 
                
            self.tags.clear()
            logger.debug("Cleared existing tags and widgets.")
            
            # Add new tags
            for tag_entry in tag_names:
                if isinstance(tag_entry, (tuple, list)) and len(tag_entry) >= 2:
                    tag_name_str = str(tag_entry[1]) 
                elif isinstance(tag_entry, dict) and 'Name' in tag_entry:
                    tag_name_str = str(tag_entry['Name'])             
                elif isinstance(tag_entry, str):
                    tag_name_str = tag_entry
                else:
                    logger.warning(f"Skipping tag with unexpected format: {tag_entry}")
                    continue

                clean_tag = tag_name_str.strip().lower()
                
                if clean_tag not in self.tags:
                    self.tags.add(clean_tag)
                    
                    tag_label_widget = TagLabel(clean_tag)
                    tag_label_widget.tag_removed.connect(self._remove_tag)
                    self.tag_flow_layout.addWidget(tag_label_widget)
                    
            logger.info(f"Successfully set tags. Total tags: {len(self.tags)}")
                                
        except Exception as e:
            logger.error(f"Critical error during set_tags operation: {e}", exc_info=True)
            # Application flow should continue, but state might be visually incorrect.
        
        finally:
            self.blockSignals(False) # Re-enable signals
            
            # Emit signal once after all tags are set
            self.tags_changed.emit(self.get_tags())
