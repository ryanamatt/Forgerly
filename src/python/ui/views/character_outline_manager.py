# src/python/ui/views/character_outline_manager.py

from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QMenu, QInputDialog, QMessageBox, QFrame,
    QVBoxLayout, QLineEdit, QWidget, QLabel, QTreeWidgetItemIterator
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QIcon

from ...resources_rc import *
from ...repository.character_repository import CharacterRepository

class CharacterOutlineManager(QWidget):
    """
    A custom widget for managing the outline and hierarchy of Characters.
    
    It combines a search bar (:py:class:`~PyQt6.QtWidgets.QLineEdit`) and a 
    tree structure (:py:class:`~PyQt6.QtWidgets.QTreeWidget`) for navigation.
    It interacts with the data layer via a :py:class:`.CharacterRepository`.
    """

    CHARACTER_ID_ROLE = Qt.ItemDataRole.UserRole + 1
    """The :py:obj:`int` role used to store the database ID of a Character on an item."""

    char_selected = pyqtSignal(int)
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (int): Emitted when a character item is 
    selected, carrying the Character ID.
    """

    new_char_created = pyqtSignal()
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal`: Emmited when a new character is created
    telling MainWindow to switch the view.
    """

    pre_char_change = pyqtSignal()
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (): Emitted before a new character is 
    selected, allowing the main window to save the current character state.
    """

    def __init__(self, project_title: str = "Narrative Forge Project", 
                 character_repository: CharacterRepository | None = None) -> None:
        """
        Initializes the :py:class:`.CharacterOutlineManager`.
        
        :param project_title: The Title of the Current Project.
        :type project_title: str
        :param character_repository: The repository object for character CRUD operations.
        :type character_repository: :py:class:`.CharacterRepository` or None, optional

        :rtype: None
        """
        super().__init__()

        self.project_title = project_title
        self.char_repo = character_repository

        # --- Setup main Layout ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create Header Label
        self.header_label = QLabel(f"{self.project_title} Characters")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.header_label.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 1)
        self.header_label.setFont(font)
        self.header_label.setStyleSheet("""
            QLabel {
                padding: 5px
                }
        """            
        )

        # Create the Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Search Characters by Name, Tags...')
        self.search_input.textChanged.connect(self._handle_search_input)

        # The actual tree widget is a child
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setIndentation(0)
        self.tree_widget.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Configuration and Signals ---
        self.tree_widget.customContextMenuRequested.connect(self._show_context_menu)
        self.tree_widget.itemSelectionChanged.connect(self._handle_selection_change)
        self.tree_widget.itemChanged.connect(self._handle_item_renamed)

        container_frame = QFrame(self)
        container_frame.setObjectName("MainBorderFrame")

        # Create a layout FOR the frame and add the widgets to it
        frame_layout = QVBoxLayout(container_frame)
        frame_layout.addWidget(self.header_label)
        frame_layout.addWidget(self.search_input)
        frame_layout.addWidget(self.tree_widget)

        main_layout.addWidget(container_frame)

        self.load_outline()

    def load_outline(self, characters: list[dict] | None = None) -> None:
        """
        Fetches all characters from the database and populates the 
        :py:class:`~PyQt6.QtWidgets.QTreeWidget`.
        
        It attempts to restore the selection if a character was previously selected.
        
        :rtype: None
        """
        if not self.char_repo:
            return
        
        if characters is None:
            characters = self.char_repo.get_all_characters()

        self.tree_widget.clear()

        if characters:
            for character in characters:
                name = character.get("Name", "Unnamed")

                item = QTreeWidgetItem([name])
                item.setData(0, self.CHARACTER_ID_ROLE, character["ID"])
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                item.setIcon(0, QIcon(":icons/character.svg"))

                self.tree_widget.addTopLevelItem(item)

        self.tree_widget.expandAll()

    def _handle_search_input(self, query: str) -> None:
        """
        Filters the visible items in the outline based on the text entered in 
        the search bar.
        
        The search is case-insensitive.
        
        :param text: The current text in the search input field.
        :type text: :py:class:`str`

        :rtype: None
        """
        clean_query = query.strip()

        if clean_query and self.char_repo:
            search_results = self.char_repo.search_characters(clean_query)
            if search_results:
                self.load_outline(search_results)
            else:
                self.tree_widget.clear()
                no_result_item = QTreeWidgetItem(self.tree_widget, ["No search results found."])
                no_result_item.setData(0, self.CHARACTER_ID_ROLE, -1)
                self.tree_widget.expandAll()

        # Search is cleared, revert to full outline
        elif not clean_query:
            self.load_outline()

    def _handle_selection_change(self) -> None:
        """
        Handles selection changes in the :py:class:`~PyQt6.QtWidgets.QTreeWidget`.
        
        This method is connected to the :py:class:`~PyQt6.QtCore.QItemSelectionModel.currentChanged`
        signal to ensure only valid character items trigger the selection logic.
        
        :rtype: None
        """
        current_item = self.tree_widget.currentItem()
        if current_item:
            char_id = current_item.data(0, self.CHARACTER_ID_ROLE)
            # Only emit if a valid character (not the root or a 'no result' message) is selected
            if isinstance(char_id, int) and char_id > 0:
                self.char_selected.emit(char_id)

    def _handle_item_click(self, item: QTreeWidgetItem, column: int) -> None:
        """
        Handles the click event on a tree item.
        
        If a character item is clicked, it emits :py:attr:`.pre_char_change` 
        followed by :py:attr:`.char_selected`.

        :param item: The clicked tree item.
        :type item: :py:class:`~PyQt6.QtWidgets.QTreeWidgetItem`
        :param column: The column index clicked.
        :type column: int

        :rtype: None
        """
        char_id = item.data(0, self.CHARACTER_ID_ROLE)
        if char_id is not None:
            self.pre_char_change.emit()
            self.char_selected.emit(char_id)

    def _handle_item_double_click(self, item: QTreeWidgetItem, column: int) -> None:
        """
        Handles double click on a character item to initiate the rename process.
        
        The editor is only activated if the item is a valid character item (not the root).
        
        :param item: The double-clicked tree item.
        :type item: :py:class:`~PyQt6.QtWidgets.QTreeWidgetItem`
        :param column: The column index.
        :type column: :py:obj:`int`

        :rtype: None
        """
        if item.data(0, self.CHARACTER_ID_ROLE) is not None:
            self.editItem(item, 0)

    def _handle_item_renamed(self, item: QTreeWidgetItem, column: int) -> None:
        """
        Handles the signal emitted when a tree item has been successfully renamed.
        
        The new name is saved to the database via the :py:class:`.CharacterRepository`.
        
        :param item: The renamed tree item.
        :type item: :py:class:`~PyQt6.QtWidgets.QTreeWidgetItem`
        :param column: The column index.
        :type column: int

        :rtype: None
        """
        char_id = item.data(0, self.CHARACTER_ID_ROLE)
        new_name = item.text(0).strip()
        
        if not self.char_repo:
            QMessageBox.critical(self, "Internal Error", "CharacterRepository is missing.")
            return

        # Prevent actions if this is the root item or if the title is empty
        if char_id is None or not new_name:
            if not new_name:
                # If the title was cleared, revert the name (requires re-loading or smarter logic)
                QMessageBox.warning(self, "Invalid Name", "Character name cannot be empty. Reverting.")
                self.load_outline() 
            return

        # Check if the title actually changed
        current_db_title = self.char_repo.get_character_name(char_id) 
        if current_db_title and current_db_title == new_name:
            return

        # Update the database
        success = self.char_repo.update_character(char_id, new_name)
        
        if not success:
            QMessageBox.critical(self, "Database Error", "Failed to update character name in the database.")
            # Revert the item name visually if the DB update failed
            self.load_outline()

    def _show_context_menu(self, pos: QPoint) -> None:
        """
        Displays the context menu when right-clicked, offering options 
        like 'Add New Character' and 'Delete Character'.
        
        :param pos: The position of the right-click relative to the widget.
        :type pos: :py:class:`~PyQt6.QtCore.QPoint`

        :rtype: None
        """
        item = self.tree_widget.itemAt(pos)

        menu = QMenu(self)

        # New Character Action
        new_action = menu.addAction("Add New Character...")
        new_action.triggered.connect(self.prompt_and_add_character)

        if item:
            is_character = item.data(0, self.CHARACTER_ID_ROLE) is not None

            if is_character:
                rename_action = menu.addAction("Rename Character")
                delete_action = menu.addAction("Delete Character")
                
                rename_action.triggered.connect(lambda: self.editItem(item, 0))
                # Wrap the delete action to ensure save check occurs
                delete_action.triggered.connect(lambda: self.check_save_and_delete(item))

        # Show the menu
        if menu.actions():
            menu.exec(self.mapToGlobal(pos))
        
    def prompt_and_add_character(self) -> None:
        """
        Prompts the user for a new character name, creates the character in the 
        database, reloads the outline, and selects the new character.
        
        Emits :py:attr:`.pre_char_change` before prompting.
        
        :rtype: None
        """
        
        if not self.char_repo:
            QMessageBox.critical(self, "Internal Error", "ChapterRepository is missing.")
            return

        # Check save status before creating a new chapter (which implicitly changes selection)
        self.pre_char_change.emit() 
        
        name, ok = QInputDialog.getText(
            self, 
            "New Character", 
            "Enter the name for the new character:",
            text="New Character"
        )

        if ok and name:
            # Precursor_Chapter_ID is None for top-level chapters
            new_id = self.char_repo.create_character(name=name)

            if new_id:
                self.new_char_created.emit()
                # Reload the outline to display the new chapter
                self.load_outline()
                # Automatically select the new chapter
                new_item = self.find_character_item_by_id(new_id)
                if new_item:
                     self.tree_widget.setCurrentItem(new_item)
                     self._handle_item_click(new_item, 0) 
            else:
                QMessageBox.warning(self, "Database Error", "Failed to save the new character to the database.")

    def _delete_chapter(self, item: QTreeWidgetItem) -> None:
        """
        Handles confirmation and deletion of a character item and its corresponding 
        entry in the database.
        
        :param item: The character item to be deleted.
        :type item: :py:class:`~PyQt6.QtWidgets.QTreeWidgetItem`

        :rtype: None
        """
        chapter_id = item.data(0, self.CHARACTER_ID_ROLE)
        title = item.text(0)
        
        if chapter_id is None:
            return
            
        if not self.char_repo:
            QMessageBox.critical(self, "Internal Error", "ChapterRepository is missing.")
            return
            
        # Confirmation Dialog
        reply = QMessageBox.question(
            self, 
            "Confirm Deletion",
            f"Are you sure you want to permanently delete the chapter:\n'{title}'?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.char_repo.delete_character(chapter_id):
                self.load_outline()
            else:
                QMessageBox.critical(self, "Deletion Error", "A database error occurred while trying to delete the chapter.")

    def check_save_and_delete(self, item: QTreeWidgetItem) -> None:
        """
        Emits :py:attr:`.pre_char_change` to ensure the currently viewed 
        character is saved, then triggers the deletion process.

        :param item: The character item queued for deletion.
        :type item: :py:class:`~PyQt6.QtWidgets.QTreeWidgetItem`

        :rtype: None
        """
        self.pre_char_change.emit()
        self._delete_chapter(item)

    def find_character_item_by_id(self, char_id: int) -> QTreeWidgetItem | None:
        """
        Helper to find a character :py:class:`~PyQt6.QtWidgets.QTreeWidgetItem` 
        by its stored database ID.
        
        :param char_id: The unique ID of the character to find.
        :type char_id: int

        :returns: The matching item or None
        :rtype: :py:class:`~PyQt6.QtWidgets.QTreeWidgetItem` or None
        """
        iterator = QTreeWidgetItemIterator(self.tree_widget)
        while iterator.value():
            item = iterator.value()
            if item.data(0, self.CHARACTER_ID_ROLE) == char_id:
                return item
            iterator += 1
        return None