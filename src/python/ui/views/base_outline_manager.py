# src/python/ui/views/base_outline_manager.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QFrame, 
    QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint

from ..widgets.nested_tree_widget import NestedTreeWidget
from ..widgets.reordering_tree_widget import ReorderingTreeWidget

class BaseOutlineManager(QWidget):
    """
    Base class for managing hierarchical outlines.
    Consolidates UI setup, search, and common tree interactions.
    """

    item_selected = pyqtSignal(int)
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (int): Emitted when an item is 
    selected, carrying the item ID.
    """

    new_item_created = pyqtSignal()
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal`: Emmited when a new item is created
    telling MainWindow to switch the view.
    """

    pre_item_change = pyqtSignal()
    """
    :py:class:`~PyQt6.QtCore.pyqtSignal` (): Emitted before a new item is 
    selected, allowing the main window to save the current item state.
    """

    def __init__(self, project_title: str, header_text: str, id_role: int,
                 search_placeholder: str = "Search...", is_nested_tree: bool = False,
                 parent = None) -> None:
        """
        Initializes the BaseOutlineManager
        
        :param project_title: The title of the project
        :type project_title: str
        :param header_text: The header text of the OutlineManager
        :type header_text: str
        :param id_role: The ID_Role of the current selected item.
        :type id_role: int
        :param search_place_holder: The place holder text for searching.
        :type search_place_holder: str
        :param is_nested_tree: True if self.tree_widget is nested (Utilizing NestedTreeWidget)
            False if not nested (Utilizing QTreeWidget). Default is False.
        :type is_nested_tree: bool
        :param parent: The parent object.
        :type parent: :py:class:`~PyQt6.QtWidgets.QWidget`

        :rtype: None
        """
        super().__init__(parent)

        self.project_title = project_title
        self.id_role = id_role

        # --- Layout Setup ---
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Container Frame for styling
        self.container_frame = QFrame(self)
        self.container_frame.setObjectName("MainBorderFrame")
        self.frame_layout = QVBoxLayout(self.container_frame)

        # Header Label
        self.header_label = QLabel(f"{project_title} {header_text}")
        self._setup_header_style()

        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(search_placeholder)
        self.search_input.textChanged.connect(self._handle_search_input)

        # Tree Widget
        if is_nested_tree:
            self.tree_widget = NestedTreeWidget(id_role=id_role, parent=self)
        else:
            self.tree_widget = ReorderingTreeWidget(parent=self)
        self._setup_tree_widget()

        # Build UI
        self.frame_layout.addWidget(self.header_label)
        self.frame_layout.addWidget(self.search_input)
        self.frame_layout.addWidget(self.tree_widget)
        self.main_layout.addWidget(self.container_frame)

    def _setup_header_style(self) -> None:
        """
        Sets up the styling for the header label.

        :rtype: None
        """
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.header_label.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 1)
        self.header_label.setFont(font)
        self.header_label.setStyleSheet("QLabel { padding: 5px }")

    def _setup_tree_widget(self) -> None:
        """
        Sets up the tree widget
        
        :rtype: None
        """
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setIndentation(20)
        self.tree_widget.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Signal Connections
        self.tree_widget.itemClicked.connect(self._on_item_clicked)
        self.tree_widget.itemChanged.connect(self._handle_item_renamed)
        self.tree_widget.customContextMenuRequested.connect(self._show_context_menu)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """
        Handles the click event on a tree item.
        
        If an item is clicked, it emits :py:attr:`.pre_item_change` 
        followed by :py:attr:`.item_selected`.

        :param item: The clicked tree item.
        :type item: :py:class:`~PyQt6.QtWidgets.QTreeWidgetItem`
        :param column: The column index clicked.
        :type column: int

        :rtype: None
        """
        item_id = item.data(0, self.id_role)
        if isinstance(item_id, int) and item_id > 0:
            self.pre_item_change.emit()
            self.item_selected.emit(item_id)

    # -------------------------------------------------------
    # Abstract/Virtual Methods to be overridden by subclasses
    # -------------------------------------------------------

    def load_outline(self, data: list[dict] | None = None) -> None:
        """
        Loads the Outline for the OutlineManager. Must be
        Implemented in child classes. Raises NotImplemnetedError.
        
        :param data: The list of data to load in the outline.
            Default is None.
        :type data: list[dict] | None

        :rtype: None
        """
        raise NotImplementedError("Subclasses must implement load_outline")

    def _handle_search_input(self, query: str) -> None:
        """
        Handles the user's search and subsequent
        loading of searched term.
        
        :param query: The search query.
        :type query: str

        :rtype: None
        """
        raise NotImplementedError("Subclasses must implement _handle_search_input")

    def _show_context_menu(self, position: QPoint):
        """
        A method to show the context menu.
        
        :param position: The Point on the OutlineManager clicked on.
        :type pos: :py:class:`~PyQt6.QtCore.QPoint`
        """
        raise NotImplementedError("Subclasses must implement _show_context_menu")

    def _handle_item_renamed(self, item: QTreeWidgetItem, column: int):
        """
        Handles the signal emitted when a tree item has been successfully renamed.
                
        :param item: The renamed tree item.
        :type item: :py:class:`~PyQt6.QtWidgets.QTreeWidgetItem`
        :param column: The column index.
        :type column: int

        :rtype: None
        """
        raise NotImplementedError("Subclasses must implement _handle_item_renamed")