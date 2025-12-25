# tests/repository/test_lore_repository.py

import pytest
from src.python.repository.lore_repository import LoreRepository
from src.python.db_connector import DBConnector 
from src.python.repository.tag_repository import TagRepository # Needed to set up tags for search

@pytest.fixture
def lore_repo(initialized_connector: DBConnector) -> LoreRepository:
    """Provides a fresh LoreRepository instance for each test."""
    return LoreRepository(initialized_connector)

@pytest.fixture
def tag_repo(initialized_connector: DBConnector) -> TagRepository:
    """Provides a TagRepository instance for cross-repository setup."""
    return TagRepository(initialized_connector)

# --- Helper Function ---
def create_test_lore(repo: LoreRepository, title: str, category: str = "World", content: str = "...") -> int:
    """Helper to quickly create a lore entry and return its ID."""
    return repo.create_lore_entry(title, content, category)

# --- Tests ---

def test_create_and_get_details(lore_repo: LoreRepository):
    """Tests creating a lore entry and fetching its full details."""
    title = "The Shattering"
    category = "History"
    content = "The world was broken by the gods."
    
    lore_id = create_test_lore(lore_repo, title, category, content)
    
    details = lore_repo.get_lore_entry_details(lore_id)
    
    assert isinstance(lore_id, int)
    assert details['ID'] == lore_id
    assert details['Title'] == title
    assert details['Category'] == category
    assert details['Content'] == content

def test_get_all_lore_entries_ordering(lore_repo: LoreRepository):
    """Tests retrieval of all lore entries, ensuring ordering by Title ASC."""
    create_test_lore(lore_repo, "Z City", "Location")
    create_test_lore(lore_repo, "A Stone", "Item")
    create_test_lore(lore_repo, "B River", "Location")
    
    entries = lore_repo.get_all_lore_entries()
    
    assert len(entries) == 3
    # Should be ordered by Title ASC
    assert entries[0]['Title'] == "A Stone"
    assert entries[1]['Title'] == "B River"
    assert entries[2]['Title'] == "Z City"

def test_update_lore_entry(lore_repo: LoreRepository):
    """Tests updating the title, content, and category of a lore entry."""
    lore_id = create_test_lore(lore_repo, "Temp Title", "Temp Cat", "Temp Content")
    
    new_title = "Final Title"
    new_content = "Final Content."
    new_category = "Mythology"
    
    success = lore_repo.update_lore_entry(lore_id, new_title, new_content, new_category)
    assert success is True
    
    details = lore_repo.get_lore_entry_details(lore_id)
    assert details['Title'] == new_title
    assert details['Content'] == new_content
    assert details['Category'] == new_category

def test_delete_lore_entry(lore_repo: LoreRepository):
    """Tests successful deletion of a lore entry."""
    lore_id = create_test_lore(lore_repo, "Entry to Delete")
    
    success = lore_repo.delete_lore_entry(lore_id)
    assert success is True
    
    # Verify it is gone
    details = lore_repo.get_lore_entry_details(lore_id)
    assert details is None
    
def test_search_lore_entries_by_title_content_category_and_tag(lore_repo: LoreRepository, tag_repo: TagRepository):
    """Tests the hybrid search function, checking for all four search fields."""
    
    # Setup Data
    lore_id_1 = create_test_lore(lore_repo, "The Blue Staff", category="Item", content="A staff of ancient origin.")
    lore_id_2 = create_test_lore(lore_repo, "The Crystal Caves", category="Location", content="Deep, dark, and dangerous.")
    lore_id_3 = create_test_lore(lore_repo, "The Great War", category="History", content="An event in the past.")
    
    # Add a Tag to Lore 3 (tag will be 'conflict')
    tag_repo.set_tags_for_lore_entry(lore_id_3, ['conflict'])

    # 1. Search by Title fragment
    results = lore_repo.search_lore_entries("Blue")
    assert len(results) == 1
    assert results[0]['Title'] == "The Blue Staff"
    
    # 2. Search by Content fragment
    results = lore_repo.search_lore_entries("dangerous")
    assert len(results) == 1
    assert results[0]['Title'] == "The Crystal Caves"
    
    # 3. Search by Category fragment
    results = lore_repo.search_lore_entries("History")
    assert len(results) == 1
    assert results[0]['Title'] == "The Great War"
    
    # 4. Search by Tag (The tag name is 'conflict', the user query should match the tag name)
    results = lore_repo.search_lore_entries("conflict")
    assert len(results) == 1
    assert results[0]['Title'] == "The Great War"
