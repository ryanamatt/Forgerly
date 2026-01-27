# Changelog
All notable changes to Forgerly will be documented in this file.

## [0.4.7] - 2026-01-26

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
