# **🗄️ Database Schema Reference**

This document provides a detailed breakdown of the SQLite schema for Narrative Forge. All data is stored in the .nforge (SQLite) project file.

## **Base Content Tables**

### **Chapters**

The primary writing unit for the manuscript.

| Column | Type | Description |
| :---- | :---- | :---- |
| ID | INTEGER | Primary Key. |
| Title | TEXT | The name of the chapter. |
| Text\_Content | TEXT | HTML/Rich Text content of the chapter. |
| Sort\_Order | INTEGER | Position in the project outline. |
| POV\_Character\_ID | FK | Link to Characters(ID) for POV tracking. |

### **Lore\_Entries**

The world-building wiki / knowledge base entries.

| Column | Type | Description |
| :---- | :---- | :---- |
| ID | INTEGER | Primary Key. |
| Title | TEXT | Unique name (e.g., "Aethelgard"). |
| Content | TEXT | The body of the lore entry. |
| Category | TEXT | e.g., 'Location', 'Magic System', 'History'. |
| Parent\_Lore\_ID | FK | Self-reference for nested entries (Cascading). |
| Sort\_Order | INTEGER | For hierarchy ordering. |

### **Characters**

Individual profiles for story actors.

| Column | Type | Description |
| :---- | :---- | :---- |
| ID | INTEGER | Primary Key. |
| Name | TEXT | Unique character name. |
| Description | TEXT | Short summary or bio. |
| Status | TEXT | e.g., 'Alive', 'Deceased', 'Major', 'Minor'. |
| Age | INTEGER | Age in years. |
| Date\_of\_Birth | TEXT | User-defined date string. |
| Occupation\_School | TEXT | Character's profession or affiliation. |
| Physical\_Description | TEXT | Detailed physical traits. |

### **Locations**

Hierarchical setting management.

| Column | Type | Description |
| :---- | :---- | :---- |
| ID | INTEGER | Primary Key. |
| Name | TEXT | Unique name of the place. |
| Description | TEXT | Description/Vibe. |
| Type | TEXT | e.g., 'City', 'Building', 'Pocket Dimension'. |
| Parent\_Location\_ID | FK | Self-reference for nesting. |

### **Notes**

Notes on Anything

| Column | Type | Description |
| :--- | :--- | :--- |
| ID | INTENGER | Primary Key. |
| Title | TEXT | Tile of Note |
| Content | TEXT | Content of Note |
| Parent_Note_ID | INTENGER | Self-reference for nested entries (Cascading) |
| Sort_Order | INTENGER | For hierarchy ordering. Default 0 |

## Auxiliary and Join Tables

### **Tags**

Global taxonomy for organizing content.

| Column | Type | Description |
| :---- | :---- | :---- |
| ID | INTEGER | Primary Key. |
| Name | TEXT | Unique tag name. |

### **Chapter\_Tags, Lore\_Tags & Note\_Tags**

Standard tagging for project organization.

| Column | Type | Description |
| :---- | :---- | :---- |
| Parent\_ID | FK | Chapter\_ID or Lore\_ID. |
| Tag\_ID | FK | Link to Tags(ID). |

### **Chapter\_Characters**

Tracks character appearances and roles within specific chapters.

| Column | Type | Description |
| :---- | :---- | :---- |
| Chapter\_ID | FK | Link to chapter. |
| Character\_ID | FK | Link to character. |
| Role\_In\_Chapter | TEXT | e.g., 'Protagonist', 'Cameo'. |

### **Chapter\_Lore & Character\_Lore**

Links entities to relevant lore references.

| Column | Type | Description |
| :---- | :---- | :---- |
| Parent\_ID | FK | Chapter\_ID or Character\_ID. |
| Lore\_ID | FK | Link to Lore\_Entries(ID). |

### **Chapter\_Locations**

The setting(s) for a chapter.

| Column | Type | Description |
| :---- | :---- | :---- |
| Chapter\_ID | FK | Link to chapter. |
| Location\_ID | FK | Link to location. |
| Is\_Primary\_Setting | INTEGER | 1 for the main setting, 0 otherwise. |

### **Lore\_Locations**

Maps lore entries to their physical origins or relevance.

| Column | Type | Description |
| :---- | :---- | :---- |
| Lore\_ID | FK | Link to lore. |
| Location\_ID | FK | Link to location. |

### **Character\_Locations**

Significant geographic ties for characters.

