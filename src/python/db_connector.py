# src/python/db_connector.py

import sqlite3
import os
import sys
from typing import Any

from .utils.exceptions import DatabaseError
from .utils.logger import get_logger

logger = get_logger(__name__)

class DBConnector:
    """
    Handles the connection, initialization, and safe query execution for the 
    SQLite database. 
    
    This class is solely responsible for database connection management, 
    while Repositories handle application-specific data access logic.
    """
    def __init__(self, db_path : str, schema_path: str) -> None:
        """
        Initializes file paths and the connection attribute. Does not establish 
        a connection immediately.

        :param db_path: The file path to the SQLite database file.
        :type db_path: str
        :param schema_path: The file path to the SQL schema file used for initialization.
        :type schema_path: str
        
        :rtype: None
        """
        self.db_path = db_path
        
        # If no path is provided, use the resolved default path
        if schema_path is None:
            default_rel_path = os.path.join('src', 'sql', 'schema_v1.sql')
            self.schema_path = self.resource_path(default_rel_path)
        else:
            self.schema_path = schema_path

        self.conn = None

    def connect(self) -> bool:
        """
        Opens a connection to the SQLite database specified by :py:attr:`.db_path`.

        It sets the connection's :py:attr:`~sqlite3.Connection.row_factory` to 
        :py:obj:`sqlite3.Row` for dictionary-like access to results.

        :returns: True if the connection was successful, False otherwise.
        :rtype: bool
        """
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA journal_mode = WAL;")
            self.conn.execute("PRAGMA synchronous=FULL;")
            self.conn.execute("PRAGMA foreign_keys = ON;")
            logger.info(f"Successfully connected to database at: {self.db_path}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Database connection error at {self.db_path}: {e}", exc_info=True)
            self.conn = None
            raise DatabaseError(
                message=f"Failed to connect to the database at '{self.db_path}'.",
                original_exception=e
            ) from e
        
    def close(self) -> None:
        """
        Closes the active database connection safely.
        
        :rtype: None
        """
        if self.conn:
            try:
                self.conn.close()
                self.conn = None
                logger.info("Database connection closed successfully.")
            except sqlite3.Error as e:
                # While rare, guard for closing errors
                logger.error(f"Error closing database connection: {e}", exc_info=True)

    def initialize_schema(self) -> None:
        """
        Initializes the database structure by executing the schema file.

        This is typically done only when the database file is first created.

        :returns: True if initialization was successful, False otherwise.
        :rtype: bool
        """
        if not self.conn:
            # Raise an error if connection is missing
            raise DatabaseError("Cannot initialize schema, database is not connected.")

        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
                
            self.conn.executescript(schema_sql)
            self.conn.commit()
            logger.info("Database schema initialized successfully.")
            
        except sqlite3.Error as e:
            # Log and raise on SQL execution error
            logger.error(f"SQL Error during schema initialization: {e}", exc_info=True)
            raise DatabaseError(
                message="A SQL error occurred during schema initialization.",
                original_exception=e
            ) from e
        except FileNotFoundError as e:
            # Log and raise on missing schema file
            logger.error(f"Schema file not found at {self.schema_path}", exc_info=True)
            raise DatabaseError(
                message=f"Schema file not found at '{self.schema_path}'.",
                original_exception=e
            ) from e

    # --- Core Execution Methods (Used by all Repositories) ---

    def _execute_query(self, sql: str, params: tuple | None = None, fetch_one: bool = False, 
                       fetch_all: bool = False, as_list: bool = False) -> Any:
        """
        Internal method for executing SELECT queries or single non-SELECT operations 
        (INSERT/UPDATE/DELETE).

        It safely handles exceptions and connection checks.

        :param sql: The SQL query string to execute.
        :type sql: str
        :param params: A tuple of parameters to safely bind to the query. Defaults to None.
        :type params: tuple or None
        :param fetch_one: If True, fetches and returns a single row (as a dictionary).
        :type fetch_one: bool
        :param fetch_all: If True, fetches and returns all rows (as a list of dictionaries).
        :type fetch_all: bool
        :param fetch_lastrowid: If True, returns the ID of the last inserted row.
        :type fetch_lastrowid: bool
        
        :returns: The query results (row, list of rows, last ID), the number of 
                  rows affected (for non-SELECT), or None/empty list on error.
        :rtype: Any
        """
        if not self.conn:
            # Raise an error if connection is missing
            raise DatabaseError("DB not connected for query execution.")

        try:
            cursor = self.conn.execute(sql, params or ())
            
            if fetch_one:
                row = cursor.fetchone()
                return dict(row) if row and not as_list else (tuple(row) if row and as_list else None)
            
            if fetch_all:
                rows = cursor.fetchall()
                if as_list:
                    return [tuple(row) for row in rows]
                return [dict(row) for row in rows]
            
            return None # Should not happen for SELECT queries, but handles non-select
        except sqlite3.Error as e:
            # Log and raise on SQL query error
            logger.error(f"Database Query Error: {e}\nSQL: {sql}\nParams: {params}", exc_info=True)
            raise DatabaseError(
                message=f"Error executing query: {sql}.",
                original_exception=e
            ) from e

    def _execute_commit(self, sql: str, params: tuple | None = None, 
                        fetch_id: bool = False) -> bool | int | None:
        """
        Executes a non-SELECT query (INSERT/UPDATE/DELETE) and commits.
        
        This is used for more complex non-SELECT queries. It safely handles 
        exceptions and connection checks.

        :param sql: The SQL query string to execute.
        :type sql: str
        :param params: A tuple of parameters to safely bind to the query. Defaults to None.
        :type params: tuple or None

        :returns: Returns True if successful, Returns ID if fetch_id=True, Returns None if fails.
        :rtype: bool or int or None

        """
        if not self.conn:
            # Raise an error if connection is missing
            raise DatabaseError("DB not connected for commit operation.")

        try:
            cursor = self.conn.execute(sql, params or ())
            self.conn.commit()
            
            if fetch_id:
                return cursor.lastrowid
            
            return True
        except sqlite3.Error as e:
            # Log, rollback, and raise on SQL commit error
            logger.error(f"Database Commit Error: {e}\nSQL: {sql}\nParams: {params}", exc_info=True)
            self.conn.rollback()
            raise DatabaseError(
                message=f"Error executing database modification (INSERT/UPDATE/DELETE). Transaction \
                    rolled back.",
                original_exception=e
            ) from e
        
    def _execute_transaction(self, operations: list[tuple[str, tuple | None]]) -> bool:
        """
        Executes a sequence of non-SELECT operations in a single, atomic transaction.

        If any operation fails, the entire transaction is rolled back.

        :param operations: A list of tuples, where each tuple is ``(sql_query, tuple)``.
        :type operations: list[tuple[str, tuple or None]]
        
        :returns: True if all operations succeed and the transaction commits, False otherwise.
        :rtype: bool
        """
        if not self.conn:
            # Raise an error if connection is missing
            raise DatabaseError("DB not connected for transaction.")
        
        try:
            for sql, params in operations:
                self.conn.execute(sql, params or ())
            
            self.conn.commit()
            return True
        
        except sqlite3.Error as e:
            # Log, rollback, and raise on transaction error
            logger.error(f"Database Transaction Error: {e}\nOperations: {operations}", exc_info=True)
            self.conn.rollback()
            raise DatabaseError(
                message="Error executing database transaction. All operations rolled back.",
                original_exception=e
            ) from e
        
    @staticmethod
    def resource_path(relative_path: str) -> str:
        """
        Get absolute path to resource, works for dev and for PyInstaller.
        
        :param relative_path: The relative path to the file.
        :type relative_path: str
        :rtype: str
        """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except AttributeError:
            # If _MEIPASS doesn't exist, we are in a normal dev environment
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)