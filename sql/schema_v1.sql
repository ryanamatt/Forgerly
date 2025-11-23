-- schema_v1.sql
-- Complete SQLite Schema for The Narrative Forge
-- Corresponds to Epic 1: Database Foundation & Schema (Stories 1.1 - 1.4)

-- Enable Foreign Key constraints enforcement, crucial for data integrity checks
PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- 1. Base Content Tables
-- -----------------------------------------------------------------------------

-- CHAPTERS: The primary writing unit.
CREATE TABLE Chapters (
    ID                      INTEGER PRIMARY KEY, -- Auto-incrementing primary key
    Title                   TEXT NOT NULL,
    Text_Content            TEXT,                -- Stores rich text (HTML or Markdown)
    Sort_Order              INTEGER NOT NULL,    -- For outline hierarchy/order
    Start_Date              TEXT,                -- Chronological start date
    End_Date                TEXT,                -- Chronological end date
    Precursor_Chapter_ID    INTEGER,             -- Self-referencing FK for causality

    -- Foreign Key Constraint for self-reference
    FOREIGN KEY (Precursor_Chapter_ID) REFERENCES Chapters(ID) ON DELETE SET NULL
);

-- LORE_ENTRIES: The world wiki/knowledge base.
CREATE TABLE Lore_Entries (
    ID                      INTEGER PRIMARY KEY,
    Title                   TEXT NOT NULL UNIQUE,
    Content                 TEXT,
    Category                TEXT                 -- e.g., 'Location', 'Magic System', 'History'
);

-- CHARACTERS: Named entities in the narrative.
CREATE TABLE Characters (
    ID                      INTEGER PRIMARY KEY,
    Name                    TEXT NOT NULL UNIQUE,
    Description             TEXT,
    Status                  TEXT                  -- e.g., 'Alive', 'Deceased', 'Major', 'Minor'
);

-- LOCATIONS: Physical or conceptual places in the narrative.
CREATE TABLE Locations (
    ID                      INTEGER PRIMARY KEY,
    Name                    TEXT NOT NULL UNIQUE,
    Description             TEXT,
    Type                    TEXT,               -- e.g., 'City', 'Building', 'Planet', 'Pocket Dimension'
    Parent_Location_ID      INTEGER,            -- For hierarchical locations (e.g., Room inside a Building)

    FOREIGN KEY (Parent_Location_ID) REFERENCES Locations(ID) ON DELETE SET NULL
);

-- -----------------------------------------------------------------------------
-- 2. Auxiliary and Join Tables
-- -----------------------------------------------------------------------------

-- TAGS: Flexible metadata for linking knowledge.
CREATE TABLE Tags (
    ID                      INTEGER PRIMARY KEY,
    Name                    TEXT NOT NULL UNIQUE
);

-- CHAPTER_TAGS: Many-to-many relationship between Chapters and Tags.
CREATE TABLE Chapter_Tags (
    Chapter_ID              INTEGER NOT NULL,
    Tag_ID                  INTEGER NOT NULL,

    PRIMARY KEY (Chapter_ID, Tag_ID),
    FOREIGN KEY (Chapter_ID) REFERENCES Chapters(ID) ON DELETE CASCADE,
    FOREIGN KEY (Tag_ID) REFERENCES Tags(ID) ON DELETE CASCADE
);

-- LORE_TAGS: Many-to-many relationship between Lore_Entries and Tags.
CREATE TABLE Lore_Tags (
    Lore_ID                 INTEGER NOT NULL,
    Tag_ID                  INTEGER NOT NULL,

    PRIMARY KEY (Lore_ID, Tag_ID),
    FOREIGN KEY (Lore_ID) REFERENCES Lore_Entries(ID) ON DELETE CASCADE,
    FOREIGN KEY (Tag_ID) REFERENCES Tags(ID) ON DELETE CASCADE
);

-- LORE_LOCATIONS: Many-to-many relationship linking lore entries to their relevant locations.
CREATE TABLE Lore_Locations (
    Lore_ID                 INTEGER NOT NULL,
    Location_ID             INTEGER NOT NULL,

    PRIMARY KEY (Lore_ID, Location_ID),
    FOREIGN KEY (Lore_ID) REFERENCES Lore_Entries(ID) ON DELETE CASCADE,
    FOREIGN KEY (Location_ID) REFERENCES Locations(ID) ON DELETE CASCADE
);

-- CHAPTER_CHARACTERS: Many-to-many relationship tracking character appearances in chapters.
CREATE TABLE Chapter_Characters (
    Chapter_ID              INTEGER NOT NULL,
    Character_ID            INTEGER NOT NULL,
    Role_In_Chapter         TEXT,           -- e.g., 'Protagonist', 'Antagonist', 'Mentioned', 'Cameo'

    PRIMARY KEY (Chapter_ID, Character_ID)
    FOREIGN KEY (Chapter_ID) REFERENCES Chapters(ID) ON DELETE CASCADE,
    FOREIGN KEY (Character_ID) REFERENCES Characters(ID) ON DELETE CASCADE
);

