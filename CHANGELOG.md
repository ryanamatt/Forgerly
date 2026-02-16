# Changelog
All notable changes to Forgerly will be documented in this file.

## v0.4.8 - UNRELEASED

## ✨ Added

- New Button Allows the user to export their Relationship Graph with a new button the toolbar.
  - New Dialog Window with several options you may want to export your graph.
  - Export as PNG, JPG, SVG, or PDF
- A New Setting to Toggle the Spell Checker on/off (Default is off).
- Lore Entry Titles and Characters Names are now added as words for Spell Checking to ensure
you are spelling them correctly and the Spell Checker does not falsely flag them as misspelled.
- Directed Relationship Types has been added.
- A New Setting allowing the user to toggle on/off the Chapter Statistics at the top of the
Chapter Editor.
- Added a Search Bar for the Chapter Outline allowing the user to search chapter titles and tags.
- Creating a new note can now also be done in the Menu Bar.
- Added A Find Search bar (Ctrl+F) to find things in the current editor.

## 🐛 Fixes
- Fix Bug where Relationship Edge Line Style did not update when changed.
- Fix Bug  when showing the Text Size in the Text Editor allowing the user to see the full number.
- Fix Bug when renaming a Character's name using the Text Box in the Character Editor.
- 

## v0.4.7 - 2026-01-26

### ✨ Added
- Chapter Management: Integrated text editor with real-time statistics and a global story overview.

- Character Profiles: Comprehensive biography and profile management system.

- Lore Engine: Dedicated editor for worldbuilding elements, locations, and historical timelines.

- Dynamic Relationship Graph: A visual node-based system to map character connections.

  - Features custom relationship types and intensity sliders.
 
  - Includes "Snap to Grid" and background grid for precision organization.

- Inter-Entry Lookup: Quick-access shortcut (Ctrl+Shift+L) to view character or lore entries directly from the chapter editor.

- Self-Contained Projects: Portable .nforge project structure with local SQLite databases and asset folders.

- Tagging System: Global tagging for filtering entities across the project.

### ⚙️ Technical & Performance
- C++ Core Integration: Implemented a high-performance C++ library for heavy lifting.

  - Auto-Layout: Optimized Fruchterman-Reingold force-directed algorithm for the relationship graph.
  
  - Text Stats Engine: C++ powered engine for rapid chapter analysis.

- Modular Architecture: Established a clean separation between the PySide6 UI, the business logic layer, and the SQLite repository.

- Theming Engine: Support for custom QSS theme files for UI styling.

### 🛠️ Developer Experience
- Documentation-as-Code: Initialized technical specs, including DB schemas and C++ Bridge API references.

- Testing Suite: Integrated pytest for repository and database connector validation.

- Build System: Added automated scripts for Sphinx documentation and C++ core compilation via make.
