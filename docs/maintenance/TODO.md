# 🚀 Project Roadmap
- **Create the Recent Projects for Start Menu**

    - [ ] Create the Recent Projects showing the 3 most recent projects. Will need to store last 3 recent project paths in User Settings.

- **Better Exporting**

    - [ ] Expanded Format Library: Add support for .docx, .rtf, .odt, and .mobi.

    - [ ] Data Interchange: Implement .csv export for Character and Location lists.

    - [ ] C++ Tokenizer Engine: Develop a C++ parser to convert rich text into a neutral intermediate format, enabling fast translation between document syntaxes (Markdown to LaTeX, etc.).

    - [ ] Full Project Export: Allow "Bundle" exports that include Chapters, Notes, Lore, and Locations in a single formatted directory or file.

 - **Version Control** > *Note: Consider using C++ for the core logic if speed becomes an issue.*

    - [ ] Snapshots Table: Add a Snapshots table to the schema to store entity ID, timestamp, and delta data.

    - [ ] C++ Delta Engine: Implement a C++ library to compute and apply text diffs for high-speed manuscript comparison.

    - [ ] History UI: Build a VersionHistoryDialog with a side-by-side diff viewer (Red/Green highlighting).

    - [ ] Rollback Logic: Add the ability to "Restore" a snapshot, replacing the current live text in the database.

- **Importing Functionality**

    - [ ] Multi-Format Ingestion: Develop importers for .docx, .rtf, and .md to allow migration from external editors.

    - [ ] Automated Content Splitting: Use C++ regex parsing to identify chapter breaks and automatically populate the Chapters repository from a single large document.

    - [ ] Entity Discovery: Implement a C++ scanner to identify potential Characters and Locations within imported text for quick database entry.

    - [ ] Bulk Data Import: Support .csv and .json imports for Characters, Lore, and Locations.
 
- **Create Sequal Functionality**
  - [ ] An Option when Creating a New Project to be made a Sequel of a previous project.
 
  - [ ]  Correctly Fill the New Sequel Project with everything from the databse except Chapters.

## 💡 Future Ideas (Not in Any Order)

These are ideas no on the roadmap but may be interesting to add.

- Chronological Timeline View

- Advanced Narrative Analytics

    - Pacing Heatmap

    - POV Distribution

    - Dialog vs Narrative Ratio

- Smart Global Replace (Ex. Change a Characters Name it changes everywhere it is used)

- Focus-Mode

*Last Updated: 2025-1-30*
