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

        # Finally, update the .nfp file
        self._update_config_version(app_version)

    def _migrate_to_0_5_0(self) -> None:
        """
        Migrates the schema to new 0.5.0 shema.
        
        :rtype: None
        """
        create_snapshots_table = """
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
