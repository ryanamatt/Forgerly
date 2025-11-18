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
    Start_Date              TEXT,                -- Chronological start date (used by Epic 4)
    End_Date                TEXT,                -- Chronological end date (used by Epic 4)
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

-- Index for quick look up of Chapters by Title (e.g., for search/autocomplete)
CREATE INDEX idx_chapters_title ON Chapters (Title);