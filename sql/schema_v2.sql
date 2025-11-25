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
    Text_Content            TEXT,                -- Stores rich text (HTML)
    Sort_Order              INTEGER NOT NULL,    -- For outline hierarchy/order
    Start_Date              TEXT,               -- Recommended Format: 'YYYY-MM-DD' or narrative-sortable text
    End_Date                TEXT,               -- Recommended Format: 'YYYY-MM-DD' or narrative-sortable text
    Precursor_Chapter_ID    INTEGER,             -- Self-referencing FK for causality
    Status_ID               INTEGER DEFAULT 1,  -- FK to Lookup_Values (e.g., Status: 1='Outline')
    Word_Count              INTEGER DEFAULT 0,

    -- Foreign Key Constraint for self-reference
    FOREIGN KEY (Precursor_Chapter_ID) REFERENCES Chapters(ID) ON DELETE SET NULL,
	FOREIGN KEY (Status_ID) REFERENCES Lookup_Values(ID)
);

-- Lore_Entries: The world wiki/knowledge base.
CREATE TABLE Lore_Entries (
    ID                      INTEGER PRIMARY KEY,
    Title                   TEXT NOT NULL UNIQUE,
    Content                 TEXT,
    Category_ID             INTEGER,            -- FK to Lookup_Values (e.g., Category: 'Location', 'Magic System')
    Parent_Lore_ID          INTEGER,
    
    -- FOREIGN Key Contraint for self-refernce
    FOREIGN KEY (Parent_Lore_ID) REFERENCES Lore_Entries(ID) ON DELETE SET NULL,
	FOREIGN KEY (Category_ID) REFERENCES Lookup_Values(ID)
);

-- CHARACTERS: Named entities in the narrative.
CREATE TABLE Characters (
    ID                      INTEGER PRIMARY KEY,
    Name                    TEXT NOT NULL,
    Description             TEXT,
    Status_ID               INTEGER,              -- FK to Lookup_Values (e.g., Status: 'Alive', 'Deceased')
    Age                     INTEGER,
    Birth_Date              TEXT,                 -- Recommended Format: 'YYYY-MM-DD' or narrative-sortable text
    Physical_Description    TEXT,
    Personality_Traits      TEXT                  -- A summary or list of key traits

	FOREIGN KEY (Status_ID) REFERENCES Lookup_Values
);

-- LOCATIONS: Physical or conceptual places in the narrative.
CREATE TABLE Locations (
    ID                      INTEGER PRIMARY KEY,
    Name                    TEXT NOT NULL,
    Description             TEXT,
    Type_ID                 TEXT,               -- FK to Lookup_Values (e.g., Type: 'City', 'Building')
    Parent_Location_ID      INTEGER,            -- For hierarchical locations (e.g., Room inside a Building)

    FOREIGN KEY (Parent_Location_ID) REFERENCES Locations(ID) ON DELETE SET NULL,
	FOREIGN KEY (Type_ID) REFERENCES Lookup_Values(ID)
);

--- SCENES: Granular units of action within a chapter
CREATE TABLE SCENES (
	ID                      INTEGER PRIMARY KEY,
	Chapter_ID              INTEGER NOT NULL,
	Title                   TEXT,
	Text_Content            TEXT,
	Sort_Order              INTEGER NOT NULL,
	Setting_Location_ID     INTEGER,
	Point_Of_View_Character_ID INTEGER, -- Who is the POV character for the scene?

	FOREIGN KEY (Chapter_ID) REFERENCES Chapters(ID) ON DELETE CASCADE,
	FOREIGN KEY (Setting_Location_ID) REFERENCES Locations(ID) ON DELETE SET NULL,
	FOREIGN KEY (Point_Of_View_Character_ID) REFERENCES Characters(ID) ON DELETE SET NULL
);

--- PLOT POINTS: Tracking major goals, mysteris, or narrative beats
CREATE TABLE Plot_Points (
	ID						INTEGER PRIMARY KEY,
	Title					TEXT NOT NULL,
	Description				TEXT,
	Arc_ID                  INTEGER,            -- FK to Lookup_Values (e.g., Arc: 'Main Plot', 'Character Arc')
    Status_ID               INTEGER,            -- FK to Lookup_Values (e.g., Status: 'Unresolved', 'Resolved')
	Introducing_Chapter_ID	INTEGER,
	Resolving_Chapter_ID	INTEGER,

    FOREIGN KEY (Arc_ID) REFERENCES Lookup_Values(ID),
    FOREIGN KEY (Status_ID) REFERENCES Lookup_Values(ID),
	FOREIGN KEY (Introducing_Chapter_ID) REFERENCES Chapters(ID) ON DELETE SET NULL,
    FOREIGN KEY (Resolving_Chapter_ID) REFERENCES Chapters(ID) ON DELETE SET NULL
);

-- -----------------------------------------------------------------------------
-- 2. Auxiliary and Join Tables
-- -----------------------------------------------------------------------------

