# tests/repository/test_relationship_repository.py

import pytest
from src.python.repository.relationship_repository import RelationshipRepository
from src.python.db_connector import DBConnector 
from src.python.repository.character_repository import CharacterRepository
from src.python.repository.lore_repository import LoreRepository

@pytest.fixture
def rel_repo(initialized_connector: DBConnector) -> RelationshipRepository:
    """Provides a fresh RelationshipRepository instance for each test."""
    return RelationshipRepository(initialized_connector)

# --- Helper Fixtures/Functions for Dependencies ---

@pytest.fixture
def char_repo(initialized_connector: DBConnector) -> CharacterRepository:
    return CharacterRepository(initialized_connector)

@pytest.fixture
def lore_repo(initialized_connector: DBConnector) -> LoreRepository:
    return LoreRepository(initialized_connector)

def create_test_character(repo: CharacterRepository, name: str) -> int:
    return repo.create_character(name)

def create_test_rel_type(repo: RelationshipRepository, name: str, label: str = "Rel", directed: int = 0) -> int:
    """Helper to quickly create a relationship type and return its ID."""
    return repo.create_relationship_type(name, label, "#FF0000", directed)

# --- Tests for Relationship Types (Configuration) ---

def test_create_and_get_rel_type_details(rel_repo: RelationshipRepository):
    """Tests creating a relationship type and fetching its details."""
    type_id = create_test_rel_type(rel_repo, "Friends", "FND", 0)
    
    details = rel_repo.get_relationship_type_details(type_id)
    
    assert details['ID'] == type_id
    assert details['Type_Name'] == "Friends"
    assert details['Is_Directed'] == 0
    assert details['Short_Label'] == "FND"

def test_get_all_relationship_types_ordering(rel_repo: RelationshipRepository):
    """Tests retrieval of all relationship types, ordered by Type_Name ASC."""
    create_test_rel_type(rel_repo, "Rivals", "RIV")
    create_test_rel_type(rel_repo, "Allies", "ALL")
    
    types = rel_repo.get_all_relationship_types()
    
    assert len(types) == 2
    assert types[0]['Type_Name'] == "Allies"
    assert types[1]['Type_Name'] == "Rivals"

def test_update_relationship_type(rel_repo: RelationshipRepository):
    """Tests updating all fields of a relationship type."""
    type_id = create_test_rel_type(rel_repo, "Old Name", "OLD", 0)
    
    success = rel_repo.update_relationship_type(type_id, "New Name", "NEW", "#00FF00", 1, "Dashed")
    assert success is True
    
    details = rel_repo.get_relationship_type_details(type_id)
    assert details['Type_Name'] == "New Name"
    assert details['Is_Directed'] == 1
    assert details['Line_Style'] == "Dashed"

def test_delete_relationship_type(rel_repo: RelationshipRepository):
    """Tests deleting a relationship type."""
    type_id = create_test_rel_type(rel_repo, "Type to Delete", "DEL")
    
    success = rel_repo.delete_relationship_type(type_id)
    assert success is True
    
    assert rel_repo.get_relationship_type_details(type_id) is None

# --- Tests for Character Relationships (Edges) ---

def test_create_and_get_all_relationships(rel_repo: RelationshipRepository, char_repo: CharacterRepository, lore_repo: LoreRepository):
    """Tests creating a relationship and fetching it with full join data."""
    # Setup Dependencies
    char_a_id = create_test_character(char_repo, "Anya")
    char_b_id = create_test_character(char_repo, "Boris")
    type_id = create_test_rel_type(rel_repo, "Rivals", "RIV", 1)
    lore_id = lore_repo.create_lore_entry("Rivalry Background")
    
    # Act: Create Relationship
    rel_id = rel_repo.create_relationship(char_a_id, char_b_id, type_id, lore_id=lore_id, 
                                          description="They clash often.", intensity=90)
    assert rel_id is not None
    
    # Act: Get all relationships for graph
    relationships = rel_repo.get_all_relationships_for_graph()
    
    # Assert
    assert len(relationships) == 1
    rel = relationships[0]
    
    assert rel['Relationship_ID'] == rel_id
    assert rel['Character_A_Name'] == "Anya"
    assert rel['Character_B_Name'] == "Boris"
    assert rel['Type_Name'] == "Rivals"
    assert rel['Lore_ID'] == lore_id
    assert rel['Intensity'] == 90
    assert rel['Is_Directed'] == 1

def test_update_relationship_details(rel_repo: RelationshipRepository, char_repo: CharacterRepository):
    """Tests updating the non-ID fields of a relationship."""
    char_a_id = create_test_character(char_repo, "CharX")
    char_b_id = create_test_character(char_repo, "CharY")
    old_type_id = create_test_rel_type(rel_repo, "Old Type", "O")
    new_type_id = create_test_rel_type(rel_repo, "New Type", "N")
    
    rel_id = rel_repo.create_relationship(char_a_id, char_b_id, old_type_id)
    
    # Act: Update
    rel_repo.update_relationship_details(rel_id, new_type_id, "New Desc", 10, None, None, None)
    
    # Assert: Check updated values
    rel = rel_repo.get_all_relationships_for_graph()[0]
    assert rel['Description'] == "New Desc"
    assert rel['Intensity'] == 10
    assert rel['Type_ID'] == new_type_id
    assert rel['Start_Chapter_ID'] == None
    assert rel['End_Chapter_ID'] == None
    
def test_delete_relationship(rel_repo: RelationshipRepository, char_repo: CharacterRepository):
    """Tests deletion of a character relationship."""
    char_a_id = create_test_character(char_repo, "Zoe")
    char_b_id = create_test_character(char_repo, "Yuri")
    type_id = create_test_rel_type(rel_repo, "Test", "T")
    
    rel_id = rel_repo.create_relationship(char_a_id, char_b_id, type_id)
    
    rel_repo.delete_relationship(rel_id)
    
    assert len(rel_repo.get_all_relationships_for_graph()) == 0

# --- Tests for Character Node Positions ---

def test_save_and_get_node_attributes(rel_repo: RelationshipRepository, char_repo: CharacterRepository):
    """Tests saving node positions using INSERT OR REPLACE logic."""
    char_id = create_test_character(char_repo, "GraphNode")
    
    # 1. Initial Insert
    rel_repo.save_node_attributes(char_id, 100.5, 200.5, "#FF0000", "Square", 0, 0)
    positions = rel_repo.get_all_node_positions()
    assert len(positions) == 1
    assert positions[0]['X_Position'] == 100.5
    assert positions[0]['Node_Color'] == "#FF0000"
    
    # 2. Update (INSERT OR REPLACE)
    rel_repo.save_node_attributes(char_id, 50.0, 50.0, "#000000", "Circle", 1, 1)
    
    # Should still only be one row
    positions = rel_repo.get_all_node_positions()
    assert len(positions) == 1
    
    # Check that attributes were updated
    assert positions[0]['X_Position'] == 50.0
    assert positions[0]['Node_Color'] == "#000000"
    assert positions[0]['Is_Hidden'] == 1
    assert positions[0]['Is_Locked'] == 1