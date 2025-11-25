# src/python/lore_repository.py

from utils.types import LoreEntryDict, LoreSearchResultDict, DBRowList
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from db_connector import DBConnector

class LoreRepository:
    """
    Manages all database operations for the Lore_Entries entity.
    Includes methods for basic CRUD (Create, Read, Update, Delete) 
    and related associations (Tags, Locations).
    """
    def __init__(self, db_connector: DBConnector) -> None:
        self.db = db_connector

    def get_all_lore_entries(self) -> DBRowList | None:
        """Retrieves ID, Title, and Category for all lore entries."""
        query = """
        SELECT ID, Title, Category
        FROM Lore_Entries
        ORDER BY Title ASC;
        """
        return self.db._execute_query(query, fetch_all=True)

    def create_lore_entry(self, title: str, content: str = "", category: str = "") -> int | None:
        """Creates a new lore entry and returns its ID."""
        query = """
        INSERT INTO Lore_Entries (Title, Content, Category)
        VALUES (?, ?, ?)
        """
        lore_id = self.db._execute_commit(query, (title, content, category), fetch_id=True)
        return lore_id
    
    def get_lore_entry_title(self, lore_id: int) -> str:
        """Retrieves the title of a lore entry given lore id"""
        query = "SELECT Title FROM Lore_Entries WHERE ID = ?"
        result =  self.db._execute_query(query, (lore_id,), fetch_one=True)
        return result['Title'] if result else None
    
    def get_lore_entry_details(self, lore_id: int) -> LoreEntryDict | None:
        """Retrieves the full details (Title, Content, Category) for a specific ID."""
        query = """
        SELECT ID, Title, Content, Category
        FROM Lore_Entries
        WHERE ID = ?;
        """
        return self.db._execute_query(query, (lore_id,), fetch_one=True)

    def update_lore_entry(self, lore_id: int, title: str, content: str = "", category: str = "") -> bool:
        """Updates the title, content, and category of an existing lore entry."""
        query = query = "UPDATE Lore_Entries SET Title = ?, Content = ?, Category = ? WHERE ID = ?;"
        params = (title, content, category, lore_id)
        return self.db._execute_commit(query, params)
    
    def delete_lore_entry(self, lore_id: int) -> bool:
        """
        Deletes a lore entry. Cascading deletes should handle associated 
        Chapter_Lore and Lore_Tags based on the schema design.
        """
        query = "DELETE FROM Lore_Entries WHERE ID = ?;"
        return self.db._execute_commit(query, (lore_id,))
    
    def search_lore_entries(self, user_query: str) -> list[LoreSearchResultDict] | None:
        """
        Accepts a keyword query and performs a hybrid search:
        1. FTS on Title, Content, and Category (ranked results).
        2. JOIN search on Tag names (unranked results).
        3. Merges and deduplicates the results, prioritizing FTS rank.
        """

        clean_query = user_query.strip()
        if not clean_query:
            return None

        # Wildcard pattern for case-insensitive LIKE Search
        like_pattern = f'%{clean_query}%'

        query = """
        SELECT DISTINCT LE.ID, LE.Title, LE.Category
        FROM Lore_Entries AS LE
        LEFT JOIN Lore_Tags AS LT ON LE.ID = LT.Lore_ID
        LEFT JOIN Tags AS T ON LT.Tag_ID = T.ID
        WHERE
            LE.Title LIKE ? OR
            LE.Content LIKE ? OR
            LE.Category LIKE ? OR
            T.Name LIKE ?
        ORDER BY LE.Title ASC;
        """
        params = (like_pattern, like_pattern, like_pattern, like_pattern)
        return self.db._execute_query(query, params, fetch_all=True)