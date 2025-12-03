# src/python/repository/character_repository

from ..utils.types import DBRowList
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from ..db_connector import DBConnector

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
    
    def create_character(self, name: str, description: str = "", status: str = "") -> int | None:
        """Creates a new character and returns its ID, None if failed."""
        query = """INSERT INTO Characters (Name, Description, Status) 
        VALUES (?, ?, ?);
        """
        return self.db._execute_commit(query, (name, description, status), fetch_id=True)
    
    def get_character_details(self, char_id) -> list[dict]:
        """Retrieves the full details (Name, Description, Status) for a specific ID."""
        query = """
        SELECT ID, Name, Description, Status
        FROM Characters
        WHERE ID = ?;
        """
        return self.db._execute_query(query, (char_id,), fetch_one=True)
    
    def update_character(self, char_id: int, name: str, description: str = "", status: str = "") -> bool:
        """Updates the Character in the database"""
        query = """
        UPDATE Characters SET Name = ?, Description = ?, Status = ?
        WHERE ID = ?;
        """
        return self.db._execute_commit(query, (name, description, status, char_id))

    def delete_character(self, char_id) -> bool:
        """Deletes a character and returns its success"""
        query = "DELETE FROM Characters WHERE ID = ?;"
        return self.db._execute_commit(query, (char_id,))
    
    def get_character_name(self, char_id) -> str | None:
        """Retrieves a characters name given ID"""
        query = "SELECT Name FROM Characters WHERE ID = ?"
        result = self.db._execute_query(query, (char_id,), fetch_one=True)
        return result['Name'] if result else None
    
    def search_characters(self, user_query: str) -> list[dict] | None:
        """
        Accepts a keyword query and performs a hybrid search:
        1. Search on Name, Status (ranked results).
        2. Merges and deduplicates the results, prioritizing FTS rank.
        """

        clean_query = user_query.strip()
        if not clean_query:
            return None

        # Wildcard pattern for case-insensitive LIKE Search
        like_pattern = f'%{clean_query}%'

        query = """
        SELECT DISTINCT ID, Name, Status
        FROM Characters
        WHERE
            Name LIKE ? OR
            Status LIKE ?
        ORDER BY Name ASC;
        """
        params = (like_pattern, like_pattern)
        return self.db._execute_query(query, params, fetch_all=True)
    
    def get_all_characters_for_export(self, character_ids: list[int] = []) -> list[dict]:
        """
        Retrieves characters details for export purposes,
        optionally filtered by a list of IDs.
        """
        query = """
        SELECT ID, Name, Description, Status, Age, Date_Of_Birth, Pronouns,
        Sexual_Orientation, Gender_Identity, Ethnicity_Background, Occupation_School,
        Hometown_City, Physical_Description
        FROM Characters
        """
        params = ()

        # 1. Modify the query if specific IDs are requested
        if character_ids is not None and character_ids:
            # Ensure IDs are unique and sorted for consistent query execution
            unique_ids = sorted(list(set(character_ids))) 
            
            # Create placeholders for the IN clause (e.g., ?, ?, ?)
            placeholders = ', '.join(['?'] * len(unique_ids))
            
            query += f" WHERE ID IN ({placeholders})"
            # The IDs become the parameters for the query
            params = tuple(unique_ids)

        # 2. Add final ordering clause
        query += " ORDER BY Name ASC;"

        results = self.db._execute_query(query, params, fetch_all=True)
        return results if results else []