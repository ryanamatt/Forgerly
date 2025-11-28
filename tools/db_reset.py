# tools/db_reset.py
#
# Utility script to delete the existing database file and recreate a fresh
# database structure based on the schema_v1.sql file.

import os
import sys
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
DB_PATH = DATA_DIR / 'narrative_forge.db'
SCHEMA_PATH = PROJECT_ROOT / 'sql' / 'schema_v1.sql'

def run_db_reset() -> bool:
    """
    Performs the full database reset operation.
    1. Deletes the existing database file.
    2. Initializes a new database connection.
    3. Executes the schema SQL to create all tables.
    
    Returns True on success, False otherwise.
    """
    print("--- Narrative Forge Database Reset Utility ---")
    
    # --- Step 1: Delete existing database file ---
    if DB_PATH.exists():
        try:
            os.remove(DB_PATH)
            print(f"✅ Existing database deleted: {DB_PATH.name}")
        except OSError as e:
            print(f"❌ ERROR: Could not delete database file. Is the application running?")
            print(f"         Error details: {e}")
            return False
    else:
        print(f"ℹ️ Database file not found at {DB_PATH.name}. Proceeding to creation.")

    # --- Step 2: Read SQL Schema ---
    if not SCHEMA_PATH.exists():
        print(f"❌ ERROR: Schema file not found at {SCHEMA_PATH}")
        print("Please ensure 'schema_v1.sql' is in the 'sql/' directory.")
        return False
        
    try:
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
    except IOError as e:
        print(f"❌ ERROR: Could not read schema file: {e}")
        return False

    # --- Step 3: Connect and Execute Schema ---
    conn = None
    try:
        # Ensure the data directory exists before connecting
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Connect: This creates the file if it doesn't exist
        conn = sqlite3.connect(DB_PATH)
        
        # Execute the entire schema script
        conn.executescript(schema_sql)
        conn.commit()
        
        print(f"🎉 SUCCESS: New database created and initialized at {DB_PATH.name}")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ ERROR: SQLite error during schema execution: {e}")
        print("Review your 'schema_v1.sql' for syntax errors.")
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # Add project root to sys path so modules can be imported if needed
    sys.path.append(str(PROJECT_ROOT / 'src' / 'python'))
    
    if run_db_reset():
        print("\nDatabase reset complete. Ready for fresh testing.")
    else:
        print("\nDatabase reset FAILED. Check console errors.")
        sys.exit(1)