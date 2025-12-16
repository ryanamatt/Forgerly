-- schema_v1.sql
-- Complete SQLite Schema for The Narrative Forge

-- Enable Foreign Key constraints enforcement, crucial for data integrity checks
PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- 1. Base Content Tables
-- -----------------------------------------------------------------------------

-- CHAPTERS: The primary writing unit.
CREATE TABLE IF NOT EXISTS Chapters (
    ID                      INTEGER PRIMARY KEY, -- Auto-incrementing primary key
    Title                   TEXT NOT NULL,
    Text_Content            TEXT,                -- Stores rich text (HTML)
    Sort_Order              INTEGER NOT NULL,    -- For outline hierarchy/order
    Start_Date              TEXT,                -- Chronological start date (Text to allow user to set Data themeselves)
    End_Date                TEXT,                -- Chronological end date (Text to allow user to set Data themeselves)
    Precursor_Chapter_ID    INTEGER,             -- Self-referencing FK for causality
    POV_Character_ID        INTEGER,

    -- Foreign Key Constraint for self-reference
    FOREIGN KEY (Precursor_Chapter_ID) REFERENCES Chapters(ID) ON DELETE SET NULL,
    FOREIGN KEY (POV_Character_ID) REFERENCES Characters(ID) on DELETE SET NULL
);

-- Lore_Entries: The world wiki/knowledge base. Items, Magic, etc.
CREATE TABLE IF NOT EXISTS Lore_Entries (
    ID                      INTEGER PRIMARY KEY,
    Title                   TEXT NOT NULL UNIQUE,
    Content                 TEXT,
    Category                TEXT,                 -- e.g., 'Location', 'Magic System', 'History'
    Parent_Lore_ID          INTEGER,              -- Allows for Nested Lore Entries

    -- Foreign Key Constraint for self-reference (crucial for deletion)
    FOREIGN KEY (Parent_Lore_ID) REFERENCES Lore_Entries(ID) ON DELETE CASCADE
);

-- CHARACTERS: Named entities in the narrative.
CREATE TABLE IF NOT EXISTS Characters (
    ID                      INTEGER PRIMARY KEY,
    Name                    TEXT NOT NULL UNIQUE,
    Description             TEXT,
    Status                  TEXT,                  -- e.g., 'Alive', 'Deceased', 'Major', 'Minor'
    Age                     INTEGER,               -- Years
    Date_of_Birth           TEXT,                  -- Allow for User Created Dates
    Occupation_School       TEXT,
    Physical_Description    TEXT
);

-- LOCATIONS: Physical or conceptual places in the narrative.
CREATE TABLE IF NOT EXISTS Locations (
    ID                      INTEGER PRIMARY KEY,
    Name                    TEXT NOT NULL UNIQUE,
    Description             TEXT,
    Type                    TEXT,               -- e.g., 'City', 'Building', 'Planet', 'Pocket Dimension'
    Parent_Location_ID      INTEGER,            -- For hierarchical locations (e.g., Room inside a Building)

    FOREIGN KEY (Parent_Location_ID) REFERENCES Locations(ID) ON DELETE SET NULL
);

-- TIMELINE_EVENTS: Specific chronological plot points.
CREATE TABLE IF NOT EXISTS Timeline_Events (
    ID                      INTEGER PRIMARY KEY,
    Title                   TEXT NOT NULL,
    Event_Date              TEXT NOT NULL,
    Description             TEXT,
    Chapter_ID              INTEGER,
    Lore_ID                 INTEGER,

    FOREIGN KEY (Chapter_ID) REFERENCES Chapters(ID) ON DELETE SET NULL,
    FOREIGN KEY (Lore_ID) REFERENCES Lore_Entries(ID) ON DELETE SET NULL
);

-- -----------------------------------------------------------------------------
-- 2. Auxiliary and Join Tables
-- -----------------------------------------------------------------------------

-- TAGS: Flexible metadata for linking knowledge.
CREATE TABLE IF NOT EXISTS Tags (
    ID                      INTEGER PRIMARY KEY,
    Name                    TEXT NOT NULL UNIQUE
);

-- CHAPTER_TAGS: Many-to-many relationship between Chapters and Tags.
CREATE TABLE IF NOT EXISTS Chapter_Tags (
    Chapter_ID              INTEGER NOT NULL,
    Tag_ID                  INTEGER NOT NULL,

    PRIMARY KEY (Chapter_ID, Tag_ID),
    FOREIGN KEY (Chapter_ID) REFERENCES Chapters(ID) ON DELETE CASCADE,
    FOREIGN KEY (Tag_ID) REFERENCES Tags(ID) ON DELETE CASCADE
);

