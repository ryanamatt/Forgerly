# src/python/lore_repository.py

from ..utils.types import LoreEntryDict, LoreSearchResultDict, DBRowList
from ..db_connector import DBConnector

class LoreRepository:
    """
    Manages all database operations for the Lore Entry entity.

    This class serves as the Data Access Object (DAO) for Lore Entry, handling 
    CRUD operations and ensuring data integrity specific to lore_entroes.
    It uses the provided :py:class:`~app.db_connector.DBConnector` to execute queries.
    """
    def __init__(self, db_connector: DBConnector) -> None:
        """
        Initializes the :py:class:`.LoreRepository`.

        :param db_connector: The active connection object to the SQLite database.
        :type db_connector: :py:class:`~app.db_connector.DBConnector`
        
        :rtype: None
        """
        self.db = db_connector

    def get_all_lore_entries(self) -> DBRowList | None:
        """"
        Retrieves a list of all Lore Entries, ordered by their Title in ascending order.
        
        The returned data includes basic information necessary for the Outline 
        Manager, but excludes the full lore entry content.

        :returns: A list of dictionaries, each containing the lore entry's ID, Title, 
            Category, and Parent_Lore_ID.
        :rtype: :py:class:`~app.utils.types.DBRowList`
        """
        query = """
        SELECT ID, Title, Category, Parent_Lore_ID
        FROM Lore_Entries
        ORDER BY Title ASC;
        """
        return self.db._execute_query(query, fetch_all=True)
    
    def get_content_by_title(self, title: str) -> dict | None:
        """
        Retrieves full content for a Lore Entry based on its title.
        
        :param title: The title of the Lore Entry  to get content for.
        :type title: str

        :returns: A dictionary of the Lore Entry .
        :rtype: dict or None
        """ 
        search_term = f"%{title.strip()}%"
        query = "SELECT ID, Title, Content FROM Lore_Entries WHERE Title Like ? COLLATE NOCASE;"
        return self.db._execute_query(query, (search_term,), fetch_one=True)


    def create_lore_entry(self, title: str, content: str = "", category: str = "") -> int | None:
        """
        Inserts a new lore entry record into the database with a default empty content field.

        :param title: The title of the new lore entry.
        :type title: str
        :param content: The content of the lore entry, Defaults to Empty String.
        :type content: str
        :param category: The category of the lore entry (e.g. Magic System), Defaults to Empty String
        :type category: str
        
        :returns: The ID of the newly created lore entry if successful, otherwise None.
        :rtype: int or None
        """
        query = """
        INSERT INTO Lore_Entries (Title, Content, Category)
        VALUES (?, ?, ?)
        """
        lore_id = self.db._execute_commit(query, (title, content, category), fetch_id=True)
        return lore_id
    
    def get_lore_entry_title(self, lore_id: int) -> str | None:
        """
        Get the title of a lore entry based on its lore_id.
        
        :param lore_id: The lore ID of the lore entry.
        :type lore_id: int

        :return: returns the title of the lore entry or None if not found.
        :rtype: str or None
        """
        query = "SELECT Title FROM Lore_Entries WHERE ID = ?"
        result =  self.db._execute_query(query, (lore_id,), fetch_one=True)
        return result['Title'] if result else None
    
    def get_lore_entry_details(self, lore_id: int) -> LoreEntryDict | None:
        """
        Retrieves the full details of a lore entry (Title, Content, Category) for a specific ID.

        :param lore_id: The lore entry id to get details for.
        :type lore_id: int

        :returns a dictionary of the Lore Entry's details.
        :rtype: :py:class:`~app.utils.types.LoreEntryDict`
        """
        query = """
        SELECT ID, Title, Content, Category
        FROM Lore_Entries
        WHERE ID = ?;
        """
        return self.db._execute_query(query, (lore_id,), fetch_one=True)

    def update_lore_entry(self, lore_id: int, title: str, content: str = "", category: str = "") -> bool:
        """
        Updates the Lore Entry details in the database.

        :param lore_id: The lore entry ID to know which lore entry to update.
        :type lore_id: int
        :param title: The new/same title of the Lore Entry to update.
        :type title: str
        :param content: The content of a lore entry. Defaults to Empty String
        :type content: str
        :param category: The category that the lore entry is in. Defaults to Empty String.
        :type category: str

        :returns: True if successfully saved to dataase, otherwise False.
        :rtype: bool
        """
        query = query = "UPDATE Lore_Entries SET Title = ?, Content = ?, Category = ? WHERE ID = ?;"
        params = (title, content, category, lore_id)
        return self.db._execute_commit(query, params)
    
    def update_lore_entry_title(self, lore_id: int, new_title: str) -> bool:
        """
        Updates only the Title of a Lore Entry in the database.
        
        :param lore_id: The ID of the lore entry to update.
        :type lore_id: int
        :param new_title: The new title for the Lore Entry.
        :type new_title: str

        :returns: True if successfully saved to database, otherwise False.
        :rtype: bool
        """
        query = "UPDATE Lore_Entries SET Title = ? WHERE ID = ?;"
        params = (new_title, lore_id)
        return self.db._execute_commit(query, params)
    
    def update_lore_entry_parent_id(self, lore_id: int, new_parent_id: int) -> bool:
        """
        Updates the Parent_Lore_ID for a specific Lore Entry.

        :param lore_id: The ID of the lore entry to update.
        :param new_parent_id: The ID of the new parent entry, or None to make it a root entry.

        :returns: True on success, False otherwise.
        """
        query = """
        UPDATE Lore_Entries
        SET Parent_Lore_ID = ?
        WHERE ID = ?;
        """
        return self.db._execute_commit(query, (new_parent_id, lore_id))
    
    def delete_lore_entry(self, lore_id: int) -> bool:
        """
        Deletes a lore entry.
        
        :param lore_id: The lore entry ID of the lore entry to be deleted.
        :type lore_id: int

        :returns: True if successfully delete lore entry, otherwise False
        :rtype: bool
        """
        query = "DELETE FROM Lore_Entries WHERE ID = ?;"
        return self.db._execute_commit(query, (lore_id,))
    
    def search_lore_entries(self, user_query: str) -> list[LoreSearchResultDict] | None:
        """
        Accepts a keyword query and performs a hybrid search:
        1. FTS on Title, Content, and Category (ranked results).
        2. JOIN search on Tag names (unranked results).
        3. Merges and deduplicates the results, prioritizing FTS rank.

        :param user_query: The user's search query.
        :type user_query: str

        :returns: Returns a list of the Lore Entry search results.
        :rtype: list[:py:class:`~app.utils.types.LoreSearchResultDict`]
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
    
    def get_lore_entries_for_export(self, lore_ids: list[int] = None) -> list[dict]:
        """
        Retrieves lore entry details for export purposes,
        optionally filtered by a list of IDs.

        :param lore_ids: A list of all the lore entry IDs selected. Defaults
            to Empty List which means all Lore Entry IDS are selected.

        :returns: A dictionary of all the lore entries selected by ID.
        :rtype: list[dict]
        """
        query = """
        SELECT ID, Title, Content, Category
        FROM Lore_Entries
        """
        params = ()

        # 1. Modify the query if specific IDs are requested
        if lore_ids is not None and lore_ids:
            # Ensure IDs are unique and sorted for consistent query execution
            unique_ids = sorted(list(set(lore_ids))) 
            
            # Create placeholders for the IN clause (e.g., ?, ?, ?)
            placeholders = ', '.join(['?'] * len(unique_ids))
            
            query += f" WHERE ID IN ({placeholders})"
            # The IDs become the parameters for the query
            params = tuple(unique_ids)

        # 2. Add final ordering clause
        query += " ORDER BY Title ASC;"

        # 3. Execute the query using the DBConnector helper method
        results = self.db._execute_query(query, params, fetch_all=True)

        return results if results else []