# src/python/chapter_repository.py

from ..utils.types import ChapterContentDict, ChapterBasicDict
from ..utils.text_stats import calculate_word_count, calculate_character_count
from ..utils.logger import get_logger
from ..utils.exceptions import DatabaseError
from ..db_connector import DBConnector

logger = get_logger(__name__)

class ChapterRepository:
    """
    Manages all database operations for the Chapter entity.

    This class serves as the Data Access Object (DAO) for chapters, handling 
    CRUD operations and ensuring data integrity specific to chapters (e.g., sort order).
    It uses the provided :py:class:`~app.db_connector.DBConnector` to execute queries.
    """
    def __init__(self, db_connector: DBConnector) -> None:
        """
        Initializes the :py:class:`.ChapterRepository`.

        :param db_connector: The active connection object to the SQLite database.
        :type db_connector: :py:class:`~app.db_connector.DBConnector`
        
        :rtype: None
        """
        self.db = db_connector
        logger.debug("ChapterRepository initialized.")

    def get_all_chapters(self) -> ChapterBasicDict:
        """
        Retrieves a list of all chapters, ordered by their Sort_Order.
        
        The returned data includes basic information necessary for the Outline 
        Manager, but excludes the full text content.

        :returns: A list of dictionaries, each containing the chapter's ID, Title, 
                  Sort_Order.
        :rtype: :py:class:`~app.utils.types.ChapterBasicDict`
        """
        query = """
        SELECT ID, Title, Sort_Order
        FROM Chapters
        ORDER BY Sort_Order ASC;
        """
        try:
            results = self.db._execute_query(query, fetch_all=True)
            logger.info(f"Retrieved {len(results)} basic chapter records.")
            return results
        except DatabaseError as e:
            logger.error("Failed to retrieve all basic chapters.", exc_info=True)
            raise e
    
    def get_chapter_content(self, chapter_id: int) -> str | None:
        """
        Retrieves the rich text content for a specific chapter ID
        
        Gathers only the text content of a chapter.

        :param chapter_id: The chapter ID to get text content from.
        :type chapter_id: int

        :returns: Returns a str of the text content if successful, otherwise None
        :rtype: str or None
        """
        query = "SELECT Text_Content FROM Chapters WHERE ID = ?;"
        try:
            result = self.db._execute_query(query, (chapter_id,), fetch_one=True)
            content = result['Text_Content'] if result else None
            logger.debug(f"Retrieved content for chapter ID: {chapter_id}. Found: {content is not None}")
            return content
        except DatabaseError as e:
            logger.error(f"Failed to retrieve content for chapter ID: {chapter_id}.", exc_info=True)
            raise e
        
    def get_chapter_title(self, chapter_id: int) -> str | None:
        """
        Retrieves the chapter title by Chapter ID from the database.

        Used when a Chaper Item is renamed in the OutlineManager.
        
        :param chapter_id; The ID of the chapter you want the title from.
        :type chapter_id: int

        :returns: The chapter title if found, otherwise None
        :rtype: str or None
        """
        query = "SELECT Title FROM Chapters WHERE ID = ?;"
        try:
            result = self.db._execute_query(query, (chapter_id,), fetch_one=True)
            title = result['Title'] if result else None
            logger.debug(f"Retrieved title for chapter ID: {chapter_id}. Title: {title}")
            return title
        except DatabaseError as e:
            logger.error(f"Failed to retrieve title for chapter ID: {chapter_id}.", exc_info=True)
            raise e
        
    def get_all_chapters_for_export(self, chapter_ids: list[int] = None) -> list[dict]:
        """
        Retrieves chapter details (ID, Title, Content, Sort_Order) for export purposes,
        optionally filtered by a list of IDs.

        :param chapter_ids: A list of all the chapters ID that wish to be exported. Default
            is None which results in all chapters..
        :type chapter_ids: list[int]

        :returns: A list containing all Chapter dicts.
        :rtype: list[dict]
        """
        query = """
        SELECT ID, Title, Text_Content, Sort_Order
        FROM Chapters
        """
        params = ()

        # Modify the query if specific IDs are requested
        if chapter_ids is not None and chapter_ids:
            # Ensure IDs are unique and sorted for consistent query execution
            unique_ids = sorted(list(set(chapter_ids)))

            # Create placeholders for the IN clause (e.g., ?, ?, ?)
            placeholders = ', '.join(['?'] * len(unique_ids))

            query += f" WHERE ID IN ({placeholders})"
            params = tuple(unique_ids)

        # Add final ordering clause
        query += " ORDER BY Sort_Order ASC;"

        # Execute the query using the DBConnector helper method
        try:
            results = self.db._execute_query(query, params, fetch_all=True)
            if chapter_ids:
                logger.info(f"Retrieved {len(results)} chapters for export from a list of " 
                            "{len(chapter_ids)} IDs.")
            else:
                logger.info(f"Retrieved all {len(results)} chapters for export.")
            return results if results else []
        except DatabaseError as e:
            logger.error("Failed to retrieve chapters for export.", exc_info=True)
            raise e
        
    def _get_all_chapters_with_content(self) -> dict:
        """
        Retrieves all chapters with their full text content, ordered by Sort_Order.

        An Internal helper method for get_all_chapters_stats.

        :rtype: dict
        """
        query = """
        SELECT ID, Title, Text_Content, Sort_Order
        FROM Chapters
        ORDER BY Sort_Order ASC;
        """
        try:
            results = self.db._execute_query(query, fetch_all=True)
            logger.info(f"Retrieved {len(results)} chapters with full content.")
            return results
        except DatabaseError as e:
            logger.error("Failed to retrieve all chapters with content.", exc_info=True)
            raise e
        
    def get_all_chapters_stats(self, wpm: int = 250) -> list[dict]:
        """
        Retrieves all chapters with their full text content, calculates
        word count, character count, and estimated read time for each.

        :param wpm: Words per minute for read time calculation. Default is 250.
        :type wpm: int
        
        :returns: A list of dictionaries, each containing chapter basic info
                  and the calculated statistics.
        :rtype: list[dict]
        """
        all_chapters = self._get_all_chapters_with_content() # Efficiently gets all rows

        chapters_with_stats = []
        for chapter in all_chapters:
            text_content = chapter['Text_Content'] or "" # Handle potential None content
            
            # 1. Calculate Statistics
            word_count = calculate_word_count(text_content)
            char_count = calculate_character_count(text_content, include_spaces=False)

            # 2. Compile the results
            stats_dict = {
                'word_count': word_count,
                'char_count_no_spaces': char_count,
            }
            chapters_with_stats.append(stats_dict)

        logger.info(f"Calculated statistics for {len(chapters_with_stats)} chapters.")
        return chapters_with_stats

    def create_chapter(self, title: str, sort_order, text_content: str = "<p></p>", 
                       pov_character_id: int | None = None) -> int | None:
        """
        Inserts a new chapter record into the database with a default empty content field.

        :param title: The title of the new chapter.
        :type title: str
        :param sort_order: The ordering integer for the chapter within the story structure.
        :type sort_order: int
        :param text_content: The text content of the chapter. Default. '<p></p>'.
        :type text_content: str
        :param pov_character_id: The POV Characters ID
        :type pov_character_id: int
        
        :returns: The ID of the newly created chapter if successful, otherwise None.
        :rtype: int or None
        """
        query = """
        INSERT INTO Chapters (Title, Text_Content, Sort_Order, POV_Character_ID)
        VALUES (?, ?, ?, ?);
        """
        try:
            chapter_id = self.db._execute_commit(
                query, (title, text_content, sort_order, pov_character_id), fetch_id=True
            )
            if chapter_id:
                logger.info(f"Created new chapter: ID={chapter_id}, Title='{title}', SortOrder={sort_order}.")
            return chapter_id
        except DatabaseError as e:
            logger.error(f"Failed to create new chapter with title: '{title}'.", exc_info=True)
            raise e
    
    def update_chapter_content(self, chapter_id: int, content: str) -> bool:
        """
        Updates the rich text content for a chapter given the Chapter ID.
        
        :param chapter_id: The chapted ID to updaes its content.
        :type chapted_id: int
        :param content: The new content to set as Chapter's content.
        :type content: str

        :returns: True if successfully set update content otherwise False
        :rtype: bool
        """
        query = "UPDATE Chapters SET Text_Content = ? WHERE ID = ?;"
        try:
            success = self.db._execute_commit(query, (content, chapter_id))
            if success:
                logger.info(f"Content updated for chapter ID: {chapter_id}.")
            return success
        except DatabaseError as e:
            logger.error(f"Failed to update content for chapter ID: {chapter_id}.", exc_info=True)
            raise e
    
    def delete_chapter(self, chapter_id: int) -> bool:
        """
        Deletes a chapter and cascades deletion of associated tags
        
        :param chapteR_id: The chapter ID of the chapter to be deleted.
        :type chapter_id: int

        :returns: True if successfully delete chapter, otherwise False
        :rtype: bool
        """
        query = "DELETE FROM Chapters WHERE ID = ?;"
        try:
            success = self.db._execute_commit(query, (chapter_id,))
            if success:
                logger.warning(f"Chapter deleted: ID={chapter_id}.")
            return success
        except DatabaseError as e:
            logger.error(f"Failed to delete chapter ID: {chapter_id}.", exc_info=True)
            raise e

    def update_chapter_title(self, chapter_id: int, title: str) -> bool:
        """
        Updates the Chapter title by Chapter ID.
        
        Called in OutlineManager when renaming a Chapter Title.
        
        :param chapter_id: The chapter ID to update its title.
        :type chapter_id: int
        :param title: The new title to be as Chapter Title.
        :param title: str

        :returns: True if successfully update Title otherwise False
        :rtype: bool
        """
        query = "UPDATE Chapters SET Title = ? WHERE ID = ?;"
        try:
            success = self.db._execute_commit(query, (title, chapter_id))
            if success:
                logger.info(f"Title updated for chapter ID: {chapter_id}. New title: '{title}'.")
            return success
        except DatabaseError as e:
            logger.error(f"Failed to update title for chapter ID: {chapter_id}.", exc_info=True)
            raise e
    
    def reorder_chapters(self, chapter_updates: list[tuple[int, int]]) -> bool:
        """
        Updates the Sort_Order for multiple chapters in a single, atomic transaction.

        :param chapter_updates: A list of tuples, where each tuple is
                             (chapter_id, new_sort_order).
        :type chapter_updates: list[tuple[int, int]]

        :returns: True if all updates succeed and the transaction commits, False otherwise.
        :rtype: bool
        """
        query = "UPDATE Chapters SET Sort_Order = ? WHERE ID = ?;"
        
        # Each operation is a tuple: (sql_query_string, parameters_tuple)
        operations = []
        for chapter_id, new_sort_order in chapter_updates:
            # parameters are (new_sort_order, chapter_id) to match the SQL template
            operations.append((query, (new_sort_order, chapter_id)))

        # Execute all operations in a single transaction
        try:
            success = self.db._execute_transaction(operations)
            if success:
                logger.info(f"Successfully reordered {len(operations)} chapters.")
            return success
        except DatabaseError as e:
            logger.error(f"Failed to reorder chapters. Attempted updates: {chapter_updates}.", exc_info=True)
            raise e