# src/python/lore_repository.py

from db_connector import DBConnector
from typing import Any

class LoreRepository:
    """
    Manages all database operations for the Lore_Entries entity.
    Includes methods for basic CRUD (Create, Read, Update, Delete) 
    and related associations (Tags, Locations).
    """
    def __init__(self, db_connector: DBConnector) -> None:
        self.db = db_connector

    def create_lore_entry(self, title: str, category: str = "", content:str = "") -> int | None:
        """Creates a new lore entry and returns its ID."""
        query = """
        INSERT INTO Lore_Entries (Title, Content, Category)
        VALUES (?, ?, ?)
        """
        lore_id = self.db._execute_commit(query, (title, content, category), fetch_id=True)
        return lore_id
    
    def get_all_lore_entries(self) -> list[dict[str, Any]]:
        """Retrieves ID, Title, and Categroy for all lore entries."""
        query = """
        SELECT ID, Title, Category
        FROM Lore_Entries
        ORDER BY Title ASC;
        """
        return self.db._execute_query(query, fetch_all=True)
    
    def get_lore_entry_title(self, lore_id: int) -> str:
        """Retrieves the title of a lore entry given lore id"""
        query = "SELECT Title FROM Lore_Entries WHERE ID = ?"
        result =  self.db._execute_query(query, (lore_id,), fetch_one=True)
        return result['Title'] if result else None
    
    def get_lore_entry_details(self, lore_id: int) -> dict[str, Any] | None:
        """Retrieves the full details (Title, Content, Category) for a specific ID."""
        query = """
        SELECT ID, Title, Content, Category
        FROM Lore_Entries
        WHERE ID = ?;
        """
        return self.db._execute_query(query, (lore_id,), fetch_one=True)

    def update_lore_entry(self, lore_id: int, title: str, category: str, content: str) -> bool:
        """Updates the title, category, and content of an existing lore entry."""
        query = """
        UPDATE Lore_Entries 
        SET Title = ?, Content = ?, Category = ?
        WHERE ID = ?;
        """
        return self.db._execute_commit(
            query, (title, content, category, lore_id)
        )
    
    def delete_lore_entry(self, lore_id: int) -> bool:
        """
        Deletes a lore entry. Cascading deletes should handle associated 
        Chapter_Lore and Lore_Tags based on the schema design.
        """
        query = "DELETE FROM Lore_Entries WHERE ID = ?;"
        return self.db._execute_commit(query, (lore_id,))