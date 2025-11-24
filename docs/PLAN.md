# **The Narrative Forge: Reworked Development Plan (Epics \-\> Stories \-\> Tasks)**

This plan reorganizes the development roadmap to prioritize database structure and definition as the first major Epic, ensuring a stable schema foundation before implementing any application logic. The GUI layer is standardized on Python/PyQt6.

## **沈 Epic 1: Database Foundation & Schema (The Blueprint)**

**Goal:** Define and implement the complete SQLite database schema, including all tables, columns, and relationships required for the entire application.

| Story ID | Primary Language | Tasks |
| :---- | :---- | :---- |
| **1.1** | SQL | 1\. Define base tables: Chapters, Lore\_Entries, and Characters. 2\. Ensure Chapters includes: ID, Title, Text\_Content (rich text), Sort\_Order, Start\_Date, End\_Date, and Precursor\_Chapter\_ID. 3\. Implement the initial SQL schema creation script (saved to sql/schema\_v1.sql). |
| **1.2** | SQL | 1\. Define auxiliary tables for relationships: Tags (ID, Name, UNIQUE). 2\. Define join tables for many-to-many relationships: Chapter\_Tags (Chapter\_ID, Tag\_ID) and Lore\_Tags (Lore\_ID, Tag\_ID). |
| **1.3** | SQL | 1\. Define the Relationships table structure: ID, Character\_A\_ID, Character\_B\_ID, Type (e.g., "Rivalry"), and Strength\_Score (1-10 integer). 2\. Define the Version\_History table structure: ID, Chapter\_ID, Timestamp, File\_Hash, User\_Comment, and Archive\_Path. 3\. Ensure all FKs are properly constrained (ON DELETE CASCADE where applicable). |

##  **Epic 2: Core Data Management (The Editor)**

**Goal:** Implement the foundational CRUD (Create, Read, Update, Delete) logic and repository layer for all core entities (Chapters, Lore, Characters).

| Story ID | Primary Language | Tasks |
| :---- | :---- | :---- |
| **2.1** | Python / SQL | 1\. Implement Chapter CRUD methods within ChapterRepository. 2\. Implement the full Chapter Tagging logic via TagRepository. 3\. Integrate with AppCoordinator for initial save/load cycles. |
| **2.2** | Python / SQL | 1\. Implement Lore Entry CRUD methods within LoreRepository. 2\. Implement the Lore Entry Tagging logic via TagRepository. |
| **2.3** | Python / SQL | 1\. Implement Character CRUD methods within a new CharacterRepository. 2\. Define Character attributes (Name, Bio, Appearance) storage and retrieval. |

##  **Epic 3: Interface & Polish (The Writer's Room)**

**Goal:** Finalize the main UI components, views, and cross-component communication for a seamless writing experience.

| Story ID | Primary Language | Tasks |
| :---- | :---- | :---- |
| **3.1** | Python (PyQt6) | 1\. Finalize the RichTextEditor component, ensuring all toolbar actions (font, color, block style) are fully functional. 2\. Implement robust dirty-checking and autosave integration in the AppCoordinator. |
| **3.2** | Python (PyQt6) | 1\. Implement the LoreOutlineManager for displaying and managing Lore entries. 2\. Connect outline selection to the LoreEditor via AppCoordinator. |
| **3.3** | Python (PyQt6) | 1\. Create a dedicated CharacterEditor view (UI). 2\. Implement display and editing of Character metadata (Name, Bio, etc.). |

##  **Epic 4: Deep Search & Relationship Mapping (The Analyst)**

**Goal:** Leverage the database's FTS capabilities to provide powerful, grounded search, and implement the tools to map character relationships.

| Story ID | Primary Language | Tasks |
| :---- | :---- | :---- |
| **4.1** | Python / SQL (FTS5) | 1\. Implement a dedicated SearchRepository to centralize all search logic. 2\. Write a comprehensive SQL query using UNION ALL across Chapter, Lore, and Character FTS tables to return unified results. 3\. The query must return (ID, Title, Snippet, Type). |
| **4.2** | Python (PyQt6) | 1\. Create a dedicated SearchDialog accessible from the main menu or toolbar. 2\. Implement the UI with a simple query input and a results display (e.g., QListView or QTableWidget). 3\. Connect the search input to the SearchRepository via the AppCoordinator. |
| **4.3** | Python (PyQt6) | 1\. Implement selection logic in the SearchDialog to signal AppCoordinator to load the corresponding Chapter, Lore, or Character view when a result is activated. 2\. Display the type and title of the result prominently. |
| **4.4** | Python / SQL | 1\. Implement a RelationshipRepository to manage the Relationships table (CRUD). 2\. Include a method to retrieve all relationships for a given Character ID. |
| **4.5** | Python (PyQt6) | 1\. Create a CharacterRelationshipPanel UI component to be integrated into the CharacterEditor. 2\. Implement display of existing relationships (Character B, Type, Strength Score). 3\. Add full CRUD functionality (Add/Edit/Delete) for character relationships using the RelationshipRepository. |

##  **Epic 5: Version Management & History (The Archivist)**

**Goal:** Provide full version control for chapters, allowing writers to take snapshots, compare versions, and restore content.

