# ✍️ Narrative Forge

Narrative Forge is a comprehensive desktop application designed to assist **authors, storytellers, and worldbuilders** in organizing and developing their fictional universes. Built using **Python** and **PyQt6**, it provides dedicated tools for managing chapters, characters, lore, and the relationships between them.

---

## 🛠️ Requirements

* **Python:** 3.14.0
* **GUI Framework:** PyQt6 6.10.0

---

## ✨ Key Features

The application provides specialized views and editors to manage all aspects of your story:

* **Chapter Management:** Outline and edit chapters.
* **Character Profiles:** Create and manage detailed character profiles.
* **Lore/Worldbuilding Editor:** Document and organize your world's history, locations, and other lore elements.
* **Relationship Mapping:** Define and track the connections and relationships between characters and lore.
* **Tagging System:** Apply tags to various entities for easy organization and filtering.
* **Data Export:** Export your story data into a shareable format (e.g., Markdown or text).
* **Theming:** Supports custom themes, including **Dark**, **Light**, and **Green** styles.

---

## 🚀 Run

Follow these steps to set up and run the application:

### Installation

1.**Clone the Repository** (if not already done).
2.**Install Dependencies:**

    
    pip install -r requirements.txt
    

### Execution

Run the application directly from the main module:

    
    python -m src.python.main
    


## Database

This application uses an SQLite Database to manager a project.

See Schema in docs/EntityRelationshipDiagram or Click [Here](https://dbdiagram.io/d/NarrativeForge-692603ec7d9416ddff179d8c)

## Documentation

To view documentation of code.

### Build Documentation

Will build documentation using Sphinx.

    
    python tools/build_docs.py
    

### View Documentation

    Will open documentation in web browser.

    
    python tools/view_docs.py
    
