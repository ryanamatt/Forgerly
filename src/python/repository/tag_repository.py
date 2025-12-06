# src/python/tag_repository.py

from ..utils.types import TagTuple, TagTupleList
from ..db_connector import DBConnector

class TagRepository:
    """
    Manages all database operations for the Tag entity and its associations
    with other entities (e.g., Chapters, Lore).

    This class serves as the Data Access Object (DAO) for Tags, handling CRUD operations and 
    ensuring data integrity specific to Tags. It uses the provided 
    :py:class:`~app.db_connector.DBConnector` to execute queries.
    """
    def __init__(self, db_connector: DBConnector) -> None:
        """
        Initializes the :py:class:`.TagRepository`.

        :param db_connector: The active connection object to the SQLite database.
        :type db_connector: :py:class:`~app.db_connector.DBConnector`
        
        :rtype: None
        """
        self.db = db_connector

    def _normalize_tag_name(self, tag_name: str) -> str:
        """
        Utility to ensure tags are stored consistently (lowercase, no extra space).
        
        :param tag_name: The name of the tag to normalize.
        :type tag_name: str

        :returns: Returns the normalized tag name.
        :rtype: str
        """
        return tag_name.strip().lower()
    
    def _get_tag_id_by_name(self, tag_name: str) -> int | None:
        """
        Internal method to look up a Tag's ID.
        
        :param tag_name: THe name of the tag to find the tags ID.
        :type tag_name: str

        :returns: The ID of the tag if found otherwise None.
        :rtype: int or None
        """
        clean_name = self._normalize_tag_name(tag_name)
        query = "SELECT ID FROM Tags WHERE Name = ?;"
        result = self.db._execute_query(query, (clean_name,), fetch_one=True)
        return result['ID'] if result else None
    
    def _create_tag(self, tag_name: str) -> int | None:
        """
        Creates a new tag it doesn't exist
        
        :param tag_name: The name of the tag to create.
        :type tag_name: str

        :returns: The newly created tag's ID or None if failed to create Tag.
        :rtype: int or None
        """
        tag_id = self._get_tag_id_by_name(tag_name)
        if tag_id:
            return tag_id
        
        clean_name = self._normalize_tag_name(tag_name)
        query = "INSERT INTO Tags (Name) VALUES (?);"
        return self.db._execute_commit(query, (clean_name,), fetch_id=True)
    
    # --- Chapter Tag Methods ---

    def get_tags_for_chapter(self, chapter_id: int) -> TagTupleList:
        """
        Retrieves all tags (ID, Name) for a given chapter
        
        :param chapter_id: The ID of the chapter Entity to get all tags for.
        :type chapter_id: int

        :returns: A list of tuples (ID, Name) containining all tags for a chapter.
        :rtype: :py:class:`~app.utils.types.TagTupleList`
        """
        query = """
        SELECT t.ID, t.Name
        FROM Tags t
        JOIN Chapter_Tags ct ON t.ID = ct.Tag_ID
        WHERE ct.Chapter_ID = ?
        ORDER BY t.Name ASC;
        """
        return self.db._execute_query(query, (chapter_id,), fetch_all=True, as_list=True)
    
    def set_tags_for_chapter(self, chapter_id: int, tag_names: list[str]) -> bool:
        """
        Replaces all tags for a chapter with the new list.
        Performs transactions to ensure atomicity.

        :param chapter_id: The ID of the Chapter Entity to set tags to.
        :type chapter_id: int
        :param tag_names: A list of all the tags to set for the chapter.
        :type tag_names: list[str]

        :returns: True if successfully set the tags otherwise False.
        :rtype: bool
        """
        operations = []
        
        delete_query = "DELETE FROM Chapter_Tags WHERE Chapter_ID = ?;"
        operations.append((delete_query, (chapter_id,)))

        for tag_name in tag_names:
            tag_id = self._create_tag(tag_name)
            if tag_id is not None:
                insert_query = "INSERT OR IGNORE INTO Chapter_Tags (Chapter_ID, Tag_ID) VALUES (?, ?)"
                operations.append((insert_query, (chapter_id, tag_id)))
        
        return self.db._execute_transaction(operations)
        
    # --- Tags for Lore ---
    def get_tags_for_lore_entry(self, lore_id: int) -> TagTupleList:
        """"
        Retrieves all tags (ID, Name) for a given lore entry.
        
        :param lore_id: The ID of the lore entry Entity to get all tags for.
        :type lore_id: int

        :returns: A list of tuples (ID, Name) containining all tags for a lore entry.
        :rtype: :py:class:`~app.utils.types.TagTupleList`
        """
        query = """
        SELECT t.ID, t.Name
        FROM Tags t
        JOIN Lore_Tags lt ON t.ID = lt.Tag_ID
        WHERE lt.Lore_ID = ?
        ORDER BY t.Name ASC;
        """
        return self.db._execute_query(query, (lore_id,), fetch_all=True, as_list=True)
    
    def set_tags_for_lore_entry(self, lore_id: int, tag_names: list[str]) -> bool:
        """
        Replaces all tags for a lore entry with the new list.
        Performs transactions to ensure atomicity.

        :param lore_id: The ID of the lore entry Entity to set tags to.
        :type lore_id: int
        :param tag_names: A list of all the tags to set for the lore entry.
        :type tag_names: list[str]

        :returns: True if successfully set the tags otherwise False.
        :rtype: bool
        """
        operations = []

        delete_query = "DELETE FROM Lore_Tags WHERE Lore_ID = ?"
        operations.append((delete_query, (lore_id,)))

        for tag_name in tag_names:
            tag_id = self._create_tag(tag_name)
            if tag_id is not None:
                insert_query = "INSERT OR IGNORE INTO Lore_Tags (Lore_ID, Tag_ID) VALUES (?, ?)"
                operations.append((insert_query, (lore_id, tag_id)))
        
        return self.db._execute_transaction(operations)