-- LORE_TAGS: Many-to-many relationship between Lore_Entries and Tags.
CREATE TABLE IF NOT EXISTS Lore_Tags (
    Lore_ID                 INTEGER NOT NULL,
    Tag_ID                  INTEGER NOT NULL,

    PRIMARY KEY (Lore_ID, Tag_ID),
    FOREIGN KEY (Lore_ID) REFERENCES Lore_Entries(ID) ON DELETE CASCADE,
    FOREIGN KEY (Tag_ID) REFERENCES Tags(ID) ON DELETE CASCADE
);

-- LORE_LOCATIONS: Many-to-many relationship linking lore entries to their relevant locations.
CREATE TABLE IF NOT EXISTS Lore_Locations (
    Lore_ID                 INTEGER NOT NULL,
    Location_ID             INTEGER NOT NULL,

    PRIMARY KEY (Lore_ID, Location_ID),
    FOREIGN KEY (Lore_ID) REFERENCES Lore_Entries(ID) ON DELETE CASCADE,
    FOREIGN KEY (Location_ID) REFERENCES Locations(ID) ON DELETE CASCADE
);

-- CHAPTER_CHARACTERS: Many-to-many relationship tracking character appearances in chapters.
CREATE TABLE IF NOT EXISTS Chapter_Characters (
    Chapter_ID              INTEGER NOT NULL,
    Character_ID            INTEGER NOT NULL,
    Role_In_Chapter         TEXT,           -- e.g., 'Protagonist', 'Antagonist', 'Mentioned', 'Cameo'

    PRIMARY KEY (Chapter_ID, Character_ID),
    FOREIGN KEY (Chapter_ID) REFERENCES Chapters(ID) ON DELETE CASCADE,
    FOREIGN KEY (Character_ID) REFERENCES Characters(ID) ON DELETE CASCADE
);

-- CHAPTER_LORE: Explicitly links chapters to the lore entries they reference.
CREATE TABLE IF NOT EXISTS Chapter_Lore (
    Chapter_ID              INTEGER NOT NULL,
    Lore_ID                 INTEGER NOT NULL,

    PRIMARY KEY (Chapter_ID, Lore_ID),
    FOREIGN KEY (Chapter_ID) REFERENCES Chapters(ID) ON DELETE CASCADE,
    FOREIGN KEY (Lore_ID) REFERENCES Lore_Entries(ID) ON DELETE CASCADE
);

-- CHARACTER_LORE: Explicitly links characters to the lore entries they reference.
CREATE TABLE IF NOT EXISTS Character_Lore (
    Character_ID              INTEGER NOT NULL,
    Lore_ID                   INTEGER NOT NULL,

    PRIMARY KEY (Character_ID, Lore_ID),
    FOREIGN KEY (Character_ID) REFERENCES Characters(ID) ON DELETE CASCADE,
    FOREIGN KEY (Lore_ID) REFERENCES Lore_Entries(ID) ON DELETE CASCADE
);

-- CHAPTER_LOCATIONS: Links chapters to the locations where the scene takes place.
CREATE TABLE IF NOT EXISTS Chapter_Locations (
    Chapter_ID              INTEGER NOT NULL,
    Location_ID             INTEGER NOT NULL,
    Is_Primary_Setting      INTEGER DEFAULT 0,  -- 1 for the main setting, 0 otherwise

    PRIMARY KEY (Chapter_ID, Location_ID),
    FOREIGN KEY (Chapter_ID) REFERENCES Chapters(ID) ON DELETE CASCADE,
    FOREIGN KEY (Location_ID) REFERENCES Locations(ID) ON DELETE CASCADE
);

-- CHARACTER_LOCATIONS: Links characters to significant locations.
CREATE TABLE IF NOT EXISTS Character_Locations (
    Character_ID            INTEGER NOT NULL,
    Location_ID             INTEGER NOT NULL,
    Location_Role           TEXT,               -- e.g., 'Hometown', 'Current Residence', 'Place of Work'
    Is_Primary              INTEGER DEFAULT 0,  -- 1 for the most important location (e.g., Hometown)

    PRIMARY KEY (Character_ID, Location_ID),
    FOREIGN KEY (Character_ID) REFERENCES Characters(ID) ON DELETE CASCADE,
    FOREIGN KEY (Location_ID) REFERENCES Locations(ID) ON DELETE CASCADE
);

-- -----------------------------------------------------------------------------
-- 3. Supporting Tables
-- -----------------------------------------------------------------------------

