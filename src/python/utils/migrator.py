# src/python/utils/migrator.py

from ._version import __version__
from ..db_connector import DBConnector
from .resource_path import get_resource_path
import json

class SchemaMigrator:
    """
    Docstring for SchemaMigrator
    """
    def __init__(self, db_connector: DBConnector, project_config_path: str):
        """
        Intaiziates the Schema Migrator.
        
        :param db_connector: The database connector.
        :type db_connector: DBConnector
        :param project_config_path: The Project_Settings.nfp file path.
        :type project_config_path: str
        """
        self.db = db_connector
        self.config_path = get_resource_path(project_config_path)

    def get_current_project_version(self) -> str:
        """
        Get's the current project version.
        
        :return: The project version Ex '0.5.0'.
        :rtype: str
        """
        with open(self.config_path, 'r') as f:
            data = json.load(f)
            return data.get("version", "0.0.0")

    def upgrade(self) -> None:
        """
        Upgrades the previous projects to the new version.
        
        :rtype: None
        """
        app_version = __version__
        project_version = self.get_current_project_version()

        app_version = app_version.split('-')[0] # Renove Articles like -alpha, -beta.
        project_version = project_version.split('-')[0]

        if project_version == app_version:
            return

        # Migration logic (e.g., from 1.0.0 to 1.1.0)
        project_version_parts = [int(x) for x in project_version.split('.')]
        if project_version_parts < [0, 5, 0]:
            self._migrate_to_0_5_0()

        if project_version_parts <= [0, 5, 0]:
            self._migrate_to_0_5_1()

        # Finally, update the .nfp file
        self._update_config_version(app_version)

    def _migrate_to_0_5_0(self) -> None:
        """
        Migrates the schema to new 0.5.0 shema.
        
        :rtype: None
        """
        create_snapshots_table  = """
        CREATE TABLE IF NOT EXISTS Snapshots (
            ID              INTEGER PRIMARY KEY,
            Timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP,
            Label           TEXT,
            Entity_Type     TEXT NOT NULL,
            Entity_ID       INTEGER NOT NULL,
            Content_Delta   TEXT,
            Author_Comment  TEXT
        );
        """
        
        try:
            self.db._execute_transaction([(create_snapshots_table, None)])
        except Exception as e:
            raise

    def _migrate_to_0_5_1(self) -> None:
        """
        Migrates the schema to new 0.5.1 shema.
        
        :rtype: None
        """
        create_graph_junctions = """
            CREATE TABLE IF NOT EXISTS Graph_Junctions (
                ID                      INTEGER PRIMARY KEY,
                X_Position              FLOAT NOT NULL DEFAULT 0,
                Y_Position              FLOAT NOT NULL DEFAULT 0,
                Type_ID                 INTEGER NOT NULL,          -- Relationship type shown on all spokes
                Label                   TEXT DEFAULT '',           -- Override label (blank = use type Short_Label)
                Color_Override          TEXT DEFAULT '',           -- Hex override (blank = use type Default_Color)

                FOREIGN KEY (Type_ID) REFERENCES Relationship_Types(ID) ON DELETE CASCADE
            );
        """
        
        create_junction_connections = """
            CREATE TABLE IF NOT EXISTS Junction_Connections (
                ID                      INTEGER PRIMARY KEY,
                Junction_ID             INTEGER NOT NULL,
                Endpoint_Type           TEXT NOT NULL CHECK (Endpoint_Type IN ('character', 'junction')),
                Character_ID            INTEGER,           -- Set when Endpoint_Type = 'character'
                Target_Junction_ID      INTEGER,           -- Set when Endpoint_Type = 'junction'
                Role                    TEXT NOT NULL DEFAULT 'incoming'
                                            CHECK (Role IN ('incoming', 'outgoing')),
                Intensity               INTEGER DEFAULT 5, -- Line weight (1-10)
                Description             TEXT DEFAULT '',

                CHECK (
                    (Endpoint_Type = 'character' AND Character_ID IS NOT NULL AND Target_Junction_ID IS NULL) OR
                    (Endpoint_Type = 'junction'  AND Target_Junction_ID IS NOT NULL AND Character_ID IS NULL)
                ),

                FOREIGN KEY (Junction_ID)        REFERENCES Graph_Junctions(ID) ON DELETE CASCADE,
                FOREIGN KEY (Character_ID)       REFERENCES Characters(ID)      ON DELETE CASCADE,
                FOREIGN KEY (Target_Junction_ID) REFERENCES Graph_Junctions(ID) ON DELETE CASCADE
            );
        """

        create_indexes = """
                CREATE INDEX IF NOT EXISTS idx_junction_connections_junction ON Junction_Connections (Junction_ID);
                CREATE INDEX IF NOT EXISTS idx_junction_connections_character ON Junction_Connections (Character_ID);
                CREATE INDEX IF NOT EXISTS idx_junction_connections_target ON Junction_Connections (Target_Junction_ID);
                CREATE INDEX IF NOT EXISTS idx_junction_type ON Graph_Junctions (Type_ID);
        """
        
        try:
            self.db._execute_transaction([(create_graph_junctions, None), 
                                          (create_junction_connections, None), (create_indexes, None)])
        except Exception as e:
            raise

    def _update_config_version(self, new_version: str) -> None:
        """
        Updates the version in Project_Settings.nfp
        
        :param new_version: The newer version to add/
        :type new_version: str
        :rtype: None
        """
        with open(self.config_path, 'r') as f:
            data = json.load(f)
        
        data["version"] = new_version
        
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=4)
