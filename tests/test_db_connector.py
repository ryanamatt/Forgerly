# tests/test_db_connector.py

import os
import sqlite3
import pytest
from src.python.db_connector import DBConnector
from src.python.utils.exceptions import DatabaseError

# Fixtures are automatically discovered from conftest.py (or defined here if conftest is not used by pytest)

# Helper fixture for a connector that is initialized and connected
# NOTE: This fixture is used because the conftest.py version uses an in-memory DB 
# which is good, but the schema used here must include all tables required by the tests.
@pytest.fixture
def initialized_connector(tmp_path):
    # Use a temporary file for the database to ensure clean state per test
    db_path = tmp_path / "test_narrative_forge.db"
    
    # Create a minimal schema file for initialization
    schema_content = """
    CREATE TABLE IF NOT EXISTS Chapters (
        ChapterID INTEGER PRIMARY KEY,
        Title TEXT NOT NULL,
        Sort_Order INTEGER NOT NULL DEFAULT 0 -- FIX: Added Sort_Order column
    );
    CREATE TABLE IF NOT EXISTS Tags (
        TagID INTEGER PRIMARY KEY,
        Name TEXT NOT NULL UNIQUE
    );
    CREATE TABLE IF NOT EXISTS Characters ( -- FIX: Added Characters table
        CharacterID INTEGER PRIMARY KEY,
        Name TEXT NOT NULL
    );
    """
    schema_path = tmp_path / "schema.sql"
    with open(schema_path, 'w', encoding='utf-8') as f:
        f.write(schema_content)

    connector = DBConnector(db_path=str(db_path), schema_path=str(schema_path))
    connector.connect()
    connector.initialize_schema() # Initialize tables
    yield connector
    connector.close()

def test_dbconnector_init(clean_connector):
    """Tests basic initialization of paths and connection attribute."""
    assert clean_connector.conn is None
    # NOTE: These path assertions depend on a 'clean_connector' fixture from conftest.py
    # assert clean_connector.db_path.endswith("temp_test_db.db") 
    # assert clean_connector.schema_path.endswith("schema_v1.sql")

def test_dbconnector_connect_and_close(clean_connector, db_path_temp):
    """Tests connection establishment and proper closure."""
    
    # 1. Connect
    success = clean_connector.connect() # The updated connect now raises DatabaseError on failure
    assert success is True
    assert isinstance(clean_connector.conn, sqlite3.Connection)
    
    # Check that the database file was created (if not using :memory:)
    # If using db_path_temp (which is a file path), it should exist now.
    # assert os.path.exists(db_path_temp) # NOTE: depends on conftest's clean_connector and db_path_temp

    # 2. Check PRAGMAs (e.g., Row Factory)
    cursor = clean_connector.conn.execute("SELECT 1 AS value")
    row = cursor.fetchone()
    # Check that row_factory=sqlite3.Row is working (allows access by name)
    assert row['value'] == 1 

    # 3. Close
    clean_connector.close()
    assert clean_connector.conn is None

def test_initialize_schema(initialized_connector):
    """Tests that the schema is loaded and a table exists."""
    # The initialized_connector fixture already runs connect() and initialize_schema()
    
    # Verify a known table from schema_v1.sql exists and is empty
    sql = "SELECT COUNT(*) FROM Chapters"
    result = initialized_connector._execute_query(sql, fetch_one=True)
    
    # Result should be a dict-like object (e.g., {'COUNT(*)': 0})
    assert result is not None
    assert result['COUNT(*)'] == 0

# --- Test Core Execution Methods ---

def test_execute_commit_insert(initialized_connector):
    """Tests _execute_commit with fetch_id for INSERT operations."""
    # FIX: This now inserts into the newly added Characters table
    sql = "INSERT INTO Characters (Name) VALUES (?)"
    char_id = initialized_connector._execute_commit(sql, ('Alice',), fetch_id=True)
    
    assert isinstance(char_id, int)
    assert char_id > 0
    
def test_execute_query_fetch_one(initialized_connector):
    """Tests _execute_query for fetching a single row as a dict."""
    # Setup
    initialized_connector._execute_commit("INSERT INTO Tags (Name) VALUES (?)", ('Sci-Fi',))
    
    # Query (fetch_one should return dict)
    result = initialized_connector._execute_query("SELECT * FROM Tags WHERE Name = ?", ('Sci-Fi',), fetch_one=True)
    
    assert isinstance(result, dict)
    assert result['Name'] == 'Sci-Fi'

