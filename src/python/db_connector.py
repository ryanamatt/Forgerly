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
            self.conn.execute("PRAGMA foreign_keys = ON") # Enforce FK constraints
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
            with open(self.schema_path, 'r', encoding='utf-8') as f:
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
        
    def _execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor | None:
        """A utility method for safe query execution"""
        if not self.conn:
            print("Database operation failed: Not connected.")
            return None
        try:
            cursor = self.conn.execute(query, params)
            return cursor
        except sqlite3.Error as e:
            print(f"Database query error: {e}\nQuery: {query}\nParams: {params}")
            # Do not re-raise, but return None to indicate failure
            return None
        
    def _execute_commit(self, query: str, params: tuple = ()) -> bool:
        """A utility method for executing a modifying query and committing"""
        cursor = self._execute_query(query, params)
        if cursor:
            self.conn.commit()
            return True
        return False
    
    # Helper Fetch All
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
        
    # Helper Fetch One used in outline manager
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
    
    # ---------------------------------------
    # CHAPTERS CRUD
    # ---------------------------------------
    
    def get_all_chapters_for_outline(self) -> list[tuple[int, str]]:
        """Retrieves ID and Title for all chapters, ordered by Sort_Order."""
        query = "SELECT ID, Title, Sort_Order FROM Chapters ORDER BY Sort_Order ASC"
        cursor = self._execute_query(query)
        if cursor:
            # Returns a list of (ID, Title, Sort_Order) tuples
            return cursor.fetchall()
        return []

    def create_chapter(self, title: str) -> int:
        """Creates a new chapter with a given title and returns its ID."""
        # Find the max sort order and add 1, defaulting to 1 if no chapters exist
        max_sort_order_cursor = self._execute_query("SELECT MAX(Sort_Order) FROM Chapters")
        max_sort_order = max_sort_order_cursor.fetchone()[0] if max_sort_order_cursor else 0
        new_sort_order = (max_sort_order or 0) + 1

        query = """
            INSERT INTO Chapters (Title, Text_Content, Sort_Order) 
            VALUES (?, ?, ?)
        """
        if self._execute_commit(query, (title, f"<h1>{title}</h1>\n<p>Start writing here...</p>", new_sort_order)):
            return self._execute_query("SELECT last_insert_rowid()").fetchone()[0]
        return 0

    def get_chapter_content(self, chapter_id: int) -> str | None:
        """Retrieves the rich text content of a chapter."""
        query = "SELECT Text_Content FROM Chapters WHERE ID = ?"
        cursor = self._execute_query(query, (chapter_id,))
        if cursor:
            row = cursor.fetchone()
            return row['Text_Content'] if row else None
        return None

    def update_chapter_content(self, chapter_id: int, content: str) -> bool:
        """Updates the rich text content of an existing chapter."""
        query = "UPDATE Chapters SET Text_Content = ? WHERE ID = ?"
        return self._execute_commit(query, (content, chapter_id))
    
    def update_chapter_title(self, chapter_id: int, title: str) -> bool:
        """Updates the title of an existing chapter."""
        query = "UPDATE Chapters SET Title = ? WHERE ID = ?"
        return self._execute_commit(query, (title, chapter_id))

    def delete_chapter(self, chapter_id: int) -> bool:
        """Deletes a chapter and all associated records (due to ON DELETE CASCADE)."""
        query = "DELETE FROM Chapters WHERE ID = ?"
        return self._execute_commit(query, (chapter_id,))
    
    # ---------------------------------------
    # Chapter TAGGING/METADATA CRUD
    # ---------------------------------------

    def create_tag(self, tag_name: str) -> int:
        """
        Creates a new tag and returns its ID. If the tag already exists,
        it fails and returns 0
        """
        # Ensure tag_name is clean (no leading/trailing whitespace, forced lowercase for consistency)
        clean_name = tag_name.strip().lower()

        # Check if tag already exists using its unique contraint
        cursor = self._execute_query("SELECT ID FROM Tags WHERE NAME = ?", (clean_name,))
        if cursor and cursor.fetchone():
            # Tag already exists
            return 0
        
        query = "INSERT INTO Tages (Name) VALUES (?)"
        if self._execute_commit(query, (clean_name,)):
            return self._execute_query("SELECT last_insert_rowid()").fetchone()[0]
        return 0
    
    def get_tag_id_or_create(self, tag_name: str) -> int:
        """
        Retrieves the ID of an existing tag or creates a new one and returns the ID
        """
        clean_name = tag_name.strip().lower()
        
        # 1. Try to get existing ID
        cursor = self._execute_query("SELECT ID FROM Tags WHERE Name = ?", (clean_name,))
        if cursor:
            row = cursor.fetchone()
            if row:
                return row['ID']

        # 2. If not found, create it (and get the ID)
        query = "INSERT INTO Tags (Name) VALUES (?)"
        if self._execute_commit(query, (clean_name,)):
            return self._execute_query("SELECT last_insert_rowid()").fetchone()[0]
        
        # Should not happen unless a concurrent access issue
        print(f"FATAL ERROR: Could not get or create tag '{clean_name}'")
        return 0
    
    def get_chapter_tags(self, chapter_id: int) -> list[tuple[int, str]]:
        """
        Retrieves all tags associated with a specific chapter.
        Returns a list of (Tag_ID, Tag_Name) tuples.
        """
        query = """
            SELECT t.ID, t.Name 
            FROM Tags t
            JOIN Chapter_Tags ct ON t.ID = ct.Tag_ID
            WHERE ct.Chapter_ID = ?
        """
        cursor = self._execute_query(query, (chapter_id,))
        if cursor:
            # We must use a list of tuples here because row_factory is set to sqlite3.Row
            # to prevent potential type issues when accessing in other modules.
            return [(row['ID'], row['Name']) for row in cursor.fetchall()]
        return []
    
    def set_chapter_tags(self, chapter_id: int, tag_names: list[str]) -> None:
        """
        Updates the tags for a chapter. It deletes all current tags and inserts new ones.
        Creates any necessary new tags in the Tags table first.
        """
        if not self.conn:
            print("Database operation failed: Not connected.")
            return

        try:
            # 1. Start a transaction
            self.conn.execute("BEGIN TRANSACTION")

            # 2. Delete all existing tags for the chapter
            self.conn.execute("DELETE FROM Chapter_Tags WHERE Chapter_ID = ?", (chapter_id,))
            
            # 3. Process the new list of tag names
            for tag_name in tag_names:
                clean_name = tag_name.strip().lower()
                if not clean_name:
                    continue # Skip empty tags
                
                # Get the Tag_ID (creating the tag if it doesn't exist)
                tag_id = self.get_tag_id_or_create(clean_name)
                
                if tag_id > 0:
                    # 4. Create the new link in the Chapter_Tags table
                    # Using INSERT OR IGNORE in case multiple users somehow get the same tag_id
                    # within the same transaction (not strictly necessary but safe).
                    self.conn.execute(
                        "INSERT OR IGNORE INTO Chapter_Tags (Chapter_ID, Tag_ID) VALUES (?, ?)", 
                        (chapter_id, tag_id)
                    )

            # 5. Commit the transaction
            self.conn.commit()
            print(f"Successfully updated tags for Chapter ID {chapter_id}.")

        except sqlite3.Error as e:
            print(f"Transaction error during set_chapter_tags: {e}")
            self.conn.rollback() # Rollback on error

    # -------------------------------
    # Lore Entries CRUD Operations
    # -------------------------------

    def create_lore_entry(self, title: str, category: str = "General") -> int:
        """Creates a new lore entry and returns its ID."""
        initial_content = f"<h1>{title}</h1>\n<p>Describe this {category} entry here...</p>"
        query = """
            INSERT INTO Lore_Entries (Title, Content, Category) 
            VALUES (?, ?, ?)
        """
        if self._execute_commit(query, (title, initial_content, category)):
            # The last_insert_rowid() is safe because we just committed a single insert.
            cursor = self._execute_query("SELECT last_insert_rowid()")
            return cursor.fetchone()[0] if cursor else 0
        return 0
    
    def get_all_lore_entries(self) -> list[sqlite3.Row]:
        """Retrieves akk kire entires (ID, Title, Category), ordered by Title"""
        query = "SELECT ID, Title, Category FROM Lore_Entries ORDER BY Title ASC"
        return self.fetch_all(query)
    
    def get_lore_entry(self, lore_id: int) -> sqlite3.Row | None:
        """Retrieves a singe lore entry (Title, Content, Category), by ID"""
        query = "SELECT Title, Content, Category FROM Lore_Entries WHERE ID = ?"
        return self.fetch_one(query, (lore_id,))
    
    def update_lore_entry(self, lore_id: int, title: str, content: str, category: str) -> bool:
        """Updates the title, content, and category of an exisitng lore entry."""
        query = "UPDATE Lore_Entries SET Title = ?, Content = ?, Category = ? WHERE ID = ?"
        return self._execute_commit(query, (title, content, category, lore_id))
    
    def delete_lore_entry(self, lore_id: int) -> bool:
        """Deletes a lore entry and all associated records (due to ON DELETE CASCADE)."""
        query = "DELETE FROM Lore_Entries WHERE ID = ?"
        return self._execute_commit(query, (lore_id,))
    
    # ---------------------------------------
    # LORE TAGGING/METADATA CRUD
    # ---------------------------------------

    def get_lore_tags(self, lore_id: int) -> list[tuple[int, str]]:
        """
        Retrieves all tags associated with a specific lore entry.
        Returns a list of (Tag_ID, Tag_Name) tuples.
        """
        query = """
            SELECT t.ID, t.Name 
            FROM Tags t
            JOIN Lore_Tags lt ON t.ID = lt.Tag_ID
            WHERE lt.Lore_ID = ?
        """
        cursor = self._execute_query(query, (lore_id,))
        if cursor:
            # Returns a list of (ID, Name) tuples
            return [(row['ID'], row['Name']) for row in cursor.fetchall()]
        return []
    
    def set_lore_tags(self, lore_id: int, tag_names: list[str]) -> None:
        """
        Updates the tags for a lore entry. It deletes all current tags and inserts new ones.
        Creates any necessary new tags in the Tags table first.
        """
        if not self.conn:
            print("Database operation failed: Not connected.")
            return

        try:
            # 1. Start a transaction
            # Using BEGIN is safer for complex transactions involving selects and inserts
            self.conn.execute("BEGIN") 

            # 2. Delete all existing tags for the lore entry
            self.conn.execute("DELETE FROM Lore_Tags WHERE Lore_ID = ?", (lore_id,))
            
            # 3. Process the new list of tag names
            for tag_name in tag_names:
                clean_name = tag_name.strip().lower()
                if not clean_name:
                    continue # Skip empty tags
                
                # Get the Tag_ID (creating the tag if it doesn't exist) 
                # Use the new transactional-safe helper
                tag_id = self.get_tag_id_or_create(clean_name)
                
                if tag_id > 0:
                    # 4. Create the new link in the Lore_Tags table
                    self.conn.execute(
                        "INSERT OR IGNORE INTO Lore_Tags (Lore_ID, Tag_ID) VALUES (?, ?)", 
                        (lore_id, tag_id)
                    )

            # 5. Commit the transaction
            self.conn.commit()
            print(f"Successfully updated tags for Lore Entry ID {lore_id}.")

        except sqlite3.Error as e:
            # If any error occurs, rollback all changes
            print(f"Transaction error during set_lore_tags: {e}")
            if self.conn:
                self.conn.rollback()


