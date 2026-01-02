# src/python/ui/dialogs/project_stats_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QLabel, 
    QDialogButtonBox, QHBoxLayout, QGridLayout
)
from typing import TYPE_CHECKING

from ...utils.logger import get_logger

if TYPE_CHECKING:
    from services.app_coordinator import AppCoordinator
logger = get_logger(__name__)

class ProjectStatsDialog(QDialog):
    """
    A modal dialog window used to display project-wide statistics, such as 
    total word count, character count, and estimated read time.
    """
    def __init__(self, project_stats: dict, user_settings: dict, parent=None) -> None:
        """
        Initializes the :py:class:`.ProjectStatsDialog`.

        :param wpm: Words Per Minute setting, used for read time calculation.
        :type wpm: int
        :param parent: The parent Qt widget.
        :type parent: :py:class:`~PySide6.QtWidgets.QWidget` or None
        
        :rtype: None
        """
        super().__init__(parent)
        self.project_stats = project_stats
        self.wpm = user_settings['words_per_minute']
        
        self.setWindowTitle("Project Statistics")
        self.setGeometry(200, 200, 500, 300) 

        self._stats = project_stats

        self._setup_ui()

    def _setup_ui(self) -> None:
        """
        Constructs and lays out all the user interface components.
        
        :rtype: None
        """
        main_layout = QVBoxLayout(self)

        # --- Content Group Box ---
        content_group = QGroupBox("Content Statistics")
        content_layout = QGridLayout(content_group)

        # Row 1: Word Count
        content_layout.addWidget(QLabel("Total Words:"), 0, 0)
        content_layout.addWidget(QLabel(self._stats["total_word_count"]), 0, 1)

        # Row 2: Characters (No Spaces)
        content_layout.addWidget(QLabel("Characters (No Spaces):"), 1, 0)
        content_layout.addWidget(QLabel(self._stats["char_count_no_spaces"]), 1, 1)
        
        # Row 3: Estimated Read Time
        content_layout.addWidget(QLabel("Estimated Read Time:"), 3, 0)
        content_layout.addWidget(QLabel(f"{self._stats['read_time']} (at {self.wpm} WPM)"), 3, 1)
        
        content_layout.setColumnStretch(1, 1) # Makes the value column fill available space

        main_layout.addWidget(content_group)

        # --- Entity Group Box ---
        entity_group = QGroupBox("Project Entities")
        entity_layout = QGridLayout(entity_group)

        # Row 1: Chapters
        entity_layout.addWidget(QLabel("Total Chapters:"), 0, 0)
        entity_layout.addWidget(QLabel(self._stats["chapter_count"]), 0, 1)

        # Row 2: Lore
        entity_layout.addWidget(QLabel("Total Lore Entries:"), 1, 0)
        entity_layout.addWidget(QLabel(self._stats["lore_count"]), 1, 1)
        
        # Row 3: Characters
        entity_layout.addWidget(QLabel("Total Characters:"), 2, 0)
        entity_layout.addWidget(QLabel(self._stats["character_count"]), 2, 1)
        
        entity_layout.setColumnStretch(1, 1)

        main_layout.addWidget(entity_group)
        main_layout.addStretch()

        # --- Standard Close Button ---
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )
        # Use reject() which is for a simple Close button
        button_box.rejected.connect(self.reject) 
        
        h_layout = QHBoxLayout()
        h_layout.addStretch(1)
        h_layout.addWidget(button_box)
        
        main_layout.addLayout(h_layout)
