# tests/repository/test_tag_repository.py

import pytest
from src.python.repository.tag_repository import TagRepository
from src.python.repository.chapter_repository import ChapterRepository
from src.python.repository.lore_repository import LoreRepository
from src.python.db_connector import DBConnector 

@pytest.fixture
def tag_repo(initialized_connector: DBConnector) -> TagRepository:
    """Provides a fresh TagRepository instance for each test."""
    return TagRepository(initialized_connector)

@pytest.fixture
def chapter_repo(initialized_connector: DBConnector) -> ChapterRepository:
    """Provides a ChapterRepository instance for creating association targets."""
    return ChapterRepository(initialized_connector)

@pytest.fixture
def lore_repo(initialized_connector: DBConnector) -> LoreRepository:
    """Provides a LoreRepository instance for creating association targets."""
    return LoreRepository(initialized_connector)

# --- Tests ---

def test_normalize_and_create_tag(tag_repo: TagRepository):
    """Tests that _create_tag handles normalization and deduplication."""
    # 1. Create a tag with inconsistent formatting
    tag_name_a = "  sci-fi genre "
    tag_id_a = tag_repo._create_tag(tag_name_a)
    
    assert isinstance(tag_id_a, int)
    
    # 2. Check that the stored name is normalized
    conn = tag_repo.db.conn
    cursor = conn.execute("SELECT Name FROM Tags WHERE ID = ?", (tag_id_a,))
    stored_name = cursor.fetchone()['Name']
    assert stored_name == "sci-fi genre"
    
    # 3. Attempt to create the same tag (should return the same ID)
    tag_name_b = "Sci-Fi Genre" # Different capitalization/spacing
    tag_id_b = tag_repo._create_tag(tag_name_b)
    
    assert tag_id_a == tag_id_b

# --- Chapter Tag Tests ---

def test_set_tags_for_chapter_creation_and_retrieval(tag_repo: TagRepository, chapter_repo: ChapterRepository):
    """Tests creating new tags and setting them on a chapter."""
    chapter_id = chapter_repo.create_chapter("New Chapter", 1)
    tag_list = ["adventure", "fantasy", "magic"]
    
    success = tag_repo.set_tags_for_chapter(chapter_id, tag_list)
    assert success is True
    
    retrieved_tags = tag_repo.get_tags_for_chapter(chapter_id)
    
    # Check count and names (ordering by name ASC)
    assert len(retrieved_tags) == 3
    tag_names = [name for id, name in retrieved_tags]
    assert tag_names == ["adventure", "fantasy", "magic"] # Checks proper sorting

def test_set_tags_for_chapter_replacement(tag_repo: TagRepository, chapter_repo: ChapterRepository):
    """Tests that the tags are correctly replaced."""
    chapter_id = chapter_repo.create_chapter("Chapter Two", 2)
    
    # 1. Set initial tags
    tag_repo.set_tags_for_chapter(chapter_id, ["old", "keep"])
    assert len(tag_repo.get_tags_for_chapter(chapter_id)) == 2
    
    # 2. Set new list (should remove 'old' and add 'new')
    new_tag_list = ["new", "keep"]
    tag_repo.set_tags_for_chapter(chapter_id, new_tag_list)
    
    retrieved_tags = tag_repo.get_tags_for_chapter(chapter_id)
    tag_names = {name for id, name in retrieved_tags}
    
    assert len(tag_names) == 2
    assert "old" not in tag_names
    assert "new" in tag_names
    assert "keep" in tag_names

# --- Lore Tag Tests ---

def test_set_tags_for_lore_entry_creation_and_retrieval(tag_repo: TagRepository, lore_repo: LoreRepository):
    """Tests creating new tags and setting them on a lore entry."""
    lore_id = lore_repo.create_lore_entry("New Lore")
    tag_list = ["location", "desert"]
    
    # This will fail due to the bug in the provided tag_repository.py
    success = tag_repo.set_tags_for_lore_entry(lore_id, tag_list)
    assert success is True
    
    retrieved_tags = tag_repo.get_tags_for_lore_entry(lore_id)
    
    # Check count and names (ordering by name ASC)
    assert len(retrieved_tags) == 2
    tag_names = [name for id, name in retrieved_tags]
    assert tag_names == ["desert", "location"]
