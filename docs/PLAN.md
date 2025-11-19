# **The Narrative Forge: Reworked Development Plan (Epics \-\> Stories \-\> Tasks)**

This plan reorganizes the development roadmap to prioritize database structure and definition as the first major Epic, ensuring a stable schema foundation before implementing any application logic. The GUI layer is standardized on Python/PyQt6.

## **💾 Epic 1: Database Foundation & Schema (The Blueprint)**

**Goal:** Define and implement the complete SQLite database schema, including all tables, columns, and relationships required for the entire application.

| Story ID | Primary Language | Tasks |
| :---- | :---- | :---- |
| **1.1** | SQL | 1\. Define base tables: Chapters, Lore\_Entries, and Characters. 2\. Ensure Chapters includes: ID, Title, Text\_Content (rich text), Sort\_Order, Start\_Date, End\_Date, and Precursor\_Chapter\_ID. 3\. Implement the initial SQL schema creation script (saved to sql/schema\_v1.sql). |
| **1.2** | SQL | 1\. Define auxiliary tables for relationships: Tags (ID, Name, UNIQUE). 2\. Define join tables for many-to-many relationships: Chapter\_Tags (Chapter\_ID, Tag\_ID) and Lore\_Tags (Lore\_ID, Tag\_ID). |
| **1.3** | SQL | 1\. Define the Relationships table structure: ID, Character\_A\_ID, Character\_B\_ID, Type (e.g., "Rivalry"), and Strength\_Score (1-10 integer). 2\. Define the Version\_History table structure: ID, Chapter\_ID, Timestamp, File\_Hash, User\_Comment. |
| **1.4** | SQL | 1\. Review all tables to ensure foreign key constraints are correctly defined: self-referencing FK on Chapters.Precursor\_Chapter\_ID, and FKs connecting join tables (Chapter\_Tags, Lore\_Tags) and relationship tables (Relationships, Version\_History). 2\. Implement all required indexes (e.g., on foreign key columns) for optimal query performance. |

## **🏗️ Epic 2: Foundational Structure & Outline (The Scaffolding)**

**Goal:** Create the core structure, the Python GUI frame, and the rich text writing environment, with Chapters as the main content container.

| Story ID | Primary Language | Tasks |
| :---- | :---- | :---- |
| **2.1** | Python | 1\. Create src/python/db\_connector.py. 2\. Implement a class to handle the SQLite connection lifecycle (open/close). 3\. Implement a generic, safe method (execute\_query) for parameterizing and running SQL statements. |
| **2.2** | Python (PyQt6) | 1\. Initialize the PyQt6 application and the primary QMainWindow. 2\. Implement the main window layout using a splitter/dock widgets (Outline on left, Editor on right). 3\. Create the basic QMenuBar with placeholder File, Edit, and Help menus. |
| **2.3** | Python (PyQt6) | 1\. Implement the Outline Manager using a QTreeWidget. 2\. Define custom QTreeWidgetItem structure to represent Chapters. 3\. Implement basic visual differentiation (icons or font) for Chapter nodes. |
| **2.4** | Python (PyQt6) / SQL | 1\. Implement **Create** logic: modal dialog for new Chapter titles, saving new records to the database. 2\. Implement **Read/Refresh** logic: populate the QTreeWidget by fetching all Chapters from the database on startup. 3\. Implement **Update/Rename** logic: context menu action to rename a node, update the database record. 4\. Implement **Delete** logic: confirmation dialog, context menu action, and deletion of the Chapter record. |
| **2.5** | Python (PyQt6) | 1\. Implement the main drafting panel using a QTextEdit widget. 2\. Configure QTextEdit to support rich text formatting. 3\. Create a QToolBar for common text formatting actions (Bold, Italic, lists, headings). |
| **2.6** | Python (PyQt6) / SQL | 1\. Implement event handler to detect when a Chapter node is selected, triggering the content load. 2\. Implement a function to retrieve the Chapter's text content from SQL and load it into the QTextEdit. 3\. Implement an autosave timer or manual save trigger to read the formatted text (as HTML or Markdown) from the QTextEdit. 4\. Write the database function to persist the serialized text content back into the associated Chapter record. |

