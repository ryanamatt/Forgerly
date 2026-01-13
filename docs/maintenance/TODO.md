# 🚀 Project Roadmap

1. **Implement a Notes Feature**
 
    - [ ] Enable Ctrl+Shift+L inter-entry lookup and tagging support to link notes with Characters and Lore

3. **Implement Locations**

    - [ ] Create location_repository.py and a LocationOutlineManager to support the existing hierarchical Parent_Location_ID structure.

    - [ ] Build a LocationEditor view that allows users to assign "Primary Settings" to chapters and link "Residents" (Characters) or "Lore" to specific places.

    - [ ] Implement filtering and organization based on the Type attribute (e.g., City, Building, Planet).

4. **Update Relationships Graph**

    - [ ] Intensity Threshold Slider: Add a QSlider to dynamically hide edges with an Intensity score below a user-defined value, reducing visual clutter in complex character webs.

    - [ ] Snapshot/Export: Create a "Save as Image" action that renders the current QGraphicsScene into a high-resolution .png or .svg for external story bibles.

5. **Better Exporting**

    - [ ] Expanded Format Library: Add support for .docx, .rtf, .odt, and .mobi.

    - [ ] Data Interchange: Implement .csv export for Character and Location lists.

    - [ ] C++ Tokenizer Engine: Develop a C++ parser to convert rich text into a neutral intermediate format, enabling fast translation between document syntaxes (Markdown to LaTeX, etc.).

    - [ ] Full Project Export: Allow "Bundle" exports that include Chapters, Notes, Lore, and Locations in a single formatted directory or file.

6. **Version Control** > *Note: Consider using C++ for the core logic if speed becomes an issue.*

    - [ ] Snapshots Table: Add a Snapshots table to the schema to store entity ID, timestamp, and delta data.

    - [ ] C++ Delta Engine: Implement a C++ library to compute and apply text diffs for high-speed manuscript comparison.

    - [ ] History UI: Build a VersionHistoryDialog with a side-by-side diff viewer (Red/Green highlighting).

    - [ ] Rollback Logic: Add the ability to "Restore" a snapshot, replacing the current live text in the database.

7. **Importing Functionality**

    - [ ] Multi-Format Ingestion: Develop importers for .docx, .rtf, and .md to allow migration from external editors.

    - [ ] Automated Content Splitting: Use C++ regex parsing to identify chapter breaks and automatically populate the Chapters repository from a single large document.

    - [ ] Entity Discovery: Implement a C++ scanner to identify potential Characters and Locations within imported text for quick database entry.

    - [ ] Bulk Data Import: Support .csv and .json imports for Characters, Lore, and Locations.

## 💡 Future Ideas (Not in Any Order)

- Chronological Timeline View

- Advanced Narrative Analytics

    - Pacing Heatmap

    - POV Distribution

    - Dialog vs Narrative Ratio

- Smart Global Replace (Ex. Change a Characters Name it changes everywhere it is used)

- Focus-Mode

*Last Updated: 2025-1-13*
