# src/python/ui/BaseContentEditor

from abc import ABC, abstractmethod
from typing import Any, List
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PyQt6.QtCore import Qt

from ui.widgets.tag_widget import TagManagerWidget
from ui.widgets.rich_text_editor import RichTextEditor

class BaseContentEditor(QWidget, ABC):
	"""
	Base Class for editors that combine RichTextEditor and a TagManagerWidget,
	handling layout, state management, and common passthrough methods.
	"""
	def __init__(self, tag_group_title: str, parent=None) -> None:
		super().__init__(parent)

		# --- Shared sub-componenets ---
		self.rich_text_editor = RichTextEditor()
		self.tag_manager = TagManagerWidget()

		# --- Common Layout Setup ---
		main_layout = QVBoxLayout(self)
		main_layout.setContentsMargins(10, 10, 10, 10)
		main_layout.setSpacing(10)

		# The abstract method creates and returns the widget containing all 
		# specific metadata fields (like title/category/tags).
		metadata_widget = self._create_specific_metadata_widget(tag_group_title)

		# Create a vertical QSplitter for Metadata and Content
		content_splitter = QSplitter(Qt.Orientation.Vertical)

		# 1. Add the metadata/tagging area (created by subclass)
		content_splitter.addWidget(metadata_widget)

		# 2. Add the main content editor
		content_splitter.addWidget(self.rich_text_editor)

		# Set the initial ratio of the splitter (e.g., 3:7 ratio)
		content_splitter.setSizes([300, 700]) 

		main_layout.addWidget(content_splitter)

		# --- Common Connections ---
		# Any change in the tags or content makes the whole editor dirty
		self.rich_text_editor.content_changed.connect(self._set_dirty)
		self.tag_manager.tags_changed.connect(self._set_dirty)

	# --- Abstract Methods ---

	@abstractmethod
	def _create_specific_metadata_widget(self, tag_group_title: str) -> QWidget:
		"""
		This method must be implemented by subclasses to define their unique
		metadata arrangement (e.g., Title/Category for Lore, or a simple Tag Box
		for Chapter) and return the overall QWidget for the top section of the splitter.
		"""
		pass

	# --- Regular Methods ---

	def _set_dirty(self) -> None:
		pass