## **📚 Epic 3: World Knowledge Base (The Library)**

**Goal:** Integrate the Lore Wiki and tag-based linking system, linking Tags to Chapters and Lore Entries.

| Story ID | Primary Language | Tasks |
| :---- | :---- | :---- |
| **3.1** | Python (PyQt6) | 1\. Create a dedicated QWidget for the Lore Editor panel. 2\. Design the panel to include input fields for Title, Rich Text Content (QTextEdit), and a Tag selector component. 3\. Implement CRUD functionality for Lore entries. |
| **3.2** | Python (PyQt6) / SQL | 1\. Implement logic to fetch all available Tags from the database. 2\. Create a reusable Tagging UI component (e.g., a flow layout of clickable labels or a QListWidget with checkboxes). 3\. Integrate the Tagging UI into both the Lore Editor and Chapter Editor. 4\. Implement logic to save and update the relationships in the Chapter\_Tags and Lore\_Tags join tables upon saving the respective content. |
| **3.3** | Python / SQL | 1\. Write a Python function that accepts a keyword query string. 2\. Implement a SQL query using the LIKE operator to search the Title and Content fields of Lore\_Entries. 3\. Implement basic case-insensitive and, optionally, simple fuzzy matching. 4\. The function should return a structured list of matching Lore data (ID, Title, snippet). |
| **3.4** | Python (PyQt6) | 1\. Create a Search Input bar (QLineEdit) and a QListWidget for displaying results. 2\. Connect the search bar's text change signal to trigger the Python Search Module (3.3). 3\. Display the titles and snippets from the search results in the QListWidget. 4\. Implement a double-click handler on the results list to load the corresponding Lore entry into the Lore Editor Panel (3.1). |

## **🕰️ Epic 4: Chronology and Consistency (The Clockwork)**

**Goal:** Implement temporal data tracking and causality processing based on Chapters, integrating the high-performance C++ module.

| Story ID | Primary Language | Tasks |
| :---- | :---- | :---- |
| **4.1** | Python (PyQt6) | 1\. Update the Chapter editing panel in PyQt6 to include input widgets for Start\_Date and End\_Date (e.g., QDateTimeEdit). 2\. Add an input component (e.g., a QComboBox populated with other Chapters) for selecting the Precursor\_Chapter\_ID. 3\. Implement logic to save and load these new temporal and causality fields to/from the database. |
| **4.2** | C++ | 1\. Design the C++ data structure to hold chapter metadata (ID, Start Date, End Date, Precursor ID). 2\. Write the core C++ function that accepts a list of chapters and checks for chronological errors (e.g., a chapter starts before its precursor ends). 3\. Define the C++ output structure for a conflict report (Chapter ID, Conflict Type, Error Message). |
| **4.3** | Python | 1\. Use the ctypes module to load the compiled C++ library (from src/cpp/causality/). 2\. Implement a Python function that queries the necessary chapter data from SQL. 3\. Write serialization logic to convert Python data structures (list of dicts) into C++ compatible memory structures for input. 4\. Implement deserialization logic to parse the C++ conflict report back into Python data structures (list of dicts). |
| **4.4** | Python | 1\. Write a Python script that uses the database connector (2.1) to fetch all Chapter IDs, Titles, and Date fields. 2\. Use a library like **Matplotlib or Plotly** to generate a visual chronological representation (e.g., a timeline or simple Gantt chart). 3\. Implement logic to save the generated visualization to an image file (e.g., PNG). |
| **4.5** | Python (PyQt6) / C++ | 1\. Implement a function in Python to trigger the full Causality Processor run (calling 4.3). 2\. Upon receiving the conflict report, update the QTreeWidget (Outline Manager) to visually flag any chapter ID listed in the report (e.g., using a red icon or background color). 3\. Implement a click/context menu action on flagged chapters to display the detailed conflict error message in a QMessageBox or dedicated detail panel. |

