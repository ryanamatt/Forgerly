# src/python/lore_repository.py

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
    
    def search_lore_entries(self, user_query: str) -> list[dict] | None:
        """
        Accepts a keyword query and performs a hybrid search:
        1. FTS on Title, Content, and Category (ranked results).
        2. JOIN search on Tag names (unranked results).
        3. Merges and deduplicates the results, prioritizing FTS rank.
        """

        clean_query = user_query.strip()
        if not clean_query:
            return None

        fts_query = user_query.strip()
        if fts_query and not any(op in fts_query for op in [' ', '*', 'OR', 'AND', '"']):
            fts_query = fts_query + '*'

        # --- 1. Combined FTS and Tag Search ---
        # We use a UNION to combine results from FTS and a standard JOIN for tags.
        # FTS matches will have a rank, Tag matches will be assigned a poor rank (e.g., 1000000)
        # to ensure FTS results are always shown first.

        query = """
            WITH Search_Results AS (
                SELECT T1.ID, T1.Title, T1.Category, T2.rank AS search_rank
                FROM Lore_Entries AS T1
                JOIN Lore_Entries_FTS AS T2 ON T1.ID = T2.rowid
                WHERE T2.Lore_Entries_FTS MATCH ?

                UNION

                SELECT LE.ID, LE.Title, LE.Category, 1000000 as search_rank
                FROM Lore_Entries AS LE
                JOIN Lore_Tags AS LT ON LE.ID = LT.Lore_ID
                JOIN Tags AS T ON LT.Tag_ID = T.ID
                WHERE T.Name LIKE ?
            )

            SELECT ID, Title, Category, MIN(search_rank) AS final_rank
            FROM Search_Results
            GROUP BY ID
            ORDER BY final_rank ASC;
            """
        params = (fts_query, f'%{clean_query}')
        return self.db._execute_query(query, params, fetch_all=True)