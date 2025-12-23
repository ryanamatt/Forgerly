# tests/repository/test_chapter_repository.py

import pytest
from src.python.repository.chapter_repository import ChapterRepository
from src.python.db_connector import DBConnector # Used for type hinting, though injected by fixture

# The initialized_connector fixture provides a connected, schema-initialized DBConnector
# for each test function that requests it.

@pytest.fixture
def chapter_repo(initialized_connector: DBConnector) -> ChapterRepository:
    """Provides a fresh ChapterRepository instance for each test."""
    return ChapterRepository(initialized_connector)

def test_create_and_get_title(chapter_repo: ChapterRepository):
    """Tests creating a chapter and then retrieving its title."""
    title = "The Journey Begins"
    sort_order = 1
    
    # Act: Create the chapter
    chapter_id = chapter_repo.create_chapter(title, sort_order)
    
    # Assert: Creation was successful and returned an ID
    assert isinstance(chapter_id, int)
    assert chapter_id > 0

    # Act: Retrieve the title
    retrieved_title = chapter_repo.get_chapter_title(chapter_id)
    
    # Assert: Title matches
    assert retrieved_title == title
    
def test_update_chapter_title(chapter_repo: ChapterRepository):
    """Tests updating the title of an existing chapter."""
    chapter_id = chapter_repo.create_chapter("Old Title", 1)
    new_title = "The Road Taken"
    
    # Act
    success = chapter_repo.update_chapter_title(chapter_id, new_title)
    
    # Assert
    assert success is True
    assert chapter_repo.get_chapter_title(chapter_id) == new_title

def test_create_and_update_content(chapter_repo: ChapterRepository):
    """Tests creating a chapter and updating its text content."""
    chapter_id = chapter_repo.create_chapter("Draft Chapter", 2)
    new_content = "<p>This is the rich text of the new chapter.</p>"
    
    # 1. Test initial content (should be "<p></p>" as set in create_chapter)
    initial_content = chapter_repo.get_chapter_content(chapter_id)
    assert initial_content == "<p></p>"
    
    # 2. Update content
    success = chapter_repo.update_chapter_content(chapter_id, new_content)
    assert success is True
    
    # 3. Test retrieved content
    retrieved_content = chapter_repo.get_chapter_content(chapter_id)
    assert retrieved_content == new_content

def test_get_all_chapters_ordering_and_fields(chapter_repo: ChapterRepository):
    """Tests retrieval of all chapters (basic info) and correct ordering."""
    # Setup multiple chapters in random insertion order but defined Sort_Order
    c_id_3 = chapter_repo.create_chapter("Chapter C", 3)
    c_id_1 = chapter_repo.create_chapter("Chapter A", 1)
    c_id_2 = chapter_repo.create_chapter("Chapter B", 2)
    
    # Act
    chapters = chapter_repo.get_all_chapters()
    
    # Assert
    assert len(chapters) == 3
    # Check Sort_Order is correct
    assert chapters[0]['Title'] == "Chapter A"
    assert chapters[1]['Title'] == "Chapter B"
    assert chapters[2]['Title'] == "Chapter C"
    
    # Check expected fields are present (ID, Title, Sort_Order, Precursor_Chapter_ID)
    assert 'ID' in chapters[0]

def test_get_all_chapters_with_content(chapter_repo: ChapterRepository):
    """Tests retrieval of all chapters including the Text_Content field."""
    chapter_repo.create_chapter("Full Test", 1)
    
    # Act
    chapters = chapter_repo._get_all_chapters_with_content()
    
    # Assert
    assert len(chapters) == 1
    # Check that the Text_Content field is present
    assert 'Text_Content' in chapters[0]
    assert chapters[0]['Text_Content'] == "<p></p>" # Default content

def test_delete_chapter(chapter_repo: ChapterRepository):
    """Tests deletion of a chapter."""
    chapter_id = chapter_repo.create_chapter("To Be Deleted", 10)
    
    # 1. Verify existence
    assert chapter_repo.get_chapter_title(chapter_id) is not None
    
    # 2. Act: Delete
    success = chapter_repo.delete_chapter(chapter_id)
    
    # 3. Verify deletion
    assert success is True
    assert chapter_repo.get_chapter_title(chapter_id) is None