## **🔍 Epic 5: Deep Search & Relationship Mapping (The Analyst)**

**Goal:** Implement text indexing for search and visualize character interactions across Chapters.

| Story ID | Primary Language | Tasks |
| :---- | :---- | :---- |
| **5.1** | C / C++ | 1\. Implement text **tokenization** for the full manuscript. 2\. Implement the data structure for the **inverted index**: mapping each unique word to a list of its occurrences (Chapter ID, position). 3\. Write the C/C++ utility to read all manuscript text and build the index in memory. |
| **5.2** | C++ | 1\. Write the C++ lookup function that takes a search term and queries the inverted index (5.1). 2\. Implement logic to return a structured list of text locations (Chapter ID, snippet, position/offset). 3\. Expose this lookup function with a **C-compatible signature** for FFI. |
| **5.3** | Python (PyQt6) / SQL | 1\. Create a dedicated panel for Character Relationship management. 2\. Implement QComboBox widgets populated with all characters for selecting Character A and Character B. 3\. Add input for Type and a QSlider or QSpinBox for the Strength Score. 4\. Implement CRUD logic to save, load, and update data in the SQL Relationships table. |
| **5.4** | Python | 1\. Write a Python script to query the Relationships table data. 2\. Use the **Networkx** library to create a graph object where nodes are characters and edges are relationships. 3\. Implement visualization logic to apply dynamic styling to the graph (e.g., edge thickness based on Strength\_Score, node color based on character type). |
| **5.5** | Python (PyQt6) | 1\. Implement a **PyQt6 canvas integration** (e.g., using a Matplotlib backend) within a viewable application panel. 2\. Implement logic to render the Networkx graph (5.4) dynamically onto this canvas. 3\. Add controls (e.g., zoom/pan) for interacting with the visualization. |

## **🔒 Epic 6: Draft Stability and Versioning (The Vault)**

**Goal:** Implement a local, robust version control system for the Chapter drafts using C-level efficiency.

| Story ID | Primary Language | Tasks |
| :---- | :---- | :---- |
| **6.1** | C | 1\. Write the core C function to accept a file path and a destination directory. 2\. Implement file reading logic. 3\. Implement **SHA-256 hash calculation** for the file content. 4\. Implement compression/archival logic (e.g., copy or basic zip) to save the file into the archives directory (data/archives). 5\. Return the calculated hash and archive file path. |
| **6.2** | Python (PyQt6) / SQL | 1\. Create a dedicated QDialog or dockable panel for the Version Manager. 2\. Implement a QTableView or QListWidget to display the version history. 3\. Write logic to fetch and populate the view with data (Timestamp, Chapter Title, Comment) from the Version\_History table. |
| **6.3** | Python / C | 1\. Add a "Take Snapshot" button to the Chapter Editor UI. 2\. Implement Python logic to get the current Chapter's content path and prompt the user for a comment. 3\. Call the C Snapshot Engine (6.1) using **ctypes**. 4\. Upon successful return, save the resulting metadata (hash, comment, timestamp, Chapter ID) to the Version\_History table. |
| **6.4** | Python | 1\. Write a Python script that takes two archived file paths (Version A and Version B). 2\. Use Python's **difflib** module to generate a line-by-line comparison (diff). 3\. Return the diff output, formatted (e.g., as a string in unified or context format). |
| **6.5** | Python (PyQt6) | 1\. Implement a mechanism in the Version Manager (6.2) to allow the user to select two versions for comparison. 2\. Create a specialized Diff Viewer QTextEdit or panel to display the output from the Comparison Utility (6.4). 3\. Implement text formatting to apply **color-coding** for added lines (green) and removed lines (red) within the diff viewer. |

