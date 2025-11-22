# src/python/tag_repository.py

from .db_connector import DBConnector

class TagRepository:
    """
    Manages all database operations for the Tag entity and its associations
    with other entities (e.g., Chapters, Lore).
    """
    def __init__(self, db_connector: DBConnector) -> None:
        self.db = db_connector

    def _normalize_tag_name(self, tag_name: str) -> str:
        """Utility to ensure tags are stored consistently (lowercase, no extra space)."""
        return tag_name.strip().lower()
    
    def _get_tag_id_by_name(self, tag_name: str) -> int | None:
        """Internal method to look up a Tag's ID."""
        clean_name = self._normalize_tag_name(tag_name)
        query = "SELECT ID FROM Tags WHERE Name = ?;"
        result = self.db._execute_query(query, (clean_name,), fetch_one=True)
        return result['ID'] if result else None
    
    def _create_tag(self, tag_name: str) -> int | None:
        """
        Creates a new tag it doesn't exist
        Returns the ID of the new or existing tag
        """
        tag_id = self._get_tag_id_by_name(tag_name)
        if tag_id:
            return tag_id
        
        clean_name = self._normalize_tag_name(tag_name)
        query = "INSERT INTO Tags (Name) VALUES (?);"
        return self.db._execute_commit(query, (clean_name,), fetch_id=True)
    
    # --- Chapter Tag Methods ---

    def get_tags_for_chapter(self, chapter_id: int) -> list[tuple[int, str]]:
        """Retrieves all tags (ID, Name) for a given chapter"""
        query = """
        SELECT t.ID, t.Name
        FROM Tags t
        JOIN Chapter_Tags ct ON t.ID = ct.Tag_ID
        WHERE ct.Chapter_ID = ?
        ORDER BY t.Name ASC;
        """
        return self.db._execute_query(query, (chapter_id,), fetch_all=True, as_list=True)
    
    def set_tags_for_chapter(self, chapter_id: int, tag_names: list[str]) -> bool:
        """
        Replaces all tags for a chapter with the new list.
        Performs transactions to ensure atomicity.
        """
        try:
            # 1. Start a transaction
            self.db.conn.execute("BEGIN;")

            # 2. Clear existing tags for the chapter
            delete_sql = "DELETE FROM Chapter_Tags WHERE Chapter_ID = ?;"
            self.db.conn.execute(delete_sql, (chapter_id,))

            # 3. Insert new tags and associations
            for tag_name in tag_names:
                tag_id = self._create_tag(tag_name)
                if tag_id is not None:
                    insert_sql = "INSERT OR IGNORE INTO Chapter_Tags (Chapter_ID, Tag_ID) VALUES (?, ?);"
                    self.db.conn.execute(insert_sql, (chapter_id, tag_id))

            # 4. Commit the transaction
            self.db.conn.commit()
            return True
        except Exception as e:
            self.db.conn.rollback()
            print(f"Error setting chapter tags: {e}")
            return False