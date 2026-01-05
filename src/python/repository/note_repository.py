# src/python/repository/note_repository

from ..db_connector import DBConnector
from ..utils.logger import get_logger
from ..utils.exceptions import DatabaseError

logger = get_logger(__name__)

class NoteRepository:
    """
    Manages all database operations for the Note entity.

    This class serves as the Data Access Object (DAO) for Notes, handling 
    CRUD operations and ensuring data integrity specific to Notes.
    It uses the provided :py:class:`~app.db_connector.DBConnector` to execute queries.
    """

    def __init__(self, db_connector: DBConnector) -> None:
        """
        Initializes the :py:class:`.NoteRepository`.

        :param db_connector: The active connection object to the SQLite database.
        :type db_connector: :py:class:`~app.db_connector.DBConnector`
        
        :rtype: None
        """
        self.db = db_connector
        logger.debug("Tag Repository Initialized")

    def get_all_notes(self) -> dict:
        """
        Retrieves a list of all notes, ordered by their Sort_Order.
        
        The returned data includes basic information necessary for the Outline 
        Manager, but excludes the full content.

        :returns: A list of dictionaries, each containing the notes's ID, Title, 
                  Sort_Order.
        :rtype: dict
        """
        query = """
        SELECT ID, Title, Parent_Note_ID, Sort_Order
        FROM Notes
        ORDER BY Sort_Order ASC;
        """
        try:
            results = self.db._execute_query(query, fetch_all=True)
            logger.info(f"Retrieved {len(results)} basic notes records.")
            return results
        except DatabaseError as e:
            logger.error("Failed to retrieve all basic notes.", exc_info=True)
            raise e
        
    def get_note_content(self, note_id: int) -> str | None:
        """
        Retrieves the content for a specific note ID
        
        Gathers only the content of a note.

        :param note_id: The note ID to get content from.
        :type note_id: int

        :returns: Returns a str of the content if successful, otherwise None
        :rtype: str or None
        """
        query = "SELECT Content FROM Notes WHERE ID = ?;"
        try:
            result = self.db._execute_query(query, (note_id,), fetch_one=True)
            content = result['Content'] if result else None
            logger.debug(f"Retrieved content for Note ID: {note_id}. Found: {content is not None}")
            return content
        except DatabaseError as e:
            logger.error(f"Failed to retrieve content for Note ID: {note_id}.", exc_info=True)
            raise e
        
    def get_note_title(self, note_id: int) -> str | None:
        """
        Retrieves the note title by Note ID from the database.

        Used when a Note Item is renamed in the OutlineManager.
        
        :param note_id; The ID of the Note you want the title from.
        :type note_id: int

        :returns: The Note title if found, otherwise None
        :rtype: str or None
        """
        query = "SELECT Title FROM Notes WHERE ID = ?;"
        try:
            result = self.db._execute_query(query, (note_id,), fetch_one=True)
            title = result['Title'] if result else None
            logger.debug(f"Retrieved title for Note ID: {note_id}. Title: {title}")
            return title
        except DatabaseError as e:
            logger.error(f"Failed to retrieve title for Note ID: {note_id}.", exc_info=True)
            raise e
        
    def get_all_notes_for_export(self, note_ids: list[int] = None) -> list[dict]:
        """
        Retrieves chapter details (ID, Title, Content, Parent_Node_ID, Sort_Order) for export purposes,
        optionally filtered by a list of IDs.

        :param note_ids: A list of all the notes IDs that wish to be exported. Default
            is None which results in all notes.
        :type note_ids: list[int]

        :returns: A list containing all note dicts.
        :rtype: list[dict]
        """
        query = """
        SELECT ID, Title, Content, Parent_Note_ID Sort_Order
        FROM Notes
        """
        params = ()

        # Modify the query if specific IDs are requested
        if note_ids is not None and note_ids:
            # Ensure IDs are unique and sorted for consistent query execution
            unique_ids = sorted(list(set(note_ids)))

            # Create placeholders for the IN clause (e.g., ?, ?, ?)
            placeholders = ', '.join(['?'] * len(unique_ids))

            query += f" WHERE ID IN ({placeholders})"
            params = tuple(unique_ids)

        # Add final ordering clause
        query += " ORDER BY Sort_Order ASC;"

        # Execute the query using the DBConnector helper method
        try:
            results = self.db._execute_query(query, params, fetch_all=True)
            if note_ids:
                logger.info(f"Retrieved {len(results)} Notes for export from a list of {len(note_ids)} IDs.")
            else:
                logger.info(f"Retrieved all {len(results)} Notes for export.")
            return results if results else []
        except DatabaseError as e:
            logger.error("Failed to retrieve Notes for export.", exc_info=True)
            raise e
        
    def create_note(self, title: str, sort_order: int, content: str = "", 
                    parent_note_id: int | None = None) -> int | None:
        """
        Inserts a new Note record into the database with a default empty content field.
        
        :param title: The title of new Note.
        :type title: str
        :param sort_order: The Sort_Order of the New Note.
        :type sort_order: int
        :param content: The conternt of new note, Default is Empty String.
        :type content: str
        :param parent_note_id: The Parent Note of a nested note, Default is None.
        :type parent_note_id: int | None

        :returns: The ID of the created note if successful, otherwise None 
        :rtype: int or None
        """
        query = """
        INSERT INTO Notes
        (Title, Content, Parent_Note_ID, Sort_Order)
        VALUES (?, ?, ?, ?);
        """
        try:
            note_id = self.db._execute_commit(query, (title, content, parent_note_id, sort_order), fetch_id=True)
            if note_id:
                logger.info(f"Created new note: ID={note_id}, Title='{title}', SortOrder={sort_order}.")
            return note_id
        except DatabaseError as e:
            logger.error(f"Failed to create new note with title: '{title}'.", exc_info=True)
            raise e
        
    def update_note_content(self, note_id: int, content: str) -> bool:
        """
        Updates the Content of a Note in the database.
        
        :param note_id: The ID of the Note to update.
        :type note_id: int
        :param content: The new content of the note.
        :type content: str

        :return: Retunrns True if successful, otherwise False.
        :rtype: bool
        """
        query = "UPDATE Notes SET Content = ? WHERE ID = ?;"
        try:
            success = self.db._execute_commit(query, (content, note_id))
            if success:
                logger.info(f"Content updated for note ID: {note_id}.")
            return success
        except DatabaseError as e:
            logger.error(f"Failed to update content for note ID: {note_id}.", exc_info=True)
            raise e
        
    def delete_note(self, note_id: int) -> bool:
        """
        Deletes a note from the database.
        
        :param note_id: The ID of the note to delete.
        :type note_id: int

        :return: Returns True if succesfull, otherwise False
        :rtype: bool
        """
        query = "DELETE FROM Notes WHERE ID = ?;"
        try:
            success = self.db._execute_commit(query, (note_id,))
            if success:
                logger.warning(f"Note deleted: ID={note_id}.")
            return success
        except DatabaseError as e:
            logger.error(f"Failed to delete note ID: {note_id}.", exc_info=True)
            raise e
        
    def update_note_title(self, note_id: int, title: str) -> bool:
        """
        Updates the Note title by Chapter ID.
        
        Called in OutlineManager when renaming a Note Title.
        
        :param chapter_id: The note ID to update its title.
        :type chapter_id: int
        :param title: The new title.
        :param title: str

        :returns: True if successfully update Title, otherwise False
        :rtype: bool
        """
        query = "UPDATE Notes SET Title = ? WHERE ID = ?;"
        try:
            success = self.db._execute_commit(query, (title, note_id))
            if success:
                logger.info(f"Title updated for note ID: {note_id}. New title: '{title}'.")
            return success
        except DatabaseError as e:
            logger.error(f"Failed to update title for note ID: {note_id}.", exc_info=True)
            raise e
        
    def update_note_parent_id(self, note_id: int, new_parent_id: int | None) -> bool:
        """
        Updates the Parent_Note_ID for a specific Lore Entry.

        :param note_id: The ID of the note to update.
        :type note_id: int
        :param new_parent_id: The ID of the new parent note, or None to make it a root.
        :type new_parent_id: int

        :returns: True on success, False otherwise.
        """
        query = """
        UPDATE Notes
        SET Parent_Note_ID = ?
        WHERE ID = ?;
        """
        try:
            success = self.db._execute_commit(query, (new_parent_id, note_id))
            if success:
                logger.info(f"Updated parent ID for note ID: {note_id} to {new_parent_id}.")
            return success
        except DatabaseError as e:
            logger.error(f"Failed to update parent ID for note ID: {note_id} to {new_parent_id}.", exc_info=True)
            raise note_id
        
    def update_note_order(self, note_id: int, sort_order: int) -> bool:
        """
        Updates the Sort Order for a specific Note.

        :param note_id: The ID of the Note to update.
        :type note_id: int
        :param sort_order: The new value for the sort_order
        :type sort_order: int

        :returns: True on success, False otherwise.
        """
        query = """
        UPDATE Notes
        SET Sort_Order = ?
        WHERE ID = ?;
        """
        try:
            success = self.db._execute_commit(query, (sort_order, note_id))
            if success:
                logger.info(f"Updated parent ID for note ID: {note_id} to {sort_order}.")
            return success
        except DatabaseError as e:
            logger.error(f"Failed to update parent ID for note ID: {note_id} to {sort_order}.", exc_info=True)
            raise e
        
    def search_notes(self, user_query: str) -> list[dict] | None:
        """
        Accepts a keyword query and performs a hybrid search:
        1. FTS on Title, Content, and Category (ranked results).
        2. JOIN search on Tag names (unranked results).
        3. Merges and deduplicates the results, prioritizing FTS rank.

        :param user_query: The user's search query.
        :type user_query: str

        :returns: Returns a list of the Notes search results.
        :rtype: list[dict]
        """
        clean_query = user_query.strip()
        if not clean_query:
            return None

        # Wildcard pattern for case-insensitive LIKE Search
        like_pattern = f'%{clean_query}%'

        query = """
        SELECT DISTINCT N.ID, N.Title, N.Parent_Note_ID
        FROM Notes AS N
        LEFT JOIN Note_Tags AS NT ON N.ID = NT.Note_ID
        LEFT JOIN Tags AS T ON NT.Tag_ID = T.ID
        WHERE
            N.Title LIKE ? OR
            N.Content LIKE ? OR
            T.Name LIKE ?
        ORDER BY N.Title ASC;
        """
        params = (like_pattern, like_pattern, like_pattern)
        try:
            results = self.db._execute_query(query, params, fetch_all=True)
            logger.info(f"Note search for '{clean_query}' returned {len(results)} results.")
            return results
        except DatabaseError as e:
            logger.error(f"Failed to execute search for notes with query: '{clean_query}'.", exc_info=True)
            raise e