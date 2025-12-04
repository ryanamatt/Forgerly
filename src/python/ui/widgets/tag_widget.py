# src/python/ui/tag_widget.py

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, 
    QPushButton, QLabel, QSizePolicy, QLayout, 
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QRect, QPoint

class QFlowLayout(QLayout):
    """
    A layout that arranges items in a flow, wrapping to the next line
    when the row is full. This is essential for a dynamic tag list
    """
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)

        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)

        self.item_list = []
    
    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.item_list.append(item)

    def count(self):
        return len(self.item_list)

    def itemAt(self, index):
        if 0 <= index < len(self.item_list):
            return self.item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.item_list):
            return self.item_list.pop(index)
        return None
    
    def expandingDirections(self):
        return Qt.Orientation.Horizontal | Qt.Orientation.Vertical

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.item_list:
            size = size.expandedTo(item.minimumSize())
        
        # Add margins and spacing
        margin = self.contentsMargins()
        size += QSize(margin.left() + margin.right(), margin.top() + margin.bottom())
        return size
    
    def _do_layout(self, rect: QRect, test_only):
        """Performs the actual layout calculation."""
        x = rect.x()
        y = rect.y()
        line_height = 0
        
        spacing = self.spacing()

        for item in self.item_list:
            next_x = x + item.sizeHint().width() + spacing
            
            if next_x - spacing > rect.right() and line_height > 0:
                # Move to next line
                x = rect.x()
                y = y + line_height + spacing
                next_x = x + item.sizeHint().width() + spacing
                line_height = 0
            
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        # Returns the height used by the layout
        return y + line_height - rect.y() if line_height > 0 else 0
    
class TagLabel(QWidget):
    """A small, removable pill-style widget for displaying a single tag."""
    
    # Signal emitted when the remove button is clicked, carrying the tag name
    tag_removed = pyqtSignal(str)

    def __init__(self, tag_name: str, parent=None):
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
    A complete widget for managing a list of tags. 
    Allows input via QLineEdit and displays tags using QFlowLayout.
    """
    # Signal emitted when the list of tags has been modified
    tags_changed = pyqtSignal(list)

    def __init__(self, initial_tags: list[str] = None, parent=None):
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
        """Checks if the tags have unsaved changes"""
        return self._is_dirty
    
    def mark_saved(self) -> None:
        """Marks the tags as clean."""
        self._is_dirty = False
        
    def _set_dirty(self) -> None:
        """Sets the dirty flag and emits change signal if state changes."""
        if not self._is_dirty:
            self._is_dirty = True
            # The signal is emitted here, which will be handled by MainWindow
            self.tags_changed.emit(self.get_tags())

    def _add_tag_from_input(self):
        """
        Processes the input line, splitting by comma or semicolon, 
        and adds valid tags.
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
        
    def _create_tag_label(self, tag_name: str):
        """Instantiates a new TagLabel and adds it to the flow layout."""
        tag_label = TagLabel(tag_name)
        # Connect the custom signal for removal
        tag_label.tag_removed.connect(self._remove_tag)
        self.tag_flow_layout.addWidget(tag_label)

    def _remove_tag(self, tag_name: str):
        """Removes a tag from the set and its corresponding widget from the layout."""
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
        """Returns the current list of tags, sorted alphabetically."""
        # Convert the set back to a list for a stable, user-friendly order
        return sorted(list(self.tags))

    def set_tags(self, tag_names: list[str]) -> None:
        """
        Sets the tags to a new list. 
        Used when loading a new chapter/lore_entry.
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