| Story ID | Primary Language | Tasks |
| :---- | :---- | :---- |
| **5.1** | C (Extension) / Python | 1\. Write a C function (snapshot\_engine) that takes a file path, calculates its SHA-256 hash, and performs a file copy logic (e.g., copy or basic zip) to save the file into the archives directory (data/archives). 2\. Return the calculated hash and archive file path. |
| **5.2** | Python (PyQt6) / SQL | 1\. Create a dedicated QDialog or dockable panel for the VersionManager. 2\. Implement a QTableView or QListWidget to display the version history. 3\. Write logic to fetch and populate the view with data (Timestamp, Chapter Title, Comment) from the Version\_History table. |
| **5.3** | Python / C | 1\. Add a "Take Snapshot" button to the Chapter Editor UI. 2\. Implement Python logic to get the current Chapter's content path and prompt the user for a comment. 3\. Call the C Snapshot Engine (5.1) using **ctypes**. 4\. Upon successful return, save the resulting metadata (hash, comment, timestamp, Chapter ID) to the Version\_History table. |
| **5.4** | Python | 1\. Write a Python script that takes two archived file paths (Version A and Version B). 2\. Use Python's **difflib** module to generate a line-by-line comparison (diff). 3\. Return the diff output, formatted (e.g., as a string in unified or context format). |
| **5.5** | Python (PyQt6) | 1\. Implement a mechanism in the Version Manager (5.2) to allow the user to select two versions for comparison. 2\. Create a specialized Diff Viewer QTextEdit or panel to display the output from the Comparison Utility (5.4). 3\. Implement text formatting to apply **color-coding** for added lines (green) and removed lines (red). |

##  **Epic 6: Spellcheck & Custom Lexicon (The Proofreader)**

**Goal:** Implement a fast, project-aware spell-checking system using a C/C++ backend for performance and a custom user dictionary stored in the database.

| Story ID | Primary Language | Tasks |
| :---- | :---- | :---- |
| **6.1** | SQL / Python | 1\. Define a new database table Custom\_Lexicon (ID, Word TEXT UNIQUE, Status TEXT, Language TEXT DEFAULT 'en-US'). 2\. Implement a CustomDictionaryRepository (Python) for all CRUD operations on this table. 3\. Add a method to fetch all words in the lexicon. |
| **6.2** | C/C++ / Python | 1\. **Integrate a high-performance US English wordlist (e.g., via a Trie structure) into the C/C++ module for checking standard words.** 2\. Implement a C/C++ function (spell\_check\_word) that takes a word and a list of custom words, and returns a boolean (is\_spelled\_correctly). **This function will be a performance bottleneck and must be optimized.** 3\. Implement Python binding for the C/C++ function using **ctypes**. |
| **6.3** | Python (PyQt6) | 1\. Modify the RichTextEditor to listen for document content changes. 2\. Implement logic to tokenize the text and use the C/C++ function (6.2) to check each word. 3\. Use QTextCharFormat with a custom TextUnderlineStyle.SpellCheckUnderline to draw wavy red lines under misspelled words. |
| **6.4** | Python (PyQt6) | 1\. Create a CustomDictionaryDialog (QDialog) to allow the user to view, add, and remove words from the Custom\_Lexicon using the repository (6.1). 2\. Integrate the dialog into the MainWindow's menu (e.g., under "Tools"). |

##  **Epic 7: Character and Lore Statistics (The Data Analyst)**

**Goal:** Provide quantitative feedback and metrics on the story's focus, helping the writer ensure balanced pacing and character development.

| Story ID | Primary Language | Tasks |
| :---- | :---- | :---- |
| **7.1** | Python / SQL | 1\. Implement a StatsRepository method to calculate the total word count for all chapters and lore entries. 2\. Implement a separate method to count the usage frequency of each unique tag across all content. |
| **7.2** | Python / SQL | 1\. Implement a character mention analysis method that scans all chapter content (using FTS or basic string matching with character names) to count total mentions for each character. |
| **7.3** | Python (PyQt6) | 1\. Create a new StatisticsViewer component (QDockWidget or QDialog). 2\. Display word count summaries and tag frequency lists. 3\. Use a visualization tool (e.g., bar chart or pie chart) to display character mention distribution. |
| **7.4** | Python (PyQt6) | 1\. Add a menu item or toolbar button to the MainWindow to open the StatisticsViewer (7.3). 2\. Ensure data refresh logic is triggered when the view is opened or when the underlying data is saved. |

##  **Epic 8: External Resource Synchronization (The Collector)**

**Goal:** Allow users to link external documents, mood boards, or research materials, keeping everything central to the project.

| Story ID | Primary Language | Tasks |
| :---- | :---- | :---- |
| **8.1** | SQL / Python | 1\. Define a new database table External\_Resources (ID, URL TEXT NOT NULL, Description TEXT, Resource\_Type TEXT, Chapter\_ID FK, Lore\_ID FK). 2\. Implement an ResourceRepository for CRUD operations on this table. |
| **8.2** | Python (PyQt6) | 1\. Create a reusable ResourceLinkManager widget (QListWidget or QTableView) with buttons for Add/Edit/Delete links. 2\. Implement logic to open the link (URL or local file path) using platform-native calls (e.g., QDesktopServices.openUrl). |
| **8.3** | Python (PyQt6) | 1\. Integrate the ResourceLinkManager (8.2) as a panel within both the ChapterEditor and LoreEditor views. 2\. Ensure the correct Chapter\_ID or Lore\_ID is passed to the ResourceRepository when links are added or fetched for the active document. |

