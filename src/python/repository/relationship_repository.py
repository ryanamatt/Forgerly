# src/python/repository/relationship_repository.py

from ..utils.types import DBRow, DBRowList
from ..db_connector import DBConnector
from ..utils.logger import get_logger
from ..utils.exceptions import DatabaseError

logger = get_logger(__name__)

class RelationshipRepository:
    """
    Manages all database operations for the Character_Relationship, Relationship_Types, 
    and Character_Node_Positions entities.

    This class serves as the Data Access Object (DAO) for Character_Relationship, 
    Relationship_Types, and Character_Node_Positions, handling CRUD operations and 
    ensuring data integrity specific to Relationship. It uses the provided 
    :py:class:`~app.db_connector.DBConnector` to execute queries.
    """

    def __init__(self, db_connector: DBConnector) -> None:
        """
        Initializes the :py:class:`.RelationshipRepository`.

        :param db_connector: The active connection object to the SQLite database.
        :type db_connector: :py:class:`~app.db_connector.DBConnector`
        
        :rtype: None
        """
        self.db = db_connector
        logger.debug("RelationshipRepository initialized.")

    # =========================================================================
    # Character Relationships (Edges)
    # =========================================================================

    def get_all_relationships_for_graph(self) -> DBRowList:
        """
        Retrieves all character relationships, joining with Characters and
        Relationship_Types tables to get all necessary node/edge data.

        :returns: Returns a list of dictionaries, where each dict represents an edge.
        :rtype: :py:class:`~app.utils.types.DBRowList`
        """
        query = """
        SELECT
            CR.ID AS Relationship_ID,
            CR.Character_A_ID,
            CA.Name AS Character_A_Name,
            CR.Character_B_ID,
            CB.Name AS Character_B_Name,
            CR.Description,
            CR.Intensity,
            CR.Lore_ID,
            CR.Start_Chapter_ID,
            CR.End_Chapter_ID,
            RT.ID AS Type_ID,
            RT.Type_Name,
            RT.Short_Label,
            RT.Default_Color,
            RT.Is_Directed,
            RT.Line_Style
        FROM Character_Relationships CR
        JOIN Characters CA ON CR.Character_A_ID = CA.ID
        JOIN Characters CB ON CR.Character_B_ID = CB.ID
        JOIN Relationship_Types RT ON CR.Type_ID = RT.ID;
        """
        try:
            results = self.db._execute_query(query, fetch_all=True)
            logger.info(f"Retrieved {len(results)} character relationships for the graph.")
            return results
        except DatabaseError as e:
            logger.error("Failed to retrieve all character relationships for graph.", exc_info=True)
            raise e
        
    def get_relationship_details(self, rel_id: int) -> dict:
        """
        Gets the Details of a relationship from the database based on ID.
        
        :param rel_id: The ID of the relationship.
        :type rel_id: int

        :returns: Dict of all the Relationship Data.
        :rtype dict:
        """
        query = "SELECT * FROM Character_Relationships WHERE ID = ?"
        try:
            rel_data = self.db._execute_query(query, (rel_id,), fetch_one=True)
            if rel_data:
                logger.info(f"Got details for Relationship: ID={rel_id}.")
            return rel_data
        except DatabaseError as e:
            logger.error(f"Failed to get details for relationship with ID {rel_id}.", exc_info=True)
            raise e
    
    def create_relationship(self, char_a_id: int, char_b_id: int, type_id: int, lore_id: int | None = None,
                            description: str = "", intensity: int = 5, start_chapter_id: int | None = None, 
                            end_chapter_id: int | None = None) -> int | None:
        """
        Creates a new character relationship using the Relationship Type ID and returns its ID.

        :param char_a_id: The first character ID in the relationship.
        :type char_a_id: int
        :param char_b_id: The first character ID in the relationship.
        :type char_b_id: int
        :param type_id: The ID of the Relationship_Type
        :type type_id: int
        :param lore_id: The ID of the Lore Type of the Relationship.
        :type lore_id: int
        :param description: The description of the Relationship, Defaults to an Empty String.
        :type description: str
        :param intensity: The intensity (thickness) of the line connecting the character nodes. Default to 50.
        :type intensity: int
        :param start_chapter_id: The chapter ID that the relationship begins in. Default is None.
        :type start_chapter_id: int or None
        :param end_chapter_id: The chapter ID that the relationships ends in. Default is None.
        :type end_chapter_id: int or None

        :returns: Returns the ID (int) of the created relationship or None if failed to create relationship.
        :rtype: int or None
        """
        query = """
        INSERT OR IGNORE INTO Character_Relationships
        (Character_A_ID, Character_B_ID, Type_ID, Lore_ID, Description, Intensity, Start_Chapter_ID, End_Chapter_ID)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
        params = (char_a_id, char_b_id, type_id, lore_id, description, intensity, start_chapter_id, end_chapter_id)
        try:
            relationship_id = self.db._execute_commit(query, params, fetch_id=True)
            if relationship_id:
                logger.info(f"Created new relationship: ID={relationship_id}, Type_ID={type_id} between Char {char_a_id} and Char {char_b_id}.")
            return relationship_id
        except DatabaseError as e:
            logger.error(f"Failed to create relationship between {char_a_id} and {char_b_id} with Type ID {type_id}.", exc_info=True)
            raise e

    def delete_relationship(self, relationship_id: int) -> bool:
        """
        Deletes a relationship.
        
        :param relationship_id: The relationship ID of the relationship to be deleted.
        :type relationship_id: int

        :returns: True if successfully delete relationship, otherwise False
        :rtype: bool
        """
        query = "DELETE FROM Character_Relationships WHERE ID = ?;"
        try:
            success = self.db._execute_commit(query, (relationship_id,))
            if success:
                logger.info(f"Character relationship deleted: ID={relationship_id}.")
            return success
        except DatabaseError as e:
            logger.error(f"Failed to delete relationship ID: {relationship_id}.", exc_info=True)
            raise e

    def update_relationship_details(self, relationship_id: int, type_id: int, description: str, 
                                    intensity: int, lore_id: int | None = None, start_chapter_id: int | None = None, 
                                    end_chapter_id: int | None = None) -> bool:
        """
        Updates the details of a relationships.
        
        :param relationship_id: The ID of the relationship.
        :type relationship_id: int
        :param type_id: The ID of the relationship type.
        :type type_id: int
        :param description: The description of the relationship.
        :type description: str
        :param intensity: The intensity of the relationship.
        :type intensity: int
                :param lore_id: The ID of the Lore Type of the Relationship.
        :type lore_id: int
        :param start_chapter_id: The chapter ID that the relationship begins in. Default is None.
        :type start_chapter_id: int or None
        :param end_chapter_id: The chapter ID that the relationships ends in. Default is None.
        :type end_chapter_id: int or None
        """

        query = """
        UPDATE Character_Relationships SET
            Type_ID = ?,
            Description = ?,
            Intensity = ?,
            Lore_ID = ?,
            Start_Chapter_ID = ?,
            End_Chapter_ID = ?
        WHERE ID = ?;
        """
        params = (type_id, description, intensity, lore_id, start_chapter_id, end_chapter_id, relationship_id)
        try:
            success = self.db._execute_commit(query, params)
            if success:
                logger.info(f"Character relationship details updated: ID={relationship_id}.")
            return success

        except DatabaseError as e:
            logger.error(f"Failed to update relationship details, ID: {relationship_id}.", exc_info=True)
            raise e
         

    # =========================================================================
    # Character Node Positions and UI Attributes
    # =========================================================================

    def get_all_node_positions(self) -> DBRowList:
        """
        Retrieves the saved X/Y positions and visual attributes (Color, Shape, Hidden)
        for all characters that have been placed in the graph view.

        :returns: A list of all the node positions.
        :rtype: :py:class:`~app.utils.types.DBRowList`
        """
        query = """
        SELECT
            Character_ID,
            X_Position,
            Y_Position,
            Node_Color,
            Node_Shape,
            Is_Hidden,
            Is_Locked
        FROM Character_Node_Positions;
        """
        try:
            results = self.db._execute_query(query, fetch_all=True)
            logger.debug(f"Retrieved {len(results)} node positions.")
            return results
        except DatabaseError as e:
            logger.error("Failed to retrieve all character node positions.", exc_info=True)
            raise e

    def save_node_attributes(self, character_id: int, x_pos: float, y_pos: float, 
                           node_color: str, node_shape: str, is_hidden: int, is_locked: int) -> bool:
        """
        Saves or updates the position and visual attributes of a character node.
        Uses INSERT OR REPLACE to handle both creation and updates efficiently.

        :param character_id: The character ID of the node attribute.
        :type character_id: int
        :param x_pos: The X position of the node on the graph.
        :type x_pos: float
        :param y_pos: The Y position of the node on the graph.
        :type y_pos: float
        :param node_color: The hex color of the node. Include leading #.
        :type node_color: str
        :param node_shape: The shape of the node (Circle, Square, Diamond).
        :type node_shape: str
        :param is_hidden: Parameter toggles if the node is hidden or not (1 for True, 0 for False)
        :type is_hidden: int
        :param is_locked: Parameter toggles if the node is locked in place or not (1 for True 0 for False)
        :type is_locked: int

        :returns: Returns True if successfully saved/updated the node attributes, otherwise False.
        :rtype: bool
        """
        query = """
        INSERT OR REPLACE INTO Character_Node_Positions
        (Character_ID, X_Position, Y_Position, Node_Color, Node_Shape, Is_Hidden, Is_Locked)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        params = (character_id, x_pos, y_pos, node_color, node_shape, is_hidden, is_locked)
        try:
            success = self.db._execute_commit(query, params)
            if success:
                logger.info(f"Successfully saved node attributes, Char_ID: {character_id}")
            return success
        except DatabaseError as e:
            logger.warning("Failed to save character node attributes", exc_info=True)
            raise e
        
    def update_node_is_hidden(self, char_id: int, is_hidden: int) -> bool:
        """
        Updates the is_hidden table attribute of a character node.
        
        :param char_id: The ID of the character node.
        :type char_id: int
        :param is_hidden: The new value of is_hidden attribute.
        :type is_hidden: int
        :return: True if successful otherwise False.
        :rtype: bool
        """
        query = """
        UPDATE Character_Node_Positions SET Is_Hidden = ? WHERE Character_ID = ?;
        """
        params = (is_hidden, char_id)
        try:
            success = self.db._execute_commit(query, params)
            if success:
                logger.info(f"Successfully saved new is_hidden attribute, Char_ID: {char_id}")
            return success
        except DatabaseError as e:
            logger.warning("Failed to save character node new is_hidden attribute", exc_info=True)
            raise e
        
    def update_node_is_locked(self, char_id: int, is_locked: int) -> bool:
        """
        Updates the is_hidden table attribute of a character node.
        
        :param char_id: The ID of the character node.
        :type char_id: int
        :param is_locked: The new value of is_locked attribute.
        :type is_locked: int
        :return: True if successful otherwise False.
        :rtype: bool
        """
        query = """
        UPDATE Character_Node_Positions SET Is_Locked = ? WHERE Character_ID = ?;
        """
        params = (is_locked, char_id)
        try:
            success = self.db._execute_commit(query, params)
            if success:
                logger.info(f"Successfully saved new is_locked attribute, Char_ID: {char_id}")
            return success
        except DatabaseError as e:
            logger.warning("Failed to save character node new is_locked attribute", exc_info=True)
            raise e
    
    # =========================================================================
    # Relationship Types (Configuration)
    # =========================================================================

    def get_all_relationship_types(self) -> DBRowList:
        """
        Retrieves all defined relationship types for use in UI/Graph config
        
        :returns: Returns all the relationship types.
        :rtype: :py:class:`~app.utils.types.DBRowList`
        """
        query = """
        SELECT ID, Type_Name, Short_Label, Default_Color, Is_Directed, Line_Style 
        FROM Relationship_Types
        ORDER BY Type_Name ASC;
        """
        try:
            results = self.db._execute_query(query, fetch_all=True)
            logger.debug(f"Retrieved {len(results)} relationship types.")
            return results
        except DatabaseError as e:
            logger.error("Failed to retrieve all relationship types.", exc_info=True)
            raise e
    
    def get_relationship_type_details(self, type_id: int) -> DBRow | None:
        """
        Retrives the full details for a specfic relationship type given ID.
        
        :param type_id: The ID of the relationship_type.
        :type type_id: int

        :returns: Returns the dict of the relationship_details or None if could not be found.
        :rtype: :py:class:`~app.utils.types.DBRow` or None
        """
        query = """
        SELECT ID, Type_Name, Short_Label, Default_Color, Is_Directed, Line_Style
        FROM Relationship_Types
        WHERE ID = ?;
        """
        try:
            success = self.db._execute_query(query, (type_id,), fetch_one=True)
            if success:
                logger.info(f"Successfully got relationship types for {len(success)} character nodes.")
            return success
        except DatabaseError as e:
            logger.error("Failed to retrieve relationship types details.", exc_info=True)
            raise e
    

    def create_relationship_type(self, type_name: str, short_label: str = "", default_color: str = "#FFFFFF", is_directed: int = 0, line_style: str = "Solid") -> int | None:
        """
        Creates a new relationship_type.

        :param type_name: The name of the new relationship_type.
        :type type_name: str
        :param short_label: The short label to be displayed on the graph. Default is Empty Str.
        :type short_label: str
        :param default_color: The default_color of the relationship_type. Default is '#FFFFFF'
        :type default_color: str
        :param is_directed: Describes whether the relationship_type is directed. 1 yes, 0 no.
        :type is_directed: int
        :param line_style: The type of line to be shown (Solid, Dashed, Dotted). Default is 'Solid'.
        :type line_style: str

        :returns: The created relationship_type's ID or None if failed to create relationship_type:
        :rtype: int or None
        """
        query = """
        INSERT INTO Relationship_Types
        (Type_Name, Short_Label, Default_Color, Is_Directed, Line_Style)
        VALUES (?, ?, ?, ?, ?);
        """
        params = (type_name, short_label, default_color, is_directed, line_style)
        try:
            type_id = self.db._execute_commit(query, params, fetch_id=True)
            if type_id:
                logger.info(f"Created new relationship type: ID={type_id}, Name='{type_name}'.")
            return type_id
        except DatabaseError as e:
            logger.error(f"Failed to create new relationship type with name: '{type_name}'.", exc_info=True)
            raise e

    def update_relationship_type(self, type_id: int, type_name: str, short_label: str, default_color: str, is_directed: int, line_style: str) -> bool:
        """
        Updates an existing relationship type.

        :param type_name: The name of the new relationship_type.
        :type type_name: str
        :param short_label: The short label to be displayed on the graph. Default is Empty Str.
        :type short_label: str
        :param default_color: The default_color of the relationship_type. Default is '#FFFFFF'
        :type default_color: str
        :param is_directed: Describes whether the relationship_type is directed. 1 yes, 0 no.
        :type is_directed: int
        :param line_style: The type of line to be shown (Solid, Dashed, Dotted). Default is 'Solid'.
        :type line_style: str

        :returns: Returns True is successfully updated, otherwise False.
        :rtype: bool
        """

        query = """
        UPDATE Relationship_Types SET
            Type_Name = ?,
            Short_Label = ?,
            Default_Color = ?,
            Is_Directed = ?,
            Line_Style = ?
        WHERE ID = ?;
        """
        params = (type_name, short_label, default_color, is_directed, line_style, type_id)
        try:
            success = self.db._execute_commit(query, params)
            if success:
                logger.info(f"Updated relationship type ID: {type_id}. New Name: '{type_name}'.")
            return success
        except DatabaseError as e:
            logger.error(f"Failed to update relationship type ID: {type_id} with name '{type_name}'.", exc_info=True)
            raise e

    def delete_relationship_type(self, type_id: int) -> bool:
        """
        Deletes a relationship type based on its ID.
        
        :returns: Returns True if deleted the relationship_type, otherwise False
        :rtype: bool
        """
        query = "DELETE FROM Relationship_Types WHERE ID = ?;"
        try:
            success = self.db._execute_commit(query, (type_id,))
            if success:
                logger.warning(f"Relationship type deleted: ID={type_id}. Associated relationships were also deleted.")
            return success
        except DatabaseError as e:
            logger.error(f"Failed to delete relationship type ID: {type_id}.", exc_info=True)
            raise e