def test_get_all_chapters_for_export_all(chapter_repo: ChapterRepository):
    """
    Tests retrieval of all chapters for export (no ID filter) and ensures correct ordering.
    NOTE: Assuming no Tags are returned, as no JOIN is implemented in the current repo logic.
    """
    # Setup
    c2_id = chapter_repo.create_chapter("Chapter Two", 2)
    c1_id = chapter_repo.create_chapter("Chapter One", 1)
    c3_id = chapter_repo.create_chapter("Chapter Three", 3)
    
    # Act
    chapters = chapter_repo.get_all_chapters_for_export()
    
    # Assert
    assert len(chapters) == 3
    # Check ordering by Sort_Order
    assert chapters[0]['ID'] == c1_id
    assert chapters[0]['Title'] == "Chapter One"
    assert chapters[2]['ID'] == c3_id
    
    # Check required fields are present (simplified for this test)
    assert 'Text_Content' in chapters[0]
    assert chapters[0]['Text_Content'] == "<p></p>"
    assert 'Sort_Order' in chapters[0]

def test_get_all_chapters_for_export_filtered(chapter_repo: ChapterRepository):
    """Tests retrieval of a specific subset of chapters using ID filtering."""
    # Setup
    c1_id = chapter_repo.create_chapter("Chapter Alpha", 10)
    c2_id = chapter_repo.create_chapter("Chapter Beta", 20)
    c3_id = chapter_repo.create_chapter("Chapter Gamma", 30)
    
    # Act: Filter for Beta and Alpha, but request Beta first (should still return Alpha first due to Sort_Order)
    chapters = chapter_repo.get_all_chapters_for_export(chapter_ids=[c2_id, c1_id])
    
    # Assert
    assert len(chapters) == 2
    
    # Check that only the requested chapters are present, and they are still ordered by Sort_Order (10, then 20)
    assert chapters[0]['ID'] == c1_id
    assert chapters[0]['Sort_Order'] == 10
    assert chapters[1]['ID'] == c2_id
    assert chapters[1]['Sort_Order'] == 20
    
    # Ensure Chapter Gamma (c3_id) was excluded
    assert c3_id not in [c['ID'] for c in chapters]

# --- Test for reorder_chapters ---

def test_reorder_chapters_success(chapter_repo: ChapterRepository):
    """Tests reordering of chapters using the transaction-based update."""
    # Setup: Create chapters with initial order 1, 2, 3
    c1_id = chapter_repo.create_chapter("Chap One", 1)
    c2_id = chapter_repo.create_chapter("Chap Two", 2)
    c3_id = chapter_repo.create_chapter("Chap Three", 3)

    # 1. Verify initial order
    initial_chapters = chapter_repo.get_all_chapters()
    assert initial_chapters[0]['ID'] == c1_id
    assert initial_chapters[2]['ID'] == c3_id

    # Define the new desired order: 3, 1, 2 (new Sort_Order 1, 2, 3 respectively)
    reorder_operations = [
        (c3_id, 1), # Chapter 3 moves to Sort_Order 1
        (c1_id, 2), # Chapter 1 moves to Sort_Order 2
        (c2_id, 3), # Chapter 2 moves to Sort_Order 3
    ]
    
    # Act: Reorder
    success = chapter_repo.reorder_chapters(reorder_operations)
    
    # Assert
    assert success is True
    
    # Verify the new order
    reordered_chapters = chapter_repo.get_all_chapters()
    
    assert len(reordered_chapters) == 3
    # Check the new sequence: c3_id -> c1_id -> c2_id
    assert reordered_chapters[0]['ID'] == c3_id
    assert reordered_chapters[0]['Sort_Order'] == 1
    assert reordered_chapters[1]['ID'] == c1_id
    assert reordered_chapters[1]['Sort_Order'] == 2
    assert reordered_chapters[2]['ID'] == c2_id
    assert reordered_chapters[2]['Sort_Order'] == 3