-- RELATIONSHIP_TYPES: Customizable types of relationships and their colors.
CREATE TABLE IF NOT EXISTS Relationship_Types (
    ID                      INTEGER PRIMARY KEY,
    Type_Name               TEXT NOT NULL UNIQUE,       -- e.g. 'Allies', 'Rivals', 'Siblings', etc.
    Short_Label             TEXT NOT NULL,              -- Short label for display on the graph edge (e.g., 'Rival')
    Default_Color           TEXT NOT NULL,              -- e.g., '#00FF00', a hex code for UI
    Is_Directed             INTEGER NOT NULL DEFAULT 0,  -- 0 for mutual, 1 for directed
    Line_Style              TEXT NOT NULL DEFAULT 'Solid' -- for dashed/dotted lines
);

-- RELATIONSHIPS: Tracks defined relationships between two characters.
CREATE TABLE IF NOT EXISTS Character_Relationships (
    ID                      INTEGER PRIMARY KEY,
    Character_A_ID          INTEGER NOT NULL,
    Character_B_ID          INTEGER NOT NULL,
    Type_ID                 INTEGER NOT NULL,   -- e.g., "Rivalry", "Family", "Mentor/Student"
    Lore_ID                 INTEGER,   -- Links relationship to a contextual Lore Entry
    Description             TEXT,
    Intensity               INTEGER DEFAULT 50,  -- Numberical Score (1, 100) for line thickness
    Start_Chapter_ID        INTEGER,            -- When the relationship began
    End_Chapter_ID          INTEGER ,           -- When the relationship ended 

    -- Constraint: Characters A and B must be distinct
    CHECK (Character_A_ID != Character_B_ID),
    UNIQUE(Character_A_ID, Character_B_ID),

    FOREIGN KEY (Character_A_ID) REFERENCES Characters(ID) ON DELETE CASCADE,
    FOREIGN KEY (Character_B_ID) REFERENCES Characters(ID) ON DELETE CASCADE,
    FOREIGN KEY (Type_ID) REFERENCES Relationship_Types(ID) ON DELETE RESTRICT,
    FOREIGN KEY (Lore_ID) REFERENCES Lore_Entries(ID) ON DELETE SET NULL,
    FOREIGN KEY (Start_Chapter_ID) REFERENCES Chapters(ID) ON DELETE SET NULL,
    FOREIGN KEY (End_Chapter_ID) REFERENCES Chapters(ID) ON DELETE SET NULL
);

-- CHARACTER_NODE_POSITIONS: Stores the character's last known position on the graph.
CREATE TABLE IF NOT EXISTS Character_Node_Positions (
    Character_ID            INTEGER PRIMARY KEY,
    X_Position              FLOAT NOT NULL,
    Y_Position              FLOAT NOT NULL,
    Node_Color              TEXT DEFAULT '#FFFFFF',
    Node_Shape              TEXT DEFAULT 'Circle',
    Is_Hidden               INTEGER DEFAULT 0, -- BOOLEAN

    FOREIGN KEY (Character_ID) REFERENCES Characters(ID) ON DELETE CASCADE
);

-- VERSION_HISTORY: Records snapshots of chapter drafts.
CREATE TABLE IF NOT EXISTS Version_History (
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
CREATE INDEX IF NOT EXISTS idx_chapters_precursor ON Chapters (Precursor_Chapter_ID);
CREATE INDEX IF NOT EXISTS idx_version_chapter ON Version_History (Chapter_ID);

-- Updated indexes for character relationships
CREATE INDEX IF NOT EXISTS idx_relationships_a ON Character_Relationships (Character_A_ID);
CREATE INDEX IF NOT EXISTS idx_relationships_b ON Character_Relationships (Character_B_ID);
CREATE INDEX IF NOT EXISTS idx_relationships_type ON Character_Relationships (Type_ID);
CREATE INDEX IF NOT EXISTS idx_relationships_lore ON Character_Relationships (Lore_ID);

-- Node positions index
CREATE INDEX IF NOT EXISTS idx_node_positions_char ON Character_Node_Positions (Character_ID);

-- Lore indexes
CREATE INDEX IF NOT EXISTS idx_chapter_tags_tag ON Chapter_Tags (Tag_ID);
CREATE INDEX IF NOT EXISTS idx_lore_tags_tag ON Lore_Tags (Tag_ID);
CREATE INDEX IF NOT EXISTS idx_lore_locations_location on LORE_Locations (Location_ID);
CREATE INDEX IF NOT EXISTS vix_lore_title ON Lore_Entries(Title);
CREATE INDEX IF NOT EXISTS idx_lore_category ON Lore_Entries (Category);

-- Index for quick lookup of locations by character
CREATE INDEX IF NOT EXISTS idx_char_locations_char ON Character_Locations (Character_ID);

-- Index for quick lookup of characters by location
CREATE INDEX IF NOT EXISTS idx_char_locations_loc ON Character_Locations (Location_ID);

-- Index for quick look up of Chapters by Title (e.g., for search/autocomplete)
CREATE INDEX IF NOT EXISTS idx_chapters_title ON Chapters (Title);
