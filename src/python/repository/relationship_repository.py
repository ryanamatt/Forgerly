# src/python/repository/relationship_repository.py

from ..utils.types import DBRow, DBRowList
from ..db_connector import DBConnector
from ..utils.logger import get_logger
from ..utils.exceptions import DatabaseError

logger = get_logger(__name__)

class RelationshipRepository:
    """
    Manages all database operations for the Character_Relationship, Relationship_Types, 
    Character_Node_Positions, Graph_Junctions, and Junction_Connections entities.

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
        :param intensity: The intensity (thickness) of the line connecting the character nodes. 
            Default to 50.
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
                logger.info(f"Created new relationship: ID={relationship_id}, Type_ID={type_id}" 
                            f" between Char {char_a_id} and Char {char_b_id}.")
            return relationship_id
        except DatabaseError as e:
            logger.error(f"Failed to create relationship between {char_a_id} and {char_b_id} with "
                         f"Type ID {type_id}.", exc_info=True)
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
        
    def get_node_details(self, char_id: int) -> dict:
        """
        Docstring for get_all_node_positions
        
        :param char_id: The character ID.
        :type char_id: int
        :returns: Dict of all values except X and Y positon.
        :rtype: dict
        """
        query = "SELECT Node_Color, Node_Shape, Is_Hidden, Is_Locked FROM Character_Node_Positions WHERE Character_ID = ?;"
        try:
            results = self.db._execute_query(query, (char_id,), fetch_one=True)
            logger.debug(f"Retrieved node details for char_id: {char_id}.")
            return results
        except DatabaseError as e:
            logger.error(f"Failed to retrieve node data for char_id: {char_id}.", exc_info=True)
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
        
    def save_node_details(self, character_id: int, node_color: str, node_shape: str, is_hidden: int, 
                          is_locked: int) -> bool:
        """
        Saves the details of a Character nodes (Everything except Postion (X, Y))

        :param character_id: The character ID of the node attribute.
        :type character_id: int
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
        UPDATE Character_Node_Positions SET Node_Color = ?, Node_Shape = ?, Is_Hidden = ?, Is_Locked = ?
        WHERE Character_ID = ?;
        """
        params = (node_color, node_shape, is_hidden, is_locked, character_id)
        try:
            success = self.db._execute_commit(query, params)
            if success:
                logger.info(f"Successfully saved node details, Char_ID: {character_id}")
            return success
        except DatabaseError as e:
            logger.warning("Failed to save character node details", exc_info=True)
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
        
    def update_node_bulk_is_locked(self, char_ids: list[int], is_locked: bool) -> bool:
        """
        Bulk Updates a list of Node_Ids to the is_locked value.
        
        :param char_ids: A list of the Node IDs.
        :type char_ids: list[int]
        :param is_locked: The new Is_Locked value to set to each ID.
        :type is_locked: bool
        :return: Returns True if successfully saved, otherwise False
        :rtype: bool
        """
        placeholders = ', '.join(['?'] * len(char_ids))
        query = f"UPDATE Character_Node_Positions SET Is_Locked = ? WHERE Character_ID IN ({placeholders})"
        params = [1 if is_locked else 0] + char_ids
        try:
            success = self.db._execute_commit(query, params)
            if success:
                logger.info(f"Successfully saved new is_locked attribute, Char_IDs: {char_ids}")
            return success
        except DatabaseError as e:
            logger.warning("Failed to save new IDS new is_locked attribute", exc_info=True)
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
    

    def create_relationship_type(self, type_name: str, short_label: str = "", default_color: str = "#FFFFFF", 
                                 is_directed: int = 0, line_style: str = "Solid") -> int | None:
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

    def update_relationship_type(self, type_id: int, type_name: str, short_label: str, default_color: str, 
                                 is_directed: int, line_style: str) -> bool:
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
            logger.error(f"Failed to update relationship type ID: {type_id} with name '{type_name}'.", 
                         exc_info=True)
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
                logger.warning(f"Relationship type deleted: ID={type_id}. Associated relationships "
                               "were also deleted.")
            return success
        except DatabaseError as e:
            logger.error(f"Failed to delete relationship type ID: {type_id}.", exc_info=True)
            raise e

    # =========================================================================
    # Graph Junctions
    # =========================================================================

    def get_all_junctions_for_graph(self) -> DBRowList:
        """
        Retrieves all junction nodes joined with their relationship type data.

        Each row contains the junction's canvas position, its associated
        relationship type style (color, label, line style, directionality),
        and any per-junction overrides.

        :returns: List of dicts, one per junction.
        :rtype: :py:class:`~app.utils.types.DBRowList`
        """
        query = """
        SELECT
            GJ.ID           AS Junction_ID,
            GJ.X_Position,
            GJ.Y_Position,
            GJ.Label,
            GJ.Color_Override,
            RT.ID           AS Type_ID,
            RT.Short_Label,
            RT.Default_Color,
            RT.Is_Directed,
            RT.Line_Style
        FROM Graph_Junctions GJ
        JOIN Relationship_Types RT ON GJ.Type_ID = RT.ID;
        """
        try:
            results = self.db._execute_query(query, fetch_all=True)
            logger.debug(f"Retrieved {len(results)} junctions for the graph.")
            return results
        except DatabaseError as e:
            logger.error("Failed to retrieve junctions for graph.", exc_info=True)
            raise e

    def get_all_junction_connections(self) -> DBRowList:
        """
        Retrieves all junction connection spokes, joining with the parent
        junction's type data for rendering.

        :returns: List of dicts, one per spoke/connection row.
        :rtype: :py:class:`~app.utils.types.DBRowList`
        """
        query = """
        SELECT
            JC.ID               AS Connection_ID,
            JC.Junction_ID,
            JC.Endpoint_Type,
            JC.Character_ID,
            JC.Target_Junction_ID,
            JC.Role,
            JC.Intensity,
            JC.Description,
            RT.Short_Label,
            RT.Default_Color,
            RT.Is_Directed,
            RT.Line_Style
        FROM Junction_Connections JC
        JOIN Graph_Junctions GJ ON JC.Junction_ID = GJ.ID
        JOIN Relationship_Types RT ON GJ.Type_ID = RT.ID;
        """
        try:
            results = self.db._execute_query(query, fetch_all=True)
            logger.debug(f"Retrieved {len(results)} junction connections.")
            return results
        except DatabaseError as e:
            logger.error("Failed to retrieve junction connections.", exc_info=True)
            raise e

    def create_junction(self, type_id: int, x: float = 0.0, y: float = 0.0,
                        label: str = '', color_override: str = '') -> int | None:
        """
        Creates a new graph junction node.

        :param type_id: The ID of the relationship type this junction represents.
        :type type_id: int
        :param x: Initial X canvas position.
        :type x: float
        :param y: Initial Y canvas position.
        :type y: float
        :param label: Optional display label override (empty = use type Short_Label).
        :type label: str
        :param color_override: Optional hex color override (empty = use type Default_Color).
        :type color_override: str
        :returns: The new junction's database ID, or None on failure.
        :rtype: int or None
        """
        query = """
        INSERT INTO Graph_Junctions (Type_ID, X_Position, Y_Position, Label, Color_Override)
        VALUES (?, ?, ?, ?, ?);
        """
        params = (type_id, x, y, label, color_override)
        try:
            junction_id = self.db._execute_commit(query, params, fetch_id=True)
            if junction_id:
                logger.info(f"Created new junction: ID={junction_id}, Type_ID={type_id}.")
            return junction_id
        except DatabaseError as e:
            logger.error(f"Failed to create junction with Type_ID={type_id}.", exc_info=True)
            raise e

    def update_junction_position(self, junction_id: int, x: float, y: float) -> bool:
        """
        Updates the canvas position of an existing junction.

        :param junction_id: The junction's database ID.
        :type junction_id: int
        :param x: New X canvas position.
        :type x: float
        :param y: New Y canvas position.
        :type y: float
        :returns: True on success.
        :rtype: bool
        """
        query = "UPDATE Graph_Junctions SET X_Position = ?, Y_Position = ? WHERE ID = ?;"
        try:
            success = self.db._execute_commit(query, (x, y, junction_id))
            if success:
                logger.debug(f"Updated junction position: ID={junction_id}, x={x}, y={y}.")
            return success
        except DatabaseError as e:
            logger.error(f"Failed to update junction position: ID={junction_id}.", exc_info=True)
            raise e

    def delete_junction(self, junction_id: int) -> bool:
        """
        Deletes a junction and all its connected spokes (via CASCADE).

        :param junction_id: The junction's database ID.
        :type junction_id: int
        :returns: True on success.
        :rtype: bool
        """
        query = "DELETE FROM Graph_Junctions WHERE ID = ?;"
        try:
            success = self.db._execute_commit(query, (junction_id,))
            if success:
                logger.info(f"Deleted junction: ID={junction_id} (spokes cascade-deleted).")
            return success
        except DatabaseError as e:
            logger.error(f"Failed to delete junction: ID={junction_id}.", exc_info=True)
            raise e

    # =========================================================================
    # Junction Connections / Spokes
    # =========================================================================

    def create_junction_connection(self, junction_id: int, endpoint_type: str,
                                   character_id: int | None = None,
                                   target_junction_id: int | None = None,
                                   role: str = 'incoming',
                                   intensity: int = 5,
                                   description: str = '') -> int | None:
        """
        Creates a single spoke connecting a junction to a character or another junction.

        Exactly one of ``character_id`` or ``target_junction_id`` must be provided,
        matching the ``endpoint_type`` value (``'character'`` | ``'junction'``).

        :param junction_id: The parent junction's database ID.
        :type junction_id: int
        :param endpoint_type: Either ``'character'`` or ``'junction'``.
        :type endpoint_type: str
        :param character_id: Character endpoint ID (when endpoint_type='character').
        :type character_id: int or None
        :param target_junction_id: Junction endpoint ID (when endpoint_type='junction').
        :type target_junction_id: int or None
        :param role: ``'incoming'`` (endpoint→junction) or ``'outgoing'`` (junction→endpoint).
        :type role: str
        :param intensity: Visual line weight 1–10.
        :type intensity: int
        :param description: Optional descriptive note for this spoke.
        :type description: str
        :returns: The new connection's database ID, or None on failure.
        :rtype: int or None
        """
        query = """
        INSERT INTO Junction_Connections
            (Junction_ID, Endpoint_Type, Character_ID, Target_Junction_ID, Role, Intensity, Description)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        params = (junction_id, endpoint_type, character_id, target_junction_id,
                  role, intensity, description)
        try:
            conn_id = self.db._execute_commit(query, params, fetch_id=True)
            if conn_id:
                logger.info(f"Created junction connection: ID={conn_id}, "
                            f"Junction={junction_id}, Type={endpoint_type}.")
            return conn_id
        except DatabaseError as e:
            logger.error(f"Failed to create junction connection for junction {junction_id}.",
                         exc_info=True)
            raise e

    def update_junction_connection(self, connection_id: int, intensity: int,
                                   description: str = '') -> bool:
        """
        Updates the intensity and description of an existing junction spoke.

        :param connection_id: The spoke's database ID.
        :type connection_id: int
        :param intensity: New visual line weight 1–10.
        :type intensity: int
        :param description: Updated descriptive note.
        :type description: str
        :returns: True on success.
        :rtype: bool
        """
        query = """
        UPDATE Junction_Connections SET Intensity = ?, Description = ? WHERE ID = ?;
        """
        try:
            success = self.db._execute_commit(query, (intensity, description, connection_id))
            if success:
                logger.info(f"Updated junction connection: ID={connection_id}.")
            return success
        except DatabaseError as e:
            logger.error(f"Failed to update junction connection: ID={connection_id}.", exc_info=True)
            raise e

    def delete_junction_connection(self, connection_id: int) -> bool:
        """
        Deletes a single junction spoke by its ID.

        :param connection_id: The spoke's database ID.
        :type connection_id: int
        :returns: True on success.
        :rtype: bool
        """
        query = "DELETE FROM Junction_Connections WHERE ID = ?;"
        try:
            success = self.db._execute_commit(query, (connection_id,))
            if success:
                logger.info(f"Deleted junction connection: ID={connection_id}.")
            return success
        except DatabaseError as e:
            logger.error(f"Failed to delete junction connection: ID={connection_id}.", exc_info=True)
            raise e

    def delete_orphan_junctions(self) -> int:
        """
        Removes any junctions that have no remaining connections.

        Called automatically after spoke deletions to keep the database clean.

        :returns: The number of orphan junctions deleted.
        :rtype: int
        """
        query = """
        DELETE FROM Graph_Junctions
        WHERE ID NOT IN (SELECT DISTINCT Junction_ID FROM Junction_Connections);
        """
        try:
            # Use raw cursor to get rowcount
            if not self.db.conn:
                raise DatabaseError("DB not connected.")
            cursor = self.db.conn.execute(query)
            self.db.conn.commit()
            count = cursor.rowcount
            if count:
                logger.info(f"Deleted {count} orphan junction(s).")
            return count
        except Exception as e:
            logger.error("Failed to delete orphan junctions.", exc_info=True)
            raise DatabaseError("Failed to delete orphan junctions.", original_exception=e) from e