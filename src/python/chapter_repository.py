# src/python/chapter_repository.py

from .db_connector import DBConnector

from typing import Any

class ChapterRepository:
    """
    Manages all database operations for the Chapter entity
    Uses the provided DBConnector to execute queries.
    """
    def __init__(self, db_connector: DBConnector) -> None:
        self.db = db_connector

    def get_all_chapters_with_content(self) -> list[dict[str, Any]]:
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
    
    def get_all_chapters(self) -> list[dict[str, Any]]:
        """Retrives all chapters order by Sort_Order"""
        query = """
        SELECT ID, Title, Sort_Order, Precursor_Chapter_ID
        FROM Chapters
        ORDER BY Sort_Order ASC;
        """
        return self.db._execute_query(query, fetch_all=True)

    def get_chapter_content(self, chapter_id: int) -> str | None:
        """Retrieves the rich text content for a specific chapter ID"""
        query = "SELECT Text_Content FROM Chapters WHERE ID = ?;"
        result = self.db._execute_query(query, (chapter_id,), fetch_one=True)
        return result['Text_Content'] if result else None
    
    def set_chapter_content(self, chapter_id: int, content: str) -> bool:
        """Updates the rich text content for a chapter"""
        query = "UPDATE Chapters SET Text_Content = ? WHERE ID = ?;"
        return self.db._execute_commit(query, (content, chapter_id))
    
    def delete_chapter(self, chapter_id: int) -> bool:
        """Deletes a chapter and cascades deletion of associated tags"""
        query = "DELETE FROM Chapters WHERE ID = ?;"
        return self.db._execute_commit(query, (chapter_id,))
    
    def get_chapter_title(self, chapter_id: int) -> str | None:
        """Retrieves the chapter title by Chapter ID"""
        query = "SELECT Title FROM Chapters WHERE ID = ?"
        return self.db._execute_query(query, (chapter_id,))
    
    def update_chapter_title(self, chapter_id: int, title: str) -> str | None:
        """Updates the Chapter title by Chapter ID"""
        query = "UPDATE Chapters SET Title = ? WHERE ID = ?"
        return self.db._execute_commit(query, (title, chapter_id))