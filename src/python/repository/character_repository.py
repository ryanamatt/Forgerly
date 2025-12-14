# src/python/repository/character_repository

from ..utils.types import DBRowList, CharacterDetailsDict, CharacterBasicDict
from ..db_connector import DBConnector
from ..utils.logger import get_logger
from ..utils.exceptions import DatabaseError

logger = get_logger(__name__)

class CharacterRepository:
    """
    Manages all database operations for the Character entity.

    This class serves as the Data Access Object (DAO) for Character, handling 
    CRUD operations and ensuring data integrity specific to characters (e.g., sort order).
    It uses the provided :py:class:`~app.db_connector.DBConnector` to execute queries.
    """
    def __init__(self, db_connector: DBConnector) -> None:
        """
        Initializes the :py:class:`.CharacterRepository`.

        :param db_connector: The active connection object to the SQLite database.
        :type db_connector: :py:class:`~app.db_connector.DBConnector`
        
        :rtype: None
        """
        self.db = db_connector
        logger.debug("CharacterRepository initialized.")

    def get_all_characters(self) -> DBRowList | None:
        """"
        Retrieves a list of all characters, ordered by their Name in ascending order.
        
        The returned data includes basic information necessary for the Outline 
        Manager, but excludes the full text content.

        :returns: A list of dictionaries, each containing the character's ID, Name, 
            Description, and Status.
        :rtype: :py:class:`~app.utils.types.DBRowList`
        """
        query = "SELECT ID, Name FROM Characters ORDER BY Name ASC;"
        try:
            results = self.db._execute_query(query, fetch_all=True)
            logger.info(f"Retrieved {len(results)} basic character records.")
            return results
        except DatabaseError as e:
            logger.error("Failed to retrieve all characters.", exc_info=True)
            raise e
    
    def get_character_details(self, char_id: int) -> CharacterDetailsDict:
        """
        Retrieves the full details of a character (Name, Description, Status) for a specific ID.

        :param char_id: The character id to get details for.
        :type char_id: int

        :returns a dictionary of the Character's details.
        :rtype: :py:class:`~app.utils.types.CharacterDetailsDict`
        """
        query = """
        SELECT ID, Name, Description, Status
        FROM Characters
        WHERE ID = ?;
        """
        try:
            details = self.db._execute_query(query, (char_id,), fetch_one=True)
            logger.debug(f"Retrieved details for character ID: {char_id}. Found: {details is not None}")
            return details
        except DatabaseError as e:
            logger.error(f"Failed to retrieve details for character ID: {char_id}.", exc_info=True)
            raise e
    
    def get_character_name(self, char_id) -> str | None:
        """
        Retrieves the character title by Character ID from the database.
        
        :param char_id; The ID of the character you want the title from.
        :type char_id: int

        :returns: The character title if found, otherwise False
        :rtype: str or None
        """
        query = "SELECT Name FROM Characters WHERE ID = ?"
        try:
            result = self.db._execute_query(query, (char_id,), fetch_one=True)
            name = result['Name'] if result else None
            logger.debug(f"Retrieved name for character ID: {char_id}. Name: {name}")
            return name
        except DatabaseError as e:
            logger.error(f"Failed to retrieve name for character ID: {char_id}.", exc_info=True)
            raise e
    
    def get_content_by_name(self, name: str) -> dict | None:
        """
        Retrieves full description for a character based on its title.
        
        :param title: The title of the character to get description for.
        :type title: str

        :returns: A dictionary of the character.
        :rtype: dict or None
        """ 
        search_term = f"%{name.strip()}%"
        query = "SELECT ID, Name, Description FROM Characters WHERE Name Like ? COLLATE NOCASE;"
        search_term = f"%{name.strip()}%"
        query = "SELECT ID, Name, Description FROM Characters WHERE Name Like ? COLLATE NOCASE;"
        try:
            result = self.db._execute_query(query, (search_term,), fetch_one=True)
            logger.debug(f"Retrieved content by name search: '{name}'. Found: {result is not None}")
            return result
        except DatabaseError as e:
            logger.error(f"Failed to retrieve content for character name: '{name}'.", exc_info=True)
            raise e
        
    def get_number_of_characters(self) -> int:
        """
        Retrieves the number of characters in the Datbase.

        Used for Project Statistics

        :returns: The number of characters.
        :rtype: int
        """
        query = "SELECT COUNT(*) FROM Characters;"
        try:
            result = self.db._execute_query(query, fetch_all=True)
            try:
                count = result[0]['COUNT(*)']
            except:
                count = 0

            return count
        
        except DatabaseError as e:
            logger.error("Failed to count all chapters.", exc_info=True)
            raise e
    
    def create_character(self, name: str, description: str = "", status: str = "") -> int | None:
        """
        Inserts a new chapter record into the database with a default empty content field.

        :param title: The title of the new chapter.
        :type title: str
        :param description: The description of the character, Defaults to Empty String.
        :type status: str
        :param status: The status of the character (Dead, Alive, etc.), Defaults to Empty String
        :type status: str
        
        :returns: The ID of the newly created chapter if successful, otherwise None.
        :rtype: int or None
        """
        query = "INSERT INTO Characters (Name, Description, Status) VALUES (?, ?, ?);"
        try:
            char_id = self.db._execute_commit(query, (name, description, status), fetch_id=True)
            if char_id:
                logger.info(f"Created new character: ID={char_id}, Name='{name}'.")
            return char_id
        except DatabaseError as e:
            logger.error(f"Failed to create new character with name: '{name}'.", exc_info=True)
            raise e
    
    def update_character(self, char_id: int, name: str, description: str = "", status: str = "") -> bool:
        """
        Updates the Character details in the database.

        :param char_id: The character ID to know which character to update.
        :type char_id: int
        :param name: The name of the character.
        :type name: str
        :param description: The description of the character. Defaults to Empty String
        :type description: str
        :param status: The status of the character. Defaults to Empty String.
        :type status: str

        :returns: True if successfully saved to dataase, otherwise False.
        :rtype: bool
        """
        query = """
        UPDATE Characters SET Name = ?, Description = ?, Status = ?
        WHERE ID = ?;
        """
        try:
            success = self.db._execute_commit(query, (name, description, status, char_id))
            if success:
                logger.info(f"Updated character ID: {char_id}. New Name: '{name}'.")
            return success
        except DatabaseError as e:
            logger.error(f"Failed to update character ID: {char_id} with name '{name}'.", exc_info=True)
            raise e

    def delete_character(self, char_id) -> bool:
        """
        Deletes a character
        
        :param char_id: The character ID of the character to be deleted.
        :type char_id: int

        :returns: True if successfully delete character, otherwise False
        :rtype: bool
        """
        query = "DELETE FROM Characters WHERE ID = ?;"
        try:
            success = self.db._execute_commit(query, (char_id,))
            if success:
                logger.warning(f"Character deleted: ID={char_id}.")
            return success
        except DatabaseError as e:
            logger.error(f"Failed to delete character ID: {char_id}.", exc_info=True)
            raise e
    
    def search_characters(self, user_query: str) -> CharacterBasicDict | None:
        """
        Accepts a keyword query and performs a hybrid search:
        1. Search on Name, Status (ranked results).
        2. Merges and deduplicates the results, prioritizing FTS rank.

        :param user_query: The users search query.
        :type user_query: str

        :returns: A dictionary is found something in search otherwise None
        :rtype: :py:class:`~app.utils.types.CharacterBasicDict`
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
        try:
            results = self.db._execute_query(query, params, fetch_all=True)
            logger.info(f"Character search for '{clean_query}' returned {len(results)} results.")
            return results
        except DatabaseError as e:
            logger.error(f"Failed to execute search for characters with query: '{clean_query}'.", exc_info=True)
            raise e
    
    def get_all_characters_for_export(self, character_ids: list[int] = []) -> CharacterDetailsDict:
        """
        Retrieves characters details for export purposes,
        optionally filtered by a list of IDs.

        :param character_ids: A list of all the character IDs selected. Defaults
            to Empty List which means all Character IDS are selected.

        :returns: A dictionary of all the characters selected by ID.
        :rtype: :py:class:`~app.utils.types.CharacterDetailsDict`
        """
        query = """
        SELECT ID, Name, Description, Status, Age, Date_Of_Birth, Pronouns,
        Sexual_Orientation, Gender_Identity, Ethnicity_Background, Occupation_School,
        Physical_Description
        FROM Characters
        """
        params = ()

        # Modify the query if specific IDs are requested
        if character_ids is not None and character_ids:
            # Ensure IDs are unique and sorted for consistent query execution
            unique_ids = sorted(list(set(character_ids))) 
            
            # Create placeholders for the IN clause (e.g., ?, ?, ?)
            placeholders = ', '.join(['?'] * len(unique_ids))
            
            query += f" WHERE ID IN ({placeholders})"
            params = tuple(unique_ids)

        # Add final ordering clause
        query += " ORDER BY Name ASC;"

        try:
            results = self.db._execute_query(query, params, fetch_all=True)
            if character_ids:
                logger.info(f"Retrieved {len(results)} characters for export from a list of {len(character_ids)} IDs.")
            else:
                logger.info(f"Retrieved all {len(results)} characters for export.")
            return results if results else []
        except DatabaseError as e:
            logger.error("Failed to retrieve characters for export.", exc_info=True)
            raise e