# **🌉 C++ Bridge API Reference**

This document outlines the architecture for the bridge between the **Python frontend** and the **C++ Core Library (nf\_core\_lib)**.

## **1\. Architecture Overview**

Forgerly uses a modular hybrid architecture. The bridge is split into three components to 
manage a single shared library handle efficiently:

* **Core Configuration (ffi\_base.py):** Centralizes ffi.dlopen() to ensure the .dll/.so is loaded 
only once.  
* **Logic Modules (text\_stats.py, graph\_layout.py):** Use the shared ffi object to define specific 
C-structures and export clean Python functions.  
* **Core Library (C++17):** High-performance engines for graph theory and text analysis.

## **2\. Directory Structure**

```Plaintext

src/python/utils/  
├── ffi_base.py      # Shared FFI instance and DLL loading  
├── text_stats.py    # Text analysis wrapper functions  
└── graph_layout.py  # GraphLayoutEngineWrapper class

```

## **3\. Shared Data Structures**

Common structures are defined in ffi\_base.py. Module-specific structures are defined in their 
respective files via ffi.cdef().

### **Base Structures (ffi\_base.py)**

- None

### **Graph Structures (graph\_layout.py)**

* **Point:** A simple X/Y coordinate pair.

* **NodeInput / NodeOutput:** Used to pass character positions and retrieve results.  
* **EdgeInput:** Defines "spring" forces between characters.



## **4\. Exported C-API Functions**

### **Text Analysis (text\_stats.py)**

| Function | Description | Returns |
| :---- | :---- | :---- |
| calculate\_word\_count | Replicates Python .split() logic in C++. | int |
| calculate\_character\_count | Counts total bytes or non-whitespace bytes. | int |
| calculate\_read\_time | Calculates reading time string (e.g., "5 min"). | const char\* |

### **Graph Layout (graph\_layout.py)**

| Function | Description | Returns |
| :---- | :---- | :---- |
| graph\_layout\_create | Initializes a GraphLayoutEngine instance. | void\* (Handle) |
| graph\_layout\_compute | Runs the Fruchterman-Reingold iterations. | int (Status) |
| graph\_layout\_destroy | Destroys the C++ object and frees memory. | void |

### **Spell Checker (spell\_checker.py)**

| Function | Description | Returns |
| :---- | :---- | :---- |
| spell_checker_create | Initializes the C++ SpellCheckerEngine. | void* (Handle) |
| spell_checker_is_correct | Validates a word against all loaded Tries | int (Boolean) |
| spell_checker_get_suggestions | Populates a SuggestionOutput array for Python. | int (Status) |

## **5\. Memory Management & Safety**

1. **Single Load:** Never call dlopen outside of ffi\_base.py. This prevents multiple instances of 
the library from occupying memory.  
2. **Allocation:** Python must allocate memory for output arrays (e.g., NodeOutput\[\]) before 
calling C++.  
3. **Handles:** The void\* handle must be paired with graph\_layout\_destroy to prevent heap leaks. 
This is handled automatically by the GraphLayoutEngineWrapper destructor. Same is done with SpellChecker.

## **6\. Usage Examples**

### **Using Text Statistics**

```Python

from src.python.utils.text_stats import calculate_word_count

count = calculate_word_count("Sample text here")

```

### **Using Graph Layout**

```Python

from src.python.utils.graph_layout import GraphLayoutEngineWrapper

engine = GraphLayoutEngineWrapper(nodes, edges, 800, 600)  
results = engine.compute_layout()

```
