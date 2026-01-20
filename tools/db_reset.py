# tools/db_reset.py

import os
import sys
import sqlite3
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
# DATA_DIR and DB_PATH constants are removed
SCHEMA_PATH = PROJECT_ROOT / 'src' / 'sql' / 'schema_v1.sql'

def run_db_reset(db_path: Path) -> bool:
    """
    Performs the full database reset operation.
    1. Deletes the existing database file.
    2. Initializes a new database connection.
    3. Executes the schema SQL to create all tables.
    
    Returns True on success, False otherwise.
    """
    print("--- Forgerly Database Reset Utility ---")
    
    # --- Step 1: Delete existing database file ---
    if db_path.exists():
        try:
            os.remove(db_path)
            print(f"✅ Existing database deleted: {db_path.name} in {db_path.parent.name}")
        except OSError as e:
            print(f"❌ ERROR: Could not delete database file. Is the application running?")
            print(f"         Error details: {e}")
            return False
    else:
        print(f"ℹ️ Database file not found at {db_path}. Proceeding to creation.")

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
        # Connect: This creates the file if it doesn't exist
        conn = sqlite3.connect(db_path)
        
        # Execute the entire schema script
        conn.executescript(schema_sql)
        conn.commit()
        
        print(f"🎉 SUCCESS: New database created and initialized at {db_path.name}")
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

    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="Delete and recreate a project's database.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'project_path',
        type=str,
        help="The full path to the root project folder (e.g., /path/to/projects/MyProject)."
    )
    args = parser.parse_args()

    # Determine database path
    project_path = Path(args.project_path)
    if not project_path.is_dir():
        print(f"❌ ERROR: Project path not found or is not a directory: {project_path}")
        sys.exit(1)

    project_name = project_path.name
    dynamic_db_path = project_path / f"{project_name}.db"
    
    if run_db_reset(dynamic_db_path):
        print("\nDatabase reset complete. Ready for fresh testing.")
    else:
        print("\nDatabase reset FAILED. Check console errors.")
        sys.exit(1)