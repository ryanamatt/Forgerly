# src/python/ui/dialogs/lookup_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QPushButton, QFrame, QListWidget, QListWidgetItem, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ...utils.constants import EntityType

class LookupDialog(QDialog):
    """
    A sleek, floating HUD for quick reference of lore and characters 
    without interrupting the writing flow.
    
    Features:
    - Clean, readable layout with sectioned information
    - Entity-specific formatting (Character vs Lore)
    - Compact but informative display
    - Always-on-top window for easy reference
    - Multiple entity selection when needed
    """
    
    def __init__(self, lookup_data: dict[str, dict[str, str]], parent=None) -> None:
        """
        Initializes the Lookup Window with enhanced display features.
        
        :param lookup_data: The data needed to lookup containing {'char_data': list, 'lore_data': list}
        :type lookup_data: dict
        :param parent: The parent widget.
        :type parent: QWidget
        :rtype: None
        """
        super().__init__(parent)

        self.char_data = lookup_data.get('char_data', [])
        self.lore_data = lookup_data.get('lore_data', [])
        
        # Combine all entities for selection
        self.all_entities = []
        for char in self.char_data:
            self.all_entities.append({
                'type': EntityType.CHARACTER,
                'title': char.get('Name', 'Unnamed Character'),
                'content': char.get('Description', ''),
                'data': char
            })
        for lore in self.lore_data:
            self.all_entities.append({
                'type': EntityType.LORE,
                'title': lore.get('Title', 'Untitled Lore'),
                'content': lore.get('Content', ''),
                'data': lore
            })
        
        # Current selection
        self.current_entity = None
        self.show_selection = len(self.all_entities) > 1
        
        # Set initial entity if only one exists
        if len(self.all_entities) == 1:
            self.current_entity = self.all_entities[0]
            self.entity_type = self.current_entity['type']
            self.title = self.current_entity['title']
            self.content = self.current_entity['content']

        # Window configuration
        self.setWindowTitle(f"Quick Reference Search Results")
        self.setMinimumSize(450, 350)
        self.setBaseSize(500, 500)
        
        # Keep on top but allow clicking through to parent if needed
        self.setWindowFlags(
            Qt.WindowType.Window | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        """
        Sets up the user interface with sectioned, readable content.
        
        :rtype: None
        """
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        
        # Selection list (only shown when multiple entities exist)
        if self.show_selection:
            self._create_selection_section(main_layout)
        else:
            self._rebuild_ui()
    
    def _create_selection_section(self, layout: QVBoxLayout) -> None:
        """
        Creates the selection interface for multiple entities.
        
        :param layout: The main layout to add widgets to.
        :type layout: QVBoxLayout
        :rtype: None
        """
        # Selection header
        selection_header = QLabel("Multiple Results Found - Select One:")
        selection_header.setStyleSheet("font-weight: bold; font-size: 12pt; color: #888;")
        layout.addWidget(selection_header)
        
        # Entity list
        self.entity_list = QListWidget()
        for entity in self.all_entities:
            item = QListWidgetItem()
            
            # Create display text with entity type badge
            if entity['type'] == EntityType.CHARACTER:
                badge = "👤"
                type_text = "Character"
            else:
                badge = "📚"
                type_text = "Lore"
            
            item.setText(f"{badge} {entity['title']} ({type_text})")
            item.setData(Qt.ItemDataRole.UserRole, entity)
            self.entity_list.addItem(item)
        
        # Connect selection
        self.entity_list.itemDoubleClicked.connect(self._confirm_selection)
        
        layout.addWidget(self.entity_list, stretch=1)
        
        # Selection buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        select_btn = QPushButton("View Selected")
        select_btn.setFixedWidth(120)
        select_btn.clicked.connect(self._confirm_selection)
        select_btn.setDefault(True)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(80)
        cancel_btn.clicked.connect(self.close)
        
        button_layout.addStretch()
        button_layout.addWidget(select_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _confirm_selection(self) -> None:
        """
        Confirm the selected entity and switch to detail view.
        
        :rtype: None
        """
        current_item = self.entity_list.currentItem()
        if not current_item:
            return
        
        # Get the selected entity
        self.current_entity = current_item.data(Qt.ItemDataRole.UserRole)
        self.entity_type = self.current_entity['type']
        self.title = self.current_entity['title']
        self.content = self.current_entity['content']
        
        # Clear and rebuild the UI with detail view
        self.show_selection = False
        self._rebuild_ui()
    
    def _rebuild_ui(self) -> None:
        """
        Rebuilds the UI to show the detail view.
        
        :rtype: None
        """
        layout = self.layout()
        self._clear_layout(layout)
        
        # Rebuild with detail view
        self._create_header(layout)
        
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Content Section
        self._create_content_section(layout)
        
        # Footer with quick actions
        self._create_footer(layout)
    
    def _clear_layout(self, layout) -> None:
        """
        Recursively clears a layout.
        
        :param layout: The layout to clear.
        :type layout: QLayout
        :rtype: None
        """
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())
        
    def _create_header(self, layout: QVBoxLayout) -> None:
        """
        Creates the header section with entity type badge and title.
        
        :param layout: The main layout to add widgets to.
        :type layout: QVBoxLayout
        :rtype: None
        """
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        # Entity Type Badge
        type_badge = QLabel(self._get_entity_badge_text())
        type_badge.setStyleSheet(self._get_badge_style())
        type_badge.setAlignment(Qt.AlignmentFlag.AlignLeft)
        header_layout.addWidget(type_badge)
        
        # Title/Name
        title_label = QLabel(self.title)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setWordWrap(True)
        header_layout.addWidget(title_label)
        
        layout.addLayout(header_layout)
        
    def _create_content_section(self, layout: QVBoxLayout) -> None:
        """
        Creates the scrollable content area with formatted text.
        
        :param layout: The main layout to add widgets to.
        :type layout: QVBoxLayout
        :rtype: None
        """
        # Section label
        content_label = QLabel("Description:" if self.entity_type == EntityType.CHARACTER else "Content:")
        content_label.setStyleSheet("font-weight: bold; font-size: 11pt; color: #888;")
        layout.addWidget(content_label)
        
        # Content viewer
        self.content_viewer = QTextEdit()
        self.content_viewer.setReadOnly(True)
        self.content_viewer.setHtml(self._format_content())
        
        # Styling for better readability
        self.content_viewer.setStyleSheet("""
            QTextEdit {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
                background-color: palette(base);
                font-size: 10pt;
                line-height: 1.5;
            }
        """)
        
        layout.addWidget(self.content_viewer, stretch=1)
        
    def _create_footer(self, layout: QVBoxLayout) -> None:
        """
        Creates the footer with action buttons.
        
        :param layout: The main layout to add widgets to.
        :type layout: QVBoxLayout
        :rtype: None
        """
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(8)
        
        # Info label
        info_label = QLabel("💡 Tip: This window stays on top while you write")
        info_label.setStyleSheet("color: #888; font-size: 9pt; font-style: italic;")
        footer_layout.addWidget(info_label, stretch=1)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(80)
        close_btn.clicked.connect(self.close)
        close_btn.setDefault(True)
        footer_layout.addWidget(close_btn)
        
        layout.addLayout(footer_layout)
        
    def _get_entity_badge_text(self) -> str:
        """
        Returns the badge text based on entity type.
        
        :returns: Badge text to display.
        :rtype: str
        """
        if self.entity_type == EntityType.CHARACTER:
            return "👤 CHARACTER"
        elif self.entity_type == EntityType.LORE:
            return "📚 LORE ENTRY"
        else:
            return f"📄 {self.entity_type.name}"
            
    def _get_badge_style(self) -> str:
        """
        Returns CSS styling for the entity type badge.
        
        :returns: CSS style string.
        :rtype: str
        """
        if self.entity_type == EntityType.CHARACTER:
            bg_color = "#3B82F6"  # Blue
        elif self.entity_type == EntityType.LORE:
            bg_color = "#8B5CF6"  # Purple
        else:
            bg_color = "#6B7280"  # Gray
            
        return f"""
            QLabel {{
                background-color: {bg_color};
                color: white;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 9pt;
                font-weight: bold;
                letter-spacing: 0.5px;
            }}
        """
        
    def _format_content(self) -> str:
        """
        Formats the content HTML for better readability.
        
        :returns: Formatted HTML string.
        :rtype: str
        """
        # Add some basic formatting if the content is plain text
        if not self.content.strip().startswith('<'):
            # Convert plain text to HTML with proper line breaks
            formatted = self.content.replace('\n', '<br>')
            return f'<div style="line-height: 1.6;">{formatted}</div>'
        
        # If already HTML, ensure good line spacing
        if '<div' not in self.content and '<p' not in self.content:
            return f'<div style="line-height: 1.6;">{self.content}</div>'
            
        return self.content
    
    def keyPressEvent(self, event):
        """
        Handle keyboard shortcuts.
        
        :param event: The key event.
        :rtype: None
        """
        # Close on Escape
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        # Confirm selection on Enter/Return when in selection mode
        elif self.show_selection and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._confirm_selection()
        else:
            super().keyPressEvent(event)