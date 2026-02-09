# src/python/lore_repository.py

from ..utils.types import LoreEntryDict, LoreSearchResultDict, DBRowList
from ..db_connector import DBConnector
from ..utils.logger import get_logger
from ..utils.exceptions import DatabaseError

logger = get_logger(__name__)

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
        logger.debug("LoreRepository initialized.")

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
        SELECT ID, Title, Category, Parent_Lore_ID, Sort_Order
        FROM Lore_Entries
        ORDER BY Sort_Order ASC, Title ASC;
        """
        try:
            results = self.db._execute_query(query, fetch_all=True)
            logger.info(f"Retrieved {len(results)} basic lore entry records.")
            return results
        except DatabaseError as e:
            logger.error("Failed to retrieve all lore entries.", exc_info=True)
            raise e
        
    def get_all_lore_entry_titles(self) -> list[str]:
        """
        Retrieves a list of all lore entry titles.

        :returns: A list each index containing the lore entry's Title.
        :rtype: list[str]
        """
        query = "SELECT Title FROM Lore_Entries;"
        try:
            lore_dict = self.db._execute_query(query, fetch_all=True)
            results = []
            for lore in lore_dict:
                results.append(lore['Title'])
            logger.info(f"Retrieved {len(results)} of all Lore Entry Titles.")
            return results
        except DatabaseError as e:
            logger.error("Failed to retrieve all lore entry titles.", exc_info=True)
            raise e
    
    def get_content_by_title(self, title: str) -> dict | None:
        """
        Retrieves full content for all the Lore Entry that match the title.
        
        :param title: The title of the Lore Entry  to get content for.
        :type title: str

        :returns: A dictionary of the Lore Entry .
        :rtype: dict or None
        """ 
        search_term = f"%{title.strip()}%"
        query = "SELECT ID, Title, Content FROM Lore_Entries WHERE Title Like ? COLLATE NOCASE;"
        try:
            result = self.db._execute_query(query, (search_term,), fetch_all=True)
            logger.debug(f"Retrieved content by title search: '{title}'. Found: {result is not None}")
            return result
        except DatabaseError as e:
            logger.error(f"Failed to retrieve content for lore entry title search: '{title}'.", exc_info=True)
            raise e


    def create_lore_entry(self, title: str, content: str = "", category: str = "", 
                          parent_lore_id: int | None = None, sort_order: int = 0) -> int | None:
        """
        Inserts a new lore entry record into the database with a default empty content field.

        :param title: The title of the new lore entry.
        :type title: str
        :param content: The content of the lore entry, Defaults to Empty String.
        :type content: str
        :param category: The category of the lore entry (e.g. Magic System), Defaults to Empty String
        :type category: str
        :param parent_lore_id: The Lore ID of the parent Lore Entry.
        :type parent_lore_id: int
        :param sort_order: The sort order of the Lore Entries
        :type sort_order: int
        
        :returns: The ID of the newly created lore entry if successful, otherwise None.
        :rtype: int or None
        """
        query = """
        INSERT INTO Lore_Entries (Title, Content, Category, Parent_Lore_ID, Sort_Order)
        VALUES (?, ?, ?, ?, ?)
        """
        try:
            lore_id = self.db._execute_commit(query, (title, content, category, parent_lore_id, 
                                                      sort_order), fetch_id=True)
            if lore_id:
                logger.info(f"Created new lore entry: ID={lore_id}, Title='{title}'.")
            return lore_id
        except DatabaseError as e:
            logger.error(f"Failed to create new lore entry with title: '{title}'.", exc_info=True)
            raise e
    
    def get_lore_entry_title(self, lore_id: int) -> str | None:
        """
        Get the title of a lore entry based on its lore_id.
        
        :param lore_id: The lore ID of the lore entry.
        :type lore_id: int

        :return: returns the title of the lore entry or None if not found.
        :rtype: str or None
        """
        query = "SELECT Title FROM Lore_Entries WHERE ID = ?"
        try:
            result =  self.db._execute_query(query, (lore_id,), fetch_one=True)
            title = result['Title'] if result else None
            logger.debug(f"Retrieved title for lore entry ID: {lore_id}. Title: {title}")
            return title
        except DatabaseError as e:
            logger.error(f"Failed to retrieve title for lore entry ID: {lore_id}.", exc_info=True)
            raise e
    
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
        try:
            details = self.db._execute_query(query, (lore_id,), fetch_one=True)
            logger.debug(f"Retrieved details for lore entry ID: {lore_id}. Found: {details is not None}")
            return details
        except DatabaseError as e:
            logger.error(f"Failed to retrieve details for lore entry ID: {lore_id}.", exc_info=True)
            raise e
        
    def get_number_of_lore_entries(self) -> int:
        """
        Retrieves the number of lore entries in the Datbase.

        Used for Project Statistics

        :returns: The number of lore entries.
        :rtype: int
        """
        query = "SELECT COUNT(*) FROM Lore_Entries;"
        try:
            result = self.db._execute_query(query, fetch_all=True)
            try:
                count = result[0]['COUNT(*)']
            except:
                count = 0

            return count
        
        except DatabaseError as e:
            logger.error("Failed to count all Lore Entries.", exc_info=True)
            raise e
        
    def get_unique_categories(self) -> list[str]:
        """
        Retrieves all the unique categories from the database.
        
        :return: A list of the string names of the categories.
        :rtype: list[str]
        """
        query = """
        SELECT DISTINCT Category 
        FROM Lore_Entries 
        WHERE Category IS NOT NULL AND Category != '' 
        ORDER BY Category ASC;
        """
        try:
            results = self.db._execute_query(query, fetch_all=True)
            return [row['Category'] for row in results] if results else []
        except DatabaseError as e:
            logger.error("Failed to retrieve unique lore categories.", exc_info=True)
            raise e

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
        try:
            success = self.db._execute_commit(query, params)
            if success:
                logger.info(f"Updated lore entry ID: {lore_id}. New Title: '{title}'.")
            return success
        except DatabaseError as e:
            logger.error(f"Failed to update lore entry ID: {lore_id} with title '{title}'.", exc_info=True)
            raise e
    
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
        try:
            success = self.db._execute_commit(query, params)
            if success:
                logger.info(f"Updated title for lore entry ID: {lore_id}. New title: '{new_title}'.")
            return success
        except DatabaseError as e:
            logger.error(f"Failed to update title for lore entry ID: {lore_id} to '{new_title}'.", exc_info=True)
            raise e
    
    def update_lore_entry_parent_id(self, lore_id: int, new_parent_id: int | None) -> bool:
        """
        Updates the Parent_Lore_ID for a specific Lore Entry.

        :param lore_id: The ID of the lore entry to update.
        :type lore_id: int
        :param new_parent_id: The ID of the new parent entry, or None to make it a root entry.
        :type new_parent_id: int

        :returns: True on success, False otherwise.
        """
        query = """
        UPDATE Lore_Entries
        SET Parent_Lore_ID = ?
        WHERE ID = ?;
        """
        try:
            success = self.db._execute_commit(query, (new_parent_id, lore_id))
            if success:
                logger.info(f"Updated parent ID for lore entry ID: {lore_id} to {new_parent_id}.")
            return success
        except DatabaseError as e:
            logger.error(f"Failed to update parent ID for lore entry ID: {lore_id} to "
                         f"{new_parent_id}.", exc_info=True)
            raise e
        
    def update_lore_order(self, lore_id: int, sort_order: int) -> bool:
        """
        Updates the Sort Order for a specific Lore Entry.

        :param lore_id: The ID of the lore entry to update.
        :type lord_id: int
        :param sort_order: The new value for the sort_order
        :type sort_order: int

        :returns: True on success, False otherwise.
        """
        query = """
        UPDATE Lore_Entries
        SET Sort_Order = ?
        WHERE ID = ?;
        """
        try:
            success = self.db._execute_commit(query, (sort_order, lore_id))
            if success:
                logger.info(f"Updated parent ID for lore entry ID: {lore_id} to {sort_order}.")
            return success
        except DatabaseError as e:
            logger.error(f"Failed to update parent ID for lore entry ID: {lore_id} to {sort_order}.",
                         exc_info=True)
            raise e
    
    def delete_lore_entry(self, lore_id: int) -> bool:
        """
        Deletes a lore entry.
        
        :param lore_id: The lore entry ID of the lore entry to be deleted.
        :type lore_id: int

        :returns: True if successfully delete lore entry, otherwise False
        :rtype: bool
        """
        query = "DELETE FROM Lore_Entries WHERE ID = ?;"
        try:
            success = self.db._execute_commit(query, (lore_id,))
            if success:
                logger.warning(f"Lore entry deleted: ID={lore_id}.")
            return success
        except DatabaseError as e:
            logger.error(f"Failed to delete lore entry ID: {lore_id}.", exc_info=True)
            raise e
    
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
        SELECT DISTINCT LE.ID, LE.Title, LE.Category, LE.Parent_Lore_ID
        FROM Lore_Entries AS LE
        LEFT JOIN Lore_Tags AS LT ON LE.ID = LT.Lore_ID
        LEFT JOIN Tags AS T ON LT.Tag_ID = T.ID
        WHERE
            LE.Title LIKE ? OR
            LE.Category LIKE ? OR
            T.Name LIKE ?
        ORDER BY LE.Title ASC;
        """
        params = (like_pattern, like_pattern, like_pattern, like_pattern)
        try:
            results = self.db._execute_query(query, params, fetch_all=True)
            logger.info(f"Lore search for '{clean_query}' returned {len(results)} results.")
            return results
        except DatabaseError as e:
            logger.error(f"Failed to execute search for lore entries with query: '{clean_query}'.", 
                         exc_info=True)
            raise e
    
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

        # Modify the query if specific IDs are requested
        if lore_ids is not None and lore_ids:
            # Ensure IDs are unique and sorted for consistent query execution
            unique_ids = sorted(list(set(lore_ids))) 
            
            # Create placeholders for the IN clause (e.g., ?, ?, ?)
            placeholders = ', '.join(['?'] * len(unique_ids))
            
            query += f" WHERE ID IN ({placeholders})"
            params = tuple(unique_ids)

        # Add final ordering clause
        query += " ORDER BY Title ASC;"

        # Execute the query using the DBConnector helper method
        try:
            results = self.db._execute_query(query, params, fetch_all=True)
            if lore_ids:
                logger.info(f"Retrieved {len(results)} lore entries for export from a list of "
                            f"{len(lore_ids)} IDs.")
            else:
                logger.info(f"Retrieved all {len(results)} lore entries for export.")
            return results if results else []
        except DatabaseError as e:
            logger.error("Failed to retrieve lore entries for export.", exc_info=True)
            raise e