# 🚀 Project Roadmap

1. **Implement a Notes Feature**

    - [X] Add Notes and Note_Tags tables to schema_v1.sql with Sort_Order and Parent_Note_ID for nested organization.

    - [X] Create note_repository.py and a NoteOutlineManager view, reusing the RichTextEditor widget.

    - [ ] Enable Ctrl+Shift+L inter-entry lookup and tagging support to link notes with Characters and Lore

2. **Implement Locations**

    - [ ] Create location_repository.py and a LocationOutlineManager to support the existing hierarchical Parent_Location_ID structure.

    - [ ] Build a LocationEditor view that allows users to assign "Primary Settings" to chapters and link "Residents" (Characters) or "Lore" to specific places.

    - [ ] Implement filtering and organization based on the Type attribute (e.g., City, Building, Planet).

3. **Update Relationships Graph**

    - [ ] Refactor RelationshipOutlineManager to QFrame: Transition the class from a QWidget to a QFrame with a StyledPanel shape to ensure visual consistency with the other outline managers in the project.

    - [ ] Relationship Type Filter: Implement a QComboBox in the toolbar that queries the Relationship_Types table, allowing users to toggle the visibility of specific connection categories (e.g., "Family," "Rivals").

    - [ ] Intensity Threshold Slider: Add a QSlider to dynamically hide edges with an Intensity score below a user-defined value, reducing visual clutter in complex character webs.

    - [ ] Toggle Labels: Add a toolbar action to show or hide the Short_Label on relationship edges, which helps maintain readability when the graph is zoomed out.

    - [ ] Lock All Nodes: Implement a "Global Pin" feature that sets the is_fixed flag for all NodeInput structures, preventing the C++ GraphLayoutEngine from moving manually positioned characters during an auto-layout run.

    - [ ] Zoom to Fit: Add a navigation tool to instantly rescale the RelationshipCanvas to encompass all active CharacterNode items in the scene.

    - [ ] Snapshot/Export: Create a "Save as Image" action that renders the current QGraphicsScene into a high-resolution .png or .svg for external story bibles.

4. **Better Exporting**

    - [ ] Expanded Format Library: Add support for .docx, .rtf, .odt, and .mobi.

    - [ ] Data Interchange: Implement .csv export for Character and Location lists.

    - [ ] C++ Tokenizer Engine: Develop a C++ parser to convert rich text into a neutral intermediate format, enabling fast translation between document syntaxes (Markdown to LaTeX, etc.).

    - [ ] Full Project Export: Allow "Bundle" exports that include Chapters, Notes, Lore, and Locations in a single formatted directory or file.

5. **Version Control** > *Note: Consider using C++ for the core logic if speed becomes an issue.*

    - [ ] Snapshots Table: Add a Snapshots table to the schema to store entity ID, timestamp, and delta data.

    - [ ] C++ Delta Engine: Implement a C++ library to compute and apply text diffs for high-speed manuscript comparison.

    - [ ] History UI: Build a VersionHistoryDialog with a side-by-side diff viewer (Red/Green highlighting).

    - [ ] Rollback Logic: Add the ability to "Restore" a snapshot, replacing the current live text in the database.

6. **Importing Functionality**

    - [ ] Multi-Format Ingestion: Develop importers for .docx, .rtf, and .md to allow migration from external editors.

    - [ ] Automated Content Splitting: Use C++ regex parsing to identify chapter breaks and automatically populate the Chapters repository from a single large document.

    - [ ] Entity Discovery: Implement a C++ scanner to identify potential Characters and Locations within imported text for quick database entry.

    - [ ] Bulk Data Import: Support .csv and .json imports for Characters, Lore, and Locations.

## 💡 Future Ideas (Not in Any Order)

- Add SpellChecker

    - C++ Hybrid Engine: Build a spell checker that combines a standard Hunspell dictionary with a Dynamic White-list pulled from Character, Lore, and Location titles.

    - Spell-Check Toggle: Add a toolbar button to enable/disable real-time spell checking (Show/Hide red underlines).

    - Smart Entity Recognition: Automatically suggest existing Character/Location names if a user makes a typo in a proper noun (e.g., if they type "Gandalph," suggest "Gandalf").

    - Personal Dictionary Table: Create a User_Dictionary table in the schema for words the user wants the engine to ignore globally.

- Chronological Timeline View

- Advanced Narrative Analytics

    - Pacing Heatmap

    - POV Distribution

    - Dialog vs Narrative Ratio

- Smart Global Replace (Ex. Change a Characters Name it changes everywehre it is used)

- Focus-Mode

*Last Updated: 2025-12-21*