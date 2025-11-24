# src/python/repository/character_repository

from utils.types import DBRowList
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from db_connector import DBConnector

class CharacterRepository:
    """
    Manages all database operations for the character entity
    Uses the provided DBConnector to execute queries.
    """
    def __init__(self, db_connector: DBConnector) -> None:
        self.db = db_connector

    def get_all_characters(self) -> DBRowList | None:
        """Retrieves ID, Name from Characters entity."""
        query = "SELECT ID, Name FROM Characters ORDER BY Name ASC;"
        return self.db._execute_query(query, fetch_all=True)
    
    def create_character(self, title: str, description: str = "", status: str = "") -> int | None:
        """Creates a new character and returns its ID, None if failed."""
        query = """INSERT INTO Characters (Title, Description, Status) 
        VALUES (?, ?, ?);
        """
        return self.db._execute_commit(query, (title, description, status), fetch_id=True)
    
    def update_character(self, char_id: int, title: str, description: str, status: str) -> bool:
        """Updates the Character in the database"""
        query = """
        UPDATE Characters SET Title = ?, Description = ?, Status = ?,
        WHERE ID = ?;
        """
        self.db._execute_commit(query, (title, description, status, char_id))

    def delete_character(self, char_id) -> bool:
        """Deletes a character and returns its success"""
        query = "DELETE Characters WHERE ID = ?;"
        return self.db._execute_commit(query, (char_id,))
    
    def get_character_name(self, char_id) -> str | None:
        """Retrieves a characters name given ID"""
        query = "SELECT Name FROM Characters WHERE ID = ?"
        result = self.db._execute_query(self, (char_id,), fetch_one=True)
        return result['Name'] if result else None