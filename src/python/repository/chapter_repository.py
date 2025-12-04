# src/python/chapter_repository.py

from ..utils.types import ChapterContentDict, ChapterBasicDict
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..db_connector import DBConnector

class ChapterRepository:
    """
    Manages all database operations for the Chapter entity
    Uses the provided DBConnector to execute queries.
    """
    def __init__(self, db_connector: DBConnector) -> None:
        self.db = db_connector

    def get_all_chapters(self) -> ChapterBasicDict:
        """Retrives all chapters order by Sort_Order"""
        query = """
        SELECT ID, Title, Sort_Order, Precursor_Chapter_ID
        FROM Chapters
        ORDER BY Sort_Order ASC;
        """
        return self.db._execute_query(query, fetch_all=True)

    def get_all_chapters_with_content(self) -> ChapterContentDict:
        """
        Retrieves all chapters with their full text content, ordered by Sort_Order.
        Used for full story export.
        """
        query = """
        SELECT ID, Title, Text_Content, Sort_Order, Precursor_Chapter_ID
        FROM Chapters
        ORDER BY Sort_Order ASC;
        """
        return self.db._execute_query(query, fetch_all=True)

    def create_chapter(self, title: str, sort_order: int, precursor_id: int | None = None) -> int | None:
        """Creates a new chapter and returns its ID"""
        query = """
        INSERT INTO Chapters (Title, Text_Content, Sort_Order, Precursor_Chapter_ID)
        VALUES (?, ?, ?, ?);
        """
        chapter_id = self.db._execute_commit(
            query, (title, "<p></p>", sort_order, precursor_id), fetch_id=True
        )
        return chapter_id

    def get_chapter_content(self, chapter_id: int) -> str | None:
        """Retrieves the rich text content for a specific chapter ID"""
        query = "SELECT Text_Content FROM Chapters WHERE ID = ?;"
        result = self.db._execute_query(query, (chapter_id,), fetch_one=True)
        return result['Text_Content'] if result else None
    
    def update_chapter_content(self, chapter_id: int, content: str) -> bool:
        """Updates the rich text content for a chapter"""
        query = "UPDATE Chapters SET Text_Content = ? WHERE ID = ?;"
        return self.db._execute_commit(query, (content, chapter_id))
    
    def delete_chapter(self, chapter_id: int) -> bool:
        """Deletes a chapter and cascades deletion of associated tags"""
        query = "DELETE FROM Chapters WHERE ID = ?;"
        return self.db._execute_commit(query, (chapter_id,))
    
    def get_chapter_title(self, chapter_id: int) -> str | None:
        """Retrieves the chapter title by Chapter ID"""
        query = "SELECT Title FROM Chapters WHERE ID = ?;"
        result = self.db._execute_query(query, (chapter_id,), fetch_one=True)
        return result['Title'] if result else None

    def update_chapter_title(self, chapter_id: int, title: str) -> str | None:
        """Updates the Chapter title by Chapter ID"""
        query = "UPDATE Chapters SET Title = ? WHERE ID = ?;"
        return self.db._execute_commit(query, (title, chapter_id))
    
    def get_all_chapters_for_export(self, chapter_ids: list[int] = None) -> list[dict]:
        """
        Retrieves chapter details (ID, Title, Content, Sort_Order) for export purposes,
        optionally filtered by a list of IDs.
        """
        query = """
        SELECT ID, Title, Text_Content, Sort_Order
        FROM Chapters
        """
        params = ()

        # 1. Modify the query if specific IDs are requested
        if chapter_ids is not None and chapter_ids:
            # Ensure IDs are unique and sorted for consistent query execution
            unique_ids = sorted(list(set(chapter_ids))) 
            
            # Create placeholders for the IN clause (e.g., ?, ?, ?)
            placeholders = ', '.join(['?'] * len(unique_ids))
            
            query += f" WHERE ID IN ({placeholders})"
            # The IDs become the parameters for the query
            params = tuple(unique_ids)

        # 2. Add final ordering clause
        query += " ORDER BY Sort_Order ASC;"

        # 3. Execute the query using the DBConnector helper method
        results = self.db._execute_query(query, params, fetch_all=True)

        return results if results else []
    
    def reorder_chapters(self, chapter_updates: list[tuple[int, int]]) -> bool:
        """
        Updates the Sort_Order for multiple chapters in a single, atomic transaction.

        Args:
            chapter_updates: A list of tuples, where each tuple is
                             (chapter_id, new_sort_order).

        Returns:
            True if all updates succeed and the transaction commits, False otherwise.
        """
        query = "UPDATE Chapters SET Sort_Order = ? WHERE ID = ?;"
        
        # Each operation is a tuple: (sql_query_string, parameters_tuple)
        operations = []
        for chapter_id, new_sort_order in chapter_updates:
            # parameters are (new_sort_order, chapter_id) to match the SQL template
            operations.append((query, (new_sort_order, chapter_id)))

        # Execute all operations in a single transaction
        return self.db._execute_transaction(operations)