# src/python/ui/widgets/chapter_tree.py

from PyQt6.QtWidgets import QTreeWidget
from PyQt6.QtGui import QDropEvent

class ChapterTreeWidget(QTreeWidget):
    """
    A specialized :py:class:`~PyQt6.QtWidgets.QTreeWidget` that handles the 
    visual representation and drag-and-drop reordering of chapters.

    This widget is designed to work in tandem with a parent editor (typically 
    a :py:class:`.ChapterOutlineManager`) to ensure that any structural 
    changes made via the UI are synchronized with the underlying database.
    """

    def __init__(self, editor=None) -> None:
        """
        Initializes the ChapterTree.
        
        :param editor: The parent manager managing the data synchronization.
        :type editor: :py:class:`ChapterOutlineManager` or :py:obj:`None`, optional
        """
        self.editor = editor
        super().__init__()

    def dropEvent(self, event: QDropEvent) -> None:
        """
        Overrides the default drop event to handle chapter reordering.
        
        When an item is dropped, this method triggers a save of the current 
        work, updates the sort orders of all chapters in the database based 
        on the new visual order, and reloads the outline to ensure UI/DB 
        consistency.

        :param event: The drop event containing information about the operation.
        :type event: :py:class:`~PyQt6.QtGui.QDropEvent`
        
        :rtype: None
        """
        super().dropEvent(event)

        dropped_item = self.currentItem()
        if not dropped_item:
            return

        # 1. Save current work before re-ordering in DB
        if self.editor:
            self.editor.pre_chapter_change.emit()

        # 2. Sync the NEW order (established by super()) to the database
        if self.editor:
            # This reads the tree in its current state and updates DB 'sort_order'
            self.editor._update_all_chapter_sort_orders()
            
            # 3. Reload to ensure consistency (and refresh item widgets if any)
            self.editor.load_outline()
        
        event.accept()