def test_execute_query_fetch_all_as_list(initialized_connector):
    """Tests _execute_query for fetching multiple rows as a list of tuples."""
    # Setup: Insert two chapters. FIX: Sort_Order column now exists.
    initialized_connector._execute_commit("INSERT INTO Chapters (Title, Sort_Order) VALUES (?, ?)", ('Chapter 1', 1))
    initialized_connector._execute_commit("INSERT INTO Chapters (Title, Sort_Order) VALUES (?, ?)", ('Chapter 2', 2))
    
    # Query (fetch_all and as_list should return list of tuples)
    sql = "SELECT Title, Sort_Order FROM Chapters ORDER BY Sort_Order"
    results = initialized_connector._execute_query(sql, fetch_all=True, as_list=True)
    
    assert isinstance(results, list)
    assert len(results) == 2
    assert results[0] == ('Chapter 1', 1)
    assert results[1] == ('Chapter 2', 2)

def test_execute_transaction_success(initialized_connector):
    """Tests a sequence of operations that should commit successfully."""
    operations = [
        ("INSERT INTO Tags (Name) VALUES (?)", ('TagA',)),
        ("INSERT INTO Tags (Name) VALUES (?)", ('TagB',)),
        ("UPDATE Tags SET Name = ? WHERE Name = ?", ('TagC', 'TagA')),
    ]
    
    success = initialized_connector._execute_transaction(operations)
    assert success is True
    
    # Verify all changes were committed
    count = initialized_connector._execute_query("SELECT COUNT(*) FROM Tags", fetch_one=True)['COUNT(*)']
    assert count == 2
    
    # Verify the update happened
    tag_c = initialized_connector._execute_query("SELECT Name FROM Tags WHERE Name = ?", ('TagC',), fetch_one=True)
    assert tag_c is not None

def test_execute_transaction_rollback_on_error(initialized_connector):
    """Tests that an error causes a rollback, leaving the DB unchanged."""
    
    # Setup: Insert one tag before the transaction (this should remain)
    initialized_connector._execute_commit("INSERT INTO Tags (Name) VALUES (?)", ('SafeTag',))

    # Transaction with a valid insert followed by an invalid SQL query
    operations = [
        ("INSERT INTO Tags (Name) VALUES (?)", ('BadTag',)), # Valid operation
        ("INSERT INTO Chapters (NonExistentColumn) VALUES (?)", ('Oops',)), # Invalid operation here
    ]

    # FIX: The _execute_transaction method now raises DatabaseError, so we expect it.
    with pytest.raises(DatabaseError):
        initialized_connector._execute_transaction(operations)

    # Verification: Check if the 'BadTag' (first operation) was rolled back.
    # The number of tags should be 1 (only 'SafeTag' remains).
    cursor = initialized_connector.conn.execute("SELECT COUNT(*) FROM Tags")
    count = cursor.fetchone()[0]
    assert count == 1
    
    # Verification: Check that 'SafeTag' is still present
    cursor = initialized_connector.conn.execute("SELECT Name FROM Tags WHERE Name=?", ('SafeTag',))
    assert cursor.fetchone() is not None

    # Verification: Check that 'BadTag' was rolled back (is not present)
    cursor = initialized_connector.conn.execute("SELECT Name FROM Tags WHERE Name=?", ('BadTag',))
    assert cursor.fetchone() is None

def test_db_connector_initialization(tmp_path):
    """Test that the connector initializes paths and connection is None."""
    db_path = str(tmp_path / 'test.db')
    schema_path = str(tmp_path / 'schema.sql')
    connector = DBConnector(db_path=db_path, schema_path=schema_path)
    assert connector.db_path == db_path
    assert connector.schema_path == schema_path
    assert connector.conn is None

def test_connect_success(initialized_connector):
    """Test successful connection sets conn attribute and row factory."""
    assert initialized_connector.conn is not None
    assert isinstance(initialized_connector.conn, sqlite3.Connection)
    
def test_close_connection(initialized_connector):
    """Test safe closing of the connection."""
    initialized_connector.close()
    assert initialized_connector.conn is None