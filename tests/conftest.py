# tests/conftest.py

import pytest
import sqlite3
import os

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src', 'sql', 'schema_v1.sql')

@pytest.fixture
def db_path_temp(tmp_path):
    """
    Creates a temporary path for the database file.
    'tmp_path' is a built-in pytest fixture that provides a temporary directory.
    """
    return tmp_path / "temp_test_db.db"

@pytest.fixture
def clean_connector(db_path_temp):
    """
    Provides a DBConnector instance that uses a temporary, non-existent file
    and has not yet connected.
    """
    from src.python.db_connector import DBConnector
    # The schema path will point to the real one, but the db_path is temporary
    connector = DBConnector(db_path=str(db_path_temp))
    return connector

@pytest.fixture
def initialized_connector(clean_connector):
    """
    Provides a fully connected and schema-initialized DBConnector instance
    using an in-memory database.
    """
    from src.python.db_connector import DBConnector
    
    # Use a pure in-memory database for ultra-fast, isolated testing
    connector = DBConnector(db_path=':memory:') 
    
    # 1. Connect
    assert connector.connect() is True

    # 2. Initialize schema
    connector.initialize_schema()
    
    # 3. Yield the connected object to the test function
    yield connector
    
    # 4. Teardown (runs after the test completes)
    connector.close()
