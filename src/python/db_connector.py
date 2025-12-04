# src/python/db_connector.py

import sqlite3
import os
from typing import Any

class DBConnector:
    """
    Handles the connection, initialization, and safe query execution for the
    SQLite database. It is solely responsible for database management,
    while Repositories handle application data access logic.
    """
    def __init__(self, db_path : str = os.path.join('data', 'narrative_forge.db'), 
                 schema_path: str = os.path.join('sql', 'schema_v1.sql')) -> None:
        """Initializes paths and connection attribute"""
        self.db_path = db_path
        self.schema_path = schema_path
        self.conn = None
        self.initialize_directories()

    def initialize_directories(self) -> None:
        """Ensures the 'data' and 'sql' direcotries exist"""
        data_dir = os.path.dirname(self.db_path) or os.path.join('data')
        sql_dir = os.path.dirname(self.schema_path) or os.path.join('sql')

        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(sql_dir, exist_ok=True)

    def connect(self) -> bool:
        """Opens a connection to the SQLite database"""
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
        """Closes the database connection safely."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def initialize_schema(self) -> None:
        """Reads the schema file and creates tables if they don't exist."""
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
        """Executes a SELECT query and returns results."""
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
        """Executes a non-SELECT query (INSERT/UPDATE/DELETE) and commits."""
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
        Executes a sequence of non-SELECT operations in a single transaction.
        'operations' is a list of (sql_query, parameters_tuple) pairs.
        Returns True on success, False on error (with automatic rollback).
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