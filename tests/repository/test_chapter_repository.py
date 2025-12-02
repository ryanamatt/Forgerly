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
    c_id_2 = chapter_repo.create_chapter("Chapter B", 2, precursor_id=c_id_1)
    
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
    assert 'Precursor_Chapter_ID' in chapters[1]
    assert chapters[1]['Precursor_Chapter_ID'] == c_id_1
    assert chapters[0]['Precursor_Chapter_ID'] is None

def test_get_all_chapters_with_content(chapter_repo: ChapterRepository):
    """Tests retrieval of all chapters including the Text_Content field."""
    chapter_repo.create_chapter("Full Test", 1)
    
    # Act
    chapters = chapter_repo.get_all_chapters_with_content()
    
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