CREATE TABLE Lookup_Values (
    ID          INTEGER PRIMARY KEY,
    Type_Name   TEXT NOT NULL,  -- e.g., 'ChapterStatus', 'CharacterRole', 'LocationType'
    Value       TEXT NOT NULL,  -- e.g., 'Drafting', 'Complete', 'Protagonist', 'City'
    UNIQUE (Type_Name, Value)
);

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

-- CHARACTER_TAGS: Many-to-many relationship between Characters and Tags.
CREATE TABLE Character_Tags (
    Character_ID            INTEGER NOT NULL,
    Tag_ID                  INTEGER NOT NULL,

    PRIMARY KEY (Character_ID, Tag_ID),
    FOREIGN KEY (Character_ID) REFERENCES Characters(ID) ON DELETE CASCADE,
    FOREIGN KEY (Tag_ID) REFERENCES Tags(ID) ON DELETE CASCADE
);

-- LOCATION_TAGS: Many-to-many relationship between Locations and Tags.
CREATE TABLE Location_Tags (
    Location_ID             INTEGER NOT NULL,
    Tag_ID                  INTEGER NOT NULL,

    PRIMARY KEY (Location_ID, Tag_ID),
    FOREIGN KEY (Location_ID) REFERENCES Locations(ID) ON DELETE CASCADE,
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

-- SCENE_VERSION_HISTORY: Records snapshots of scene drafts
CREATE TABLE Scene_Version_History (
    ID                      INTEGER PRIMARY KEY,
    Scene_ID                INTEGER NOT NULL,
    Timestamp               TEXT NOT NULL,      -- UTC Timestamp of snapshot
    File_Hash               TEXT NOT NULL UNIQUE, -- SHA-256 hash of the archived file
    User_Comment            TEXT,

    FOREIGN KEY (Scene_ID) REFERENCES SCENES(ID) ON DELETE CASCADE
);

-- ARCHIVE_LOG: Tracks items that are soft-deleted or archived
CREATE TABLE Archive_Log (
    ID                      INTEGER PRIMARY KEY,
    Content_Type            TEXT NOT NULL,      -- e.g., 'Chapter', 'Character', 'Lore', 'Scene'
    Content_ID              INTEGER NOT NULL,   -- The ID of the archived record in its original table
    Archive_Date            TEXT NOT NULL,
    Reason_Archived         TEXT,               -- Why was it removed?

    -- Ensures only one archive log entry exists per unique content item
    UNIQUE (Content_Type, Content_ID)
);

-- -----------------------------------------------------------------------------
-- 4. Indexes (Performance)
-- -----------------------------------------------------------------------------

-- Core Indexes
CREATE INDEX idx_chapters_precursor ON Chapters (Precursor_Chapter_ID);
CREATE INDEX idx_chapters_title ON Chapters (Title);
CREATE INDEX idx_version_chapter ON Version_History (Chapter_ID);
CREATE INDEX idx_relationships_a ON Relationships (Character_A_ID);
CREATE INDEX idx_relationships_b ON Relationships (Character_B_ID);
CREATE INDEX idx_chapter_tags_tag ON Chapter_Tags (Tag_ID);
CREATE INDEX idx_lore_tags_tag ON Lore_Tags (Tag_ID);
CREATE INDEX idx_lore_locations_location ON Lore_Locations (Location_ID);
CREATE INDEX idx_character_tags_tag ON Character_Tags (Tag_ID);
CREATE INDEX idx_location_tags_tag ON Location_Tags (Tag_ID);
CREATE INDEX idx_relationships_type ON Relationships (Type_ID);
CREATE INDEX idx_chapter_status ON Chapters (Status_ID);

-- Lore Indexes
CREATE INDEX idx_lore_parent ON Lore_Entries (Parent_Lore_ID);
CREATE INDEX idx_lore_title ON Lore_Entries(Title);
CREATE INDEX idx_lore_category ON Lore_Entries (Category_ID);

-- Scenes and Plot Points Indexes
CREATE INDEX idx_scenes_chapter ON SCENES (Chapter_ID);
CREATE INDEX idx_scenes_location ON SCENES (Setting_Location_ID);
CREATE INDEX idx_scenes_pov ON SCENES (Point_Of_View_Character_ID);
CREATE INDEX idx_plot_points_intro ON Plot_Points (Introducing_Chapter_ID);
CREATE INDEX idx_plot_points_resolve ON Plot_Points (Resolving_Chapter_ID);
CREATE INDEX idx_plot_points_arc ON Plot_Points (Arc_ID);

-- Dependent Table Indexes
CREATE INDEX idx_scene_version_scene ON Scene_Version_History (Scene_ID);
CREATE INDEX idx_archive_type_id ON Archive_Log (Content_Type, Content_ID);
-- NEW INDEX
CREATE INDEX idx_scene_characters_character ON Scene_Characters (Character_ID);

-- Lookup_Values Index
CREATE UNIQUE INDEX idx_lookup_values_unique ON Lookup_Values (Type_Name, Value);