| Column | Type | Description |
| :---- | :---- | :---- |
| Character\_ID | FK | Link to character. |
| Location\_ID | FK | Link to location. |
| Location\_Role | TEXT | e.g., 'Hometown', 'Workplace'. |
| Is\_Primary | INTEGER | 1 for most important location. |

## Supporting Tables

### Relationship\_Types

The Types of Relationships.

| Column | Type | Description |
| :---- | :---- | :---- |
| ID | INTEGER | Primary Key |
| Type\_Name | TEXT | Friends, Rivals, etc. |
| Short_Label | TEXT | Frim Riv, etc. |
| Default_Color | TEXT | #f00FF00 |
| Is\_Directed | INTENGER | 0 mutual, 1 directed |
| Line\_Style | TEXT | Default: 'Solid' |

### **Character\_Relationships**

The "edges" of the social graph.

| Column | Type | Description |
| :---- | :---- | :---- |
| ID | INTEGER | Primary Key. |
| Character\_A\_ID | FK | Source character. |
| Character\_B\_ID | FK | Target character. |
| Type\_ID | FK | Link to Relationship\_Types. |
| Lore\_ID | FK | Link to a Lore entry describing the context. |
| Description | TEXT | Detailed notes on the relationship. |
| Intensity | INTEGER | Strength score (1-100). |
| Start\_Chapter\_ID | FK | Reference to when the bond began. |
| End\_Chapter\_ID | FK | Reference to when the bond ended. |

### **Character\_Node\_Positions**

Stores UI coordinates and styling for the Relationship Canvas.

| Column | Type | Description |
| :---- | :---- | :---- |
| Character\_ID | PK/FK | Link to Characters(ID). |
| X\_Position | FLOAT | X coordinate. |
| Y\_Position | FLOAT | Y coordinate. |
| Node\_Color | TEXT | Hex code for the node background. |
| Node\_Shape | TEXT | e.g., 'Circle', 'Square'. |
| Is\_Hidden | INTEGER | Boolean flag for visibility. |
| Is\_Locked | INTEGER | Boolean Flag for locked position. |

## **⚡ Performance Optimization (Indexes)**

To ensure smooth UI performance (especially in the Relationship Graph and Outline Managers), the following indexes are maintained:

| Index Name | Target Table | Target Column(s) | Use Case |
| :---- | :---- | :---- | :---- |
| **idx\_relationships\_a** | Character\_Relationships | Character\_A\_ID | Fast fetching of neighbors in the social graph. |
| **idx\_relationships\_b** | Character\_Relationships | Character\_B\_ID | Fast fetching of neighbors in the social graph. |
| **idx\_relationships\_type** | Character\_Relationships | Type\_ID | Filtering relationships by category or connection type. |
| **idx\_relationships\_lore** | Character\_Relationships | Lore\_ID | Mapping social connections to specific lore context. |
| **idx\_node\_positions\_char** | Character\_Node\_Positions | Character\_ID | Quick lookup of node coordinates for graph visualization. |
| **idx\_chapter\_tags\_tag** | Chapter\_Tags | Tag\_ID | Retrieving all chapters associated with a specific tag. |
| **idx\_lore\_tags\_tag** | Lore\_Tags | Tag\_ID | Retrieving all lore entries associated with a specific tag. |
| **idx\_lore\_locations\_loc** | LORE\_Locations | Location\_ID | Linking lore entries to specific geographical locations. |
| **vix\_lore\_title** | Lore\_Entries | Title | Optimized search, sorting, and lookup by entry name. |
| **idx\_lore\_category** | Lore\_Entries | Category | Quick filtering of lore entries by their classification. |
| **idx\_notes\_parent** | Notes | Parent\_Note\_ID | Efficient fetching of threaded comments or sub-notes. |
| **idx\_note\_tags\_tag** | Note\_Tags | Tag\_ID | Retrieving user notes associated with a specific tag. |
| **idx\_char\_locations\_char** | Character\_Locations | Character\_ID | Quick lookup of all locations visited by a character. |
| **idx\_char\_locations\_loc** | Character\_Locations | Location\_ID | Quick lookup of all characters present in a location. |
| **idx\_chapters\_title** | Chapters | Title | Support for search and autocomplete on chapter names. |

## **⚙️ Core Configuration**

* **Foreign Keys:** Enabled via PRAGMA foreign\_keys \= ON;.  
* **Integrity:** UNIQUE constraints are applied to Lore\_Entries(Title), Locations(Name), and Tags(Name).

*Last Updated: 2025-1-13*