# src/python/repository/relationship_repository.py

from ..utils.types import DBRow, DBRowList
from ..db_connector import DBConnector

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
        return self.db._execute_query(query, fetch_all=True)
    
    def create_relationship(self, char_a_id: int, char_b_id: int, type_id: int, lore_id: int | None = None,
                            description: str = "", intensity: int = 50, start_chapter_id: int | None = None, 
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
        INSERT INTO Character_Relationships
        (Character_A_ID, Character_B_ID, Type_ID, Lore_ID, Description, Intensity, Start_Chapter_ID, End_Chapter_ID)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
        params = (char_a_id, char_b_id, type_id, lore_id, description, intensity, start_chapter_id, end_chapter_id)
        return self.db._execute_commit(query, params, fetch_id=True)

    def delete_relationship(self, relationship_id: int) -> bool:
        """
        Deletes a relationship.
        
        :param relationship_id: The relationship ID of the relationship to be deleted.
        :type relationship_id: int

        :returns: True if successfully delete relationship, otherwise False
        :rtype: bool
        """
        query = "DELETE FROM Character_Relationships WHERE ID = ?;"
        return self.db._execute_commit(query, (relationship_id,))

    def update_relationship_details(self, relationship_id: int, type_id: int, description: str, 
                                    intensity: int, lore_id: int | None, start_chapter_id: int | None, 
                                    end_chapter_id: int | None) -> bool:
        """Updates the non-ID fields of an existing relationship."""
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
        return self.db._execute_commit(query, params)

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
            Is_Hidden
        FROM Character_Node_Positions;
        """
        return self.db._execute_query(query, fetch_all=True)

    def save_node_attributes(self, character_id: int, x_pos: float, y_pos: float, 
                           node_color: str, node_shape: str, is_hidden: int) -> bool:
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

        :returns: Returns True if successfully saved/updated the node attributes, otherwise False.
        :rtype: bool
        """
        query = """
        INSERT OR REPLACE INTO Character_Node_Positions
        (Character_ID, X_Position, Y_Position, Node_Color, Node_Shape, Is_Hidden)
        VALUES (?, ?, ?, ?, ?, ?);
        """
        params = (character_id, x_pos, y_pos, node_color, node_shape, is_hidden)
        return self.db._execute_commit(query, params)

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
        return self.db._execute_query(query, fetch_all=True)
    
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
        return self.db._execute_query(query, (type_id,), fetch_one=True)

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
        return self.db._execute_commit(query, params, fetch_id=True)

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
        return self.db._execute_commit(query, params)

    def delete_relationship_type(self, type_id: int) -> bool:
        """
        Deletes a relationship type based on its ID.
        
        :returns: Returns True if deleted the relationship_type, otherwise False
        :rtype: bool
        """
        query = "DELETE FROM Relationship_Types WHERE ID = ?;"
        return self.db._execute_commit(query, (type_id,))