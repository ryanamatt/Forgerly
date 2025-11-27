# tools/db_inspector.py
#
# Utility script to connect to the database and print out the schema,
# table contents, and key entity counts for quick debugging and verification.

import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / 'data' / 'narrative_forge.db'

def print_table_structure(conn: sqlite3.Connection, table_name: str) -> None:
    """Prints the column names and data types for a given table."""
    try:
        cursor = conn.execute(f"PRAGMA table_info({table_name});")
        columns = [f"{col[1]} ({col[2]})" for col in cursor.fetchall()]
        print(f"\n--- Schema: {table_name} ---")
        print(", ".join(columns))
    except sqlite3.Error:
        print(f"\n--- Table {table_name} does not exist. ---")

def print_table_data_summary(conn: sqlite3.Connection, table_name: str, limit: int = 5) -> None:
    """Prints the row count and the first N rows of a table."""
    try:
        # Get count
        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"--- Data Summary: {table_name} ({count} rows) ---")
        
        if count > 0:
            # Fetch first N rows
            cursor = conn.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            
            # Print column headers
            columns = [desc[0] for desc in cursor.description]
            print(" | ".join(columns))
            print("-" * (sum(len(c) + 3 for c in columns)))
            
            # Print rows
            for row in cursor.fetchall():
                # Simple string representation of row data
                print(" | ".join(str(item) for item in row))

    except sqlite3.Error as e:
        # This will catch errors if the table doesn't exist or is locked
        if "no such table" not in str(e):
             print(f"Error accessing table {table_name}: {e}")

def run_db_inspector():
    """Main function to run the database inspection."""
    print(f"--- Narrative Forge Database Inspector ---")
    
    if not DB_PATH.exists():
        print(f"❌ ERROR: Database file not found at {DB_PATH}. Run db_reset.py first.")
        return

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Get list of all user tables
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        all_tables = [row[0] for row in cursor.fetchall()]
        
        # Priority tables for inspection
        priority_tables = ['Chapters', 'Lore_Entries', 'Characters', 'Tags']
        other_tables = [t for t in all_tables if t not in priority_tables]
        
        tables_to_inspect = priority_tables + sorted(other_tables)

        for table in tables_to_inspect:
            print_table_structure(conn, table)
            print_table_data_summary(conn, table, limit=5)
            
    except sqlite3.Error as e:
        print(f"❌ ERROR: Database connection failed: {e}")
        
    finally:
        if conn:
            conn.close()
            
if __name__ == '__main__':
    run_db_inspector()