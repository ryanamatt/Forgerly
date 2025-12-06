# tests/repository/test_character_repository.py

import pytest
from src.python.repository.character_repository import CharacterRepository
from src.python.db_connector import DBConnector 

@pytest.fixture
def char_repo(initialized_connector: DBConnector) -> CharacterRepository:
    """Provides a fresh CharacterRepository instance for each test."""
    return CharacterRepository(initialized_connector)

# --- Helper Function (or Fixture, if reusable) ---
def create_test_character(repo: CharacterRepository, name: str, status: str = "Alive") -> int:
    """Helper to quickly create a character and return its ID."""
    return repo.create_character(name, description=f"Desc for {name}", status=status)

# --- Tests ---

def test_create_and_get_details(char_repo: CharacterRepository):
    """Tests creating a character and fetching its full details."""
    name = "Elora Danan"
    status = "Main"
    
    char_id = create_test_character(char_repo, name, status)
    
    details = char_repo.get_character_details(char_id)
    
    assert isinstance(char_id, int)
    assert char_id > 0
    assert details['ID'] == char_id
    assert details['Name'] == name
    assert details['Status'] == status
    assert 'Description' in details # Checks structure

def test_get_all_characters_ordering(char_repo: CharacterRepository):
    """Tests retrieval of all characters, ensuring ordering by Name ASC."""
    create_test_character(char_repo, "Zoe")
    create_test_character(char_repo, "Alice")
    create_test_character(char_repo, "Bob")
    
    characters = char_repo.get_all_characters()
    
    assert len(characters) == 3
    # Should be ordered by Name ASC
    assert characters[0]['Name'] == "Alice"
    assert characters[1]['Name'] == "Bob"
    assert characters[2]['Name'] == "Zoe"

def test_update_character(char_repo: CharacterRepository):
    """Tests updating a character's details."""
    char_id = create_test_character(char_repo, "Old Name", "Minor")
    
    new_name = "New Name"
    new_description = "Updated description."
    new_status = "Deceased"
    
    success = char_repo.update_character(char_id, new_name, new_description, new_status)
    assert success is True
    
    details = char_repo.get_character_details(char_id)
    assert details['Name'] == new_name
    assert details['Description'] == new_description
    assert details['Status'] == new_status

def test_delete_character(char_repo: CharacterRepository):
    """Tests successful deletion of a character."""
    char_id = create_test_character(char_repo, "Temporary Character")
    
    success = char_repo.delete_character(char_id)
    assert success is True
    
    # Verify it is gone
    details = char_repo.get_character_details(char_id)
    assert details is None

def test_get_character_name(char_repo: CharacterRepository):
    """Tests fetching only the name."""
    name = "Captain Nemo"
    char_id = create_test_character(char_repo, name)
    
    retrieved_name = char_repo.get_character_name(char_id)
    assert retrieved_name == name
    
    # Test non-existent ID
    assert char_repo.get_character_name(9999) is None

def test_search_characters_by_name_and_status(char_repo: CharacterRepository):
    """Tests the character search functionality using LIKE patterns."""
    create_test_character(char_repo, "Commander Shepard", "N7")
    create_test_character(char_repo, "Garrus Vakarian", "Archangel")
    
    # Test search by name fragment
    results = char_repo.search_characters("shep")
    assert len(results) == 1
    assert results[0]['Name'] == "Commander Shepard"
    
    # Test search by status
    results = char_repo.search_characters("Archangel")
    assert len(results) == 1 
    assert results[0]['Name'] == "Garrus Vakarian"