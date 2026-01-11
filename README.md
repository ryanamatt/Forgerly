# **✍️ Narrative Forge**

Narrative Forge is a comprehensive desktop application designed to assist **authors, storytellers, and worldbuilders** in organizing and developing their fictional universes. Built using **Python** and **PySide6**, it provides dedicated tools for managing chapters, characters, lore, and the relationships between them.

![Screenshot of Narrative Forge Main Interface](docs/user/screenshots/character_editor.png)

## **🛠️ Requirements**

* **Python:** 3.14.0  
* **GUI Framework:** PySide6 6.10.1  
* **Build Tools:** C++ compiler (for core library optimization)

## **✨ Key Features**

The application provides specialized views and editors to manage all aspects of your story:

* **Chapter Management:** Outline and edit chapters.  
  * **Chapter Statistics:** The **Chapter Editor** displays real-time statistics for the active chapter, with an additional global statistics dialog for the entire story.

![Screenshot of Chapter Editor with Statistics Panel](docs/user/screenshots/project_statistics.png)

* **Character Profiles:** Create and manage detailed character profiles and biographies.  
* **Lore/Worldbuilding Editor:** Document and organize your world's history, locations, and other lore elements.  
* **Relationship Graph:** Visualize character connections through a dynamic node graph.  
  * **Custom Relationships:** Define custom RelationshipTypes and adjust relationship intensity.  
  * **High-Performance Layout:** Utilizes a custom **C++ library** implementing the **Fruchterman-Reingold** force-directed algorithm for the "Auto Layout" feature.  
  * **Precision Tools:** Toggleable background grid and "Snap to Grid" functionality for manual node organization.

![Screenshot of Relationship Graph with Node Layout and Grid enabled](docs/user/screenshots/relationship_graph.png)

* **Tagging System:** Apply tags to various entities for easy organization and filtering.  
* **Inter-Entry Lookup:** While editing a chapter, highlight text and press **Ctrl+Shift+L** to instantly view associated character or lore entries.  
* **Data Export:** Export your story data into shareable formats like Markdown or plain text.

## **💾 Project Structure**

Narrative Forge follows a modular architecture separating the GUI, business logic, and high-performance core:

narrative-forge/  
├── src/  
│   ├── c\_lib/          \# C++ Core (Graph layout & Text stats engines)  
│   ├── python/  
│   │   ├── repository/ \# Data access layer (SQLite)  
│   │   ├── services/   \# Business logic & Exporters  
│   │   ├── ui/         \# PySide6 Windows, Widgets, Menu and Dialogs  
│   │   └── utils/      \# Custom UI components (Graph, Text Editors)  
│   └── sql/            \# Database schema migrations  
├── tools/              \# Developer utility scripts  
├── styles/             \# QSS Theme files  
└── docs/               \# Technical documentation & ERDs  
└── tools/              \# Helpful Development Tools

### **Individual Project Folders**

Each user project is self-contained:

\[ProjectName\]/  
├── \[ProjectName\].db         \# SQLite Database  
├── config/                  \# Project-specific settings (.nfp)  
├── assets/                  \# Images and local media  
└── exports/                 \# Generated documents

## **🧪 Testing**

The project uses pytest for unit and integration testing of the repositories and database connectors.

To run the tests:

```Bash
python -m pytest
```

### **Documentation**

Technical specifications and project guides are maintained in the docs/ directory using a "Documentation-as-Code" approach.

#### Core Technical Specs

- [Coding Standars](docs/development/STYLE_GUIDE.md): The Style Guide for Contributing Code.

- [Database Schema](docs/SCHEMA.md): Detailed breakdown of SQLite tables, constraints, and performance indexes.

- [C++ Bridge API](docs/CPP_BRIDGE.md): Reference for the cffi layer, memory management, and C-API exports.

- [Project Standards](docs/NarrativeForgeProjectFolder.md): Specifications for the .nforge portable project directory.

#### Algorithms & Logic

- [Fruchterman-Reingold](docs/fruchterman-reingold.md): Deep-dive into the modified force-directed layout engine used for relationship graphs.

#### Project Management

- [Roadmap & TODO](docs/TODO.md): Tracking upcoming features like the C++ Delta Engine and Entity Discovery.

- [Known Bugs](docs/BUGS.md): Active issue tracking and reproduction steps.

**Build Documentation** (Sphinx):

```Bash
python tools/build_docs.py
```

**View Documentation**:

```Bash
python tools/view_docs.py
```

## **🚀 Run**

### **Installation**

1. **Clone the Repository.**  
2. **Install Dependencies:**

```Bash
pip install -r requirements.txt
```

3. Build C++ Core (Required for Auto-Layout):  
   Compile the source in src/c\_lib/ into nf\_core\_lib.dll or .so.

### **Execution**

Run the application directly from the main module:

```Bash
python -m src.python.main
```

## **📄 License**

This project is licensed under the MIT License \- see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Please review our [Code of Condcut](CODE_OF_CONDUCT.md) and the [Style Guide](docs/development/STYLE_GUIDE.md) 
before submitting a Pull Request.
