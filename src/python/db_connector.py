# src/python/db_connector.py

import sqlite3
import os
from typing import Any

class DBConnector:
    """
    Handles the connection, initialization, and safe query execution for the 
    SQLite database. 
    
    This class is solely responsible for database connection management, 
    while Repositories handle application-specific data access logic.
    """
    def __init__(self, db_path : str = os.path.join('data', 'narrative_forge.db'), 
                 schema_path: str = os.path.join('sql', 'schema_v1.sql')) -> None:
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
        self.schema_path = schema_path
        self.conn = None
        self.initialize_directories()

    def initialize_directories(self) -> None:
        """
        Ensures the 'data' and 'sql' directories, required for the database 
        and schema files, exist on the filesystem.
        
        :rtype: None
        """
        data_dir = os.path.dirname(self.db_path) or os.path.join('data')
        sql_dir = os.path.dirname(self.schema_path) or os.path.join('sql')

        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(sql_dir, exist_ok=True)

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
            return True
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            self.conn = None
            return False
        
    def close(self) -> None:
        """
        Closes the active database connection safely.
        
        :rtype: None
        """
        if self.conn:
            self.conn.close()
            self.conn = None

    def initialize_schema(self) -> None:
        """
        Initializes the database structure by executing the schema file.

        This is typically done only when the database file is first created.

        :returns: True if initialization was successful, False otherwise.
        :rtype: bool
        """
        if not self.conn:
            print("Error: Cannot initialize schema, database is not connected.")
            return

        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            self.conn.executescript(schema_sql)
            self.conn.commit()
            # print("Database schema initialized successfully.") # Debugging line
        except sqlite3.Error as e:
            print(f"SQL Error during schema initialization: {e}")
        except FileNotFoundError:
            print(f"Error: Schema file not found at {self.schema_path}")

    # --- Core Execution Methods (Used by all Repositories) ---

    def _execute_query(self, sql: str, params: tuple | None = None, fetch_one: bool = False, fetch_all: bool = False, as_list: bool = False) -> Any:
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
            print("ERROR: DB not connected for query.")
            return None

        try:
            cursor = self.conn.execute(sql, params or ())
            
            if fetch_one:
                row = cursor.fetchone()
                # Return dict-like object (sqlite3.Row) or None
                return dict(row) if row and not as_list else (tuple(row) if row and as_list else None)
            
            if fetch_all:
                rows = cursor.fetchall()
                # Convert sqlite3.Row objects to standard dicts or lists of tuples
                if as_list:
                    return [tuple(row) for row in rows]
                return [dict(row) for row in rows]
            
            return None # Should not happen for SELECT queries
        except sqlite3.Error as e:
            print(f"Database Query Error: {e}\nSQL: {sql}\nParams: {params}")
            return None

    def _execute_commit(self, sql: str, params: tuple | None = None, fetch_id: bool = False) -> bool | int | None:
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
            print("ERROR: DB not connected for commit.")
            return False

        try:
            cursor = self.conn.execute(sql, params or ())
            self.conn.commit()
            
            if fetch_id:
                # Used for INSERT operations to return the new row ID
                return cursor.lastrowid
            
            # Return True for successful UPDATE/DELETE
            return True
        except sqlite3.Error as e:
            print(f"Database Commit Error: {e}\nSQL: {sql}\nParams: {params}")
            self.conn.rollback()
            return False
        
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
            print("ERROR: DB not connected for transaction.")
            return False
        
        try:
            for sql, params in operations:
                self.conn.execute(sql, params or ())
            
            self.conn.commit()
            return True
        
        except sqlite3.Error as e:
            print(f"Database Transaction Error: {e}\nOperations: {operations}")
            self.conn.rollback()
            return False