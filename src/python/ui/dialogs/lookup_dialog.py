# src/python/ui/dialogs/lookup_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QPushButton, QScrollArea, QWidget, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QPalette, QFont

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
    """
    
    def __init__(self, entity_type: EntityType, title: str, content: str, parent=None) -> None:
        """
        Initializes the Lookup Window with enhanced display features.
        
        :param entity_type: The Entity type (CHARACTER or LORE).
        :type entity_type: EntityType
        :param title: The Title/Name of the Entity.
        :type title: str
        :param content: The main content/description.
        :type content: str
        :param parent: The parent widget.
        :rtype: None
        """
        super().__init__(parent)

        self.entity_type = entity_type
        self.title = title
        self.content = content

        # Window configuration
        self.setWindowTitle(f"Quick Reference: {title}")
        self.setMinimumSize(450, 350)
        self.setMaximumSize(600, 700)
        self.resize(500, 500)
        
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
        
        # Header Section
        self._create_header(main_layout)
        
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)
        
        # Content Section
        self._create_content_section(main_layout)
        
        # Footer with quick actions
        self._create_footer(main_layout)
        
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
        else:
            super().keyPressEvent(event)