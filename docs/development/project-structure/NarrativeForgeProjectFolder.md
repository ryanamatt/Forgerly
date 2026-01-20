# Forgerly Project Structure

The project directory is designed to be self-contained, ensuring portability between different installations of the application.

## Current Structure

```Tree
MyProjectName/  
├── MyProjectName.db  
├── config/  
│   └── Project_Settings.nfp  
├── assets/  
└── exports/  
```

## Proposed Updated Structure

```Tree
MyProjectName/  
├── MyProjectName.nforge             # The primary SQLite database file  
├── .snapshots/                  # Hidden directory for C++ delta versions & backups  
├── attachments/                 # User-linked media (Maps, Character Art, Research)  
│   ├── locations/               # Images specifically for the Locations feature  
│   └── characters/              # Reference images for Character entries  
├── exports/                     # Generated output files  
│   ├── manuscripts/             # Drafts in .docx, .rtf, or .pdf format  
│   └── world_bible/             # Exported Lore, Notes, and Relationship data  
└── project_settings.json        # Project-specific UI state (e.g., last zoom level in Graph)
```

*Last Updated: 2025-12-25*
