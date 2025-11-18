# SQLite Database Connector: src/python/db_connector.py

import sqlite3
import os

class DBConnector:
    """
    Handles the connection, initialization, and safe query execution for the
    SQLite database used by The Narrative Forge.

    The database file is expected to be located at 'data/narrative_forge.db'.
    The schema creation script is expected at 'sql/schema_v1.sql'.
    """
    def __init__(self, db_path : str = os.path.join('data', 'narrative_forge.db'), 
                 schema_path: str = os.path.join('sql', 'schema_v1.sql')) -> None:
        """Initializses paths and connection attribute"""
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
            print(f"Successfully connected to the database: {self.db_path}")
            return True
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            self.conn = None
            return False
        
    def close(self) -> None:
        """Closes the database connection if it is open"""
        if self.conn:
            self.conn.close()
            self.conn = None
            print("Database connection closed")

    def initialize_schema(self) -> bool:
        """
        Reads and executes the SQL schema script to set up all tables.
        This should only be called if the database file is new or tables are missing.
        """
        if not self.conn:
            print("Cannot initialize schema: Not connected to the database.")
            return False
        
        try:
            with open(self.schema_path, 'r') as f:
                sql_script = f.read()

            # Executes the entire script at once
            self.conn.executescript(sql_script)
            print(f"Database schema initialized form {self.schema_path}")
            return True
        except FileNotFoundError:
            print(f"Error: Scheme file not found at {self.schema_path}. Cannot initialized database")
        except sqlite3.Error as e:
            print(f"Error executing scheme script: {e}")
            return False
        
    def execute_query(self, query: str, params: tuple=()) -> int:
        """
        Executes non-SELECT query (INSERT, UPDATE, DELETE)

        Args:
            query (str): The SQL query string
            params (tuple): Parameters to substitue into the query (for safety)

        Returns:
            int: The number of rows affected by the operation
        """
        if not self.conn:
            print(f"Query failed: Not connected to the database.")
            return 0
        
        try:
            cursor = self.conn.execute(query, params)
            self.conn.commit()
            return cursor.rowcount
        except sqlite3.Error as e:
            print(f"Database WRITE error in query: {query}. Error: {e}")
            return 0
        
    def fetch_all(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        """
        Executes a SELECT query and fetches all results as a list of dicts/Rows.

        Args:
            query (str): The SQL SELECT query string.
            params (tuple): Parameters to substitute into the query.

        Returns:
            list: A list of sqlite3.Row objects (dictionary-like).
        """
        if not self.conn:
            print("Fetch failed: Not connected to the database.")
            return []
        try:
            cursor = self.conn.execute(query, params)
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Database READ error in query: {query}. Error: {e}")
            return []
        
    def fetch_one(self, query: str, params: tuple=()) -> sqlite3.Row | None:
        """
        Executes a SELECT query and fetches a single result.

        Args:
            query (str): The SQL SELECT query string.
            params (tuple): Parameters to substitute into the query.

        Returns:
            sqlite3.Row or None: A single Row object if found, otherwise None.
        """
        results = self.fetch_all(query, params)
        return results[0] if results else None
    
    def fetch_all_chapters(self) -> list[sqlite3.Row]:
        """Retrieves all chapters orderered by their sort order"""
        query = "SELECT ID, Title, Sort_Order, Precursor_Chapter_ID FROM Chapters ORDER BY Sort_Order ASC"
        return self.fetch_all(query)
    
    def create_chapter(self, title: str) -> int | None:
        """
        Creates a new chapter record, automatically determining the next Sort_Order.
        
        Returns:
            int: The ID of the newly created chapter, or None if creation failed
        """
        if not self.conn:
            return None
        
        # 1. Find the maximum current Sort_Order and increment it by 1
        sort_order_query = "SELECT MAX(Sort_Order) AS max_order FROM Chapters"
        max_order_result = self.fetch_one(sort_order_query)
        next_sort_order = (max_order_result['max_order'] or 0) + 1

        # 2. Insert the new Chapter
        insert_query = "INSERT INTO Chapters (Title, Sort_Order) VALUES (?, ?)"
        try:
            cursor = self.conn.execute(insert_query, (title, next_sort_order))
            self.conn.commit()
            # Return the ID of the last inserted row
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Database INSERT error (Chapter): {e}")
            return None
        
    def update_chapter_title(self, chapter_id: int, new_title: str) -> bool:
        """Updates the title of an exisiting chapter"""
        query = "UPDATE Chapters SET Title = ? WHERE ID = ?"
        rows = self.execute_query(query, (new_title, chapter_id))
        return rows > 0
    
    def delete_chapter(self, chapter_id: int) -> bool:
        """Deletes a chapter record based on its ID."""
        query = "DELETE FROM Chapters WHERE ID = ?"
        rows = self.execute_query(query, (chapter_id,))
        return rows > 0

    
# Example usage (for testing and demonstration only)
if __name__ == '__main__':
    # To run this script from the project root (C:\...\narrative-forge>), 
    # the paths should be relative to the root.
    # E.g., python src/python/db_connector.py
    
    # Corrected path assumption: Running from project root
    db_connector = DBConnector(
        db_path=os.path.join('data', 'test_narrative_forge.db'), 
        schema_path=os.path.join('sql', 'schema_v1.sql')
    )

    if db_connector.connect():
        # Initialize the schema (will run the script created in Epic 1)
        db_connector.initialize_schema()

        # --- Example CRUD Operation ---
        try:
            # 1. INSERT a Chapter
            new_id = db_connector.create_chapter("Test Chapter One")
            print(f"Created new chapter with ID: {new_id}")

            # 2. SELECT all Chapters
            all_chapters = db_connector.fetch_all_chapters()
            print(f"\nFetched {len(all_chapters)} total chapters.")
            for chapter in all_chapters:
                print(f" - ID: {chapter['ID']}, Title: {chapter['Title']}")
            
            # 3. UPDATE a Chapter
            if new_id:
                db_connector.update_chapter_title(new_id, "Test Chapter One - Renamed")
            
            # 4. DELETE a Chapter
            if new_id:
                db_connector.delete_chapter(new_id)
                print(f"\nDeleted chapter with ID: {new_id}")


        finally:
            # Always close the connection
            db_connector.close()