# ------------------------------------
# TESTING
# ------------------------------------

if __name__ == '__main__':
    # Adjust paths for testing if running this file directly
    db_path_test = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'test_tagging.db')
    schema_path_test = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'sql', 'schema_v1.sql')

    print(f"Testing DBConnector with path: {db_path_test}")
    # Remove old test DB file if it exists
    if os.path.exists(db_path_test):
        os.remove(db_path_test)
        print("Removed old test database.")

    db_connector = DBConnector(
        db_path=db_path_test, 
        schema_path=schema_path_test
    )

    if db_connector.connect():
        # Initialize the schema
        db_connector.initialize_schema()

        try:
            # 1. Create a Test Chapter
            chapter_title = "Epic 3.1 Test Chapter"
            chapter_id = db_connector.create_chapter(chapter_title)
            print(f"\n1. Created new chapter with ID: {chapter_id}")

            # 2. Define tags and set them
            tags_to_set = ["action", "fantasy", "test tag", "TAG_UPPERCASE", " tag with whitespace "]
            print(f"\n2. Setting tags: {tags_to_set}")
            db_connector.set_chapter_tags(chapter_id, tags_to_set)

            # 3. Retrieve and verify
            retrieved_tags = db_connector.get_chapter_tags(chapter_id)
            print(f"\n3. Retrieved tags for Chapter {chapter_id}:")
            for tag_id, tag_name in retrieved_tags:
                print(f"   ID: {tag_id}, Name: '{tag_name}'")
            
            # Expected result: 5 tags, all lowercase and trimmed
            
            # 4. Update tags (remove some, add new)
            new_tags_to_set = ["sci-fi", "thriller", "action"] # Action should be reused
            print(f"\n4. Updating tags to: {new_tags_to_set}")
            db_connector.set_chapter_tags(chapter_id, new_tags_to_set)

            # 5. Retrieve and verify update
            retrieved_tags_updated = db_connector.get_chapter_tags(chapter_id)
            print(f"\n5. Retrieved tags after update for Chapter {chapter_id}:")
            for tag_id, tag_name in retrieved_tags_updated:
                print(f"   ID: {tag_id}, Name: '{tag_name}'")
            
            # Expected result: 3 tags ("sci-fi", "thriller", "action")

            # ------------------------------------
            # 6. Test Lore Entry CRUD and Tagging
            # ------------------------------------
            
            print("\n" + "="*50)
            print("6. Testing Lore Entry CRUD and Tagging")
            print("="*50)

            # 6a. Create Lore Entry
            lore_title = "The Obsidian Tower"
            lore_category = "Location"
            lore_id = db_connector.create_lore_entry(lore_title, lore_category)
            print(f"6a. Created new lore entry with ID: {lore_id}")

            # 6b. Retrieve Lore Entry
            lore_entry = db_connector.get_lore_entry(lore_id)
            print(f"6b. Retrieved Lore Entry: {dict(lore_entry)}")
            
            # 6c. Update Lore Entry
            new_content = "<p>A dark, brooding tower.</p>"
            update_success = db_connector.update_lore_entry(lore_id, lore_title, new_content, "Landmark")
            print(f"6c. Update success: {update_success}")
            
            # 6d. Get All Lore Entries (should be 1)
            all_lore = db_connector.get_all_lore_entries()
            print(f"6d. All Lore Entries (Count: {len(all_lore)}):")
            for entry in all_lore:
                print(f"    ID: {entry['ID']}, Title: {entry['Title']}, Category: {entry['Category']}")
                
            # 6e. Set Lore Tags
            lore_tags = ["dark", "magical", "location"]
            print(f"6e. Setting lore tags: {lore_tags}")
            db_connector.set_lore_tags(lore_id, lore_tags)
            
            # 6f. Retrieve Lore Tags
            retrieved_lore_tags = db_connector.get_lore_tags(lore_id)
            print(f"6f. Retrieved Lore Tags:")
            for tag_id, tag_name in retrieved_lore_tags:
                print(f"    ID: {tag_id}, Name: '{tag_name}'")
                
            # 6g. Delete Lore Entry
            delete_success = db_connector.delete_lore_entry(lore_id)
            print(f"6g. Deletion success: {delete_success}")
            
            # 6h. Verify deletion (should be 0)
            all_lore_after_delete = db_connector.get_all_lore_entries()
            print(f"6h. All Lore Entries after delete (Count: {len(all_lore_after_delete)})")
            
        except Exception as e:
            print(f"An unexpected error occurred during testing: {e}")
        finally:
            # Clean up the test environment
            db_connector.close()
            # os.remove(db_path_test) # Keep for manual inspection if needed
            print("\nTest finished.")
    else:
        print("Test environment setup failed.")