# src/python/chapter_repository.py

from ..utils.types import ChapterContentDict, ChapterBasicDict
from ..db_connector import DBConnector

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

    def get_all_chapters(self) -> ChapterBasicDict:
        """
        Retrieves a list of all chapters, ordered by their Sort_Order.
        
        The returned data includes basic information necessary for the Outline 
        Manager, but excludes the full text content.

        :returns: A list of dictionaries, each containing the chapter's ID, Title, 
                  Sort_Order, and Precursor_Chapter_ID.
        :rtype: :py:class:`~app.utils.types.ChapterBasicDict`
        """
        query = """
        SELECT ID, Title, Sort_Order, Precursor_Chapter_ID
        FROM Chapters
        ORDER BY Sort_Order ASC;
        """
        return self.db._execute_query(query, fetch_all=True)

    def get_all_chapters_with_content(self) -> ChapterContentDict:
        """
        Retrieves all chapters with their full text content, ordered by Sort_Order.

        :rtype: :py:class:`~app.utils.types.ChapterContentDict`
        """
        query = """
        SELECT ID, Title, Text_Content, Sort_Order, Precursor_Chapter_ID
        FROM Chapters
        ORDER BY Sort_Order ASC;
        """
        return self.db._execute_query(query, fetch_all=True)
    
    def get_chapter_content(self, chapter_id: int) -> str | None:
        """
        Retrieves the rich text content for a specific chapter ID
        
        Gathers only the text content of a chapter.

        :param chapter_id: The chapted ID to get text content from.
        :type chapter_id: int

        :returns: Returns a str of the text content if successful, otherwise None
        :rtype: str or None
        
        """
        query = "SELECT Text_Content FROM Chapters WHERE ID = ?;"
        result = self.db._execute_query(query, (chapter_id,), fetch_one=True)
        return result['Text_Content'] if result else None
    
    def get_content_by_title(self, title: str) -> dict | None:
        """
        Retrieves full content for a chapter based on its title.
        
        :param title: The title of the chapter to get content for.
        :type title: str

        :returns: A dictionary of the chapter.
        :rtype dict or None
        """
        query = "SELECT ID, Title, Text_Content FROM CHAPTERS WHERE Title = ? COLLATE NOCASE;"
        return self.db._execute_query(query, (title,), fetch_one=True)

    def create_chapter(self, title: str, sort_order: int, precursor_id: int | None = None) -> int | None:
        """
        Inserts a new chapter record into the database with a default empty content field.

        :param title: The title of the new chapter.
        :type title: str
        :param sort_order: The ordering integer for the chapter within the story structure.
        :type sort_order: int
        :param precursor_id: The ID of the chapter immediately preceding this one, or None.
        :type precursor_id: int or None
        
        :returns: The ID of the newly created chapter if successful, otherwise None.
        :rtype: int or None
        """
        query = """
        INSERT INTO Chapters (Title, Text_Content, Sort_Order, Precursor_Chapter_ID)
        VALUES (?, ?, ?, ?);
        """
        chapter_id = self.db._execute_commit(
            query, (title, "<p></p>", sort_order, precursor_id), fetch_id=True
        )
        return chapter_id
    
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
        return self.db._execute_commit(query, (content, chapter_id))
    
    def delete_chapter(self, chapter_id: int) -> bool:
        """
        Deletes a chapter and cascades deletion of associated tags
        
        :param chapteR_id: The chapter ID of the chapter to be deleted.
        :type chapter_id: int

        :returns: True if successfully delete chapter, otherwise False
        :rtype: bool
        """
        query = "DELETE FROM Chapters WHERE ID = ?;"
        return self.db._execute_commit(query, (chapter_id,))
    
    def get_chapter_title(self, chapter_id: int) -> str | None:
        """
        Retrieves the chapter title by Chapter ID from the database.
        
        :param chapter_id; The ID of the chapter you want the title from.
        :type chapter_id: int

        :returns: The chapter title if found, otherwise False
        :rtype: str or None
        """
        query = "SELECT Title FROM Chapters WHERE ID = ?;"
        result = self.db._execute_query(query, (chapter_id,), fetch_one=True)
        return result['Title'] if result else None

    def update_chapter_title(self, chapter_id: int, title: str) -> bool:
        """
        Updates the Chapter title by Chapter ID.
        
        :param chapter_id: The chapter ID to update its title.
        :type chapter_id: int
        :param title: The new title to be as Chapter Title.
        :param title: str

        :returns: True if successfully update Title otherwise False
        :rtype: bool
        """
        query = "UPDATE Chapters SET Title = ? WHERE ID = ?;"
        return self.db._execute_commit(query, (title, chapter_id))
    
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

        # 1. Modify the query if specific IDs are requested
        if chapter_ids is not None and chapter_ids:
            # Ensure IDs are unique and sorted for consistent query execution
            unique_ids = sorted(list(set(chapter_ids))) 
            
            # Create placeholders for the IN clause (e.g., ?, ?, ?)
            placeholders = ', '.join(['?'] * len(unique_ids))
            
            query += f" WHERE ID IN ({placeholders})"
            # The IDs become the parameters for the query
            params = tuple(unique_ids)

        # 2. Add final ordering clause
        query += " ORDER BY Sort_Order ASC;"

        # 3. Execute the query using the DBConnector helper method
        results = self.db._execute_query(query, params, fetch_all=True)

        return results if results else []
    
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
        return self.db._execute_transaction(operations)