-- CHAPTER_LORE: Explicitly links chapters to the lore entries they reference.
CREATE TABLE Chapter_Lore (
    Chapter_ID              INTEGER NOT NULL,
    Lore_ID                 INTEGER NOT NULL,

    PRIMARY KEY (Chapter_ID, Lore_ID),
    FOREIGN KEY (Chapter_ID) REFERENCES Chapters(ID) ON DELETE CASCADE,
    FOREIGN KEY (Lore_ID) REFERENCES Lore_Entries(ID) ON DELETE CASCADE
);

-- CHAPTER_LOCATIONS: Links chapters to the locations where the scene takes place.
CREATE TABLE Chapter_Locations (
    Chapter_ID              INTEGER NOT NULL,
    Location_ID             INTEGER NOT NULL,
    Is_Primary_Setting      INTEGER DEFAULT 0,  -- 1 for the main setting, 0 otherwise

    PRIMARY KEY (Chapter_ID, Location_ID),
    FOREIGN KEY (Chapter_ID) REFERENCES Chapters(ID) ON DELETE CASCADE,
    FOREIGN KEY (Location_ID) REFERENCES Locations(ID) ON DELETE CASCADE
);

-- -----------------------------------------------------------------------------
-- 3. Supporting Tables
-- -----------------------------------------------------------------------------

-- RELATIONSHIPS: Tracks defined relationships between two characters.
CREATE TABLE Relationships (
    ID                      INTEGER PRIMARY KEY,
    Character_A_ID          INTEGER NOT NULL,
    Character_B_ID          INTEGER NOT NULL,
    Type                    TEXT,               -- e.g., "Rivalry", "Family", "Mentor/Student"
    Strength_Score          INTEGER,            -- Score from 1-10

    -- Constraint: Characters A and B must be distinct
    CHECK (Character_A_ID != Character_B_ID),

    FOREIGN KEY (Character_A_ID) REFERENCES Characters(ID) ON DELETE CASCADE,
    FOREIGN KEY (Character_B_ID) REFERENCES Characters(ID) ON DELETE CASCADE
);

-- VERSION_HISTORY: Records snapshots of chapter drafts.
CREATE TABLE Version_History (
    ID                      INTEGER PRIMARY KEY,
    Chapter_ID              INTEGER NOT NULL,
    Timestamp               TEXT NOT NULL,      -- UTC Timestamp of snapshot
    File_Hash               TEXT NOT NULL UNIQUE, -- SHA-256 hash of the archived file
    User_Comment            TEXT,

    FOREIGN KEY (Chapter_ID) REFERENCES Chapters(ID) ON DELETE CASCADE
);

-- -----------------------------------------------------------------------------
-- 4. Indexes (Performance)
-- -----------------------------------------------------------------------------

-- Indexes to improve lookup performance on foreign keys
CREATE INDEX idx_chapters_precursor ON Chapters (Precursor_Chapter_ID);
CREATE INDEX idx_version_chapter ON Version_History (Chapter_ID);
CREATE INDEX idx_relationships_a ON Relationships (Character_A_ID);
CREATE INDEX idx_relationships_b ON Relationships (Character_B_ID);
CREATE INDEX idx_chapter_tags_tag ON Chapter_Tags (Tag_ID);
CREATE INDEX idx_lore_tags_tag ON Lore_Tags (Tag_ID);
CREATE INDEX idx_lore_locations_location on LORE_Locations (Location_ID);

-- Index for quick look up of Chapters by Title (e.g., for search/autocomplete)
CREATE INDEX idx_chapters_title ON Chapters (Title);

--- DDL For Lore Entry Full-Text Search (FTS5)

-- 1. Create the virtual FTS table, linking it to the Lore Entries content
CREATE VIRTUAL TABLE Lore_Entries_FTS using fts5(
    Title,                  -- Index the Title for searching
    Content,                -- Index the main Content for searching
    Category,
    content='Lore_Entries', -- Link the FTS table to the main Lore_Entries table
    content_rowid='ID',     -- Use the Lore_Entries.ID column as the ROWID
    tokenize='porter'       -- Use the Porter Stemmer for better results (e.g., 'jumping' matches 'jump')
);

-- 2. Create Triggers to keep the FTS index synchronized with the main table
-- The FTS5 module uses triggers to automatically maintain the index when 
-- the content in the original table changes.
CREATE TRIGGER lore_fts_insert AFTER INSERT ON Lore_Entries BEGIN
  INSERT INTO Lore_Entries_FTS(rowid, Title, Content, Category) VALUES (new.ID, new.Title, new.Content, new.Category);
END;

CREATE TRIGGER lore_fts_update AFTER UPDATE ON Lore_Entries BEGIN
  UPDATE Lore_Entries_FTS SET Title = new.Title, Content = new.Content, Category = new.Category WHERE rowid = old.ID;
END;
-- Delete trigger remains unchanged for the FTS table structure
CREATE TRIGGER lore_fts_delete AFTER DELETE ON Lore_Entries BEGIN
  INSERT INTO Lore_Entries_FTS(Lore_Entries_FTS, rowid, Title, Content, Category) VALUES('delete', old.ID, old.Title, old.Content, old.Category);
END;